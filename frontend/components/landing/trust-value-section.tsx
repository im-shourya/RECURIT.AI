'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export function TrustValueSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  // Fade in the text early, keep it visible, then fade out at the very end
  const opacity = useTransform(scrollYProgress, [0, 0.1, 0.9, 1], [0, 1, 1, 0])
  const y = useTransform(scrollYProgress, [0, 0.1, 0.9, 1], [40, 0, 0, -40])

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[300vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center">
          
          <motion.div
            style={prefersReducedMotion ? {} : { opacity, y }}
            className="flex flex-col items-center"
          >
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
          </motion.div>

        </div>
      </div>
    </section>
  )
}
