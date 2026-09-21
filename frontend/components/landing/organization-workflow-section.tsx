'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { Building2, FolderPlus, Share2, Brain, CheckSquare, ArrowRight } from 'lucide-react'

import { useStickyStage } from '@/hooks/use-sticky-stage'
import { Reveal } from './motion'

const steps = [
  { id: '01', title: 'Create Account', desc: 'Set up your organization profile securely.', icon: Building2 },
  { id: '02', title: 'Create Drive', desc: 'Define roles, required skills, and deadlines.', icon: FolderPlus },
  { id: '03', title: 'Share Link', desc: 'Distribute the unique drive link to candidates.', icon: Share2 },
  { id: '04', title: 'AI Evaluates', desc: 'AI conducts adaptive interviews automatically.', icon: Brain },
  { id: '05', title: 'Review & Hire', desc: 'Review deep evaluations and make final decisions.', icon: CheckSquare },
]

export function OrganizationWorkflowSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const trackRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)
  const pinned = useStickyStage()

  // Measured travel distance, so the final step always lands flush with the
  // right edge regardless of viewport width.
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
    offset: ["start start", "end end"]
  })

  const x = useTransform(scrollYProgress, [0, 1], [0, -distance])

  return (
    <section ref={containerRef} id="trusted" className="relative bg-background sm:h-[220vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0 border-t border-border/30">
        
        {/* Section Header */}
        <Reveal className="w-full px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-16 lg:mb-24 shrink-0">
          <span className="eyebrow text-muted-foreground/70 mb-4 block">For Organizations</span>
          <h2 className="section-title text-foreground">
            The Recruiter Journey
          </h2>
        </Reveal>

        {/* Desktop Horizontal Scroll Track */}
        <div ref={viewportRef} className="hidden sm:flex items-center w-full overflow-hidden">
          <motion.div
            ref={trackRef}
            style={pinned ? { x } : undefined}
            className="flex items-center gap-12 px-4 sm:px-6 lg:px-8"
          >
            {steps.map((step, index) => {
              const Icon = step.icon
              const isLast = index === steps.length - 1

              return (
                <div key={step.id} className="flex items-center gap-12 shrink-0">
                  <div className="panel w-[320px] h-[360px] p-8 flex flex-col justify-between relative group overflow-hidden">
                    <div className="absolute inset-0 bg-primary/5 translate-y-full group-hover:translate-y-0 transition-transform duration-500 ease-out" />

                    <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center relative z-10">
                      <Icon className="w-8 h-8 text-primary" />
                    </div>
                    
                    <div className="relative z-10">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                          {step.id}
                        </span>
                        <h3 className="text-xl font-semibold tracking-tight text-foreground">{step.title}</h3>
                      </div>
                      <p className="text-base text-muted-foreground leading-relaxed">
                        {step.desc}
                      </p>
                    </div>
                  </div>
                  
                  {/* Visual connector between steps */}
                  {!isLast && (
                    <div className="w-12 h-px bg-border flex items-center justify-center relative shrink-0">
                      <ArrowRight className="w-4 h-4 absolute text-muted-foreground bg-background rounded-full" />
                    </div>
                  )}
                </div>
              )
            })}
          </motion.div>
        </div>

        {/* Mobile Static View */}
        <div className="sm:hidden flex flex-col gap-8 w-full px-4">
          {steps.map((step, index) => {
            const isLast = index === steps.length - 1
            return (
              <div key={`mobile-${step.id}`} className="flex flex-col items-center">
                <div className="panel w-full p-6 flex items-start gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center shrink-0">
                    <step.icon className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold tracking-tight text-foreground mb-1">{step.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {step.desc}
                    </p>
                  </div>
                </div>
                {!isLast && (
                  <div className="h-8 w-0.5 bg-border my-2" />
                )}
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}
