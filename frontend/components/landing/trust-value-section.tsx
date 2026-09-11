'use client'

import { motion, useReducedMotion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function TrustValueSection() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <section className="relative py-24 sm:py-32 overflow-hidden bg-background">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center">
        
        {/* Trust */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: '-10%' }}
          transition={{ duration: 0.8, ease: appleEase }}
          className="mb-32"
        >
          <p className="eyebrow opacity-50 text-muted-foreground">
            Trusted by 500+ Engineering Teams
          </p>
        </motion.div>

        {/* Value Proposition */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 32, scale: 0.96 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: '-20%' }}
          transition={{ duration: 0.9, ease: appleEase }}
          className="mb-8"
        >
          <h2 className="section-title text-foreground">
            Hire smarter.<br />Interview less.
          </h2>
        </motion.div>

        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-20%' }}
          transition={{ duration: 0.9, delay: 0.15, ease: appleEase }}
          className="mb-12"
        >
          <p className="body-large text-muted-foreground text-balance max-w-3xl mx-auto">
            Automate screening and technical interviews so your team can focus on the candidates who actually matter. Five minutes per candidate, not five hours.
          </p>
        </motion.div>

        {/* Secondary Action */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-20%' }}
          transition={{ duration: 0.9, delay: 0.25, ease: appleEase }}
        >
          <Link 
            href="/#how-it-works" 
            className="inline-flex items-center text-primary font-medium hover:text-primary/80 transition-colors"
          >
            See How It Works
            <ArrowRight className="ml-1.5 h-4 w-4" />
          </Link>
        </motion.div>

      </div>
    </section>
  )
}
