'use client'

import { motion } from 'framer-motion'

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
  return (
    <section id="trusted" className="py-12 border-y border-border/40 overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground mb-8"
        >
          Trusted by organizations worldwide
        </motion.p>
      </div>
      
      {/* Infinite marquee */}
      <div className="relative">
        <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-background to-transparent z-10" />
        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-background to-transparent z-10" />
        
        <div className="flex animate-marquee">
          {/* Repeat the list 4 times for seamless infinite scroll */}
          {[...companies, ...companies, ...companies, ...companies].map((company, i) => (
            <div
              key={`${company}-${i}`}
              className="flex-shrink-0 mx-4"
            >
              <div className="px-6 py-2.5 rounded-full border border-border/50 bg-card/40 hover:bg-card hover:border-border transition-all duration-300 cursor-default">
                <span className="text-sm font-semibold text-muted-foreground/60 whitespace-nowrap tracking-tight">
                  {company}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
