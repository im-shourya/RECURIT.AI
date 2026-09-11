'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight, Play, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

export function HeroSection() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center pt-24 pb-16 overflow-hidden">
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          {/* Trust Badge */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="flex justify-center mb-8"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/50 border border-border text-sm font-medium text-secondary-foreground">
              <span className="w-2 h-2 rounded-full bg-primary" />
              Trusted by 500+ Engineering Teams
            </div>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="display-title mb-6"
          >
            Hire smarter. <br />
            <span className="text-muted-foreground">Interview less.</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, filter: 'blur(4px)' }}
            animate={{ opacity: 1, filter: 'blur(0px)' }}
            transition={{ duration: 0.7, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="mx-auto mt-6 max-w-2xl text-lg sm:text-xl text-muted-foreground text-pretty leading-relaxed"
          >
            Automate screening and technical interviews so your team can focus on the candidates who actually matter. Five minutes per candidate, not five hours.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button
              asChild
              size="lg"
              className="w-full sm:w-auto h-14 px-8 text-base font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-all rounded-lg"
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
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="mt-24 relative max-w-5xl mx-auto"
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
            ].map((item) => (
              <div key={item.step} className="subtle-panel p-8 text-left transition-colors hover:border-primary/30">
                <div className="text-sm font-mono text-primary font-semibold mb-4">{item.step}</div>
                <h3 className="text-xl font-semibold text-foreground mb-3">{item.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
