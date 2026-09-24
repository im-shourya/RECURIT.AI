'use client'

import { useState, useEffect, useCallback, use } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import {
  Brain,
  Upload,
  File,
  Github,
  X,
  CheckCircle,
  Calendar,
  Clock,
  AlertCircle,
} from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'

export default function SubmitPage({ params }: { params: Promise<{ applicantId: string }> }) {
  const { applicantId } = use(params)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [formData, setFormData] = useState({
    githubUrl: '',
    description: '',
  })

  const [applicantName, setApplicantName] = useState('')
  const [driveName, setDriveName] = useState('')
  const [orgName, setOrgName] = useState('')
  const [taskDescription, setTaskDescription] = useState('')
  const [taskDeadline, setTaskDeadline] = useState('')
  const [loading, setLoading] = useState(true)
  const [pageError, setPageError] = useState('')

  useEffect(() => {
    // The submit page re-uses applicant info — we'll set defaults
    // The backend POST endpoint handles the submission
    setLoading(false)
  }, [applicantId])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      setFile(droppedFile)
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const removeFile = () => {
    setFile(null)
    setUploadProgress(0)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    // Show progress animation
    for (let i = 0; i <= 80; i += 10) {
      await new Promise((resolve) => setTimeout(resolve, 100))
      setUploadProgress(i)
    }

    try {
      await api.submitTask(applicantId, {
        github_url: formData.githubUrl || undefined,
        description: formData.description || undefined,
      })
      setUploadProgress(100)
      setIsComplete(true)
      toast.success('Submission uploaded successfully!')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Submission failed'
      toast.error('Submission failed', { description: message })
      setUploadProgress(0)
    } finally {
      setIsSubmitting(false)
    }
  }

  const daysRemaining = taskDeadline ? Math.ceil(
    (new Date(taskDeadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  ) : 7 // default to 7 days if no deadline

  if (isComplete) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-8 text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
                className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-emerald/10 mb-6"
              >
                <CheckCircle className="h-10 w-10 text-emerald" />
              </motion.div>

              <h1 className="text-2xl font-bold mb-2">Submission Received!</h1>
              <p className="text-muted-foreground mb-6">
                Your task submission for <strong>{driveName || 'this drive'}</strong> has been received successfully.
              </p>

              <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 mb-6">
                <div className="flex items-center justify-center gap-2 text-primary">
                  <Brain className="h-5 w-5" />
                  <span className="font-medium">AI Interview Link Coming Soon</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  You will receive an email with your AI interview link within 24 hours.
                </p>
              </div>

              <Button asChild variant="outline">
                <Link href="/">Back to Home</Link>
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-0.5">
            <span className="text-lg font-extrabold tracking-tight">
              RECRUIT<span className="text-primary">.</span>AI
            </span>
          </Link>
          <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20">
            {orgName || 'Organization'}
          </Badge>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Welcome */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold">Submit Your Task</h1>
            <p className="text-muted-foreground mt-1">
              Hello, submit your completed task for {driveName || 'this drive'}.
            </p>
          </div>

          {/* Task Info Card */}
          <Card className="border-border/50 bg-card/50 mb-8">
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>{driveName || 'Task Submission'}</CardTitle>
                  <CardDescription className="mt-1">
                    Task Assignment
                  </CardDescription>
                </div>
                <Badge
                  variant="secondary"
                  className={cn(
                    daysRemaining > 3
                      ? 'bg-emerald/10 text-emerald border-emerald/20'
                      : daysRemaining > 0
                      ? 'bg-amber/10 text-amber border-amber/20'
                      : 'bg-rose/10 text-rose border-rose/20'
                  )}
                >
                  <Clock className="mr-1 h-3 w-3" />
                  {daysRemaining > 0 ? `${daysRemaining} days left` : 'Deadline passed'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-lg bg-muted/50">
                <h3 className="font-medium mb-2">Task Description</h3>
                <p className="text-sm text-muted-foreground">{taskDescription || 'Complete the assigned task and submit your work.'}</p>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Deadline: {taskDeadline ? new Date(taskDeadline).toLocaleDateString() : 'TBD'}</span>
              </div>
            </CardContent>
          </Card>

          {/* Submission Form */}
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6 sm:p-8">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* File Upload */}
                <div className="space-y-2">
                  <Label>Upload Files</Label>
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                      'relative border-2 border-dashed rounded-xl p-8 text-center transition-all',
                      isDragging
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50',
                      file && 'border-emerald bg-emerald/5'
                    )}
                  >
                    {file ? (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-emerald/10">
                            <File className="h-6 w-6 text-emerald" />
                          </div>
                          <div className="text-left">
                            <p className="font-medium truncate max-w-[200px]">{file.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {(file.size / (1024 * 1024)).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={removeFile}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
                        <p className="font-medium">Drag and drop your files here</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          or click to browse (ZIP, PDF, up to 50MB)
                        </p>
                        <input
                          type="file"
                          onChange={handleFileChange}
                          className="absolute inset-0 opacity-0 cursor-pointer"
                          accept=".zip,.pdf,.doc,.docx"
                        />
                      </>
                    )}
                  </div>
                </div>

                {/* OR Divider */}
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-border" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card px-2 text-muted-foreground">Or</span>
                  </div>
                </div>

                {/* GitHub URL */}
                <div className="space-y-2">
                  <Label htmlFor="githubUrl">GitHub Repository URL</Label>
                  <div className="relative">
                    <Github className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="githubUrl"
                      placeholder="https://github.com/username/repo"
                      value={formData.githubUrl}
                      onChange={(e) =>
                        setFormData({ ...formData, githubUrl: e.target.value })
                      }
                      className="pl-10"
                    />
                  </div>
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">Additional Notes (Optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="Any additional information about your submission..."
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    rows={4}
                  />
                </div>

                {/* Upload Progress */}
                {isSubmitting && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                  </div>
                )}

                {/* Warning */}
                {daysRemaining <= 0 && (
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-rose/10 border border-rose/20">
                    <AlertCircle className="h-5 w-5 text-rose flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-rose">Deadline has passed</p>
                      <p className="text-sm text-muted-foreground">
                        Late submissions may not be considered.
                      </p>
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={(!file && !formData.githubUrl) || isSubmitting}
                  className="w-full gradient-primary border-0"
                >
                  {isSubmitting ? (
                    <Spinner className="h-4 w-4" />
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Submit Task
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  )
}
