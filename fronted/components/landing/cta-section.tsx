'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

export function CTASection() {
  return (
    <section className="py-32 lg:py-48">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className="text-center"
        >
          <h2 className="headline-display text-4xl sm:text-5xl lg:text-6xl max-w-3xl mx-auto text-balance">
            Ready to find your{' '}
            <span className="gradient-text">next great hire</span>?
          </h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="mt-6 text-lg text-muted-foreground max-w-md mx-auto"
          >
            Set up your first recruitment drive in under 5 minutes. No credit card required.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button
              asChild
              className="h-14 px-10 text-base font-semibold bg-foreground text-background hover:bg-foreground/90 rounded-full transition-all duration-200"
            >
              <Link href="/auth/register">
                Get Started Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              variant="ghost"
              className="h-14 px-6 text-base font-medium text-muted-foreground hover:text-foreground"
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
