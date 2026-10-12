'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowRight, Building2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Spinner } from '@/components/ui/spinner'
import { api, type PendingOAuthSignup } from '@/lib/api'

const PROVIDER_NAMES = { google: 'Google', github: 'GitHub' } as const

/**
 * The last step of signing up with Google or GitHub.
 *
 * The API has already verified the email address and holds it in a
 * short-lived cookie; all that is missing is the organisation's name.
 */
export default function CompleteOAuthSignupPage() {
  const router = useRouter()
  const [pending, setPending] = useState<PendingOAuthSignup | null>(null)
  const [loading, setLoading] = useState(true)
  const [orgName, setOrgName] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.getPendingOAuthSignup()
      .then(setPending)
      .catch(() => setPending(null))
      .finally(() => setLoading(false))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.completeOAuthSignup(orgName.trim())
      toast.success('Account created successfully!', { description: 'Welcome to RECRUIT.AI' })
      // A full load, so the auth context reads the new session from scratch.
      window.location.assign('/dashboard')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Sign-up failed'
      toast.error('Sign-up failed', { description: message })
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    )
  }

  if (!pending) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight">Sign-up expired</h1>
        <p className="mt-2 text-muted-foreground">
          It took too long to finish. Start again and it will only take a moment.
        </p>
        <Button className="mt-6 border-0" onClick={() => router.push('/auth/register')}>
          Back to sign-up
        </Button>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Name your organisation</h1>
        <p className="mt-2 text-muted-foreground">
          Signed in with {PROVIDER_NAMES[pending.provider] ?? pending.provider} as{' '}
          <span className="font-medium text-foreground">{pending.email}</span>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="orgName">Organization Name</Label>
          <div className="relative">
            <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              id="orgName"
              placeholder="e.g., Sparkles Ltd"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              className="pl-10"
              minLength={2}
              maxLength={255}
              required
              autoFocus
            />
          </div>
        </div>

        <Button
          type="submit"
          disabled={saving || orgName.trim().length < 2}
          className="w-full border-0 h-11"
        >
          {saving ? (
            <Spinner className="h-4 w-4" />
          ) : (
            <>
              Create organisation
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-muted-foreground">
        Not you?{' '}
        <Link href="/auth/login" className="text-primary hover:underline font-medium">
          Use a different account
        </Link>
      </p>
    </motion.div>
  )
}
