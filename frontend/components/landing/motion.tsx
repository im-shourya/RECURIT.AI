'use client'

import { motion, useReducedMotion } from 'framer-motion'

/**
 * Shared motion vocabulary for the landing page.
 *
 * Every section leans on the same curve so the page feels animated by one
 * hand: `appleOut` decelerates into place, the way Apple's own transitions do.
 */

export const appleOut = [0.22, 1, 0.36, 1] as const

/** Distance (px) elements travel on a fade-up. Short — Apple never throws things far. */
const TRAVEL = 24

type RevealProps = {
  children: React.ReactNode
  className?: string
  /** Seconds to wait before starting. */
  delay?: number
  /** Render as a different element — defaults to a div. */
  as?: 'div' | 'section' | 'h2' | 'p' | 'span'
}

/**
 * Fades + lifts its children the first time they scroll into view, once.
 *
 * Entrance opacity lives here rather than on scroll progress on purpose: a
 * pinned section's content fills the viewport for its whole pin, so tying its
 * opacity to scroll leaves it unreadable at both ends of that range.
 *
 * Collapses to a plain render when the user prefers reduced motion.
 */
export function Reveal({ children, className, delay = 0, as = 'div' }: RevealProps) {
  const prefersReducedMotion = useReducedMotion()
  const Component = motion[as]

  if (prefersReducedMotion) {
    return <Component className={className}>{children}</Component>
  }

  return (
    <Component
      className={className}
      initial={{ opacity: 0, y: TRAVEL }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-12% 0px -12% 0px' }}
      transition={{ duration: 0.8, delay, ease: appleOut }}
    >
      {children}
    </Component>
  )
}
