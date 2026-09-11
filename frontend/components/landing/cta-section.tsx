'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

export function CTASection() {
  return (
    <section className="py-24 lg:py-32 relative bg-secondary/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-10%' }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="text-center solid-panel max-w-4xl mx-auto p-12 lg:p-20"
        >
          <h2 className="section-title text-4xl sm:text-5xl max-w-2xl mx-auto text-balance mb-6">
            Your next great team starts here.
          </h2>

          <p className="body-text text-lg max-w-md mx-auto mb-10">
            Set up your first recruitment drive in under 5 minutes. No credit card required.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
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
              className="w-full sm:w-auto h-14 px-8 text-base font-medium transition-all rounded-lg hover:bg-secondary"
            >
              <Link href="#how-it-works">
                See a Demo
              </Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
