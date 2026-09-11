'use client'

import { motion } from 'framer-motion'
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

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 lg:py-32 bg-secondary/30 border-y border-border">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-10%' }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
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
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-10%' }}
              transition={{ 
                duration: 0.6, 
                delay: index * 0.05,
                ease: [0.16, 1, 0.3, 1] 
              }}
              className="group solid-panel p-8 transition-colors hover:border-primary/40"
            >
              <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary transition-transform group-hover:scale-105">
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
