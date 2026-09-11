'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { FolderPlus, User, Brain, FileSearch, CheckSquare } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

const workflowSteps = [
  { id: '01', title: 'Create Drive', icon: FolderPlus, description: 'Define roles and requirements.' },
  { id: '02', title: 'Candidate', icon: User, description: 'Applicants submit profiles seamlessly.' },
  { id: '03', title: 'AI Interview', icon: Brain, description: 'Adaptive technical evaluation.' },
  { id: '04', title: 'Evidence', icon: FileSearch, description: 'Code analysis and integrity checks.' },
  { id: '05', title: 'Decision', icon: CheckSquare, description: 'Make the final hiring call.' },
]

export function AIInterviewSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  // Horizontal translation for desktop (x goes from 0% to -X%)
  // 5 cards, to scroll them we need to move container left
  const xTransform = useTransform(scrollYProgress, [0, 1], ["0%", "-60%"])

  return (
    <section ref={containerRef} className="relative bg-background sm:h-[300vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex flex-col justify-center overflow-hidden py-24 sm:py-0">
        
        <div className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full mb-16 sm:mb-24">
          <motion.div
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ duration: 0.8, ease: appleEase }}
          >
            <h2 className="section-title text-foreground">
              The interview happens<br className="hidden sm:block" /> automatically.
            </h2>
          </motion.div>
        </div>

        {/* Horizontal scroll track (Desktop) / Vertical list (Mobile) */}
        <div className="px-4 sm:px-6 lg:px-8 w-full">
          <motion.div 
            style={prefersReducedMotion ? {} : { x: xTransform }}
            className="flex flex-col sm:flex-row gap-8 sm:gap-12 w-full sm:w-[250%]"
          >
            {workflowSteps.map((step, index) => {
              const StepIcon = step.icon
              return (
                <motion.div
                  key={step.id}
                  initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-5%' }}
                  transition={{ duration: 0.6, delay: index * 0.1, ease: appleEase }}
                  className="flex-shrink-0 flex items-start sm:w-80 group"
                >
                  <div className="mr-6 flex-shrink-0 mt-1">
                    <div className="w-16 h-16 rounded-2xl bg-card border border-border flex items-center justify-center text-muted-foreground group-hover:text-primary group-hover:border-primary/40 transition-colors duration-500">
                      <StepIcon className="w-7 h-7" />
                    </div>
                  </div>
                  <div>
                    <span className="eyebrow block mb-3 opacity-60 group-hover:opacity-100 transition-opacity">{step.id}</span>
                    <h3 className="text-xl font-semibold text-foreground mb-2">{step.title}</h3>
                    <p className="text-base text-muted-foreground leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </motion.div>
              )
            })}
          </motion.div>
        </div>

      </div>
    </section>
  )
}
