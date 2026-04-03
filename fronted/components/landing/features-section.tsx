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
    description: 'Intelligent AI conducts structured interviews, asking relevant questions based on candidate profiles and project submissions.',
  },
  {
    icon: Github,
    title: 'GitHub Integration',
    description: 'Automatically analyze candidate repositories with RepoLens to evaluate code quality, tech stack, and project complexity.',
  },
  {
    icon: Video,
    title: 'Video Analysis',
    description: 'Real-time malpractice detection using computer vision. Ensure interview integrity with face and gaze tracking.',
  },
  {
    icon: BarChart3,
    title: 'Smart Scoring',
    description: 'BERT-powered answer evaluation across communication, technical depth, and domain knowledge dimensions.',
  },
  {
    icon: QrCode,
    title: 'Instant Drive Links',
    description: 'Generate shareable links and QR codes for your recruitment drives. Candidates apply in seconds.',
  },
  {
    icon: Mail,
    title: 'Automated Emails',
    description: 'Trigger automated emails for applications, task assignments, interview invitations, and results.',
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 lg:py-32 bg-secondary">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-center max-w-3xl mx-auto"
        >
          <h2 className="headline-display text-3xl sm:text-4xl lg:text-5xl text-balance">
            Everything you need for{' '}
            <span className="gradient-text">modern recruitment</span>
          </h2>
          <p className="mt-6 text-lg text-muted-foreground leading-relaxed">
            Streamline your entire recruitment pipeline with AI-powered tools designed 
            for modern teams and organizations.
          </p>
        </motion.div>

        {/* Feature Grid */}
        <div className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-15%' }}
              transition={{ 
                duration: 0.8, 
                delay: index * 0.1,
                ease: [0.16, 1, 0.3, 1] 
              }}
              className="group relative rounded-xl border border-border bg-card p-8 shadow-whisper shadow-whisper-hover transition-all duration-300"
            >
              <div className="inline-flex rounded-xl p-3 bg-primary-subtle">
                <feature.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mt-6 text-lg font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
