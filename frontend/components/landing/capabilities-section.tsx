'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { Brain, Github, Video, Calculator, Link as LinkIcon, Zap } from 'lucide-react'

const capabilities = [
  {
    id: '01',
    title: 'AI-Powered Interviews',
    description: 'Structured interviews that adapt to each candidate. Relevant questions based on their profile, projects, and experience.',
    icon: Brain
  },
  {
    id: '02',
    title: 'GitHub Integration',
    description: 'Analyze candidate repositories automatically — code quality, tech stack, commit patterns, and project complexity.',
    icon: Github
  },
  {
    id: '03',
    title: 'Video Analysis',
    description: 'Real-time integrity checks using computer vision. Face and gaze tracking catch malpractice securely and privately.',
    icon: Video
  },
  {
    id: '04',
    title: 'Smart Scoring',
    description: 'Advanced NLP evaluation across communication, technical depth, and domain knowledge. Deep, explainable metrics.',
    icon: Calculator
  },
  {
    id: '05',
    title: 'Instant Drive Links',
    description: 'Generate shareable links and QR codes for your recruitment drives. Candidates can apply in under 30 seconds.',
    icon: LinkIcon
  },
  {
    id: '06',
    title: 'Automated Workflows',
    description: 'Confirmation emails, task assignments, interview invitations, and results — all triggered automatically upon phase completion.',
    icon: Zap
  }
]

export function CapabilitiesSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  // To scroll 6 items (each takes space + gap), we move the track horizontally.
  // The exact percentage depends on the track width vs viewport width.
  // We'll move it by a conservative percentage or rely on explicit pixel units.
  // Using -80% works well for a long flex container to bring the end into view.
  const x = useTransform(scrollYProgress, [0, 1], ["0%", "-80%"])

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[400vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0 border-t border-border/30">
        
        {/* Section Header */}
        <div className="w-full px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-12 flex-shrink-0">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight text-foreground">
            Everything you need for <br className="hidden lg:block" />
            modern recruitment.
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground mt-4 max-w-2xl">
            From first application to final decision — one unified platform without the spreadsheets, friction, or guesswork.
          </p>
        </div>

        {/* Desktop Horizontal Scroll Track */}
        <div className="hidden sm:flex items-center w-full overflow-hidden">
          <motion.div 
            style={prefersReducedMotion ? {} : { x }}
            className="flex gap-8 px-4 sm:px-6 lg:px-8"
          >
            {capabilities.map((cap) => {
              const Icon = cap.icon
              return (
                <div 
                  key={cap.id} 
                  className="w-[360px] h-[380px] flex-shrink-0 bg-surface border border-border rounded-2xl shadow-sm flex flex-col p-6"
                >
                  <div className="w-14 h-14 rounded-xl bg-background border border-border flex items-center justify-center mb-6">
                    <Icon className="w-7 h-7 text-primary" />
                  </div>
                  <div className="mt-auto">
                    <span className="eyebrow text-primary opacity-60 block mb-2">{cap.id}</span>
                    <h3 className="text-xl font-semibold tracking-tight text-foreground mb-3">{cap.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {cap.description}
                    </p>
                  </div>
                </div>
              )
            })}
            {/* End Spacer */}
            <div className="w-[10vw] flex-shrink-0" />
          </motion.div>
        </div>

        {/* Mobile Static View */}
        <div className="sm:hidden flex flex-col gap-8 w-full px-4">
          {capabilities.map((cap) => {
            const Icon = cap.icon
            return (
              <div key={`mobile-${cap.id}`} className="bg-surface border border-border rounded-2xl shadow-sm p-6 flex flex-col gap-4">
                <div className="w-12 h-12 rounded-xl bg-background border border-border flex items-center justify-center">
                  <Icon className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <span className="eyebrow text-primary opacity-60 block mb-2">{cap.id}</span>
                  <h3 className="text-xl font-semibold tracking-tight text-foreground mb-3">{cap.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {cap.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}
