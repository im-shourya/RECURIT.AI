'use client'

import Link from 'next/link'

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
          <div className="absolute inset-0 bg-gradient-to-br from-primary/12 via-indigo/8 to-cyan/6 animate-gradient" />
          <div className="absolute top-1/3 left-1/4 w-[28rem] h-[28rem] bg-primary/15 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-1/3 right-1/4 w-[24rem] h-[24rem] bg-cyan/15 rounded-full blur-3xl animate-float" style={{ animationDelay: '3s' }} />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-0.5">
            <span className="text-2xl font-extrabold tracking-tight">
              RECRUIT<span className="text-primary">.</span>AI
            </span>
          </Link>

          {/* Testimonial / Feature Highlight */}
          <div className="max-w-md">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <blockquote className="font-serif text-2xl font-medium leading-relaxed italic">
                &ldquo;We went from spending 40 hours screening candidates to getting ranked results overnight. It just works.&rdquo;
              </blockquote>
              <div className="mt-6 flex items-center gap-4">
                <div className="h-11 w-11 rounded-full bg-primary/15 flex items-center justify-center">
                  <span className="text-base font-semibold text-primary">SP</span>
                </div>
                <div>
                  <div className="font-semibold text-[15px]">Shourya Parashar</div>
                  <div className="text-sm text-muted-foreground">CEO, Sparkles Ltd</div>
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
            <Link href="/" className="flex items-center gap-0.5">
              <span className="text-2xl font-extrabold tracking-tight">
                RECRUIT<span className="text-primary">.</span>AI
              </span>
            </Link>
          </div>
          
          {children}
        </div>
      </div>
    </div>
  )
}
