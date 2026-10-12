'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { CheckSquare, FileUp, Link as LinkIcon, Mail, UserCheck, Video } from 'lucide-react'

import { useStickyStage } from '@/hooks/use-sticky-stage'
import { Reveal } from './motion'

const capabilities = [
  {
    id: '01',
    title: 'Recorded Interviews',
    description: 'Candidates answer a structured interview in the browser while their camera records. You watch the recording and read the transcript.',
    icon: Video
  },
  {
    id: '02',
    title: 'Task Submissions',
    description: 'Candidates upload their work or share a repository from a private link, before the deadline you set.',
    icon: FileUp
  },
  {
    id: '03',
    title: 'You Choose Who Interviews',
    description: 'Nobody is interviewed automatically. A recruiter reviews the submitted work and invites the candidates worth talking to.',
    icon: UserCheck
  },
  {
    id: '04',
    title: 'Decisions in Bulk',
    description: 'Select or reject one candidate or a hundred at once. Each one is emailed the outcome, and the decision is kept in the audit trail.',
    icon: CheckSquare
  },
  {
    id: '05',
    title: 'Instant Drive Links',
    description: 'Generate shareable links and QR codes for your recruitment drives. Candidates apply without making an account.',
    icon: LinkIcon
  },
  {
    id: '06',
    title: 'Email That Arrives',
    description: 'Confirmations, tasks, interview invitations and results go through an outbox that retries until each one is delivered.',
    icon: Mail
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
