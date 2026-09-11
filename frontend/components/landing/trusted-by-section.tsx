'use client'

import { motion, useReducedMotion } from 'framer-motion'

const companies = [
  'Google',
  'Apple',
  'Microsoft',
  'Amazon',
  'Meta',
  'Netflix',
  'Spotify',
  'Stripe',
  'Airbnb',
  'Uber',
  'Slack',
  'Shopify',
]

export function TrustedBySection() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <section id="trusted" className="py-12 border-y border-border/30 overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.p
          initial={prefersReducedMotion ? {} : { opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground mb-8"
        >
          Trusted by organizations worldwide
        </motion.p>
      </div>
      
      {/* Infinite marquee — text-first, no pill borders */}
      <div className="relative">
        <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-background to-transparent z-10" />
        <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-background to-transparent z-10" />
        
        <div
          className="flex animate-marquee"
          style={prefersReducedMotion ? { animation: 'none' } : undefined}
        >
          {[...companies, ...companies, ...companies, ...companies].map((company, i) => (
            <div
              key={`${company}-${i}`}
              className="flex-shrink-0 mx-6"
            >
              <span className="text-sm font-semibold text-muted-foreground/40 whitespace-nowrap tracking-tight hover:text-muted-foreground/70 transition-colors duration-300 cursor-default select-none">
                {company}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
