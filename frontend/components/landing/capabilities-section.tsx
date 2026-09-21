'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { Brain, Github, Video, Calculator, Link as LinkIcon, Zap } from 'lucide-react'

import { useStickyStage } from '@/hooks/use-sticky-stage'
import { Reveal } from './motion'

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
  const containerRef = useRef<HTMLElement>(null)
  const trackRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)
  const pinned = useStickyStage()

  // How far the track must travel so the last card lands flush with the right
  // edge. Measured rather than guessed — a fixed percentage over-scrolls on
  // wide monitors and leaves the last card cut off on small laptops.
  const [distance, setDistance] = useState(0)

  useEffect(() => {
    const measure = () => {
      const track = trackRef.current
      const viewport = viewportRef.current
      if (!track || !viewport) return
      setDistance(Math.max(0, track.scrollWidth - viewport.clientWidth))
    }

    measure()
    const observer = new ResizeObserver(measure)
    if (trackRef.current) observer.observe(trackRef.current)
    if (viewportRef.current) observer.observe(viewportRef.current)
    return () => observer.disconnect()
  }, [])

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  })

  const x = useTransform(scrollYProgress, [0, 1], [0, -distance])

  return (
    <section ref={containerRef} id="features" className="relative bg-background sm:h-[250vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0 border-t border-border/30">

        {/* Section Header */}
        <Reveal className="w-full px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-12 shrink-0">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight text-foreground">
            Everything you need for <br className="hidden lg:block" />
            modern recruitment.
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground mt-4 max-w-2xl">
            From first application to final decision — one unified platform without the spreadsheets, friction, or guesswork.
          </p>
        </Reveal>

        {/* Desktop Horizontal Scroll Track */}
        <div ref={viewportRef} className="hidden sm:flex items-center w-full overflow-hidden">
          <motion.div
            ref={trackRef}
            style={pinned ? { x } : undefined}
            className="flex gap-8 px-4 sm:px-6 lg:px-8"
          >
            {capabilities.map((cap) => {
              const Icon = cap.icon
              return (
                <article
                  key={cap.id}
                  className="panel lift w-[360px] h-[380px] shrink-0 flex flex-col p-8"
                >
                  <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center shrink-0">
                    <Icon className="w-7 h-7 text-primary" />
                  </div>
                  {/* Top-aligned so every card's title sits on the same baseline,
                      regardless of how long its description runs. */}
                  <div className="mt-8">
                    <span className="eyebrow text-primary/60 block mb-2">{cap.id}</span>
                    <h3 className="text-xl font-semibold tracking-tight text-foreground mb-3">{cap.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {cap.description}
                    </p>
                  </div>
                </article>
              )
            })}
          </motion.div>
        </div>

        {/* Mobile Static View */}
        <div className="sm:hidden flex flex-col gap-6 w-full px-4">
          {capabilities.map((cap) => {
            const Icon = cap.icon
            return (
              <Reveal key={`mobile-${cap.id}`}>
                <article className="panel p-6 flex flex-col gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <span className="eyebrow text-primary/60 block mb-2">{cap.id}</span>
                    <h3 className="text-xl font-semibold tracking-tight text-foreground mb-3">{cap.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {cap.description}
                    </p>
                  </div>
                </article>
              </Reveal>
            )
          })}
        </div>

      </div>
    </section>
  )
}
