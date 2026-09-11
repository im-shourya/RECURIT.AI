'use client'

import Link from 'next/link'
import { motion, useReducedMotion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function CTASection() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <section className="relative py-32 sm:py-48 lg:py-64 overflow-hidden bg-background">
      <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center text-center">
        
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 32, scale: 0.96 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: '-20%' }}
          transition={{ duration: 0.9, ease: appleEase }}
          className="mb-12"
        >
          <h2 className="hero-title text-foreground tracking-tight">
            Ready to recruit with <br className="hidden sm:block" />
            more signal and less noise?
          </h2>
        </motion.div>

        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-20%' }}
          transition={{ duration: 0.9, delay: 0.15, ease: appleEase }}
          className="flex flex-col sm:flex-row items-center gap-6"
        >
          <Button
            asChild
            size="lg"
            className="h-14 px-8 text-base font-medium bg-primary text-primary-foreground hover:bg-primary/90 rounded-full transition-transform active:scale-95"
          >
            <Link href="/auth/register">
              Start Hiring Now
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Link 
            href="/#how-it-works" 
            className="text-base font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            See How It Works
          </Link>
        </motion.div>

      </div>
    </section>
  )
}
