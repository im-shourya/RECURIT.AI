'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { CheckSquare, ShieldCheck, UserCheck } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function DecisionMomentSection() {
  const containerRef = useRef<HTMLDivElement>(null)

  return (
    <section ref={containerRef} className="relative bg-background overflow-hidden border-t border-border/30 sm:h-[300vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center py-24 sm:py-0">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center">
          
          {/* Major Typographic Moment */}
          <div className="mb-16 sm:mb-24">
            <h2 className="section-title text-foreground">
              AI assists.<br />
              <span className="text-primary">Recruiter decides.</span>
            </h2>
          </div>

          {/* Restrained Evaluation UI Reveal */}
          <div className="w-full max-w-2xl bg-surface border border-border rounded-2xl shadow-sm overflow-hidden text-left">
            <div className="p-6 border-b border-border bg-background">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-surface border border-border flex items-center justify-center">
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
                Based on the technical interview and GitHub repository analysis, the candidate demonstrated strong architectural reasoning but may require ramping up on CI/CD pipelines.
              </p>
            </div>
            
            <div className="p-6 bg-surface flex items-center justify-between">
              <p className="text-xs font-medium text-muted-foreground">
                Review evidence and make your final decision.
              </p>
              <div className="flex gap-3">
                <button className="px-4 py-2 rounded-lg border border-border bg-background text-sm font-medium hover:bg-muted transition-colors">
                  Reject
                </button>
                <button className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium flex items-center gap-2 hover:bg-primary/90 transition-colors shadow-sm">
                  <CheckSquare className="w-4 h-4" />
                  Proceed to Hire
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
