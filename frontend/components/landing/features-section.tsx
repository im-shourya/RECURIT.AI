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
    accent: 'border-l-primary',
    iconBg: 'bg-primary/8',
  },
  {
    icon: Github,
    title: 'GitHub Integration',
    description: 'Analyze candidate repositories automatically — code quality, tech stack, commit patterns, and project complexity.',
    accent: 'border-l-foreground',
    iconBg: 'bg-foreground/8',
  },
  {
    icon: Video,
    title: 'Video Analysis',
    description: 'Real-time integrity checks using computer vision. Face and gaze tracking catch malpractice so you don\'t have to.',
    accent: 'border-l-cyan',
    iconBg: 'bg-cyan/8',
  },
  {
    icon: BarChart3,
    title: 'Smart Scoring',
    description: 'BERT-powered answer evaluation across communication, technical depth, and domain knowledge. No gut feelings needed.',
    accent: 'border-l-emerald',
    iconBg: 'bg-emerald/8',
  },
  {
    icon: QrCode,
    title: 'Instant Drive Links',
    description: 'Generate shareable links and QR codes for your recruitment drives. Candidates apply in under 30 seconds.',
    accent: 'border-l-amber',
    iconBg: 'bg-amber/8',
  },
  {
    icon: Mail,
    title: 'Automated Emails',
    description: 'Confirmation emails, task assignments, interview invitations, and results — all triggered automatically.',
    accent: 'border-l-rose',
    iconBg: 'bg-rose/8',
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 lg:py-28 bg-secondary/50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header — Left-aligned on desktop */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="section-offset mb-16"
        >
          <h2 className="headline-display text-3xl sm:text-4xl lg:text-[44px]">
            Everything you need for{' '}
            <span className="text-gradient-warm">modern recruitment</span>
          </h2>
          <p className="mt-5 text-lg text-muted-foreground leading-relaxed max-w-xl">
            From first application to final decision — one platform, 
            no spreadsheets, no guesswork.
          </p>
        </motion.div>

        {/* Feature Grid — Varied layout: 2 large + 4 smaller */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-10%' }}
              transition={{ 
                duration: 0.7, 
                delay: index * 0.06,
                ease: [0.16, 1, 0.3, 1] 
              }}
              className={`group relative rounded-xl border border-border bg-card p-7 shadow-whisper shadow-whisper-hover transition-all duration-300`}
            >
              <div className={`inline-flex rounded-lg p-2.5 ${feature.iconBg} transition-transform duration-300 group-hover:scale-110`}>
                <feature.icon className="h-5 w-5 text-foreground/70" />
              </div>
              <h3 className="mt-5 text-[15px] font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="mt-2.5 text-sm text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
