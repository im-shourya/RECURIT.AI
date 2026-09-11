'use client'

import Link from 'next/link'
import { motion, useReducedMotion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import {
  AlertCircle,
  Lock,
  ShieldX,
  Search,
  Clock,
  GitBranch,
  Gauge,
  ServerCrash,
  Wifi,
  Server,
  Timer,
  ArrowLeft,
  Home,
  LogIn,
  RefreshCw,
  Mail,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

// ── Error variant configuration ──────────────────────────────────────

interface ErrorVariant {
  code: number
  title: string
  description: string
  icon?: LucideIcon
  primary: {
    label: string
    action: 'dashboard' | 'back' | 'signin' | 'retry' | 'support'
  }
  secondary?: {
    label: string
    action: 'dashboard' | 'back' | 'signin' | 'retry' | 'support'
  }
}

const errorVariants: Record<number, ErrorVariant> = {
  400: {
    code: 400,
    title: 'Bad Request',
    description: 'The request could not be processed. Please check the information and try again.',
    icon: AlertCircle,
    primary: { label: 'Try again', action: 'retry' },
    secondary: { label: 'Go back', action: 'back' },
  },
  401: {
    code: 401,
    title: 'Session Expired',
    description: 'Your session has expired. Please sign in again to continue.',
    icon: Lock,
    primary: { label: 'Sign in again', action: 'signin' },
    secondary: { label: 'Go back', action: 'back' },
  },
  403: {
    code: 403,
    title: 'Access Denied',
    description: "You don't have permission to view this page. Contact your administrator if you believe this is an error.",
    icon: ShieldX,
    primary: { label: 'Go to Dashboard', action: 'dashboard' },
    secondary: { label: 'Contact support', action: 'support' },
  },
  404: {
    code: 404,
    title: 'Page Not Found',
    description: "This page doesn't exist. It may have been moved or the link may be incorrect.",
    primary: { label: 'Go to Dashboard', action: 'dashboard' },
    secondary: { label: 'Go back', action: 'back' },
  },
  408: {
    code: 408,
    title: 'Request Timeout',
    description: 'The request took too long to complete. Please check your connection and try again.',
    icon: Clock,
    primary: { label: 'Try again', action: 'retry' },
    secondary: { label: 'Go back', action: 'back' },
  },
  409: {
    code: 409,
    title: 'Conflict',
    description: 'This action conflicts with the current state. The resource may have been modified.',
    icon: GitBranch,
    primary: { label: 'Try again', action: 'retry' },
    secondary: { label: 'Go back', action: 'back' },
  },
  429: {
    code: 429,
    title: 'Too Many Requests',
    description: 'Too many requests were made. Please wait a moment before trying again.',
    icon: Gauge,
    primary: { label: 'Try again', action: 'retry' },
    secondary: { label: 'Go back', action: 'back' },
  },
  500: {
    code: 500,
    title: 'Something Went Wrong',
    description: 'An unexpected error occurred. Our team has been notified.',
    icon: ServerCrash,
    primary: { label: 'Try again', action: 'retry' },
    secondary: { label: 'Go to Dashboard', action: 'dashboard' },
  },
  502: {
    code: 502,
    title: 'Bad Gateway',
    description: 'The service could not complete the request. Please try again in a moment.',
    icon: Wifi,
    primary: { label: 'Try again', action: 'retry' },
    secondary: { label: 'Go to Dashboard', action: 'dashboard' },
  },
  503: {
    code: 503,
    title: 'Service Unavailable',
    description: 'The service is temporarily unavailable. We are working to restore it as quickly as possible.',
    icon: Server,
    primary: { label: 'Try again', action: 'retry' },
    secondary: { label: 'Go to Dashboard', action: 'dashboard' },
  },
  504: {
    code: 504,
    title: 'Gateway Timeout',
    description: 'The service took too long to respond. Please try again shortly.',
    icon: Timer,
    primary: { label: 'Try again', action: 'retry' },
    secondary: { label: 'Go to Dashboard', action: 'dashboard' },
  },
}

// ── Action button helpers ────────────────────────────────────────────

function getActionIcon(action: string): LucideIcon {
  switch (action) {
    case 'dashboard': return Home
    case 'back': return ArrowLeft
    case 'signin': return LogIn
    case 'retry': return RefreshCw
    case 'support': return Mail
    default: return ArrowLeft
  }
}

function getActionHref(action: string): string | null {
  switch (action) {
    case 'dashboard': return '/'
    case 'signin': return '/auth/login'
    case 'support': return 'mailto:support@recuritai.shouryaparashar.in'
    default: return null
  }
}

// ── Animation config ─────────────────────────────────────────────────

const appleEase = [0.25, 0.1, 0.25, 1] as const


// ── Shared error page component ──────────────────────────────────────

interface ErrorPageProps {
  /** HTTP status code or custom error code */
  code: number
  /** Override the default title */
  title?: string
  /** Override the default description */
  description?: string
  /** Called when the user clicks "Try again" */
  onRetry?: () => void
  /** Called when the user clicks "Go back" */
  onBack?: () => void
}

export function ErrorPage({
  code,
  title,
  description,
  onRetry,
  onBack,
}: ErrorPageProps) {
  const prefersReducedMotion = useReducedMotion()
  const variant = errorVariants[code] || errorVariants[500]

  const resolvedTitle = title || variant.title
  const resolvedDescription = description || variant.description

  const Icon = variant.icon

  const handleAction = (action: string) => {
    if (action === 'retry' && onRetry) {
      onRetry()
      return
    }
    if (action === 'back') {
      if (onBack) {
        onBack()
      } else if (typeof window !== 'undefined') {
        window.history.back()
      }
      return
    }
    const href = getActionHref(action)
    if (href && typeof window !== 'undefined') {
      window.location.href = href
    }
  }

  const PrimaryIcon = getActionIcon(variant.primary.action)
  const SecondaryIcon = variant.secondary ? getActionIcon(variant.secondary.action) : null

  const primaryHref = getActionHref(variant.primary.action)
  const secondaryHref = variant.secondary ? getActionHref(variant.secondary.action) : null

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 bg-background">
      <div className="w-full max-w-lg text-center">
        {/* Error Code */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: appleEase }}
        >
          <span className="text-[8rem] sm:text-[10rem] font-bold leading-none tracking-tighter text-foreground/[0.06] select-none block">
            {variant.code}
          </span>
        </motion.div>

        {/* Icon */}
        {Icon && (
          <motion.div
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.08, ease: appleEase }}
            className="-mt-12 mb-6 flex justify-center"
          >
            <div className="h-12 w-12 rounded-xl bg-primary/8 flex items-center justify-center text-primary">
              <Icon className="h-6 w-6" />
            </div>
          </motion.div>
        )}

        {/* Title */}
        <motion.h1
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.14, ease: appleEase }}
          className="text-2xl sm:text-3xl font-semibold tracking-tight text-foreground mb-3"
        >
          {resolvedTitle}
        </motion.h1>

        {/* Description */}
        <motion.p
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2, ease: appleEase }}
          className="text-base text-muted-foreground leading-relaxed max-w-sm mx-auto mb-10"
        >
          {resolvedDescription}
        </motion.p>

        {/* Actions */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.26, ease: appleEase }}
          className="flex flex-col sm:flex-row items-center justify-center gap-3"
        >
          {/* Primary action */}
          {primaryHref && variant.primary.action !== 'retry' ? (
            <Button
              asChild
              className="w-full sm:w-auto h-11 px-6 text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg"
            >
              <Link href={primaryHref}>
                <PrimaryIcon className="mr-2 h-4 w-4" />
                {variant.primary.label}
              </Link>
            </Button>
          ) : (
            <Button
              onClick={() => handleAction(variant.primary.action)}
              className="w-full sm:w-auto h-11 px-6 text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg"
            >
              <PrimaryIcon className="mr-2 h-4 w-4" />
              {variant.primary.label}
            </Button>
          )}

          {/* Secondary action */}
          {variant.secondary && (
            secondaryHref && variant.secondary.action !== 'back' ? (
              <Button
                asChild
                variant="outline"
                className="w-full sm:w-auto h-11 px-6 text-sm font-medium rounded-lg hover:bg-secondary/40"
              >
                <Link href={secondaryHref}>
                  {SecondaryIcon && <SecondaryIcon className="mr-2 h-4 w-4" />}
                  {variant.secondary.label}
                </Link>
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => handleAction(variant.secondary!.action)}
                className="w-full sm:w-auto h-11 px-6 text-sm font-medium rounded-lg hover:bg-secondary/40"
              >
                {SecondaryIcon && <SecondaryIcon className="mr-2 h-4 w-4" />}
                {variant.secondary.label}
              </Button>
            )
          )}
        </motion.div>
      </div>
    </div>
  )
}

// ── Convenience exports ──────────────────────────────────────────────

export function Error404() {
  return <ErrorPage code={404} />
}

export function Error500({ onRetry }: { onRetry?: () => void }) {
  return <ErrorPage code={500} onRetry={onRetry} />
}

export function Error401() {
  return <ErrorPage code={401} />
}

export function Error403() {
  return <ErrorPage code={403} />
}

export function Error503() {
  return <ErrorPage code={503} />
}
