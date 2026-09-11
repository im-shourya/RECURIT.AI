'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Play } from 'lucide-react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { useRef } from 'react'

export function HeroSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  })

  // Apple-style scroll transforms
  const contentY = useTransform(scrollYProgress, [0, 1], ["0%", "25%"])
  const contentOpacity = useTransform(scrollYProgress, [0, 0.6], [1, 0])
  const contentScale = useTransform(scrollYProgress, [0, 0.8], [1, 0.92])

  // Workflow cards parallax — slightly slower scroll
  const cardsY = useTransform(scrollYProgress, [0, 1], ["0%", "15%"])
  const cardsOpacity = useTransform(scrollYProgress, [0, 0.9], [1, 0])

  // Ease curve matching Apple's motion
  const appleEase = [0.25, 0.1, 0.25, 1] as const

  return (
    <section
      ref={containerRef}
      className="relative min-h-[100vh] flex items-center justify-center pt-20 pb-16 overflow-hidden"
    >
      <motion.div
        style={prefersReducedMotion ? {} : { opacity: contentOpacity, scale: contentScale, y: contentY }}
        className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 w-full"
      >
        <div className="text-center max-w-4xl mx-auto">
          {/* Trust Badge */}
          <motion.div
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: appleEase }}
            className="flex justify-center mb-10"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-border/60 text-sm font-medium text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              Trusted by 500+ Engineering Teams
            </div>
          </motion.div>

          {/* Headline — sequential word reveal */}
          <div className="mb-8">
            <motion.h1 className="display-title">
              <motion.span
                className="inline-block"
                initial={prefersReducedMotion ? {} : { opacity: 0, y: 30, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.8, delay: 0.1, ease: appleEase }}
              >
                Hire smarter.
              </motion.span>
              <br />
              <motion.span
                className="inline-block text-muted-foreground"
                initial={prefersReducedMotion ? {} : { opacity: 0, y: 30, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.8, delay: 0.25, ease: appleEase }}
              >
                Interview less.
              </motion.span>
            </motion.h1>
          </div>

          {/* Subheadline */}
          <motion.p
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4, ease: appleEase }}
            className="mx-auto max-w-2xl text-lg sm:text-xl text-muted-foreground text-pretty leading-relaxed"
          >
            Automate screening and technical interviews so your team can focus on the candidates who actually matter. Five minutes per candidate, not five hours.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.55, ease: appleEase }}
            className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button
              asChild
              size="lg"
              className="w-full sm:w-auto h-14 px-8 text-base font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-all rounded-lg shadow-sm"
            >
              <Link href="/auth/register">
                Start Hiring Now
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="w-full sm:w-auto h-14 px-8 text-base font-medium transition-all rounded-lg hover:bg-secondary/50"
            >
              <Link href="#how-it-works" className="flex items-center gap-2">
                <Play className="h-4 w-4" />
                See How It Works
              </Link>
            </Button>
          </motion.div>
        </div>

        {/* Workflow Storytelling */}
        <motion.div
          style={prefersReducedMotion ? {} : { y: cardsY, opacity: cardsOpacity }}
          className="mt-28 relative max-w-5xl mx-auto"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                step: '01',
                title: 'Create a Drive',
                description: 'Define roles, required skills, and custom AI evaluation criteria.',
              },
              {
                step: '02',
                title: 'AI Interviews',
                description: 'Candidates take structured, adaptive technical interviews securely.',
              },
              {
                step: '03',
                title: 'Recruiter Decision',
                description: 'Review deep evaluations, transcripts, and hire with confidence.',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={prefersReducedMotion ? {} : { opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.8,
                  delay: 0.65 + (index * 0.12),
                  ease: appleEase
                }}
                className="p-8 text-left transition-all duration-300 border border-border/40 rounded-xl hover:border-primary/30 hover:-translate-y-1 bg-background"
              >
                <div className="text-sm font-mono text-primary font-bold mb-4">{item.step}</div>
                <h3 className="text-xl font-semibold text-foreground mb-3">{item.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </section>
  )
}
