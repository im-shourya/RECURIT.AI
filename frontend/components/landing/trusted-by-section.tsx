'use client'

import { motion } from 'framer-motion'

const orgs = [
  'TechSoc',
  'InnovatorsHub',
  'CodeCraft',
  'DesignLab',
  'AI Society',
  'RoboClub',
  'DataDriven',
  'CloudNine',
  'DevCircle',
  'StartupCell',
  'CyberSec',
  'OpenSource',
]

export function TrustedBySection() {
  return (
    <section id="trusted" className="py-16 border-y border-border/50 bg-secondary/50 overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center text-sm font-medium text-muted-foreground mb-8 tracking-wide uppercase"
        >
          Trusted by organizations worldwide
        </motion.p>
      </div>
      
      {/* Infinite marquee */}
      <div className="relative">
        <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-secondary/50 to-transparent z-10" />
        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-secondary/50 to-transparent z-10" />
        
        <div className="flex animate-marquee">
          {[...orgs, ...orgs].map((org, i) => (
            <div
              key={`${org}-${i}`}
              className="flex-shrink-0 mx-8 flex items-center justify-center"
            >
              <span className="text-lg font-semibold text-muted-foreground/40 whitespace-nowrap tracking-tight">
                {org}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
