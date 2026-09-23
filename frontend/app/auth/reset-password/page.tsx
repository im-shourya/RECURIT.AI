'use client'

import { Suspense, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { KeyRound, ArrowLeft, Check } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'

const MIN_PASSWORD_LENGTH = 8

function ResetPasswordForm() {
  const router = useRouter()
  // The token arrives in the emailed link and is never shown or edited.
  const token = useSearchParams().get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)

  const tooShort = password.length > 0 && password.length < MIN_PASSWORD_LENGTH
  const mismatch = confirm.length > 0 && password !== confirm
  const canSubmit =
    !loading && password.length >= MIN_PASSWORD_LENGTH && password === confirm

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    setLoading(true)
    try {
      await api.resetPassword({ token, new_password: password })
      toast.success('Password updated. Please sign in.')
      router.push('/auth/login')
    } catch (err: any) {
      toast.error('Could not reset your password', { description: err.message })
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="text-center p-4 bg-muted/30 rounded-lg border border-border/50">
        <p className="text-sm font-medium">This link is not valid</p>
        <p className="text-xs text-muted-foreground mt-1">
          Request a new recovery link and try again.
        </p>
        <Button asChild variant="outline" className="mt-4">
          <Link href="/auth/forgot-password">Request a new link</Link>
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="password">New password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
          aria-invalid={tooShort}
          aria-describedby="password-hint"
          className="bg-muted/50"
        />
        <p
          id="password-hint"
          className={`text-xs ${tooShort ? 'text-destructive' : 'text-muted-foreground'}`}
        >
          At least {MIN_PASSWORD_LENGTH} characters.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="confirm">Confirm new password</Label>
        <Input
          id="confirm"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
          disabled={loading}
          aria-invalid={mismatch}
          aria-describedby="confirm-hint"
          className="bg-muted/50"
        />
        {mismatch && (
          <p id="confirm-hint" className="text-xs text-destructive">
            Passwords do not match.
          </p>
        )}
      </div>

      <Button type="submit" className="w-full" disabled={!canSubmit}>
        {loading ? (
          'Updating...'
        ) : (
          <>
            <Check className="mr-2 h-4 w-4" />
            Set new password
          </>
        )}
      </Button>
    </form>
  )
}

export default function ResetPasswordPage() {
  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-col space-y-2 text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 15 }}
          className="mx-auto bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mb-4"
        >
          <KeyRound className="h-8 w-8 text-primary" />
        </motion.div>
        <h1 className="text-2xl font-semibold tracking-tight">Choose a new password</h1>
        <p className="text-sm text-muted-foreground">
          Recovery links expire one hour after they are sent.
        </p>
      </div>

      {/* useSearchParams needs a Suspense boundary to keep the route static. */}
      <Suspense fallback={<div className="h-48" aria-hidden />}>
        <ResetPasswordForm />
      </Suspense>

      <div className="text-center">
        <Link
          href="/auth/login"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-primary transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to login
        </Link>
      </div>
    </div>
  )
}
