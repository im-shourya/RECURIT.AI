'use client'

import { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  Sparkles,
  User,
  Mail,
  Hash,
  Github,
  ArrowRight,
  Check,
  Calendar,
  Brain,
  Clock,
  CheckCircle,
  X,
} from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { api, type DrivePublicResponse } from '@/lib/api'

const skills = [
  'JavaScript', 'TypeScript', 'React', 'Next.js', 'Vue.js', 'Angular',
  'Node.js', 'Python', 'Java', 'Go', 'Rust', 'C++',
  'HTML/CSS', 'Tailwind CSS', 'GraphQL', 'REST API',
  'PostgreSQL', 'MongoDB', 'Redis', 'Docker',
  'AWS', 'GCP', 'Azure', 'CI/CD',
  'UI/UX Design', 'Figma', 'Adobe XD',
  'Git', 'Agile', 'Problem Solving',
]

const domains = [
  'Frontend Development',
  'Backend Development',
  'Full Stack Development',
  'Mobile Development',
  'UI/UX Design',
  'Data Science',
  'Machine Learning',
  'DevOps',
  'Cloud Computing',
  'Cybersecurity',
]

export default function ApplyPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params)
  const [step, setStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [selectedSkills, setSelectedSkills] = useState<string[]>([])
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    regNo: '',
    primaryDomain: '',
    githubUrl: '',
  })

  const [drive, setDrive] = useState<DrivePublicResponse | null>(null)
  const [loadingDrive, setLoadingDrive] = useState(true)
  const [driveError, setDriveError] = useState('')

  useEffect(() => {
    api.getDriveForApply(token)
      .then(setDrive)
      .catch(err => setDriveError(err.message || 'Drive not found'))
      .finally(() => setLoadingDrive(false))
  }, [token])

  const updateFormData = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill)
        ? prev.filter((s) => s !== skill)
        : prev.length < 10
        ? [...prev, skill]
        : prev
    )
  }

  const canSubmit = () => {
    return (
      formData.name &&
      formData.email &&
      formData.primaryDomain &&
      selectedSkills.length >= 3 &&
      (drive?.task_type === 'task' || formData.githubUrl)
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!drive) return
    setIsSubmitting(true)

    try {
      await api.submitApplication(token, {
        name: formData.name,
        email: formData.email,
        reg_no: formData.regNo || undefined,
        skills: selectedSkills,
        primary_domain: formData.primaryDomain,
        github_url: formData.githubUrl || undefined,
      })

      setIsComplete(true)
      toast.success('Application submitted successfully!')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Submission failed'
      toast.error('Failed to submit application', { description: message })
    } finally {
      setIsSubmitting(false)
    }
  }

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

              <h1 className="text-2xl font-bold mb-2">Application Submitted!</h1>
              <p className="text-muted-foreground mb-6">
                Thank you for applying to <strong>{drive?.name}</strong> at{' '}
                <strong>{drive?.organisation_name}</strong>.
              </p>

              <div className="p-4 rounded-lg bg-muted/50 text-left mb-6">
                <h3 className="font-medium mb-2">What&apos;s Next?</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <Check className="h-4 w-4 text-emerald mt-0.5" />
                    <span>You will receive a confirmation email shortly.</span>
                  </li>
                  {drive?.task_type === 'github' ? (
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-emerald mt-0.5" />
                      <span>Your GitHub project will be analyzed by our AI.</span>
                    </li>
                  ) : (
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-emerald mt-0.5" />
                      <span>Complete your assigned task and submit before the deadline.</span>
                    </li>
                  )}
                  <li className="flex items-start gap-2">
                    <Check className="h-4 w-4 text-emerald mt-0.5" />
                    <span>You will receive an AI interview link via email.</span>
                  </li>
                </ul>
              </div>

              <Button asChild variant="outline">
                <Link href="/">
                  Back to Home
                </Link>
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  if (loadingDrive) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    )
  }

  if (driveError || !drive) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="border-border/50 bg-card/50 max-w-md w-full">
          <CardContent className="p-8 text-center">
            <X className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h1 className="text-xl font-bold mb-2">Drive Not Found</h1>
            <p className="text-muted-foreground mb-4">{driveError || 'This drive does not exist or has been closed.'}</p>
            <Button asChild variant="outline">
              <Link href="/">Back to Home</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              RECRUIT<span className="gradient-text">.AI</span>
            </span>
          </Link>
          <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20">
            {drive.organisation_name}
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
          {/* Drive Info Card */}
          <Card className="border-border/50 bg-card/50 mb-8">
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-2xl">{drive.name}</CardTitle>
                  <CardDescription className="mt-1">
                    {drive.organisation_name}
                  </CardDescription>
                </div>
                <Badge className="gradient-primary border-0">
                  {drive.domain}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {drive.task_description && (
                <p className="text-muted-foreground text-sm">{drive.task_description}</p>
              )}
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>Apply by {new Date(drive.apply_deadline).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Brain className="h-4 w-4" />
                  <span className="capitalize">{drive.question_level} level</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>5 min AI interview</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Progress Steps */}
          <div className="flex items-center justify-center gap-4 mb-8">
            {[1, 2].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-all',
                    s === step
                      ? 'gradient-primary text-white'
                      : s < step
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground'
                  )}
                >
                  {s < step ? <Check className="h-4 w-4" /> : s}
                </div>
                {s < 2 && (
                  <div className={cn('h-0.5 w-12', step > 1 ? 'bg-primary' : 'bg-muted')} />
                )}
              </div>
            ))}
          </div>

          {/* Application Form */}
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6 sm:p-8">
              <form onSubmit={handleSubmit}>
                <AnimatePresence mode="wait">
                  {step === 1 ? (
                    <motion.div
                      key="step1"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.3 }}
                      className="space-y-6"
                    >
                      <div>
                        <h2 className="text-xl font-semibold mb-1">Personal Information</h2>
                        <p className="text-muted-foreground text-sm">
                          Tell us about yourself
                        </p>
                      </div>

                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Full Name *</Label>
                          <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                              id="name"
                              placeholder="John Doe"
                              value={formData.name}
                              onChange={(e) => updateFormData('name', e.target.value)}
                              className="pl-10"
                              required
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="email">Email Address *</Label>
                          <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                              id="email"
                              type="email"
                              placeholder="john@example.com"
                              value={formData.email}
                              onChange={(e) => updateFormData('email', e.target.value)}
                              className="pl-10"
                              required
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="regNo">Registration / Roll Number</Label>
                          <div className="relative">
                            <Hash className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                              id="regNo"
                              placeholder="2024CS001"
                              value={formData.regNo}
                              onChange={(e) => updateFormData('regNo', e.target.value)}
                              className="pl-10"
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="primaryDomain">Primary Domain *</Label>
                          <Select
                            value={formData.primaryDomain}
                            onValueChange={(value) => updateFormData('primaryDomain', value)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select your primary domain" />
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

                        {drive.task_type === 'github' && (
                          <div className="space-y-2">
                            <Label htmlFor="githubUrl">GitHub Profile URL *</Label>
                            <div className="relative">
                              <Github className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                              <Input
                                id="githubUrl"
                                placeholder="https://github.com/username"
                                value={formData.githubUrl}
                                onChange={(e) => updateFormData('githubUrl', e.target.value)}
                                className="pl-10"
                                required
                              />
                            </div>
                            <p className="text-xs text-muted-foreground">
                              We will analyze your best projects using AI
                            </p>
                          </div>
                        )}
                      </div>

                      <Button
                        type="button"
                        onClick={() => setStep(2)}
                        disabled={!formData.name || !formData.email || !formData.primaryDomain || (drive.task_type === 'github' && !formData.githubUrl)}
                        className="w-full gradient-primary border-0"
                      >
                        Continue
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="step2"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.3 }}
                      className="space-y-6"
                    >
                      <div>
                        <h2 className="text-xl font-semibold mb-1">Your Skills</h2>
                        <p className="text-muted-foreground text-sm">
                          Select 3-10 skills that best describe your expertise
                        </p>
                      </div>

                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">
                            Selected: {selectedSkills.length}/10
                          </span>
                          {selectedSkills.length < 3 && (
                            <span className="text-sm text-amber">
                              Select at least 3 skills
                            </span>
                          )}
                        </div>

                        <div className="flex flex-wrap gap-2">
                          {skills.map((skill) => {
                            const isSelected = selectedSkills.includes(skill)
                            return (
                              <button
                                key={skill}
                                type="button"
                                onClick={() => toggleSkill(skill)}
                                className={cn(
                                  'px-3 py-1.5 rounded-full text-sm font-medium transition-all',
                                  isSelected
                                    ? 'gradient-primary text-white scale-105'
                                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                                )}
                              >
                                {isSelected && <Check className="inline h-3 w-3 mr-1" />}
                                {skill}
                              </button>
                            )
                          })}
                        </div>
                      </div>

                      <div className="flex gap-3">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setStep(1)}
                          className="flex-1"
                        >
                          Back
                        </Button>
                        <Button
                          type="submit"
                          disabled={!canSubmit() || isSubmitting}
                          className="flex-1 gradient-primary border-0"
                        >
                          {isSubmitting ? (
                            <Spinner className="h-4 w-4" />
                          ) : (
                            <>
                              Submit Application
                              <ArrowRight className="ml-2 h-4 w-4" />
                            </>
                          )}
                        </Button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  )
}
