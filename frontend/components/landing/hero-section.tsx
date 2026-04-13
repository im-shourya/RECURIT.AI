'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useRef } from 'react'

const stats = [
  { label: 'Organizations', value: '500+' },
  { label: 'Candidates Evaluated', value: '50K+' },
  { label: 'Time Saved', value: '80%' },
]

export function HeroSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'],
  })

  const heroY = useTransform(scrollYProgress, [0, 1], ['0%', '20%'])
  const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const mockupScale = useTransform(scrollYProgress, [0, 0.5], [0.92, 1])
  const mockupRotate = useTransform(scrollYProgress, [0, 0.5], [3, 0])
  const mockupY = useTransform(scrollYProgress, [0, 0.5], ['0%', '-10%'])

  return (
    <section
      ref={containerRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden pt-[52px]"
    >
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
        <motion.div
          style={{ y: heroY, opacity: heroOpacity }}
          className="text-center"
        >
          {/* Pill Badge */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="flex justify-center mb-8"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary border border-border">
              <span className="w-2 h-2 rounded-full bg-primary pulse-dot" />
              <span className="text-[13px] font-medium text-muted-foreground">
                AI-Powered Recruitment
              </span>
            </div>
          </motion.div>

          {/* Headline - Playfair Display */}
          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="headline-display text-5xl sm:text-6xl md:text-7xl lg:text-[80px] text-balance"
          >
            <span className="block text-foreground">Recruitment,</span>
            <span className="block gradient-text mt-2">reinvented.</span>
          </motion.h1>

          {/* Subheadline - DM Sans */}
          <motion.p
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="mx-auto mt-8 max-w-xl text-[21px] text-muted-foreground text-pretty leading-relaxed"
          >
            Transform how your organization recruits with intelligent AI interviews,
            automated screening, and data-driven candidate evaluation.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Button
              asChild
              className="h-12 px-8 text-base font-semibold bg-foreground text-background hover:bg-foreground/90 rounded-full transition-all duration-200"
            >
              <Link href="/auth/register">
                Start Hiring Free
              </Link>
            </Button>
            <Button
              asChild
              variant="ghost"
              className="h-12 px-6 text-base font-medium text-muted-foreground hover:text-foreground group"
            >
              <Link href="#how-it-works" className="flex items-center gap-2">
                See How It Works
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
          </motion.div>
        </motion.div>

        {/* Dashboard Mockup with Apple-style scale effect */}
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          style={{
            scale: mockupScale,
            rotateX: mockupRotate,
            y: mockupY,
          }}
          className="mt-20 relative perspective-1000"
        >
          <div className="relative mx-auto max-w-5xl">
            {/* Dashboard Preview */}
            <div className="relative rounded-xl border border-border bg-card shadow-whisper overflow-hidden">
              {/* Browser Chrome */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-secondary/50">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-destructive/60" />
                  <div className="w-3 h-3 rounded-full bg-warning/60" />
                  <div className="w-3 h-3 rounded-full bg-success/60" />
                </div>
                <div className="flex-1 flex justify-center">
                  <div className="px-4 py-1 rounded-md bg-background text-xs text-muted-foreground font-mono">
                    recruit.ai/dashboard
                  </div>
                </div>
              </div>

              {/* Dashboard Content */}
              <div className="p-6 space-y-6 bg-background">
                {/* Stats Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: 'Active Drives', value: '12', change: '+3' },
                    { label: 'Total Applicants', value: '847', change: '+24' },
                    { label: 'Interviews Done', value: '234', change: '+12' },
                    { label: 'Avg Score', value: '78%', change: '+5%' },
                  ].map((item, i) => (
                    <motion.div
                      key={item.label}
                      initial={{ opacity: 0, y: 20 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: 0.6 + i * 0.1, duration: 0.5 }}
                      className="p-4 rounded-lg border border-border bg-card shadow-whisper"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-8 h-8 rounded-lg bg-primary-subtle flex items-center justify-center">
                          <div className="w-3 h-3 rounded-full bg-primary" />
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground mb-1">{item.label}</div>
                      <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-foreground">{item.value}</span>
                        <span className="text-xs font-medium text-success">{item.change}</span>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Table Preview */}
                <div className="rounded-lg border border-border overflow-hidden">
                  <div className="px-4 py-3 border-b border-border bg-secondary/30">
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
                        transition={{ delay: 0.8 + i * 0.1 }}
                        className="px-4 py-3 flex items-center justify-between hover:bg-secondary/20 transition-colors"
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
                            <div className="text-sm font-medium text-success">{applicant.score}%</div>
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
