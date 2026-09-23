'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  CheckSquare,
  Download,
  FileText,
  Github,
  Mail,
  ShieldCheck,
  Trash2,
  XSquare,
} from 'lucide-react'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { Spinner } from '@/components/ui/spinner'
import { api, ApplicantResponse } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

const STATUS_LABEL: Record<string, string> = {
  applied: 'Applied',
  task_sent: 'Task sent',
  submitted: 'Submitted',
  interview_sent: 'Interview sent',
  interviewed: 'Interviewed',
  selected: 'Selected',
  rejected: 'Rejected',
}

/** Decisions are terminal — the API rejects a second one. */
const DECIDED = new Set(['selected', 'rejected'])

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="text-sm font-semibold tabular-nums">{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-[width] duration-500"
          style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
        />
      </div>
    </div>
  )
}

export default function ApplicantProfilePage() {
  const router = useRouter()
  const id = useParams().id as string
  const { can } = useAuth()

  const [applicant, setApplicant] = useState<ApplicantResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [deciding, setDeciding] = useState(false)

  const load = useCallback(async () => {
    try {
      setApplicant(await api.getApplicant(id))
    } catch (err: any) {
      toast.error('Could not load this candidate', { description: err.message })
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  const decide = async (decision: 'selected' | 'rejected') => {
    setDeciding(true)
    try {
      await api.decideApplicant(id, decision)
      toast.success(
        decision === 'selected' ? 'Candidate selected' : 'Candidate rejected',
        { description: 'They have been emailed the outcome.' },
      )
      await load()
    } catch (err: any) {
      toast.error('Could not record the decision', { description: err.message })
    } finally {
      setDeciding(false)
    }
  }

  const openSubmission = async () => {
    try {
      // The link is minted per request and expires in minutes, so it is
      // fetched on click rather than rendered into the page.
      const { url } = await api.getSubmissionFileLink(id)
      window.open(url, '_blank', 'noopener')
    } catch (err: any) {
      toast.error('Could not open the file', { description: err.message })
    }
  }

  const resend = async (type: 'applied' | 'task' | 'interview' | 'result') => {
    try {
      await api.resendEmail(id, type)
      toast.success(`${type} email re-sent`)
    } catch (err: any) {
      toast.error('Could not resend', { description: err.message })
    }
  }

  const remove = async () => {
    if (
      !confirm(
        'Permanently erase this candidate, their submission, interview and ' +
          'transcript? This cannot be undone.',
      )
    ) {
      return
    }
    try {
      await api.deleteApplicant(id)
      toast.success('Candidate erased')
      router.push('/dashboard/drives')
    } catch (err: any) {
      toast.error('Could not delete', { description: err.message })
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <Spinner className="h-8 w-8 text-primary" />
        <p className="text-muted-foreground">Loading candidate…</p>
      </div>
    )
  }

  if (!applicant) return null

  const interview = applicant.interview
  const decided = DECIDED.has(applicant.status)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-5xl"
    >
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.back()}
        className="-ml-2 text-muted-foreground"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back
      </Button>

      {/* Identity */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{applicant.name}</h1>
          <p className="text-muted-foreground mt-1">{applicant.email}</p>
          <div className="flex flex-wrap items-center gap-2 mt-3">
            <Badge variant={decided ? 'default' : 'secondary'}>
              {STATUS_LABEL[applicant.status] ?? applicant.status}
            </Badge>
            {applicant.reg_no && (
              <span className="text-xs text-muted-foreground">{applicant.reg_no}</span>
            )}
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" disabled={!can('admin')}>
              <Mail className="mr-2 h-4 w-4" />
              Resend email
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => resend('applied')}>
              Application received
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => resend('task')}>Task</DropdownMenuItem>
            <DropdownMenuItem onClick={() => resend('interview')}>
              Interview invitation
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => resend('result')} disabled={!decided}>
              Result
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Evidence */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Primary domain</p>
                  <p className="font-medium">{applicant.primary_domain || '—'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Applied</p>
                  <p className="font-medium">
                    {new Date(applicant.applied_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {applicant.skills?.length > 0 && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Skills</p>
                  <div className="flex flex-wrap gap-1.5">
                    {applicant.skills.map((skill) => (
                      <Badge key={skill} variant="secondary" className="font-normal">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {applicant.github_url && (
                <a
                  href={applicant.github_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                >
                  <Github className="h-4 w-4" />
                  {applicant.github_url.replace(/^https?:\/\//, '')}
                </a>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Submission</CardTitle>
            </CardHeader>
            <CardContent>
              {applicant.submission ? (
                <div className="space-y-3">
                  {applicant.submission.description && (
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                      {applicant.submission.description}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {applicant.submission.file_url && (
                      <Button variant="outline" size="sm" onClick={openSubmission}>
                        <Download className="mr-2 h-4 w-4" />
                        Open file
                      </Button>
                    )}
                    {applicant.submission.github_url && (
                      <Button variant="outline" size="sm" asChild>
                        <a
                          href={applicant.submission.github_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <Github className="mr-2 h-4 w-4" />
                          Repository
                        </a>
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Nothing submitted yet.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Interview</CardTitle>
            </CardHeader>
            <CardContent>
              {interview?.ended_at ? (
                <div className="space-y-5">
                  <div className="flex items-baseline gap-3">
                    <span className="text-4xl font-bold tabular-nums">
                      {interview.total_score}
                    </span>
                    <span className="text-muted-foreground">/ 100 overall</span>
                  </div>

                  <div className="space-y-3">
                    <ScoreBar label="Introduction" value={interview.score_intro} />
                    <ScoreBar label="Project" value={interview.score_project} />
                    <ScoreBar label="Domain" value={interview.score_domain} />
                  </div>

                  {interview.malpractice_flags?.length > 0 ? (
                    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
                      <p className="text-sm font-medium text-destructive">
                        {interview.malpractice_flags.length} integrity flag(s)
                      </p>
                    </div>
                  ) : (
                    <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                      <ShieldCheck className="h-4 w-4" />
                      No integrity flags raised
                    </div>
                  )}
                </div>
              ) : interview ? (
                <p className="text-sm text-muted-foreground">
                  Invited, but the interview has not been completed yet.
                </p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No interview has been scheduled.
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Decision */}
        <div>
          <Card className="md:sticky md:top-6">
            <CardHeader>
              <CardTitle className="text-base">Decision</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {decided ? (
                <>
                  <div
                    className={`rounded-lg border p-3 text-sm font-medium ${
                      applicant.status === 'selected'
                        ? 'border-emerald/30 bg-emerald/10 text-emerald'
                        : 'border-border bg-muted text-muted-foreground'
                    }`}
                  >
                    {applicant.status === 'selected'
                      ? 'Selected — the candidate has been told.'
                      : 'Rejected — the candidate has been told.'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    A decision is final. Re-send the result email from the menu
                    above if it needs to go out again.
                  </p>
                </>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">
                    {can('admin')
                      ? 'Review the evidence, then decide. The candidate is emailed the outcome immediately, and the decision cannot be undone.'
                      : 'This candidate has not been decided on yet. Deciding requires the admin role — ask an admin or the owner.'}
                  </p>
                  {can('admin') && (
                    <div className="flex flex-col gap-2">
                      <Button
                        onClick={() => decide('selected')}
                        disabled={deciding}
                        className="w-full"
                      >
                        <CheckSquare className="mr-2 h-4 w-4" />
                        Select candidate
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => decide('rejected')}
                        disabled={deciding}
                        className="w-full"
                      >
                        <XSquare className="mr-2 h-4 w-4" />
                        Reject
                      </Button>
                    </div>
                  )}
                </>
              )}

              {can('owner') && (
                <>
                  <Separator />

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={remove}
                    className="w-full text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Erase candidate data
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </motion.div>
  )
}
