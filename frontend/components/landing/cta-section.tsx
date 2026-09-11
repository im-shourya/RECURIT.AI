'use client'

import { useRef } from 'react'
import Link from 'next/link'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function CTASection() {
  const containerRef = useRef<HTMLDivElement>(null)

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[200vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col items-center justify-center overflow-hidden py-32 sm:py-0">
        <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center text-center">
          
          <div className="mb-12">
            <h2 className="hero-title text-foreground tracking-tight">
              Ready to recruit with <br className="hidden sm:block" />
              more signal and less noise?
            </h2>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-6">
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
          </div>

        </div>
      </div>
    </section>
  )
}
