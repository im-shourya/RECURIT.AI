'use client'

import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { useRef } from 'react'
import { 
  UserPlus, 
  FileText, 
  Share2, 
  Brain, 
  CheckCircle,
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

const interviewStages = [
  {
    stage: 'Stage 1',
    title: 'Contextual Baseline',
    description: 'Establishes candidate background and verifies identity details.',
  },
  {
    stage: 'Stage 2',
    title: 'Technical Deep-Dive',
    description: 'Analyzes past projects, GitHub commits, and architectural decisions.',
  },
  {
    stage: 'Stage 3',
    title: 'Domain Evaluation',
    description: 'Tests specific engineering constraints and problem-solving logic.',
  },
]

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function HowItWorksSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"]
  })

  // Scroll-driven progress line
  const orgLineScale = useTransform(scrollYProgress, [0, 0.4], [0, 1])
  const appLineScale = useTransform(scrollYProgress, [0.3, 0.7], [0, 1])

  return (
    <section id="how-it-works" ref={containerRef} className="py-24 lg:py-32 bg-background relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-10%' }}
          transition={{ duration: 0.7, ease: appleEase }}
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
        <div className="mb-24">
          <div className="text-center mb-12">
            <motion.span
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, ease: appleEase }}
              className="inline-flex items-center px-4 py-1.5 rounded bg-primary/8 text-primary text-sm font-semibold tracking-wide uppercase"
            >
              For Organizations
            </motion.span>
          </div>

          <div className="relative">
            {/* Scroll-driven progress line */}
            <div className="absolute top-7 left-[10%] right-[10%] h-px bg-border hidden lg:block overflow-hidden">
              <motion.div
                className="h-full bg-primary"
                style={prefersReducedMotion ? { scaleX: 1 } : { scaleX: orgLineScale, transformOrigin: "left" }}
              />
            </div>

            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5">
              {orgSteps.map((step, index) => (
                <motion.div
                  key={step.title}
                  initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-8%' }}
                  transition={{
                    duration: 0.6,
                    delay: index * 0.08,
                    ease: appleEase
                  }}
                  className="relative text-center group"
                >
                  <div className="relative inline-flex mb-6">
                    <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-lg bg-background text-muted-foreground transition-all duration-300 group-hover:bg-primary group-hover:text-primary-foreground border border-border group-hover:border-primary/40 group-hover:shadow-sm">
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
        </div>

        {/* Applicant Flow */}
        <div className="mb-28">
          <div className="text-center mb-12">
            <motion.span
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, ease: appleEase }}
              className="inline-flex items-center px-4 py-1.5 rounded bg-foreground/6 text-foreground text-sm font-semibold tracking-wide uppercase"
            >
              For Applicants
            </motion.span>
          </div>

          <div className="relative max-w-4xl mx-auto">
            <div className="absolute top-7 left-[12%] right-[12%] h-px bg-border hidden md:block overflow-hidden">
              <motion.div
                className="h-full bg-foreground"
                style={prefersReducedMotion ? { scaleX: 1 } : { scaleX: appLineScale, transformOrigin: "left" }}
              />
            </div>

            <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
              {applicantSteps.map((step, index) => (
                <motion.div
                  key={step.title}
                  initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-8%' }}
                  transition={{
                    duration: 0.6,
                    delay: index * 0.08,
                    ease: appleEase
                  }}
                  className="relative text-center group"
                >
                  <div className="relative inline-flex mb-6">
                    <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-lg bg-background text-muted-foreground transition-all duration-300 group-hover:bg-foreground group-hover:text-background border border-border group-hover:border-foreground/40 group-hover:shadow-sm">
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
        </div>

        {/* Inside the AI Interview — open canvas, no dark box */}
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 32 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-10%' }}
          transition={{ duration: 0.8, ease: appleEase }}
          className="max-w-5xl mx-auto"
        >
          <h3 className="text-2xl sm:text-3xl font-semibold text-center mb-4 text-foreground">
            Inside the AI Interview
          </h3>
          <p className="text-center text-muted-foreground mb-12 max-w-xl mx-auto">
            Three structured stages designed to evaluate depth, not surface knowledge.
          </p>

          <div className="grid gap-6 md:grid-cols-3 relative">
            {/* Connecting line between stages */}
            <div className="absolute top-1/2 left-[17%] right-[17%] h-px bg-border hidden md:block" />

            {interviewStages.map((round, index) => (
              <motion.div
                key={round.stage}
                initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{
                  duration: 0.6,
                  delay: index * 0.1,
                  ease: appleEase
                }}
                className="relative rounded-xl border border-border/60 bg-background p-7 transition-all duration-300 hover:border-primary/30 hover:-translate-y-1"
              >
                <div className="mb-4">
                  <span className="text-xs font-semibold uppercase tracking-wider text-primary font-mono">
                    {round.stage}
                  </span>
                </div>
                <h4 className="font-semibold text-lg text-foreground mb-2">{round.title}</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {round.description}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
