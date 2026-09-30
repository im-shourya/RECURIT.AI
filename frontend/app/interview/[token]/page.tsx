'use client'

import { useState, useEffect, useRef, useCallback, use } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Spinner } from '@/components/ui/spinner'
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Play,
  Square,
  AlertCircle,
  CheckCircle,

  Clock,
  User,
  Brain,
  Send,
  Volume2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { api, type InterviewConfig } from '@/lib/api'

// Interview configuration
const TOTAL_TIME = 300 // 5 minutes in seconds
// Badge classes are written out in full: Tailwind generates only the class
// names it finds in source, so a name assembled at runtime such as
// `bg-${color}/10` is never generated and renders with no colour.
const ROUNDS = [
  { id: 'intro', name: 'Introduction', duration: 60, badge: 'bg-primary/10 text-primary border-primary/20' },
  { id: 'project', name: 'Project Round', duration: 90, badge: 'bg-indigo/10 text-indigo border-indigo/20' },
  { id: 'domain', name: 'Domain Knowledge', duration: 90, badge: 'bg-cyan/10 text-cyan border-cyan/20' },
]

// Keeps a five-minute session well under the server's 200MB recording cap.
const RECORDING_BITS_PER_SECOND = 1_000_000

// webm almost everywhere; Safari only produces mp4.
const RECORDING_TYPES = [
  { mimeType: 'video/webm;codecs=vp8,opus', extension: 'webm' },
  { mimeType: 'video/webm', extension: 'webm' },
  { mimeType: 'video/mp4', extension: 'mp4' },
]

function pickRecordingType() {
  if (typeof MediaRecorder === 'undefined') return null
  return RECORDING_TYPES.find((t) => MediaRecorder.isTypeSupported(t.mimeType)) ?? null
}

export default function InterviewPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params)
  const [stage, setStage] = useState<
    'checking' | 'unavailable' | 'setup' | 'ready' | 'interview' | 'processing' | 'complete' | 'failed' | 'error'
  >('checking')
  const [currentRound, setCurrentRound] = useState(0)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [timeRemaining, setTimeRemaining] = useState(TOTAL_TIME)
  const [isRecording, setIsRecording] = useState(false)
  const [isMicOn, setIsMicOn] = useState(true)
  const [isVideoOn, setIsVideoOn] = useState(true)
  const [isAISpeaking, setIsAISpeaking] = useState(false)
  const [messages, setMessages] = useState<Array<{ role: 'ai' | 'user'; text: string }>>([])
  const [userResponse, setUserResponse] = useState('')
  const [showMalpracticeWarning, setShowMalpracticeWarning] = useState(false)
  const [endError, setEndError] = useState('')
  const [recordingSaved, setRecordingSaved] = useState<boolean | null>(null)
  const [interviewConfig, setInterviewConfig] = useState<InterviewConfig | null>(null)
  const [linkError, setLinkError] = useState('')
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const recordingExtensionRef = useRef('webm')
  // The timer and the last answer can both end the interview.
  const endingRef = useRef(false)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        recorderRef.current.stop()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  // Check the link before asking for anything. Camera and microphone access
  // is the most invasive thing this page requests, so nobody holding an
  // expired, used or mistyped link should be asked for it.
  useEffect(() => {
    let active = true

    api
      .getInterviewConfig(token)
      .then((config) => {
        if (!active) return
        setInterviewConfig(config)
        setStage('setup')
      })
      .catch((err) => {
        if (!active) return
        setLinkError(err instanceof Error ? err.message : '')
        setStage('unavailable')
      })

    return () => {
      active = false
    }
  }, [token])

  // Setup camera
  useEffect(() => {
    let active = true

    const setupCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        })
        if (!active) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
        setStage('ready')
      } catch (error) {
        if (!active) return
        console.error('Error accessing camera:', error)
        toast.error('Camera and microphone access is required for the interview.')
        setStage('error')
      }
    }

    if (stage === 'setup') {
      setupCamera()
    }

    return () => {
      active = false
    }
  }, [stage])

  // Timer
  useEffect(() => {
    let interval: NodeJS.Timeout

    if (stage === 'interview' && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            endInterview()
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }

    return () => clearInterval(interval)
  }, [stage, timeRemaining])

  // Toggle media
  const toggleMic = () => {
    if (streamRef.current) {
      const audioTrack = streamRef.current.getAudioTracks()[0]
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled
        setIsMicOn(audioTrack.enabled)
      }
    }
  }

  const toggleVideo = () => {
    if (streamRef.current) {
      const videoTrack = streamRef.current.getVideoTracks()[0]
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled
        setIsVideoOn(videoTrack.enabled)
      }
    }
  }

  // The badge follows the recorder, not the stage: if the browser cannot
  // record, the candidate must not be told that it is.
  const startRecording = () => {
    const stream = streamRef.current
    const type = pickRecordingType()
    if (!stream || !type) return

    try {
      const recorder = new MediaRecorder(stream, {
        mimeType: type.mimeType,
        videoBitsPerSecond: RECORDING_BITS_PER_SECOND,
      })
      chunksRef.current = []
      recordingExtensionRef.current = type.extension
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.onstart = () => setIsRecording(true)
      recorder.onstop = () => setIsRecording(false)
      recorder.onerror = () => setIsRecording(false)
      // Timesliced, so a crash mid-interview still leaves most of it in memory.
      recorder.start(1000)
      recorderRef.current = recorder
    } catch (err) {
      console.error('Recording could not start:', err)
    }
  }

  const stopRecording = (): Promise<Blob | null> => {
    const recorder = recorderRef.current
    if (!recorder) return Promise.resolve(null)

    const collect = () =>
      chunksRef.current.length ? new Blob(chunksRef.current, { type: recorder.mimeType }) : null

    if (recorder.state === 'inactive') return Promise.resolve(collect())
    return new Promise((resolve) => {
      recorder.addEventListener('stop', () => resolve(collect()), { once: true })
      recorder.stop()
    })
  }

  // Start interview
  const startInterview = useCallback(async () => {
    setStage('interview')
    startRecording()
    
    try {
      await api.startInterview(token)
      // Show first AI question from config or a default
      setTimeout(() => {
        setMessages([{ role: 'ai', text: "Hello! Welcome to your interview. Let's start with you telling me a bit about yourself - your background, interests, and what motivates you." }])
        setIsAISpeaking(true)
        setTimeout(() => setIsAISpeaking(false), 3000)
      }, 1000)
    } catch (err) {
      console.error('Failed to start interview:', err)
      toast.error('Failed to connect to interview server. Please refresh and try again.')
      setTimeout(() => {
        setMessages([{ role: 'ai', text: "We're having trouble connecting. Please refresh the page and try again." }])
        setIsAISpeaking(true)
        setTimeout(() => setIsAISpeaking(false), 3000)
      }, 1000)
    }
  }, [token])

  // Submit response
  const submitResponse = async () => {
    if (!userResponse.trim()) return

    setMessages((prev) => [...prev, { role: 'user', text: userResponse }])
    const currentAnswer = userResponse
    setUserResponse('')

    try {
      const roundName = ROUNDS[currentRound]?.id || 'intro'
      const lastAiMessage = messages.filter(m => m.role === 'ai').pop()?.text || ''
      
      const res = await api.submitAnswer(token, {
        question_text: lastAiMessage,
        answer_text: currentAnswer,
        round_name: roundName,
      })

      setIsAISpeaking(true)

      if (res.is_last) {
        setMessages((prev) => [
          ...prev,
          { role: 'ai', text: res.next_question || "Thank you for your responses! That concludes our interview." },
        ])
        setTimeout(() => endInterview(), 3000)
      } else {
        // Next question from API
        if (res.round_name !== roundName) {
          // Round changed
          const nextRoundIndex = ROUNDS.findIndex(r => r.id === res.round_name)
          if (nextRoundIndex >= 0) setCurrentRound(nextRoundIndex)
          setCurrentQuestion(0)
        } else {
          setCurrentQuestion(prev => prev + 1)
        }
        setMessages((prev) => [...prev, { role: 'ai', text: res.next_question }])
      }

      setTimeout(() => setIsAISpeaking(false), 2000)
    } catch (err) {
      console.error('Failed to submit answer:', err)
      toast.error('Failed to process your response. Please try again.')
      setTimeout(() => {
        setIsAISpeaking(true)
        setMessages((prev) => [
          ...prev,
          { role: 'ai', text: "Sorry, I had trouble processing that. Could you please repeat your answer?" },
        ])
        setTimeout(() => setIsAISpeaking(false), 2000)
      }, 1500)
    }
  }

  // End interview
  const endInterview = async () => {
    if (endingRef.current) return
    endingRef.current = true
    setStage('processing')
    setEndError('')

    const recording = await stopRecording()

    try {
      await api.endInterview(token)
    } catch (err) {
      const message = err instanceof Error ? err.message : ''
      // A retry after a response that was lost on the way back: the interview
      // was saved, so there is nothing left to do but finish.
      if (!/already ended/i.test(message)) {
        console.error('Failed to end interview:', err)
        setEndError(message || 'We could not save your interview.')
        setStage('failed')
        endingRef.current = false
        return
      }
    }

    // After /end, so a slow or failed upload can never cost the candidate
    // their answers.
    if (recording) {
      try {
        await api.uploadInterviewRecording(
          token,
          recording,
          `interview.${recordingExtensionRef.current}`,
        )
        setRecordingSaved(true)
      } catch (err) {
        console.error('Failed to upload recording:', err)
        setRecordingSaved(false)
      }
    }

    setStage('complete')
  }

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Calculate progress percentage
  const progressPercentage = ((TOTAL_TIME - timeRemaining) / TOTAL_TIME) * 100
  const progressColor = progressPercentage < 60 ? 'bg-cyan' : progressPercentage < 85 ? 'bg-primary' : 'bg-rose'

  if (stage === 'checking') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    )
  }

  if (stage === 'unavailable') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-border/50">
          <CardContent className="p-8 text-center">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-rose/10 mb-5">
              <AlertCircle className="h-8 w-8 text-rose" />
            </div>
            <h1 className="text-xl font-bold mb-2">This interview link cannot be used</h1>
            <p className="text-muted-foreground text-sm">
              {/* Server messages carry no trailing full stop. */}
              {(linkError || 'The link is invalid').replace(/\.?$/, '.')} If you
              think this is a mistake, reply to the email that sent you the link.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (stage === 'failed') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-border/50">
          <CardContent className="p-8 text-center">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-rose/10 mb-5">
              <AlertCircle className="h-8 w-8 text-rose" />
            </div>
            <h1 className="text-xl font-bold mb-2">Your interview has not been saved yet</h1>
            <p className="text-muted-foreground text-sm mb-6">
              {endError} Your answers are stored as you give them. Check your
              connection and try again; please do not close this page.
            </p>
            <Button onClick={endInterview}>Try again</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (stage === 'complete') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-lg"
        >
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-8 text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
                className="inline-flex items-center justify-center h-24 w-24 rounded-full bg-emerald/10 mb-6"
              >
                <CheckCircle className="h-12 w-12 text-emerald" />
              </motion.div>

              <h1 className="text-2xl font-bold mb-2">Interview Complete!</h1>
              <p className="text-muted-foreground mb-8">
                Thank you for completing your AI interview.
              </p>

              {recordingSaved === false && (
                <div className="flex items-start gap-3 p-4 rounded-lg bg-amber/10 border border-amber/20 mb-6 text-left">
                  <AlertCircle className="h-5 w-5 text-amber flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-muted-foreground">
                    Your answers were saved, but the video recording could not be uploaded.
                    The recruiter will still see your interview transcript.
                  </p>
                </div>
              )}

              <p className="text-sm text-muted-foreground mb-6">
                The recruiter will review your interview and let you know the
                outcome by email.
              </p>

              <Button variant="outline" onClick={() => window.close()}>
                Close Window
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  if (stage === 'processing') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-primary/10 mb-6">
            <Spinner className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Processing Your Interview</h2>
          <p className="text-muted-foreground">
            Our AI is analyzing your responses...
          </p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Timer Bar */}
      {stage === 'interview' && (
        <div className="sticky top-0 z-50 bg-background border-b border-border/50">
          <div className="h-1 bg-muted">
            <motion.div
              className={cn('h-full', progressColor)}
              initial={{ width: 0 }}
              animate={{ width: `${progressPercentage}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <div className="flex items-center justify-between px-4 py-2">
            <div className="flex items-center gap-4">
              <Badge variant="secondary" className={ROUNDS[currentRound].badge}>
                {ROUNDS[currentRound].name}
              </Badge>
              {isRecording && (
                <div className="flex items-center gap-2 text-rose text-sm">
                  <span className="w-2 h-2 rounded-full bg-rose animate-pulse" />
                  Recording
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className={cn(
                'font-mono font-medium',
                timeRemaining < 60 ? 'text-rose' : 'text-foreground'
              )}>
                {formatTime(timeRemaining)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Malpractice Warning */}
      <AnimatePresence>
        {showMalpracticeWarning && (
          <motion.div
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -100, opacity: 0 }}
            className="fixed top-20 left-1/2 -translate-x-1/2 z-50"
          >
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber text-black">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Please stay in frame</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:flex-row p-4 gap-4">
        {/* Video Section */}
        <div className="lg:w-2/5">
          <Card className="border-border/50 bg-card/50 h-full">
            <CardContent className="p-4 h-full flex flex-col">
              <div className="relative flex-1 rounded-lg overflow-hidden bg-muted min-h-[300px]">
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  playsInline
                  className={cn(
                    'w-full h-full object-cover',
                    !isVideoOn && 'hidden'
                  )}
                />
                {!isVideoOn && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center">
                      <User className="h-12 w-12 text-primary" />
                    </div>
                  </div>
                )}
                
                {/* AI Speaking Indicator */}
                {isAISpeaking && (
                  <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan/90 text-white text-sm">
                    <Volume2 className="h-4 w-4 animate-pulse" />
                    AI Speaking
                  </div>
                )}
              </div>

              {/* Controls */}
              <div className="flex items-center justify-center gap-4 mt-4">
                <Button
                  variant={isMicOn ? 'outline' : 'destructive'}
                  size="icon"
                  onClick={toggleMic}
                  className="h-12 w-12 rounded-full"
                >
                  {isMicOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
                </Button>
                <Button
                  variant={isVideoOn ? 'outline' : 'destructive'}
                  size="icon"
                  onClick={toggleVideo}
                  className="h-12 w-12 rounded-full"
                >
                  {isVideoOn ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
                </Button>
                {stage === 'interview' && (
                  <Button
                    variant="destructive"
                    size="icon"
                    onClick={endInterview}
                    className="h-12 w-12 rounded-full"
                  >
                    <Square className="h-5 w-5" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chat Section */}
        <div className="lg:w-3/5 flex flex-col">
          <Card className="border-border/50 bg-card/50 flex-1 flex flex-col">
            <CardContent className="p-4 flex-1 flex flex-col">
              {stage === 'setup' || stage === 'ready' || stage === 'error' ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                  <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-primary/10 mb-6">
                    <Brain className="h-10 w-10 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold mb-2">AI Interview Room</h2>
                  <p className="text-muted-foreground max-w-md mb-8">
                    {stage === 'setup'
                      ? 'Setting up your camera and microphone...'
                      : stage === 'error'
                      ? 'Camera and microphone access denied.'
                      : 'Your camera is ready. When you start, you will have 5 minutes to complete 3 interview rounds.'}
                  </p>
                  
                  {stage === 'ready' && (
                    <div className="space-y-4">
                      <div className="flex flex-wrap justify-center gap-2">
                        {ROUNDS.map((round) => (
                          <Badge
                            key={round.id}
                            variant="secondary"
                            className={round.badge}
                          >
                            {round.name} ({round.duration}s)
                          </Badge>
                        ))}
                      </div>
                      <Button
                        onClick={startInterview}
                        size="lg"
                        className="gradient-primary border-0 animate-pulse-glow"
                      >
                        <Play className="mr-2 h-5 w-5" />
                        Start Interview
                      </Button>
                    </div>
                  )}
                  
                  {stage === 'setup' && (
                    <Spinner className="h-6 w-6 text-primary" />
                  )}

                  {stage === 'error' && (
                    <div className="space-y-4">
                      <p className="text-rose-500 text-sm">
                        Please allow camera and microphone access in your browser settings to continue.
                      </p>
                      <Button
                        onClick={() => setStage('setup')}
                        variant="outline"
                      >
                        Try Again
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                    {messages.map((message, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className={cn(
                          'flex gap-3',
                          message.role === 'user' && 'flex-row-reverse'
                        )}
                      >
                        <div className={cn(
                          'h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0',
                          message.role === 'ai'
                            ? 'gradient-primary'
                            : 'bg-primary/10'
                        )}>
                          {message.role === 'ai' ? (
                            <Brain className="h-5 w-5 text-white" />
                          ) : (
                            <User className="h-5 w-5 text-primary" />
                          )}
                        </div>
                        <div className={cn(
                          'rounded-2xl px-4 py-3 max-w-[80%]',
                          message.role === 'ai'
                            ? 'bg-muted'
                            : 'gradient-primary text-white'
                        )}>
                          <p className="text-sm">{message.text}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {/* Input */}
                  <div className="flex items-center gap-2">
                    <div className="flex-1 relative">
                      <input
                        type="text"
                        value={userResponse}
                        onChange={(e) => setUserResponse(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && submitResponse()}
                        placeholder="Type your response or speak..."
                        className="w-full px-4 py-3 rounded-full bg-muted border border-border/50 focus:border-primary focus:outline-none"
                      />
                    </div>
                    <Button
                      onClick={submitResponse}
                      disabled={!userResponse.trim()}
                      size="icon"
                      className="h-12 w-12 rounded-full gradient-primary border-0"
                    >
                      <Send className="h-5 w-5" />
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
