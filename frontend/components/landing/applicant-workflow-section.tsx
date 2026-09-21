'use client'

import { useRef, useState } from 'react'
import { motion, useScroll, useMotionValueEvent, AnimatePresence } from 'framer-motion'
import { Link2, Upload, Brain, FileCheck } from 'lucide-react'

import { useStickyStage } from '@/hooks/use-sticky-stage'
import { Reveal, appleOut } from './motion'

const steps = [
  { id: '01', title: 'Open Link', desc: 'Access the drive securely without friction.', icon: Link2 },
  { id: '02', title: 'Submit Profile', desc: 'Upload resume or connect GitHub repositories.', icon: Upload },
  { id: '03', title: 'AI Interview', desc: 'Complete the structured technical interview.', icon: Brain },
  { id: '04', title: 'Get Results', desc: 'Receive fair, automated evaluation feedback.', icon: FileCheck },
]

export function ApplicantWorkflowSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const pinned = useStickyStage()
  const [activeIndex, setActiveIndex] = useState(0)

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    if (!pinned) return
    const index = Math.min(
      steps.length - 1,
      Math.max(0, Math.floor(latest * steps.length))
    )
    setActiveIndex(index)
  })

  const activeStep = steps[activeIndex]
  const ActiveIcon = activeStep.icon

  return (
    <section ref={containerRef} className="relative bg-surface sm:h-[250vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden px-4 sm:px-6 lg:px-8 py-24 sm:py-0 border-t border-border/30">
        
        <Reveal className="w-full max-w-5xl mx-auto mb-16 lg:mb-24 text-center">
          <span className="eyebrow text-muted-foreground/70 mb-4 block">For Applicants</span>
          <h2 className="section-title text-foreground">
            A frictionless experience.
          </h2>
        </Reveal>

        {/* Desktop Sticky Narrative */}
        <div className="hidden sm:flex w-full max-w-5xl mx-auto flex-col items-center">
          
          {/* Visual Presentation Area - Top */}
          <div className="panel relative h-[240px] w-full max-w-2xl flex items-center justify-center mb-12">
            <AnimatePresence mode="wait">
              <motion.div
                key={`visual-${activeStep.id}`}
                initial={{ opacity: 0, scale: 0.97, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.985, y: -10 }}
                transition={{ duration: 0.35, ease: appleOut }}
                className="absolute flex items-center justify-center gap-6 p-8"
              >
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                  <ActiveIcon className="w-8 h-8 text-primary" />
                </div>
                <div className="space-y-3 flex-1 min-w-[200px]">
                  <div className="h-3 w-3/4 bg-border/80 rounded-full" />
                  <div className="h-2 w-1/2 bg-border/40 rounded-full" />
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Steps Track - Bottom */}
          <div className="w-full grid grid-cols-4 gap-4">
            {steps.map((step, i) => {
              const isActive = activeIndex === i
              const isPast = activeIndex > i
              
              return (
                <div 
                  key={step.id}
                  className={`transition-all duration-500 flex flex-col items-center text-center p-4 rounded-2xl border ${
                    isActive
                      ? 'bg-surface border-border/70 shadow-elevation-1 opacity-100'
                      : isPast
                        ? 'border-transparent opacity-60'
                        : 'border-transparent opacity-35'
                  }`}
                >
                  <h3 className={`text-base font-semibold tracking-tight mb-2 transition-colors duration-500 ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                    {step.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed hidden lg:block">
                    {step.desc}
                  </p>
                </div>
              )
            })}
          </div>

        </div>

        {/* Mobile Static Narrative */}
        <div className="sm:hidden flex flex-col gap-8 w-full">
          {steps.map((step) => (
            <div key={`mobile-${step.id}`} className="panel flex items-start gap-4 p-5">
              <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <step.icon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-semibold tracking-tight text-foreground mb-1">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  )
}
