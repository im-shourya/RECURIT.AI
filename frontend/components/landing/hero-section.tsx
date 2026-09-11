'use client'

import { motion, useReducedMotion } from 'framer-motion'
import Link from 'next/link'

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function HeroSection() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <section className="relative h-screen flex flex-col justify-center items-center overflow-hidden bg-background">
      <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        
        {/* Main Title */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 32, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.9, ease: appleEase }}
          className="mb-8"
        >
          <h1 className="hero-title text-foreground">
            Hiring, <span className="text-primary">rethought.</span>
          </h1>
        </motion.div>

        {/* Subtitle */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.15, ease: appleEase }}
          className="mb-10"
        >
          <p className="body-large text-muted-foreground text-balance mx-auto max-w-2xl">
            Create drives. Interview candidates. Evaluate with evidence.
          </p>
        </motion.div>

        {/* Action */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.25, ease: appleEase }}
        >
          <Link
            href="/auth/register"
            className="inline-flex items-center justify-center h-10 px-6 rounded-full bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-transform active:scale-95 shadow-sm"
          >
            Start Recruiting
          </Link>
        </motion.div>

      </div>
    </section>
  )
}
