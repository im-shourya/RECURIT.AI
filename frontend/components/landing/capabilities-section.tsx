'use client'

import { useRef, useState } from 'react'
import { motion, useScroll, useMotionValueEvent, useReducedMotion, AnimatePresence } from 'framer-motion'
import { Brain, Github, Video, Calculator, Link as LinkIcon, Zap } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

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
  const [activeIndex, setActiveIndex] = useState(0)

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    if (prefersReducedMotion) return
    const index = Math.min(
      capabilities.length - 1,
      Math.floor(latest * capabilities.length)
    )
    setActiveIndex(index)
  })

  const activeCap = capabilities[activeIndex]
  const ActiveIcon = activeCap.icon

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[600vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden px-4 sm:px-6 lg:px-8 py-24 sm:py-0">
        
        <div className="w-full max-w-7xl mx-auto mb-16 lg:mb-24">
          <motion.div
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ duration: 0.8, ease: appleEase }}
          >
            <h2 className="section-title text-foreground">
              Everything you need for <br className="hidden sm:block" />
              modern recruitment.
            </h2>
            <p className="body-large text-muted-foreground mt-6 max-w-2xl">
              From first application to final decision — one unified platform without the spreadsheets, friction, or guesswork.
            </p>
          </motion.div>
        </div>

        {/* Desktop Sticky Narrative */}
        <div className="hidden sm:grid w-full max-w-7xl mx-auto grid-cols-12 gap-12 items-start">
          
          {/* Index Sidebar */}
          <div className="col-span-3 flex flex-col gap-4">
            {capabilities.map((cap, i) => (
              <div 
                key={cap.id} 
                className={`text-sm font-semibold transition-colors duration-500 ${
                  activeIndex === i ? 'text-primary' : 'text-muted-foreground/40'
                }`}
              >
                {cap.id} &mdash; {cap.title}
              </div>
            ))}
          </div>

          {/* Active Description */}
          <div className="col-span-5 relative h-[200px] flex flex-col justify-start">
            <AnimatePresence mode="wait">
              <motion.div
                key={`desc-${activeCap.id}`}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.4, ease: appleEase }}
                className="absolute"
              >
                <div className="mb-4">
                  <span className="eyebrow text-primary opacity-60">{activeCap.id}</span>
                </div>
                <h3 className="text-3xl font-semibold tracking-tight text-foreground mb-4">
                  {activeCap.title}
                </h3>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  {activeCap.description}
                </p>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Visual Presentation Area */}
          <div className="col-span-4 relative h-[300px] flex items-center justify-center">
            <AnimatePresence mode="wait">
              <motion.div
                key={`visual-${activeCap.id}`}
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.985 }}
                transition={{ duration: 0.5, ease: appleEase }}
                className="absolute w-full h-full flex items-center justify-center"
              >
                <div className="w-48 h-48 rounded-2xl bg-surface border border-border flex items-center justify-center shadow-sm">
                  <ActiveIcon className="w-16 h-16 text-primary/40" />
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

        </div>

        {/* Mobile Static Narrative */}
        <div className="sm:hidden flex flex-col gap-16 w-full">
          {capabilities.map((cap) => {
            const Icon = cap.icon
            return (
              <div key={`mobile-${cap.id}`} className="flex flex-col gap-4">
                <div className="w-12 h-12 rounded-xl bg-surface border border-border flex items-center justify-center mb-2">
                  <Icon className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <span className="eyebrow text-primary opacity-60 block mb-2">{cap.id}</span>
                  <h3 className="text-2xl font-semibold tracking-tight text-foreground mb-3">{cap.title}</h3>
                  <p className="text-base text-muted-foreground leading-relaxed">
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
