'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { KeyRound, ArrowLeft, Send } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setLoading(false)
      setSubmitted(true)
      toast.success('Recovery email sent!')
    }, 1500)
  }

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex flex-col space-y-2 text-center">
        <motion.div 
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 15 }}
          className="mx-auto bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mb-4"
        >
          <KeyRound className="h-8 w-8 text-primary" />
        </motion.div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Forgot your password?
        </h1>
        <p className="text-sm text-muted-foreground">
          Enter your email address and we will send you a recovery link.
        </p>
      </div>

      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              className="bg-muted/50"
            />
          </div>

          <Button type="submit" className="w-full gradient-primary border-0" disabled={loading}>
            {loading ? 'Sending...' : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Send Recovery Link
              </>
            )}
          </Button>
        </form>
      ) : (
        <motion.div
           initial={{ opacity: 0, y: 10 }}
           animate={{ opacity: 1, y: 0 }}
           className="text-center p-4 bg-muted/30 rounded-lg border border-border/50"
        >
          <p className="text-sm font-medium">Check your email</p>
          <p className="text-xs text-muted-foreground mt-1">
            We've sent a password recovery link to <span className="font-semibold text-foreground">{email}</span>.
          </p>
        </motion.div>
      )}

      <div className="text-center">
        <Link href="/auth/login" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary transition-colors">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to login
        </Link>
      </div>
    </div>
  )
}
