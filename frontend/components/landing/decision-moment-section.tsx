'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { CheckSquare, ShieldCheck, UserCheck } from 'lucide-react'

import { useStickyStage } from '@/hooks/use-sticky-stage'
import { Reveal } from './motion'

export function DecisionMomentSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const pinned = useStickyStage()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  })

  // Parallax only. Opacity is intentionally NOT driven by scroll here: the
  // content is pinned across the whole section, so a scroll-linked fade would
  // blank it out at the start and end of the pin. <Reveal> fades it in once.
  const headlineY = useTransform(scrollYProgress, [0, 1], [0, -70])
  const cardY = useTransform(scrollYProgress, [0, 1], [40, -20])

  const headlineStage = pinned ? { y: headlineY } : undefined
  const cardStage = pinned ? { y: cardY } : undefined

  return (
    <section
      ref={containerRef}
      className="relative bg-background border-t border-border/30 sm:h-[220vh]"
    >
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0">
        <div className="mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center">
          {/* Major Typographic Moment */}
          <motion.div style={headlineStage} className="mb-16 sm:mb-24">
            <Reveal>
              <h2 className="section-title text-foreground">
                AI assists.
                <br />
                <span className="text-gradient">Recruiter decides.</span>
              </h2>
            </Reveal>
          </motion.div>

          {/* Restrained Evaluation UI Reveal */}
          <motion.div style={cardStage} className="w-full max-w-2xl">
            <Reveal delay={0.12} className="panel overflow-hidden text-left">
            <div className="p-6 border-b border-border/70">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-muted border border-border flex items-center justify-center">
                    <UserCheck className="w-5 h-5 text-muted-foreground" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">Alex Developer</h3>
                    <p className="text-xs text-muted-foreground">Evaluation Complete</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald/10 text-emerald text-xs font-medium border border-emerald/20">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Integrity Verified
                </div>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Based on the technical interview and GitHub repository analysis, the
                candidate demonstrated strong architectural reasoning but may require
                ramping up on CI/CD pipelines.
              </p>
            </div>

            <div className="p-6 bg-surface-elevated flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <p className="text-xs font-medium text-muted-foreground">
                Review evidence and make your final decision.
              </p>
              <div className="flex gap-3">
                <button className="press px-4 py-2 rounded-full border border-border bg-surface text-sm font-medium transition-colors hover:bg-muted">
                  Reject
                </button>
                <button className="press px-4 py-2 rounded-full bg-primary text-primary-foreground text-sm font-medium flex items-center gap-2 transition-colors hover:bg-primary/90 shadow-elevation-1">
                  <CheckSquare className="w-4 h-4" />
                  Proceed to Hire
                </button>
              </div>
            </div>
            </Reveal>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
