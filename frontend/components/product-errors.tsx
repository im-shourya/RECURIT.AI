'use client'

import { motion, useReducedMotion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import {
  Brain,
  Wifi,
  Upload,
  FolderPlus,
  Users,
  RefreshCw,
  ArrowLeft,
  Mail,
  Eye,
  Play,
  type LucideIcon,
} from 'lucide-react'

// ── Base inline error component ──────────────────────────────────────

const appleEase = [0.25, 0.1, 0.25, 1] as const


interface InlineErrorProps {
  icon: LucideIcon
  title: string
  description: string
  actions: Array<{
    label: string
    onClick: () => void
    variant?: 'default' | 'outline'
    icon?: LucideIcon
  }>
  /** Additional contextual information */
  detail?: string
}

function InlineError({ icon: Icon, title, description, actions, detail }: InlineErrorProps) {
  const prefersReducedMotion = useReducedMotion()

  return (
    <motion.div
      initial={prefersReducedMotion ? {} : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: appleEase }}
      className="w-full py-16 px-6 flex flex-col items-center text-center"
      role="alert"
    >
      {/* Icon */}
      <motion.div
        initial={prefersReducedMotion ? {} : { opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, delay: 0.05, ease: appleEase }}
        className="h-12 w-12 rounded-xl bg-destructive/8 flex items-center justify-center text-destructive mb-5"
      >
        <Icon className="h-6 w-6" />
      </motion.div>

      {/* Title */}
      <motion.h3
        initial={prefersReducedMotion ? {} : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1, ease: appleEase }}
        className="text-lg font-semibold text-foreground mb-2"
      >
        {title}
      </motion.h3>

      {/* Description */}
      <motion.p
        initial={prefersReducedMotion ? {} : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.15, ease: appleEase }}
        className="text-sm text-muted-foreground leading-relaxed max-w-sm mb-2"
      >
        {description}
      </motion.p>

      {/* Detail */}
      {detail && (
        <motion.p
          initial={prefersReducedMotion ? {} : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.2, ease: appleEase }}
          className="text-xs text-muted-foreground/70 font-mono mb-6 max-w-sm truncate"
        >
          {detail}
        </motion.p>
      )}

      {!detail && <div className="mb-4" />}

      {/* Actions */}
      <motion.div
        initial={prefersReducedMotion ? {} : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.22, ease: appleEase }}
        className="flex flex-wrap items-center justify-center gap-2"
      >
        {actions.map((action, index) => {
          const ActionIcon = action.icon
          return (
            <Button
              key={action.label}
              onClick={action.onClick}
              variant={action.variant || (index === 0 ? 'default' : 'outline')}
              size="sm"
              className={
                index === 0
                  ? 'h-9 px-4 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg'
                  : 'h-9 px-4 text-sm font-medium rounded-lg hover:bg-secondary/40'
              }
            >
              {ActionIcon && <ActionIcon className="mr-1.5 h-3.5 w-3.5" />}
              {action.label}
            </Button>
          )
        })}
      </motion.div>
    </motion.div>
  )
}

// ── Product-specific error components ────────────────────────────────

/**
 * Use when an AI interview/evaluation cannot be completed.
 * Never display fabricated evaluation data.
 */
export function AIEvaluationFailed({
  onRetry,
  onReviewCandidate,
  onContactSupport,
  candidateName,
}: {
  onRetry: () => void
  onReviewCandidate?: () => void
  onContactSupport?: () => void
  candidateName?: string
}) {
  const actions = [
    { label: 'Retry evaluation', onClick: onRetry, icon: RefreshCw },
    ...(onReviewCandidate
      ? [{ label: 'Review candidate', onClick: onReviewCandidate, variant: 'outline' as const, icon: Eye }]
      : []),
    ...(onContactSupport
      ? [{ label: 'Contact support', onClick: onContactSupport, variant: 'outline' as const, icon: Mail }]
      : []),
  ]

  return (
    <InlineError
      icon={Brain}
      title="AI Evaluation Failed"
      description={
        candidateName
          ? `The evaluation for ${candidateName} could not be completed. No scores have been recorded.`
          : 'The AI evaluation could not be completed. No scores have been recorded.'
      }
      actions={actions}
    />
  )
}

/**
 * Use when an interview loses connection.
 * Preserve interview state whenever possible.
 */
export function InterviewConnectionFailed({
  onReconnect,
  onRetry,
  onResume,
}: {
  onReconnect?: () => void
  onRetry: () => void
  onResume?: () => void
}) {
  const actions = [
    ...(onReconnect
      ? [{ label: 'Reconnect', onClick: onReconnect, icon: Wifi }]
      : []),
    { label: 'Retry', onClick: onRetry, variant: (onReconnect ? 'outline' : 'default') as 'outline' | 'default', icon: RefreshCw },

    ...(onResume
      ? [{ label: 'Resume interview', onClick: onResume, variant: 'outline' as const, icon: Play }]
      : []),
  ]

  return (
    <InlineError
      icon={Wifi}
      title="Interview Connection Failed"
      description="The connection to the interview was lost. Your progress has been saved where possible."
      actions={actions}
    />
  )
}

/**
 * Use when CV/document/file upload fails.
 * Shows what failed and provides retry.
 */
export function UploadFailed({
  onRetry,
  fileName,
  reason,
}: {
  onRetry: () => void
  fileName?: string
  reason?: string
}) {
  return (
    <InlineError
      icon={Upload}
      title="Upload Failed"
      description={
        fileName
          ? `"${fileName}" could not be uploaded. ${reason || 'Please check the file and try again.'}`
          : `The file could not be uploaded. ${reason || 'Please check the file and try again.'}`
      }
      detail={fileName ? `File: ${fileName}` : undefined}
      actions={[
        { label: 'Retry upload', onClick: onRetry, icon: RefreshCw },
      ]}
    />
  )
}

/**
 * Use when drive creation fails.
 * Preserves entered information — does not force form reset.
 */
export function DriveCreationFailed({
  onRetry,
  onBack,
}: {
  onRetry: () => void
  onBack?: () => void
}) {
  const actions = [
    { label: 'Try again', onClick: onRetry, icon: RefreshCw },
    ...(onBack
      ? [{ label: 'Go back', onClick: onBack, variant: 'outline' as const, icon: ArrowLeft }]
      : []),
  ]

  return (
    <InlineError
      icon={FolderPlus}
      title="Drive Creation Failed"
      description="The recruitment drive could not be created. Your entered information has been preserved."
      actions={actions}
    />
  )
}

/**
 * Use when candidate list/profile data cannot load.
 * Does not destroy filters, pagination, or search state.
 */
export function CandidateDataLoadFailed({
  onRetry,
}: {
  onRetry: () => void
}) {
  return (
    <InlineError
      icon={Users}
      title="Could Not Load Candidates"
      description="The candidate data could not be loaded. Your current filters and search have been preserved."
      actions={[
        { label: 'Retry', onClick: onRetry, icon: RefreshCw },
      ]}
    />
  )
}
