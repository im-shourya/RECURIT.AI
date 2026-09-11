'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export function TrustValueSection() {
  const containerRef = useRef<HTMLDivElement>(null)

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[300vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center">
          
          <div className="flex flex-col items-center">
            {/* Value Proposition */}
            <div className="mb-8">
              <h2 className="section-title text-foreground">
                Hire smarter.<br />Interview less.
              </h2>
            </div>

            <div className="mb-12">
              <p className="body-large text-muted-foreground text-balance max-w-3xl mx-auto">
                Automate screening and technical interviews so your team can focus on the candidates who actually matter. Five minutes per candidate, not five hours.
              </p>
            </div>

            {/* Secondary Action */}
            <div>
              <Link 
                href="/#how-it-works" 
                className="inline-flex items-center text-primary font-medium hover:text-primary/80 transition-colors"
              >
                See How It Works
                <ArrowRight className="ml-1.5 h-4 w-4" />
              </Link>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
