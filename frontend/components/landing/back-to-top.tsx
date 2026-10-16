'use client'

import { useEffect, useState } from 'react'
import { ArrowUp } from 'lucide-react'

import { cn } from '@/lib/utils'

/**
 * A way back up a long page. Appears once the hero is out of view, sits in
 * the corner on liquid glass, and scrolls instantly when the user prefers
 * reduced motion.
 */
export function BackToTop() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const update = () => setVisible(window.scrollY > window.innerHeight)
    update()
    window.addEventListener('scroll', update, { passive: true })
    return () => window.removeEventListener('scroll', update)
  }, [])

  const toTop = () => {
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    window.scrollTo({ top: 0, behavior: calm ? 'auto' : 'smooth' })
  }

  return (
    <button
      type="button"
      onClick={toTop}
      aria-label="Back to top"
      // Hidden from the tab order and from assistive technology until shown,
      // so it never becomes an invisible focus stop.
      tabIndex={visible ? 0 : -1}
      aria-hidden={!visible}
      className={cn(
        'liquid-glass fixed right-4 bottom-4 z-40 flex size-11 items-center justify-center rounded-full border text-foreground transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] sm:right-6 sm:bottom-6',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring',
        visible ? 'translate-y-0 opacity-100' : 'pointer-events-none translate-y-3 opacity-0',
      )}
    >
      <ArrowUp className="size-5" aria-hidden="true" />
    </button>
  )
}
