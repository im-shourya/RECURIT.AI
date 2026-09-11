'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { motion, useReducedMotion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function HeroSection() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <section className="relative min-h-[90vh] flex flex-col justify-center items-center pt-32 pb-24 px-4 sm:px-6 lg:px-8 bg-background overflow-hidden">
      <div className="w-full max-w-5xl mx-auto flex flex-col items-center text-center">
        
        {/* Eyebrow */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: appleEase }}
          className="mb-8"
        >
          <span className="eyebrow">Recruiter AI</span>
        </motion.div>

        {/* Main Headline */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 32, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.1, ease: appleEase }}
          className="mb-8"
        >
          <h1 className="hero-title text-foreground">
            Hiring,<br />rethought.
          </h1>
        </motion.div>

        {/* Sub-headline */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.2, ease: appleEase }}
          className="mb-12"
        >
          <p className="body-large text-muted-foreground text-balance max-w-2xl mx-auto">
            Create drives. Interview candidates. Evaluate with evidence.
          </p>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.3, ease: appleEase }}
        >
          <Button
            asChild
            size="lg"
            className="h-14 px-8 text-base font-medium bg-primary text-primary-foreground hover:bg-primary/90 rounded-full transition-transform active:scale-95"
          >
            <Link href="/auth/register">
              Start recruiting
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </motion.div>
      </div>
    </section>
  )
}
