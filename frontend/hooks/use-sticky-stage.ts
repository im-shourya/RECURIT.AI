import * as React from 'react'

/**
 * The landing page pins several sections with `sm:sticky sm:h-screen` and drives
 * their contents from scroll progress. Below `sm` those sections collapse to a
 * normal stacked layout, so the scroll-linked transforms must NOT run — the
 * element is only ~1 viewport tall there and progress would race 0→1 while the
 * content is still on screen, flashing it in and out.
 *
 * Returns true only when the pinned treatment is actually active: viewport is
 * at least `sm`, and the user hasn't asked for reduced motion.
 *
 * Starts false so SSR and the first client render agree; the pinned layout is
 * a progressive enhancement applied after mount.
 */

const SM_BREAKPOINT = 640

export function useStickyStage() {
  const [enabled, setEnabled] = React.useState(false)

  React.useEffect(() => {
    const wide = window.matchMedia(`(min-width: ${SM_BREAKPOINT}px)`)
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)')

    const update = () => setEnabled(wide.matches && !calm.matches)

    update()
    wide.addEventListener('change', update)
    calm.addEventListener('change', update)
    return () => {
      wide.removeEventListener('change', update)
      calm.removeEventListener('change', update)
    }
  }, [])

  return enabled
}
