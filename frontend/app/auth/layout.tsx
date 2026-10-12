'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Link2, ScrollText, ShieldCheck } from 'lucide-react'

/**
 * What the product does, stated plainly. This panel used to carry a
 * testimonial and usage figures that were invented; these are all true of
 * the code as it ships.
 */
const FACTS = [
  {
    icon: Link2,
    title: 'One link per drive',
    body: 'Candidates apply without making an account, then follow their progress from a private status page.',
  },
  {
    icon: ShieldCheck,
    title: 'Recruiters decide',
    body: 'Nobody is interviewed or selected automatically. Roles control who can invite and who can decide.',
  },
  {
    icon: ScrollText,
    title: 'Every decision on record',
    body: 'Invitations, decisions and erasures are kept in an audit trail, and emails retry until they are delivered.',
  },
] as const

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left panel — what you are signing up for */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-muted">
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <Link href="/" className="flex items-center gap-0.5">
            <span className="text-2xl font-extrabold tracking-tight">
              RECRUIT<span className="text-primary">.</span>AI
            </span>
          </Link>

          <div className="max-w-md">
            <motion.h2
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl font-semibold tracking-tight text-balance"
            >
              Run your next recruitment drive in one place.
            </motion.h2>

            <ul className="mt-10 space-y-6">
              {FACTS.map((fact, index) => (
                <motion.li
                  key={fact.title}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 + index * 0.08 }}
                  className="flex gap-4"
                >
                  <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-subtle">
                    <fact.icon className="h-5 w-5 text-primary" aria-hidden="true" />
                  </span>
                  <span>
                    <span className="block font-semibold text-sm">{fact.title}</span>
                    <span className="mt-1 block text-sm text-muted-foreground leading-relaxed">
                      {fact.body}
                    </span>
                  </span>
                </motion.li>
              ))}
            </ul>
          </div>

          <p className="text-sm text-muted-foreground">
            Built for college clubs and small teams.
          </p>
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
