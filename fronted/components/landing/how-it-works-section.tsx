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
    description: 'Set up your organization profile with logo and domain tags.',
  },
  {
    icon: FileText,
    title: 'Create Drive',
    description: 'Define role, tasks, deadlines, and question difficulty.',
  },
  {
    icon: Share2,
    title: 'Share Link',
    description: 'Distribute auto-generated link or QR code to candidates.',
  },
  {
    icon: Brain,
    title: 'AI Evaluates',
    description: 'AI conducts interviews and provides detailed scoring.',
  },
  {
    icon: CheckCircle,
    title: 'Select Candidates',
    description: 'Review scores, watch recordings, make decisions.',
  },
]

const applicantSteps = [
  {
    icon: Share2,
    title: 'Open Link',
    description: 'Click the drive link and fill in your details.',
  },
  {
    icon: FileText,
    title: 'Submit Work',
    description: 'Upload task or connect GitHub for project analysis.',
  },
  {
    icon: Brain,
    title: 'AI Interview',
    description: '5-minute AI interview about you and your projects.',
  },
  {
    icon: CheckCircle,
    title: 'Get Results',
    description: 'Receive feedback and selection notification.',
  },
]

export function HowItWorksSection() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ['start end', 'end start'],
  })

  const textY = useTransform(scrollYProgress, [0, 1], ['0%', '10%'])

  return (
    <section id="how-it-works" ref={sectionRef} className="py-24 lg:py-32">
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
            How <span className="gradient-text">RECRUIT.AI</span> Works
          </h2>
          <p className="mt-6 text-lg text-muted-foreground leading-relaxed">
            A streamlined process for both organizations and applicants.
          </p>
        </motion.div>

        {/* Organization Flow */}
        <div className="mt-24">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-15%' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-center mb-12"
          >
            <span className="inline-block px-4 py-2 rounded-full text-sm font-medium bg-primary-subtle">
              For Organizations
            </span>
          </motion.div>

          <div className="relative">
            {/* Connection Line */}
            <div className="absolute top-16 left-0 right-0 h-px bg-border hidden lg:block" />

            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5">
              {orgSteps.map((step, index) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 40 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-15%' }}
                  transition={{ 
                    duration: 0.8, 
                    delay: index * 0.1,
                    ease: [0.16, 1, 0.3, 1] 
                  }}
                  className="relative text-center"
                >
                  <div className="relative inline-flex">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-foreground shadow-whisper">
                      <step.icon className="h-6 w-6 text-background" />
                    </div>
                    <div className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                      {index + 1}
                    </div>
                  </div>
                  <h4 className="mt-6 font-semibold text-foreground">{step.title}</h4>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* Applicant Flow */}
        <div className="mt-32">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-15%' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-center mb-12"
          >
            <span className="inline-block px-4 py-2 rounded-full text-sm font-medium bg-success-subtle">
              For Applicants
            </span>
          </motion.div>

          <div className="relative max-w-4xl mx-auto">
            {/* Connection Line */}
            <div className="absolute top-16 left-0 right-0 h-px bg-border hidden md:block" />

            <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
              {applicantSteps.map((step, index) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 40 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-15%' }}
                  transition={{ 
                    duration: 0.8, 
                    delay: index * 0.1,
                    ease: [0.16, 1, 0.3, 1] 
                  }}
                  className="relative text-center"
                >
                  <div className="relative inline-flex">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-success shadow-whisper">
                      <step.icon className="h-6 w-6 text-success-foreground" />
                    </div>
                    <div className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-foreground text-xs font-bold text-background">
                      {index + 1}
                    </div>
                  </div>
                  <h4 className="mt-6 font-semibold text-foreground">{step.title}</h4>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* Interview Flow Detail - Dark Section */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-15%' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="mt-32"
        >
          <div className="rounded-2xl bg-foreground text-background p-8 lg:p-12">
            <h3 className="headline-display text-2xl sm:text-3xl text-center mb-12">
              The AI Interview Experience
            </h3>
            <div className="grid gap-6 md:grid-cols-3">
              {[
                {
                  round: 'Round 1',
                  title: 'Introduction',
                  duration: '60s',
                  description: 'Tell us about yourself, your background, and interests.',
                },
                {
                  round: 'Round 2',
                  title: 'Project Deep-Dive',
                  duration: '90s',
                  description: 'Questions based on your GitHub projects or task submission.',
                },
                {
                  round: 'Round 3',
                  title: 'Domain Knowledge',
                  duration: '90s',
                  description: 'Technical questions at the difficulty level set by the org.',
                },
              ].map((round, index) => (
                <div
                  key={round.round}
                  className="relative rounded-xl border border-background/10 bg-background/5 p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                      {round.round}
                    </span>
                    <span className="px-2 py-1 rounded-full bg-background/10 text-xs font-mono">
                      {round.duration}
                    </span>
                  </div>
                  <h4 className="font-semibold text-lg">{round.title}</h4>
                  <p className="mt-2 text-sm text-background/70 leading-relaxed">
                    {round.description}
                  </p>
                  {index < 2 && (
                    <ArrowRight className="absolute -right-4 top-1/2 -translate-y-1/2 h-6 w-6 text-background/20 hidden md:block" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
