'use client'

import Link from 'next/link'
import { Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Animated Gradient */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-card">
        {/* Animated Gradient Mesh */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-indigo/20 to-cyan/20 animate-gradient" />
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/30 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan/30 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
          <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-indigo/30 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg gradient-primary">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight">
              RECRUIT<span className="gradient-text">.AI</span>
            </span>
          </Link>

          {/* Testimonial / Feature Highlight */}
          <div className="max-w-md">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <blockquote className="text-2xl font-medium leading-relaxed">
                &ldquo;RECRUIT.AI transformed our organization&apos;s hiring process. We saved 80% of time
                and found better candidates than ever before.&rdquo;
              </blockquote>
              <div className="mt-6 flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center">
                  <span className="text-lg font-semibold text-primary">SK</span>
                </div>
                <div>
                  <div className="font-semibold">Sneha Kapoor</div>
                  <div className="text-sm text-muted-foreground">Head of Recruitment, TechSoc</div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8">
            {[
              { value: '500+', label: 'Organizations' },
              { value: '50K+', label: 'Candidates' },
              { value: '80%', label: 'Time Saved' },
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
              >
                <div className="text-2xl font-bold gradient-text">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden mb-8 flex justify-center">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg gradient-primary">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <span className="text-2xl font-bold tracking-tight">
                RECRUIT<span className="gradient-text">.AI</span>
              </span>
            </Link>
          </div>
          
          {children}
        </div>
      </div>
    </div>
  )
}
