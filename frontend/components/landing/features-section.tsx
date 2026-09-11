'use client'

import { motion, useReducedMotion } from 'framer-motion'
import { 
  Brain, 
  Video, 
  BarChart3, 
  QrCode,
  Github,
  Mail
} from 'lucide-react'

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Interviews',
    description: 'Structured interviews that adapt to each candidate. Relevant questions based on their profile, projects, and experience.',
  },
  {
    icon: Github,
    title: 'GitHub Integration',
    description: 'Analyze candidate repositories automatically — code quality, tech stack, commit patterns, and project complexity.',
  },
  {
    icon: Video,
    title: 'Video Analysis',
    description: 'Real-time integrity checks using computer vision. Face and gaze tracking catch malpractice securely and privately.',
  },
  {
    icon: BarChart3,
    title: 'Smart Scoring',
    description: 'Advanced NLP evaluation across communication, technical depth, and domain knowledge. Deep, explainable metrics.',
  },
  {
    icon: QrCode,
    title: 'Instant Drive Links',
    description: 'Generate shareable links and QR codes for your recruitment drives. Candidates can apply in under 30 seconds.',
  },
  {
    icon: Mail,
    title: 'Automated Workflows',
    description: 'Confirmation emails, task assignments, interview invitations, and results — all triggered automatically upon phase completion.',
  },
]

const appleEase = [0.25, 0.1, 0.25, 1] as const

export function FeaturesSection() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <section id="features" className="py-24 lg:py-32 border-y border-border/40 overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.7, ease: appleEase }}
          className="mb-16 md:mb-24 text-center max-w-3xl mx-auto"
        >
          <h2 className="section-title text-4xl mb-6">
            Everything you need for modern recruitment.
          </h2>
          <p className="body-text text-lg">
            From first application to final decision — one unified platform without the spreadsheets, friction, or guesswork.
          </p>
        </motion.div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 32, scale: 0.97 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, margin: '-8%' }}
              transition={{
                duration: 0.6,
                delay: index * 0.08,
                ease: appleEase
              }}
              whileHover={prefersReducedMotion ? {} : { y: -4, transition: { duration: 0.25 } }}
              className="group p-8 rounded-xl border border-border/40 transition-colors duration-300 hover:border-primary/30 bg-background"
            >
              <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/8 text-primary transition-all duration-300 group-hover:bg-primary group-hover:text-primary-foreground group-hover:scale-105">
                <feature.icon className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-3">
                {feature.title}
              </h3>
              <p className="body-text text-[15px]">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
