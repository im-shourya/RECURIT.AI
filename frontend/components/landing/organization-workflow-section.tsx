'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { Building2, FolderPlus, Share2, Brain, CheckSquare, ArrowRight } from 'lucide-react'

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

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  // Moving the horizontal track based on scroll progress
  const x = useTransform(scrollYProgress, [0, 1], ["0%", "-70%"])

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[350vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0 border-t border-border/30">
        
        {/* Section Header */}
        <div className="w-full px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto mb-16 lg:mb-24 flex-shrink-0">
          <span className="eyebrow text-muted-foreground opacity-70 mb-4 block">For Organizations</span>
          <h2 className="section-title text-foreground">
            The Recruiter Journey
          </h2>
        </div>

        {/* Desktop Horizontal Scroll Track */}
        <div className="hidden sm:flex items-center w-full overflow-hidden">
          <motion.div 
            style={prefersReducedMotion ? {} : { x }}
            className="flex items-center gap-12 px-4 sm:px-6 lg:px-8"
          >
            {steps.map((step, index) => {
              const Icon = step.icon
              const isLast = index === steps.length - 1

              return (
                <div key={step.id} className="flex items-center gap-12 flex-shrink-0">
                  <div className="w-[320px] h-[360px] bg-background border border-border rounded-2xl p-8 flex flex-col justify-between shadow-sm relative group overflow-hidden">
                    <div className="absolute inset-0 bg-primary/5 translate-y-[100%] group-hover:translate-y-0 transition-transform duration-500 ease-out" />
                    
                    <div className="w-16 h-16 rounded-2xl bg-surface border border-border flex items-center justify-center relative z-10">
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
                    <div className="w-12 h-0.5 bg-border flex items-center justify-center relative flex-shrink-0">
                      <ArrowRight className="w-4 h-4 text-border absolute text-muted-foreground bg-background rounded-full" />
                    </div>
                  )}
                </div>
              )
            })}
            
            {/* End Spacer */}
            <div className="w-[10vw] flex-shrink-0" />
          </motion.div>
        </div>

        {/* Mobile Static View */}
        <div className="sm:hidden flex flex-col gap-8 w-full px-4">
          {steps.map((step, index) => {
            const isLast = index === steps.length - 1
            return (
              <div key={`mobile-${step.id}`} className="flex flex-col items-center">
                <div className="w-full bg-background border border-border rounded-2xl p-6 flex items-start gap-4 shadow-sm">
                  <div className="w-12 h-12 rounded-xl bg-surface border border-border flex items-center justify-center flex-shrink-0">
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
