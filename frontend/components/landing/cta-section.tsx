'use client'

import Link from 'next/link'
import { motion, useReducedMotion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function CTASection() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <section className="py-28 lg:py-40 relative bg-background">
      {/* Top separator */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto">
          {/* Oversized headline */}
          <motion.h2
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 28, scale: 0.97 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true, margin: '-15%' }}
            transition={{ duration: 0.8, ease: appleEase }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-foreground text-balance leading-[1.1] mb-6"
          >
            Your next great team starts here.
          </motion.h2>

          <motion.p
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ duration: 0.7, delay: 0.1, ease: appleEase }}
            className="body-text text-lg max-w-md mx-auto mb-12"
          >
            Set up your first recruitment drive in under 5 minutes. No credit card required.
          </motion.p>

          <motion.div
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-5%' }}
            transition={{ duration: 0.6, delay: 0.2, ease: appleEase }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button
              asChild
              size="lg"
              className="w-full sm:w-auto h-14 px-8 text-base font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-all rounded-lg"
            >
              <Link href="/auth/register">
                Get Started Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="w-full sm:w-auto h-14 px-8 text-base font-medium transition-all rounded-lg hover:bg-secondary/40"
            >
              <Link href="#how-it-works">
                See a Demo
              </Link>
            </Button>
          </motion.div>
        </div>
      </div>

      {/* Bottom separator */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
    </section>
  )
}
