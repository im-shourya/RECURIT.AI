'use client'

import { use, useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  AlertCircle,
  ArrowRight,
  Check,
  Clock,
  XCircle,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { api, type ApplicantStatusView } from '@/lib/api'
import { cn } from '@/lib/utils'

/**
 * The candidate's journey, in order.
 *
 * `status` is a single value, so progress is derived by finding where that
 * value sits in this list — everything before it is done, everything after is
 * still ahead.
 */
const STEPS = [
  { key: 'applied', label: 'Application received' },
  { key: 'task_sent', label: 'Task assigned' },
  { key: 'submitted', label: 'Work submitted' },
  { key: 'interview_sent', label: 'Interview invitation sent' },
  { key: 'interviewed', label: 'Interview completed' },
] as const

const DECIDED = new Set(['selected', 'rejected'])

function stepIndex(status: string): number {
  // A decided application has been through every stage.
  if (DECIDED.has(status)) return STEPS.length
  const found = STEPS.findIndex((s) => s.key === status)
  return found === -1 ? 0 : found
}

export default function StatusPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params)

  const [view, setView] = useState<ApplicantStatusView | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .getOwnStatus(token)
      .then(setView)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : 'This link is not valid'),
      )
      .finally(() => setLoading(false))
  }, [token])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4 p-4">
        <Spinner className="h-8 w-8 text-primary" />
        <p className="text-muted-foreground">Looking up your application…</p>
      </div>
    )
  }

  if (error || !view) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-border/50">
          <CardContent className="p-8 text-center">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-5">
              <AlertCircle className="h-8 w-8 text-muted-foreground" />
            </div>
            <h1 className="text-xl font-bold mb-2">We couldn&apos;t find that application</h1>
            <p className="text-muted-foreground text-sm mb-6">
              {error || 'This link is not valid.'} Check that you copied the whole
              link from your confirmation email.
            </p>
            <Button asChild variant="outline">
              <Link href="/">Go to homepage</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const current = stepIndex(view.status)
  const decided = view.decision !== null && DECIDED.has(view.decision ?? '')
  const selected = view.decision === 'selected'

  return (
    <div className="min-h-screen bg-background p-4 py-10 sm:py-16">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mx-auto w-full max-w-lg space-y-6"
      >
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight">
            Hello, {view.name.split(' ')[0]}
          </h1>
          <p className="text-muted-foreground mt-1">
            Your application to <strong>{view.drive_name}</strong>
            {view.organisation_name ? <> at <strong>{view.organisation_name}</strong></> : null}
          </p>
        </div>

        {/* Outcome, once there is one. Scores are deliberately not shown —
            those are the recruiter's evidence, not the candidate's. */}
        {decided && (
          <Card
            className={cn(
              'border',
              selected ? 'border-emerald/40 bg-emerald/5' : 'border-border bg-muted/40',
            )}
          >
            <CardContent className="flex items-start gap-3 p-5">
              {selected ? (
                <Check className="mt-0.5 h-5 w-5 shrink-0 text-emerald" />
              ) : (
                <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
              )}
              <div>
                <p className="font-semibold">
                  {selected ? 'You have been selected' : 'Not moving forward this time'}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {selected
                    ? 'The team will be in touch with next steps by email.'
                    : 'Thank you for the time you put into this. The team has emailed you the outcome.'}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="border-border/50">
          <CardContent className="p-6 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">Progress</h2>
              <Badge variant="secondary">
                {view.status.replace(/_/g, ' ')}
              </Badge>
            </div>

            <ol className="space-y-0">
              {STEPS.map((step, index) => {
                const done = index < current
                const active = index === current && !decided

                return (
                  <li key={step.key} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <span
                        className={cn(
                          'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs',
                          done && 'border-emerald bg-emerald text-white',
                          active && 'border-primary text-primary',
                          !done && !active && 'border-border text-muted-foreground',
                        )}
                      >
                        {done ? <Check className="h-3.5 w-3.5" /> : index + 1}
                      </span>
                      {index < STEPS.length - 1 && (
                        <span
                          className={cn(
                            'w-px flex-1 min-h-[28px]',
                            done ? 'bg-emerald' : 'bg-border',
                          )}
                        />
                      )}
                    </div>
                    <div className="pb-6">
                      <p
                        className={cn(
                          'text-sm',
                          done || active ? 'font-medium' : 'text-muted-foreground',
                        )}
                      >
                        {step.label}
                      </p>
                      {active && (
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          In progress
                        </p>
                      )}
                    </div>
                  </li>
                )
              })}
            </ol>
          </CardContent>
        </Card>

        {/* The action the candidate can still take, if any. */}
        {!view.has_submitted && !decided && (
          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="flex flex-wrap items-center justify-between gap-3 p-5">
              <div>
                <p className="text-sm font-medium">You have work still to submit</p>
                {view.task_deadline && (
                  <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Clock className="h-3.5 w-3.5" />
                    Due {new Date(view.task_deadline).toLocaleDateString()}
                  </p>
                )}
              </div>
              <Button asChild size="sm">
                <Link href={`/submit/${token}`}>
                  Submit now
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}

        <p className="text-center text-xs text-muted-foreground">
          Bookmark this page — it is the only link that shows your progress.
          Applied {new Date(view.applied_at).toLocaleDateString()}.
        </p>
      </motion.div>
    </div>
  )
}
