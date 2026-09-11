'use client'

import { motion, useScroll, useTransform } from 'framer-motion'
import { useRef } from 'react'
import { 
  UserPlus, 
  FileText, 
  Share2, 
  Brain, 
  CheckCircle,
  ArrowRight
} from 'lucide-react'

const orgSteps = [
  {
    icon: UserPlus,
    title: 'Create Account',
    description: 'Set up your organization profile securely.',
  },
  {
    icon: FileText,
    title: 'Create Drive',
    description: 'Define roles, required skills, and deadlines.',
  },
  {
    icon: Share2,
    title: 'Share Link',
    description: 'Distribute the unique drive link to candidates.',
  },
  {
    icon: Brain,
    title: 'AI Evaluates',
    description: 'AI conducts adaptive interviews automatically.',
  },
  {
    icon: CheckCircle,
    title: 'Review & Hire',
    description: 'Review deep evaluations and make final decisions.',
  },
]

const applicantSteps = [
  {
    icon: Share2,
    title: 'Open Link',
    description: 'Access the drive securely without friction.',
  },
  {
    icon: FileText,
    title: 'Submit Profile',
    description: 'Upload resume or connect GitHub repositories.',
  },
  {
    icon: Brain,
    title: 'AI Interview',
    description: 'Complete the structured technical interview.',
  },
  {
    icon: CheckCircle,
    title: 'Get Results',
    description: 'Receive fair, automated evaluation feedback.',
  },
]

export function HowItWorksSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  
  // Create a progress line effect mapped to scroll
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"]
  })
  
  const orgY = useTransform(scrollYProgress, [0, 1], ["0%", "5%"])
  const appY = useTransform(scrollYProgress, [0, 1], ["0%", "-5%"])

  return (
    <section id="how-it-works" ref={containerRef} className="py-24 lg:py-32 bg-background relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-10%' }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="text-center max-w-2xl mx-auto mb-20"
        >
          <h2 className="section-title text-4xl mb-6">
            A precise workflow for both sides of the table.
          </h2>
          <p className="body-text text-lg">
            Every step is designed to reduce friction while maximizing signal.
          </p>
        </motion.div>

        {/* Organization Flow */}
        <motion.div style={{ y: orgY }} className="mb-24">
          <div className="text-center mb-12">
            <span className="inline-flex items-center px-4 py-1.5 rounded bg-primary/10 text-primary text-sm font-semibold tracking-wide uppercase">
              For Organizations
            </span>
          </div>

          <div className="relative">
            {/* Scroll-driven progress line */}
            <div className="absolute top-7 left-[10%] right-[10%] h-0.5 bg-border hidden lg:block overflow-hidden">
              <motion.div 
                className="h-full bg-primary"
                style={{ scaleX: scrollYProgress, transformOrigin: "left" }}
              />
            </div>
            
            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5">
              {orgSteps.map((step, index) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-10%' }}
                  transition={{ 
                    duration: 0.6, 
                    delay: index * 0.1,
                    ease: [0.16, 1, 0.3, 1] 
                  }}
                  className="relative text-center group"
                >
                  <div className="relative inline-flex mb-6">
                    <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-lg bg-secondary text-secondary-foreground transition-colors duration-300 group-hover:bg-primary group-hover:text-primary-foreground border border-border shadow-sm group-hover:shadow-md">
                      <step.icon className="h-6 w-6" />
                    </div>
                    <div className="absolute -top-2 -right-2 z-20 flex h-5 w-5 items-center justify-center rounded-full bg-foreground text-background text-[10px] font-bold font-mono">
                      {index + 1}
                    </div>
                  </div>
                  <h4 className="font-semibold text-foreground text-base mb-2">{step.title}</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Applicant Flow */}
        <motion.div style={{ y: appY }} className="mb-24">
          <div className="text-center mb-12">
            <span className="inline-flex items-center px-4 py-1.5 rounded bg-foreground/10 text-foreground text-sm font-semibold tracking-wide uppercase">
              For Applicants
            </span>
          </div>

          <div className="relative max-w-4xl mx-auto">
             <div className="absolute top-7 left-[12%] right-[12%] h-0.5 bg-border hidden md:block overflow-hidden">
              <motion.div 
                className="h-full bg-foreground"
                style={{ scaleX: scrollYProgress, transformOrigin: "left" }}
              />
            </div>

            <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
              {applicantSteps.map((step, index) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-10%' }}
                  transition={{ 
                    duration: 0.6, 
                    delay: index * 0.1,
                    ease: [0.16, 1, 0.3, 1] 
                  }}
                  className="relative text-center group"
                >
                  <div className="relative inline-flex mb-6">
                    <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-lg bg-secondary text-secondary-foreground transition-colors duration-300 group-hover:bg-foreground group-hover:text-background border border-border shadow-sm group-hover:shadow-md">
                      <step.icon className="h-6 w-6" />
                    </div>
                    <div className="absolute -top-2 -right-2 z-20 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground text-[10px] font-bold font-mono">
                      {index + 1}
                    </div>
                  </div>
                  <h4 className="font-semibold text-foreground text-base mb-2">{step.title}</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Deep Dive Section */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: '-10%' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="rounded-2xl bg-foreground text-background p-8 lg:p-12 relative overflow-hidden shadow-xl">
            {/* Subtle glow effect behind */}
            <div className="absolute -inset-10 bg-primary/20 blur-3xl rounded-full opacity-50 translate-x-1/2 translate-y-1/2" />
            
            <div className="relative z-10 max-w-5xl mx-auto">
              <h3 className="text-2xl sm:text-3xl font-semibold text-center mb-12">
                Inside the AI Interview
              </h3>
              <div className="grid gap-6 md:grid-cols-3">
                {[
                  {
                    round: 'Stage 1',
                    title: 'Contextual Baseline',
                    description: 'Establishes candidate background and verifies identity details.',
                  },
                  {
                    round: 'Stage 2',
                    title: 'Technical Deep-Dive',
                    description: 'Analyzes past projects, GitHub commits, and architectural decisions.',
                  },
                  {
                    round: 'Stage 3',
                    title: 'Domain Evaluation',
                    description: 'Tests specific engineering constraints and problem-solving logic.',
                  },
                ].map((round, index) => (
                  <motion.div
                    key={round.round}
                    whileHover={{ y: -4 }}
                    className="relative rounded-xl border border-background/10 bg-background/5 p-6 backdrop-blur-sm transition-transform"
                  >
                    <div className="mb-4">
                      <span className="text-xs font-semibold uppercase tracking-wider text-background/50 font-mono">
                        {round.round}
                      </span>
                    </div>
                    <h4 className="font-semibold text-lg text-background mb-2">{round.title}</h4>
                    <p className="text-sm text-background/70 leading-relaxed">
                      {round.description}
                    </p>
                    {index < 2 && (
                      <ArrowRight className="absolute -right-5 top-1/2 -translate-y-1/2 h-5 w-5 text-background/20 hidden md:block" />
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
