'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useRef } from 'react'

export function HeroSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'],
  })

  const heroY = useTransform(scrollYProgress, [0, 1], ['0%', '20%'])
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const mockupScale = useTransform(scrollYProgress, [0, 0.5], [0.95, 1])
  const mockupY = useTransform(scrollYProgress, [0, 0.5], ['0%', '-8%'])

  return (
    <section
      ref={containerRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden pt-14 noise-overlay"
    >
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <motion.div
          style={{ y: heroY, opacity: heroOpacity }}
          className="text-center md:text-left"
        >
          {/* Pill Badge */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="flex justify-center md:justify-start mb-6"
          >
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-secondary border border-border text-[13px] font-medium text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald" />
              Now serving 500+ organizations
            </div>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="headline-display text-5xl sm:text-6xl md:text-7xl lg:text-[76px] max-w-3xl"
          >
            <span className="block text-foreground">Hire smarter.</span>
            <span className="block text-gradient-warm mt-1">Interview less.</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, filter: 'blur(4px)' }}
            animate={{ opacity: 1, filter: 'blur(0px)' }}
            transition={{ duration: 0.9, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="mx-auto md:mx-0 mt-7 max-w-lg text-lg text-muted-foreground text-pretty leading-relaxed body-large"
          >
            AI handles the screening and interviews so your team can focus 
            on the candidates who actually matter. Five minutes per candidate, 
            not five hours.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="mt-9 flex flex-col sm:flex-row items-center md:items-start gap-3"
          >
            <Button
              asChild
              className="h-12 px-8 text-[15px] font-semibold bg-foreground text-background hover:bg-foreground/90 rounded-full transition-all duration-200"
            >
              <Link href="/auth/register">
                Start Hiring Free
              </Link>
            </Button>
            <Button
              asChild
              variant="ghost"
              className="h-12 px-5 text-[15px] font-medium text-muted-foreground hover:text-foreground group"
            >
              <Link href="#how-it-works" className="flex items-center gap-2">
                See How It Works
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
          </motion.div>
        </motion.div>

        {/* Dashboard Preview — Clean floating cards, no browser chrome */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.6, ease: [0.16, 1, 0.3, 1] }}
          style={{
            scale: mockupScale,
            y: mockupY,
          }}
          className="mt-16 lg:mt-20 relative"
        >
          <div className="relative mx-auto max-w-5xl">
            {/* Floating Stats Cards */}
            <div className="rounded-2xl border border-border bg-card/80 backdrop-blur-sm shadow-whisper overflow-hidden">
              <div className="p-6 sm:p-8 space-y-6 bg-background/60">
                {/* Stats Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
                  {[
                    { label: 'Active Drives', value: '12', change: '+3 this week', accent: 'bg-primary' },
                    { label: 'Total Applicants', value: '847', change: '+24 today', accent: 'bg-cyan' },
                    { label: 'Interviews Done', value: '234', change: '12 pending', accent: 'bg-emerald' },
                    { label: 'Avg Score', value: '78%', change: '↑ 5% from last month', accent: 'bg-amber' },
                  ].map((item, i) => (
                    <motion.div
                      key={item.label}
                      initial={{ opacity: 0, y: 16 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: 0.7 + i * 0.08, duration: 0.5 }}
                      className="relative p-4 rounded-xl border border-border bg-card shadow-whisper overflow-hidden"
                    >
                      <div className={`absolute top-0 left-0 right-0 h-0.5 ${item.accent}`} />
                      <div className="text-xs text-muted-foreground mb-2">{item.label}</div>
                      <div className="text-2xl font-bold text-foreground tracking-tight">{item.value}</div>
                      <div className="text-[11px] text-muted-foreground mt-1">{item.change}</div>
                    </motion.div>
                  ))}
                </div>

                {/* Table Preview */}
                <div className="rounded-xl border border-border overflow-hidden">
                  <div className="px-5 py-3 border-b border-border bg-secondary/40">
                    <h3 className="font-semibold text-sm text-foreground">Recent Applicants</h3>
                  </div>
                  <div className="divide-y divide-border">
                    {[
                      { name: 'Sarah Chen', role: 'Frontend Developer', status: 'Interviewed', score: 85 },
                      { name: 'Alex Kumar', role: 'Backend Developer', status: 'Submitted', score: null },
                      { name: 'Maya Patel', role: 'UI/UX Designer', status: 'Applied', score: null },
                    ].map((applicant, i) => (
                      <motion.div
                        key={applicant.name}
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.9 + i * 0.08 }}
                        className="px-5 py-3 flex items-center justify-between hover:bg-secondary/20 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary-subtle flex items-center justify-center">
                            <span className="text-xs font-medium text-primary">
                              {applicant.name.split(' ').map(n => n[0]).join('')}
                            </span>
                          </div>
                          <div>
                            <div className="text-sm font-medium text-foreground">{applicant.name}</div>
                            <div className="text-xs text-muted-foreground">{applicant.role}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span
                            className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                              applicant.status === 'Interviewed'
                                ? 'bg-success-subtle'
                                : applicant.status === 'Submitted'
                                ? 'bg-primary-subtle'
                                : 'bg-warning-subtle'
                            }`}
                          >
                            {applicant.status}
                          </span>
                          {applicant.score && (
                            <div className="text-sm font-semibold text-emerald">{applicant.score}%</div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
