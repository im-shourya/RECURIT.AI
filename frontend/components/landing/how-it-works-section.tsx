'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { Squircle } from '@/components/ui/squircle'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { User, FileText, CheckCircle, Code, MessageSquare, ShieldCheck, CheckSquare, Brain } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

// ── Presentation Components (Evidence-based UI) ───────────────────────

function MockCandidate() {
  return (
    <Card className="w-full max-w-md mx-auto shadow-xl border-border/60 bg-card/95 backdrop-blur">
      <CardContent className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-full bg-secondary/30 flex items-center justify-center flex-shrink-0">
            <User className="w-6 h-6 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-base font-semibold">Alex Developer</h3>
            <p className="text-sm text-muted-foreground mb-2">alex@example.com</p>
            <div className="flex gap-2">
              <Badge variant="outline" className="text-xs font-normal">Frontend</Badge>
              <Badge variant="outline" className="text-xs font-normal">React</Badge>
            </div>
          </div>
        </div>
        <Squircle cornerRadius={8} borderClassName="stroke-border" className="p-3 bg-card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">Resume Verified</span>
          </div>
          <CheckCircle className="w-4 h-4 text-emerald" />
        </Squircle>
      </CardContent>
    </Card>
  )
}

function MockInterviewResponses() {
  return (
    <Card className="w-full max-w-lg mx-auto shadow-xl border-border/60 bg-card/95 backdrop-blur">
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <MessageSquare className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-semibold">Interview Transcript</h3>
        </div>
        
        <div className="space-y-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Q: Architectural reasoning for custom caching layer</p>
            <Squircle cornerRadius={8} borderClassName="stroke-border/40" className="p-3 bg-card text-sm leading-relaxed opacity-80">
              "...I chose Redis because the application required cross-instance cache invalidation that the standard built-in mechanisms didn't support robustly at scale..."
            </Squircle>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Q: Handling race conditions</p>
            <Squircle cornerRadius={8} borderClassName="stroke-border/40" className="p-3 bg-card text-sm leading-relaxed opacity-80">
              "...implemented distributed locks to ensure the worker processes wouldn't duplicate the data ingestion..."
            </Squircle>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function MockEvidence() {
  return (
    <Card className="w-full max-w-md mx-auto shadow-xl border-border/60 bg-card/95 backdrop-blur">
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <ShieldCheck className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-semibold">Integrity & Evidence</h3>
        </div>
        
        <div className="space-y-3">
          <Squircle cornerRadius={8} borderClassName="stroke-border" className="flex items-start gap-3 p-3 bg-card">
            <Code className="w-4 h-4 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm font-medium">GitHub Activity</p>
              <p className="text-xs text-muted-foreground mt-1">Consistent commit history matching claimed experience.</p>
            </div>
          </Squircle>
          <Squircle cornerRadius={8} borderClassName="stroke-border" className="flex items-start gap-3 p-3 bg-card">
            <User className="w-4 h-4 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm font-medium">Identity Verification</p>
              <p className="text-xs text-muted-foreground mt-1">No anomalies detected during video evaluation.</p>
            </div>
          </Squircle>
        </div>
      </CardContent>
    </Card>
  )
}

function MockDecision() {
  return (
    <Card className="w-full max-w-md mx-auto shadow-xl border-primary/40 bg-card/95 backdrop-blur ring-1 ring-primary/20">
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <Brain className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-semibold">Final Decision</h3>
        </div>
        
        <p className="text-sm text-muted-foreground mb-6">
          Review the evidence and make your hiring decision.
        </p>

        <div className="grid grid-cols-2 gap-3">
          <Squircle cornerRadius={8} borderClassName="stroke-border" className="flex items-center justify-center p-3 bg-card text-sm font-medium hover:bg-secondary/20 cursor-pointer transition-colors">
            Reject
          </Squircle>
          <Squircle cornerRadius={8} borderClassName="stroke-primary/20" className="flex items-center justify-center gap-2 p-3 bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 cursor-pointer transition-colors">
            <CheckSquare className="w-4 h-4" />
            Proceed to Hire
          </Squircle>
        </div>
      </CardContent>
    </Card>
  )
}

// ── Scene 04 Component ───────────────────────────────────────────────

export function HowItWorksSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  // 4 steps mapping scroll progress to opacity for text
  const text1Op = useTransform(scrollYProgress, [0, 0.15, 0.25, 0.4], [1, 1, 0, 0])
  const text2Op = useTransform(scrollYProgress, [0.25, 0.4, 0.5, 0.65], [0, 1, 1, 0])
  const text3Op = useTransform(scrollYProgress, [0.5, 0.65, 0.75, 0.9], [0, 1, 1, 0])
  const text4Op = useTransform(scrollYProgress, [0.75, 0.9, 1, 1], [0, 1, 1, 1])

  // UI mapping (staggered crossfades and subtle y-translations)
  const ui1Op = useTransform(scrollYProgress, [0, 0.15, 0.25, 0.4], [1, 1, 0, 0])
  const ui1Sc = useTransform(scrollYProgress, [0, 0.25, 0.4], [1, 1, 0.95])
  const ui1Y  = useTransform(scrollYProgress, [0, 0.25, 0.4], [0, 0, -20])

  const ui2Op = useTransform(scrollYProgress, [0.25, 0.4, 0.5, 0.65], [0, 1, 1, 0])
  const ui2Sc = useTransform(scrollYProgress, [0.25, 0.4, 0.5, 0.65], [0.95, 1, 1, 0.95])
  const ui2Y  = useTransform(scrollYProgress, [0.25, 0.4, 0.5, 0.65], [20, 0, 0, -20])

  const ui3Op = useTransform(scrollYProgress, [0.5, 0.65, 0.75, 0.9], [0, 1, 1, 0])
  const ui3Sc = useTransform(scrollYProgress, [0.5, 0.65, 0.75, 0.9], [0.95, 1, 1, 0.95])
  const ui3Y  = useTransform(scrollYProgress, [0.5, 0.65, 0.75, 0.9], [20, 0, 0, -20])

  const ui4Op = useTransform(scrollYProgress, [0.75, 0.9, 1, 1], [0, 1, 1, 1])
  const ui4Sc = useTransform(scrollYProgress, [0.75, 0.9, 1, 1], [0.95, 1, 1, 1])
  const ui4Y  = useTransform(scrollYProgress, [0.75, 0.9, 1, 1], [20, 0, 0, 0])

  return (
    <section ref={containerRef} className="relative h-[400vh] bg-[#f5f5f7] dark:bg-black">
      <div className="sticky top-0 h-screen w-full flex flex-col justify-center overflow-hidden px-4 sm:px-6 lg:px-8 py-12">
        
        {/* Massive section title at the top of the viewport */}
        <div className="w-full max-w-7xl mx-auto mb-16 lg:mb-24 text-center">
          <motion.h2
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ duration: 0.8, ease: appleEase }}
            className="section-title text-foreground"
          >
            AI assists. <br className="sm:hidden" />
            Recruiter decides.
          </motion.h2>
        </div>

        <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-24 items-center">
          
          {/* Visual UI Column */}
          <div className="relative h-[300px] lg:h-[400px] w-full max-w-[500px] mx-auto flex items-center justify-center order-2 lg:order-1">
            {/* UI 1 */}
            <motion.div
              style={prefersReducedMotion ? { opacity: 1, zIndex: 10 } : { opacity: ui1Op, scale: ui1Sc, y: ui1Y, zIndex: 40 }}
              className="absolute w-full"
            >
              <MockCandidate />
            </motion.div>

            {/* UI 2 */}
            <motion.div
              style={prefersReducedMotion ? { opacity: 0, zIndex: 0 } : { opacity: ui2Op, scale: ui2Sc, y: ui2Y, zIndex: 30 }}
              className="absolute w-full"
            >
              <MockInterviewResponses />
            </motion.div>

            {/* UI 3 */}
            <motion.div
              style={prefersReducedMotion ? { opacity: 0, zIndex: 0 } : { opacity: ui3Op, scale: ui3Sc, y: ui3Y, zIndex: 20 }}
              className="absolute w-full"
            >
              <MockEvidence />
            </motion.div>

            {/* UI 4 */}
            <motion.div
              style={prefersReducedMotion ? { opacity: 0, zIndex: 0 } : { opacity: ui4Op, scale: ui4Sc, y: ui4Y, zIndex: 10 }}
              className="absolute w-full"
            >
              <MockDecision />
            </motion.div>
          </div>

          {/* Narrative Column */}
          <div className="relative h-[150px] lg:h-[300px] flex flex-col justify-center text-center lg:text-left order-1 lg:order-2">
            <motion.h3
              style={prefersReducedMotion ? { opacity: 1 } : { opacity: text1Op }}
              className="absolute inset-0 flex flex-col justify-center text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight text-foreground"
            >
              Candidate
            </motion.h3>
            <motion.h3
              style={prefersReducedMotion ? { opacity: 0 } : { opacity: text2Op }}
              className="absolute inset-0 flex flex-col justify-center text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight text-foreground"
            >
              Interview responses
            </motion.h3>
            <motion.h3
              style={prefersReducedMotion ? { opacity: 0 } : { opacity: text3Op }}
              className="absolute inset-0 flex flex-col justify-center text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight text-foreground"
            >
              Evidence
            </motion.h3>
            <motion.h3
              style={prefersReducedMotion ? { opacity: 0 } : { opacity: text4Op }}
              className="absolute inset-0 flex flex-col justify-center text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight text-primary"
            >
              Recruiter decision
            </motion.h3>
          </div>
          
        </div>
      </div>
    </section>
  )
}
