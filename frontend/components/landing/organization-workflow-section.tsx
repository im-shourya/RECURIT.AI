'use client'

import { useRef, useState } from 'react'
import { motion, useScroll, useMotionValueEvent, useReducedMotion, AnimatePresence } from 'framer-motion'
import { Building2, FolderPlus, Share2, Brain, CheckSquare } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

const steps = [
  { id: '01', title: 'Create Account', desc: 'Set up your organization profile securely.', icon: Building2 },
  { id: '02', title: 'Create Drive', desc: 'Define roles, required skills, and deadlines.', icon: FolderPlus },
  { id: '03', title: 'Share Link', desc: 'Distribute the unique drive link to candidates.', icon: Share2 },
  { id: '04', title: 'AI Evaluates', desc: 'AI conducts adaptive interviews automatically.', icon: Brain },
  { id: '05', title: 'Review & Hire', desc: 'Review deep evaluations and make final decisions.', icon: CheckSquare },
]

export function OrganizationWorkflowSection() {
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
      steps.length - 1,
      Math.floor(latest * steps.length)
    )
    setActiveIndex(index)
  })

  const activeStep = steps[activeIndex]
  const ActiveIcon = activeStep.icon

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[500vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden px-4 sm:px-6 lg:px-8 py-24 sm:py-0 border-t border-border/30">
        
        <div className="w-full max-w-5xl mx-auto mb-16 lg:mb-24 text-center">
          <motion.div
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ duration: 0.8, ease: appleEase }}
          >
            <span className="eyebrow text-muted-foreground opacity-70 mb-4 block">For Organizations</span>
            <h2 className="section-title text-foreground">
              The Recruiter Journey
            </h2>
          </motion.div>
        </div>

        {/* Desktop Sticky Narrative */}
        <div className="hidden sm:grid w-full max-w-5xl mx-auto grid-cols-2 gap-16 items-center">
          
          {/* Narrative Column */}
          <div className="flex flex-col gap-8">
            {steps.map((step, i) => {
              const isActive = activeIndex === i
              const isPast = activeIndex > i
              
              return (
                <div 
                  key={step.id}
                  className={`transition-all duration-500 flex items-start gap-6 ${
                    isActive ? 'opacity-100 scale-100' : 
                    isPast ? 'opacity-30 scale-95' : 'opacity-30 scale-95'
                  }`}
                >
                  <div className={`w-12 h-12 rounded-xl border flex items-center justify-center flex-shrink-0 transition-colors duration-500 ${
                    isActive ? 'bg-primary text-primary-foreground border-primary' : 'bg-surface border-border text-muted-foreground'
                  }`}>
                    <step.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className={`text-xl font-semibold tracking-tight mb-2 transition-colors duration-500 ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                      {step.title}
                    </h3>
                    {isActive && (
                      <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="text-base text-muted-foreground leading-relaxed"
                      >
                        {step.desc}
                      </motion.p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Visual Presentation Area */}
          <div className="relative h-[400px] flex items-center justify-center bg-surface/50 border border-border rounded-2xl">
            <AnimatePresence mode="wait">
              <motion.div
                key={`visual-${activeStep.id}`}
                initial={{ opacity: 0, scale: 0.97, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.985, y: -10 }}
                transition={{ duration: 0.4, ease: appleEase }}
                className="absolute flex flex-col items-center justify-center text-center p-8"
              >
                <div className="w-20 h-20 rounded-2xl bg-background border border-border shadow-sm flex items-center justify-center mb-6">
                  <ActiveIcon className="w-8 h-8 text-primary" />
                </div>
                <div className="space-y-3">
                  <div className="h-2 w-32 bg-border rounded-full mx-auto" />
                  <div className="h-2 w-48 bg-border/50 rounded-full mx-auto" />
                  <div className="h-2 w-24 bg-border/50 rounded-full mx-auto" />
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

        </div>

        {/* Mobile Static Narrative */}
        <div className="sm:hidden flex flex-col gap-12 w-full">
          {steps.map((step) => (
            <div key={`mobile-${step.id}`} className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0">
                <step.icon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-semibold tracking-tight text-foreground mb-1">{step.title}</h3>
                <p className="text-base text-muted-foreground leading-relaxed">
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
