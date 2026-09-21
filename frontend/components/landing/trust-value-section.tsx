'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

import { useStickyStage } from '@/hooks/use-sticky-stage'
import { Reveal } from './motion'

export function TrustValueSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const pinned = useStickyStage()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  })

  // Parallax only — deliberately no scroll-linked opacity. While this section
  // is pinned its copy fills the viewport the whole time, so fading it against
  // scroll progress would leave it unreadable at both ends of the pin.
  // Entrance fading is handled once, on view, by <Reveal>.
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.96])
  const y = useTransform(scrollYProgress, [0, 1], [0, -40])

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[200vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0">
        <div aria-hidden className="pointer-events-none absolute inset-0 ambient-glow opacity-40" />

        <motion.div
          style={pinned ? { scale, y } : undefined}
          className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center"
        >
          <Reveal>
            <h2 className="section-title text-foreground mb-8">
              Hire smarter.
              <br />
              Interview less.
            </h2>
          </Reveal>

          <Reveal delay={0.1}>
            <p className="body-large text-muted-foreground text-balance max-w-3xl mx-auto mb-12">
              Automate screening and technical interviews so your team can focus on the
              candidates who actually matter. Five minutes per candidate, not five hours.
            </p>
          </Reveal>

          <Reveal delay={0.18}>
            <Link
              href="/#how-it-works"
              className="group inline-flex items-center text-primary font-medium transition-colors hover:text-primary/80"
            >
              See How It Works
              <ArrowRight className="ml-1.5 h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
            </Link>
          </Reveal>
        </motion.div>
      </div>
    </section>
  )
}
