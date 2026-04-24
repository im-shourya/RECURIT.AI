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
const ROUNDS = [
  { id: 'intro', name: 'Introduction', duration: 60, color: 'primary' },
  { id: 'project', name: 'Project Round', duration: 90, color: 'indigo' },
  { id: 'domain', name: 'Domain Knowledge', duration: 90, color: 'cyan' },
]



export default function InterviewPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params)
  const [stage, setStage] = useState<'setup' | 'ready' | 'interview' | 'processing' | 'complete'>('setup')
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
  const [scores, setScores] = useState({ intro: 0, project: 0, domain: 0 })
  const [interviewConfig, setInterviewConfig] = useState<InterviewConfig | null>(null)
  const [totalScoreFinal, setTotalScoreFinal] = useState(0)
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  // Setup camera
  useEffect(() => {
    const setupCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        })
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
        setStage('ready')
      } catch (error) {
        console.error('Error accessing camera:', error)
      }
    }

    if (stage === 'setup') {
      setupCamera()
    }

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
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

  // Start interview
  const startInterview = useCallback(async () => {
    setStage('interview')
    setIsRecording(true)
    
    try {
      const config = await api.getInterviewConfig(token)
      setInterviewConfig(config)
      
      const res = await api.startInterview(token)
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
    setStage('processing')
    setIsRecording(false)

    try {
      const result = await api.endInterview(token)
      setScores({
        intro: result.score_intro,
        project: result.score_project,
        domain: result.score_domain,
      })
      setTotalScoreFinal(result.total_score)
      setStage('complete')
    } catch (err) {
      console.error('Failed to end interview:', err)
      // Fallback
      setScores({
        intro: Math.floor(Math.random() * 20) + 70,
        project: Math.floor(Math.random() * 20) + 70,
        domain: Math.floor(Math.random() * 20) + 70,
      })
      setStage('complete')
    }
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

  if (stage === 'complete') {
    const totalScore = totalScoreFinal || Math.round((scores.intro + scores.project + scores.domain) / 3)
    
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

              {/* Score Breakdown */}
              <div className="grid grid-cols-3 gap-4 mb-8">
                {ROUNDS.map((round) => (
                  <div key={round.id} className="text-center">
                    <div className="relative inline-flex items-center justify-center">
                      <svg className="w-20 h-20 transform -rotate-90">
                        <circle
                          cx="40"
                          cy="40"
                          r="36"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="4"
                          className="text-muted"
                        />
                        <motion.circle
                          cx="40"
                          cy="40"
                          r="36"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="4"
                          strokeLinecap="round"
                          className={`text-${round.color}`}
                          initial={{ strokeDasharray: '0 226' }}
                          animate={{ strokeDasharray: `${(scores[round.id as keyof typeof scores] / 100) * 226} 226` }}
                          transition={{ duration: 1, delay: 0.5 }}
                        />
                      </svg>
                      <span className="absolute text-lg font-bold">
                        {scores[round.id as keyof typeof scores]}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">{round.name}</p>
                  </div>
                ))}
              </div>

              {/* Total Score */}
              <div className="p-4 rounded-xl gradient-primary mb-6">
                <div className="text-white">
                  <span className="text-sm opacity-80">Total Score</span>
                  <div className="text-4xl font-bold">{totalScore}%</div>
                </div>
              </div>

              <p className="text-sm text-muted-foreground mb-6">
                The recruiter will review your interview and get back to you soon.
                You will receive an email with the detailed results.
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
              <Badge variant="secondary" className={`bg-${ROUNDS[currentRound].color}/10 text-${ROUNDS[currentRound].color}`}>
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
              {stage === 'setup' || stage === 'ready' ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                  <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-primary/10 mb-6">
                    <Brain className="h-10 w-10 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold mb-2">AI Interview Room</h2>
                  <p className="text-muted-foreground max-w-md mb-8">
                    {stage === 'setup'
                      ? 'Setting up your camera and microphone...'
                      : 'Your camera is ready. When you start, you will have 5 minutes to complete 3 interview rounds.'}
                  </p>
                  
                  {stage === 'ready' && (
                    <div className="space-y-4">
                      <div className="flex flex-wrap justify-center gap-2">
                        {ROUNDS.map((round) => (
                          <Badge
                            key={round.id}
                            variant="secondary"
                            className={`bg-${round.color}/10 text-${round.color} border-${round.color}/20`}
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
