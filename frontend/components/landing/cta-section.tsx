'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

export function CTASection() {
  return (
    <section className="py-20 lg:py-28 relative">
      {/* Subtle dot pattern background */}
      <div className="absolute inset-0 dot-pattern" />
      
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="text-center"
        >
          <h2 className="headline-display text-4xl sm:text-5xl lg:text-[56px] max-w-2xl mx-auto text-balance">
            Your next great team{' '}
            <span className="text-gradient-warm">starts here</span>.
          </h2>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, delay: 0.12, ease: [0.16, 1, 0.3, 1] }}
            className="mt-5 text-lg text-muted-foreground max-w-md mx-auto"
          >
            Set up your first recruitment drive in under 5 minutes. No credit card required.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, delay: 0.24, ease: [0.16, 1, 0.3, 1] }}
            className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-3"
          >
            <Button
              asChild
              className="h-13 px-8 text-[15px] font-semibold bg-foreground text-background hover:bg-foreground/90 rounded-full transition-all duration-200"
            >
              <Link href="/auth/register">
                Get Started Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              variant="ghost"
              className="h-13 px-5 text-[15px] font-medium text-muted-foreground hover:text-foreground"
            >
              <Link href="#how-it-works">
                See a Demo
              </Link>
            </Button>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
