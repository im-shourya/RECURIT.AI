'use client'

import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

import { Reveal } from './motion'

export function CTASection() {
  // Deliberately not pinned. This is the last beat before the footer, so
  // holding it for extra viewport-heights only delays the footer, and tying
  // its opacity to scroll progress left the primary CTA invisible at the ends
  // of the pin. A plain section with a single on-view reveal is calmer and
  // reliable.
  return (
    <section className="relative bg-background overflow-hidden py-32 sm:py-48">
      <div aria-hidden className="pointer-events-none absolute inset-0 ambient-glow opacity-60" />

      <div className="relative w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center text-center">
        <Reveal>
          <h2 className="section-title text-foreground text-balance mb-12">
            Ready to recruit with <br className="hidden sm:block" />
            more signal and less noise?
          </h2>
        </Reveal>

        <Reveal delay={0.12}>
          <div className="flex flex-col sm:flex-row items-center gap-5 sm:gap-6">
            <Link
              href="/auth/register"
              className="press group inline-flex h-14 items-center justify-center rounded-full bg-primary px-8 text-base font-medium text-primary-foreground shadow-elevation-2 transition-colors hover:bg-primary/90"
            >
              Start Hiring Now
              <ArrowRight className="ml-2 h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/#how-it-works"
              className="text-base font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              See How It Works
            </Link>
          </div>
        </Reveal>
      </div>
    </section>
  )
}
