'use client'

import { motion, useReducedMotion } from 'framer-motion'

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function HeroSection() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <section className="relative min-h-[90vh] flex flex-col justify-center items-center overflow-hidden bg-background">
      <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center mt-20">
        
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
          className="mb-32 lg:mb-48"
        >
          <p className="body-large text-muted-foreground text-balance mx-auto max-w-2xl">
            Create drives. Interview candidates. Evaluate with evidence.
          </p>
        </motion.div>

        {/* Value Proposition Merged into Hero */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.3, ease: appleEase }}
          className="max-w-3xl mx-auto flex flex-col gap-6"
        >
          <h2 className="section-title text-foreground">
            Hire smarter.<br />Interview less.
          </h2>
          <p className="text-lg sm:text-xl text-muted-foreground text-balance">
            Automate screening and technical interviews so your team can focus on the candidates who actually matter. Five minutes per candidate, not five hours.
          </p>
        </motion.div>
        
      </div>
    </section>
  )
}
