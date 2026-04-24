'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  FileText,
  Github,
  Calendar,
  Brain,
  Copy,
  QrCode,
  Download,
  Share2,
} from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { QRCodeSVG } from 'qrcode.react'
import { api } from '@/lib/api'

const steps = [
  { id: 1, title: 'Basic Info', description: 'Drive name and domain' },
  { id: 2, title: 'Task Setup', description: 'Task or GitHub' },
  { id: 3, title: 'Interview', description: 'Question settings' },
  { id: 4, title: 'Review', description: 'Confirm and create' },
]

const domains = [
  'Web Development',
  'Mobile Development',
  'Backend Development',
  'UI/UX Design',
  'Data Science',
  'Machine Learning',
  'DevOps',
  'Content Writing',
  'Marketing',
  'Management',
  'Other',
]

const questionLevels = ['beginner', 'intermediate', 'advanced'] as const

export default function CreateDrivePage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [generatedLink, setGeneratedLink] = useState('')
  
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    description: '',
    taskType: 'github' as 'github' | 'task',
    taskDescription: '',
    applyDeadline: '',
    taskDeadline: '',
    questionLevel: 'intermediate' as typeof questionLevels[number],
  })

  const updateFormData = (field: string, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return formData.name && formData.domain
      case 2:
        return formData.taskType && formData.applyDeadline && 
          (formData.taskType === 'github' || (formData.taskDescription && formData.taskDeadline))
      case 3:
        return formData.questionLevel
      case 4:
        return true
      default:
        return false
    }
  }

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    
    try {
      const res = await api.createDrive({
        name: formData.name,
        domain: formData.domain,
        task_type: formData.taskType,
        task_description: formData.taskDescription,
        question_level: formData.questionLevel,
        apply_deadline: formData.applyDeadline,
        task_deadline: formData.taskDeadline || null,
      })
      
      setGeneratedLink(`${window.location.origin}/apply/${res.link_token}`)
      setIsComplete(true)
      toast.success('Drive created successfully!')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create drive'
      toast.error('Failed to create drive', { description: message })
    } finally {
      setIsSubmitting(false)
    }
  }

  const copyLink = () => {
    navigator.clipboard.writeText(generatedLink)
    toast.success('Link copied to clipboard!')
  }

  if (isComplete) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl mx-auto"
      >
        <Card className="border-border/50 bg-card/50 overflow-hidden">
          <CardContent className="p-8 text-center">
            {/* Success Animation */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
              className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-emerald/10 mb-6"
            >
              <Check className="h-10 w-10 text-emerald" />
            </motion.div>

            <h1 className="text-2xl font-bold mb-2">Drive Created Successfully!</h1>
            <p className="text-muted-foreground mb-8">
              Share this link with applicants to start receiving applications.
            </p>

            {/* QR Code */}
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-white rounded-xl">
                <QRCodeSVG
                  value={generatedLink}
                  size={200}
                  bgColor="#ffffff"
                  fgColor="#7c3aed"
                  level="H"
                />
              </div>
            </div>

            {/* Link Display */}
            <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50 border border-border/50 mb-6">
              <code className="flex-1 text-sm font-mono truncate">{generatedLink}</code>
              <Button variant="ghost" size="icon" onClick={copyLink}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={copyLink} className="gradient-primary border-0">
                <Copy className="mr-2 h-4 w-4" />
                Copy Link
              </Button>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Download QR
              </Button>
              <Button variant="outline">
                <Share2 className="mr-2 h-4 w-4" />
                Share
              </Button>
            </div>

            <div className="mt-8 pt-6 border-t border-border/50">
              <Button
                variant="ghost"
                onClick={() => router.push('/dashboard/drives')}
              >
                Go to All Drives
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-3xl mx-auto"
    >
      {/* Header */}
      <div className="mb-8">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <h1 className="text-2xl font-bold">Create New Drive</h1>
        <p className="text-muted-foreground mt-1">
          Set up a new recruitment drive in a few simple steps.
        </p>
      </div>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium transition-all',
                    currentStep === step.id
                      ? 'gradient-primary text-white animate-pulse-glow'
                      : currentStep > step.id
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground'
                  )}
                >
                  {currentStep > step.id ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    step.id
                  )}
                </div>
                <div className="mt-2 text-center hidden sm:block">
                  <div className={cn(
                    'text-sm font-medium',
                    currentStep >= step.id ? 'text-foreground' : 'text-muted-foreground'
                  )}>
                    {step.title}
                  </div>
                  <div className="text-xs text-muted-foreground">{step.description}</div>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'h-0.5 w-full min-w-8 mx-2 sm:mx-4',
                    currentStep > step.id ? 'bg-primary' : 'bg-muted'
                  )}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Form Card */}
      <Card className="border-border/50 bg-card/50">
        <CardContent className="p-6 sm:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {currentStep === 1 && (
                <StepOne formData={formData} updateFormData={updateFormData} />
              )}
              {currentStep === 2 && (
                <StepTwo formData={formData} updateFormData={updateFormData} />
              )}
              {currentStep === 3 && (
                <StepThree formData={formData} updateFormData={updateFormData} />
              )}
              {currentStep === 4 && (
                <StepFour formData={formData} />
              )}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-border/50">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={currentStep === 1}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            {currentStep < 4 ? (
              <Button
                onClick={handleNext}
                disabled={!canProceed()}
                className="gradient-primary border-0"
              >
                Continue
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="gradient-primary border-0"
              >
                {isSubmitting ? (
                  <Spinner className="h-4 w-4" />
                ) : (
                  <>
                    <Check className="mr-2 h-4 w-4" />
                    Create Drive
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function StepOne({ formData, updateFormData }: {
  formData: any
  updateFormData: (field: string, value: string) => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-1">Basic Information</h2>
        <p className="text-muted-foreground text-sm">
          Enter the name and domain for your recruitment drive.
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Drive Name *</Label>
          <Input
            id="name"
            placeholder="e.g., Frontend Developer Intern"
            value={formData.name}
            onChange={(e) => updateFormData('name', e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="domain">Domain *</Label>
          <Select
            value={formData.domain}
            onValueChange={(value) => updateFormData('domain', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a domain" />
            </SelectTrigger>
            <SelectContent>
              {domains.map((domain) => (
                <SelectItem key={domain} value={domain}>
                  {domain}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description (Optional)</Label>
          <Textarea
            id="description"
            placeholder="Brief description of the role and requirements..."
            value={formData.description}
            onChange={(e) => updateFormData('description', e.target.value)}
            rows={4}
          />
        </div>
      </div>
    </div>
  )
}

function StepTwo({ formData, updateFormData }: {
  formData: any
  updateFormData: (field: string, value: string) => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-1">Task Setup</h2>
        <p className="text-muted-foreground text-sm">
          Choose how candidates will submit their work.
        </p>
      </div>

      {/* Task Type Toggle */}
      <div className="grid grid-cols-2 gap-4">
        <button
          type="button"
          onClick={() => updateFormData('taskType', 'github')}
          className={cn(
            'flex flex-col items-center gap-3 p-6 rounded-xl border-2 transition-all',
            formData.taskType === 'github'
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50'
          )}
        >
          <div className={cn(
            'p-3 rounded-lg',
            formData.taskType === 'github' ? 'bg-primary/10' : 'bg-muted'
          )}>
            <Github className={cn(
              'h-6 w-6',
              formData.taskType === 'github' ? 'text-primary' : 'text-muted-foreground'
            )} />
          </div>
          <div className="text-center">
            <div className="font-medium">GitHub Project</div>
            <div className="text-xs text-muted-foreground">
              Analyze their best repository
            </div>
          </div>
        </button>

        <button
          type="button"
          onClick={() => updateFormData('taskType', 'task')}
          className={cn(
            'flex flex-col items-center gap-3 p-6 rounded-xl border-2 transition-all',
            formData.taskType === 'task'
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50'
          )}
        >
          <div className={cn(
            'p-3 rounded-lg',
            formData.taskType === 'task' ? 'bg-primary/10' : 'bg-muted'
          )}>
            <FileText className={cn(
              'h-6 w-6',
              formData.taskType === 'task' ? 'text-primary' : 'text-muted-foreground'
            )} />
          </div>
          <div className="text-center">
            <div className="font-medium">Custom Task</div>
            <div className="text-xs text-muted-foreground">
              Assign a specific task
            </div>
          </div>
        </button>
      </div>

      {/* Conditional Fields */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="applyDeadline">
            <Calendar className="inline h-4 w-4 mr-1" />
            Application Deadline *
          </Label>
          <Input
            id="applyDeadline"
            type="date"
            value={formData.applyDeadline}
            onChange={(e) => updateFormData('applyDeadline', e.target.value)}
          />
        </div>

        {formData.taskType === 'task' && (
          <>
            <div className="space-y-2">
              <Label htmlFor="taskDescription">Task Description *</Label>
              <Textarea
                id="taskDescription"
                placeholder="Describe the task candidates need to complete..."
                value={formData.taskDescription}
                onChange={(e) => updateFormData('taskDescription', e.target.value)}
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="taskDeadline">
                <Calendar className="inline h-4 w-4 mr-1" />
                Task Submission Deadline *
              </Label>
              <Input
                id="taskDeadline"
                type="date"
                value={formData.taskDeadline}
                onChange={(e) => updateFormData('taskDeadline', e.target.value)}
              />
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function StepThree({ formData, updateFormData }: {
  formData: any
  updateFormData: (field: string, value: string) => void
}) {
  const levelIndex = questionLevels.indexOf(formData.questionLevel)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-1">Interview Settings</h2>
        <p className="text-muted-foreground text-sm">
          Configure the AI interview difficulty level.
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <Label>Question Difficulty Level</Label>
          </div>

          <div className="px-4">
            <Slider
              value={[levelIndex]}
              onValueChange={([value]) => updateFormData('questionLevel', questionLevels[value])}
              max={2}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between mt-2">
              {questionLevels.map((level) => (
                <span
                  key={level}
                  className={cn(
                    'text-sm capitalize transition-colors',
                    formData.questionLevel === level
                      ? 'text-primary font-medium'
                      : 'text-muted-foreground'
                  )}
                >
                  {level}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Level Description */}
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Brain className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h4 className="font-medium capitalize">{formData.questionLevel} Level</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  {formData.questionLevel === 'beginner' &&
                    'Basic questions covering fundamentals and introductory concepts. Suitable for freshers and those new to the domain.'}
                  {formData.questionLevel === 'intermediate' &&
                    'Moderate difficulty questions testing practical knowledge and problem-solving. Suitable for candidates with some experience.'}
                  {formData.questionLevel === 'advanced' &&
                    'Complex questions requiring in-depth knowledge and expertise. Suitable for experienced candidates and senior roles.'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Interview Preview */}
        <div className="space-y-3">
          <Label>Interview Structure</Label>
          <div className="grid gap-3">
            {[
              { round: 'Round 1', title: 'Introduction', duration: '60 sec', color: 'primary' },
              { round: 'Round 2', title: 'Project Deep-Dive', duration: '90 sec', color: 'indigo' },
              { round: 'Round 3', title: 'Domain Knowledge', duration: '90 sec', color: 'cyan' },
            ].map((item) => (
              <div
                key={item.round}
                className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-muted/30"
              >
                <div className="flex items-center gap-3">
                  <Badge variant="secondary" className={`bg-${item.color}/10 text-${item.color} border-${item.color}/20`}>
                    {item.round}
                  </Badge>
                  <span className="font-medium">{item.title}</span>
                </div>
                <span className="text-sm text-muted-foreground">{item.duration}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function StepFour({ formData }: { formData: any }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-1">Review & Confirm</h2>
        <p className="text-muted-foreground text-sm">
          Please review your drive settings before creating.
        </p>
      </div>

      <div className="space-y-4">
        {/* Summary Card */}
        <Card className="border-border/50 bg-muted/30">
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between pb-4 border-b border-border/50">
              <span className="text-muted-foreground">Drive Name</span>
              <span className="font-medium">{formData.name}</span>
            </div>
            <div className="flex items-center justify-between pb-4 border-b border-border/50">
              <span className="text-muted-foreground">Domain</span>
              <span className="font-medium">{formData.domain}</span>
            </div>
            <div className="flex items-center justify-between pb-4 border-b border-border/50">
              <span className="text-muted-foreground">Task Type</span>
              <Badge variant="secondary" className="capitalize">
                {formData.taskType === 'github' ? (
                  <>
                    <Github className="mr-1 h-3 w-3" />
                    GitHub Project
                  </>
                ) : (
                  <>
                    <FileText className="mr-1 h-3 w-3" />
                    Custom Task
                  </>
                )}
              </Badge>
            </div>
            <div className="flex items-center justify-between pb-4 border-b border-border/50">
              <span className="text-muted-foreground">Application Deadline</span>
              <span className="font-medium">
                {new Date(formData.applyDeadline).toLocaleDateString()}
              </span>
            </div>
            {formData.taskType === 'task' && formData.taskDeadline && (
              <div className="flex items-center justify-between pb-4 border-b border-border/50">
                <span className="text-muted-foreground">Task Deadline</span>
                <span className="font-medium">
                  {new Date(formData.taskDeadline).toLocaleDateString()}
                </span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Question Level</span>
              <Badge className="gradient-primary border-0 capitalize">
                <Brain className="mr-1 h-3 w-3" />
                {formData.questionLevel}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Description Preview */}
        {formData.description && (
          <div className="space-y-2">
            <Label>Description</Label>
            <p className="text-sm text-muted-foreground p-4 rounded-lg bg-muted/30">
              {formData.description}
            </p>
          </div>
        )}

        {/* Task Description Preview */}
        {formData.taskType === 'task' && formData.taskDescription && (
          <div className="space-y-2">
            <Label>Task Description</Label>
            <p className="text-sm text-muted-foreground p-4 rounded-lg bg-muted/30">
              {formData.taskDescription}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
