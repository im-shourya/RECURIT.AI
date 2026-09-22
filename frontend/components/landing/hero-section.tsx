'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight, ChevronDown } from 'lucide-react'

import { appleOut } from './motion'

export function HeroSection() {
  const prefersReducedMotion = useReducedMotion()
  const sectionRef = useRef<HTMLElement>(null)

  // The hero recedes as you scroll past it — fades and settles back slightly,
  // so the next section feels like it rises over the top of it.
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start start', 'end start'],
  })
  const opacity = useTransform(scrollYProgress, [0, 0.6], [1, 0])
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.94])
  const y = useTransform(scrollYProgress, [0, 1], [0, 60])

  const stage = prefersReducedMotion ? {} : { opacity, scale, y }

  return (
    <section
      ref={sectionRef}
      className="relative h-screen flex flex-col justify-center items-center overflow-hidden bg-background"
    >
      {/* Ambient wash behind the headline */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 ambient-glow opacity-70"
      />

      <motion.div
        style={stage}
        className="relative w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center"
      >
        {/* Main Title */}
        <motion.h1
          initial={prefersReducedMotion ? false : { opacity: 0, y: 28, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 1, ease: appleOut }}
          className="hero-title text-foreground mb-8"
        >
          Hiring, <span className="text-gradient">rethought.</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.12, ease: appleOut }}
          className="body-large text-muted-foreground text-balance mx-auto max-w-2xl mb-10"
        >
          Create drives. Interview candidates. Evaluate with evidence.
        </motion.p>

        {/* Actions */}
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.22, ease: appleOut }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6"
        >
          <Link
            href="/auth/register"
            className="press group inline-flex h-12 items-center justify-center rounded-full bg-primary px-7 text-[15px] font-medium text-primary-foreground shadow-elevation-2 transition-colors hover:bg-primary/90"
          >
            Start Recruiting
            <ArrowRight className="ml-1.5 h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/#how-it-works"
            className="text-[15px] font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            See how it works
          </Link>
        </motion.div>
      </motion.div>

      {/* Scroll cue */}
      <motion.div
        style={prefersReducedMotion ? {} : { opacity }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2"
        aria-hidden
      >
        <ChevronDown className="h-5 w-5 text-muted-foreground animate-scroll-cue" />
      </motion.div>
    </section>
  )
}
