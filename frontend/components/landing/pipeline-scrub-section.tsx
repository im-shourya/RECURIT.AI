'use client'

import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

import { appleOut } from './motion'
import { FRAME_COUNT, STAGES, frameAt, phaseAt, type CardState } from './pipeline-frames'

const BEATS = [
  'Everyone applies through one link.',
  'The task shows who can do the work.',
  'You choose who to interview.',
  'And you make the call.',
] as const

/**
 * Whether this device should scrub at all.
 *
 * Apple drops its frame sequences on slow devices and connections in favour
 * of one still. This does the same: reduced motion, Save-Data, or two cores
 * or fewer get the finished frame and a normal-height section.
 */
function useCanScrub() {
  const [canScrub, setCanScrub] = useState(false)

  useEffect(() => {
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)')
    const connection = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection
    const update = () =>
      setCanScrub(
        !calm.matches &&
          !connection?.saveData &&
          (navigator.hardwareConcurrency ?? 4) > 2,
      )
    update()
    calm.addEventListener('change', update)
    return () => calm.removeEventListener('change', update)
  }, [])

  return canScrub
}

type Palette = {
  card: string
  border: string
  muted: string
  text: string
  subtle: string
  primary: string
  primarySubtle: string
  font: string
}

/** Colours come from the theme tokens, so the canvas follows light and dark. */
function readPalette(): Palette {
  const css = getComputedStyle(document.documentElement)
  const v = (name: string) => css.getPropertyValue(name).trim()
  return {
    card: v('--card'),
    border: v('--border'),
    muted: v('--muted'),
    text: v('--foreground'),
    subtle: v('--muted-foreground'),
    primary: v('--primary'),
    primarySubtle: v('--primary-subtle'),
    font: getComputedStyle(document.body).fontFamily,
  }
}

function roundedRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.roundRect(x, y, w, h, Math.min(r, h / 2))
}

function draw(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  index: number,
  palette: Palette,
) {
  const { cards } = frameAt(index)
  ctx.clearRect(0, 0, width, height)

  const columns = STAGES.length
  const columnWidth = width / columns
  const headerHeight = 40
  const cardHeight = Math.max(14, Math.min(26, (height - headerHeight - 8) / 18 - 4))
  const gap = Math.max(3, cardHeight * 0.22)
  const cardWidth = Math.min(columnWidth - 16, 200)

  // Column headings and guides.
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.font = `600 ${width < 480 ? 12 : 14}px ${palette.font}`
  STAGES.forEach((stage, i) => {
    const cx = columnWidth * (i + 0.5)
    ctx.fillStyle = palette.subtle
    ctx.fillText(stage, cx, headerHeight / 2)
    if (i > 0) {
      ctx.strokeStyle = palette.border
      ctx.globalAlpha = 0.6
      ctx.beginPath()
      ctx.moveTo(columnWidth * i, headerHeight)
      ctx.lineTo(columnWidth * i, height)
      ctx.stroke()
      ctx.globalAlpha = 1
    }
  })

  const drawCard = (card: CardState) => {
    if (card.presence <= 0) return
    const cx = columnWidth * (card.column + 0.5)
    const x = cx - cardWidth / 2
    const y = headerHeight + 8 + card.row * (cardHeight + gap)
    const selected = card.outcome === 'selected'
    const faded = card.stalled || card.outcome === 'declined'

    ctx.globalAlpha = card.presence * (faded ? 0.4 : 1)
    roundedRect(ctx, x, y, cardWidth, cardHeight, 6)
    ctx.fillStyle = selected ? palette.primarySubtle : palette.card
    ctx.fill()
    ctx.lineWidth = selected ? 1.5 : 1
    ctx.strokeStyle = selected ? palette.primary : palette.border
    ctx.stroke()

    // An avatar and a name line, abstracted: no invented people.
    const r = cardHeight * 0.28
    ctx.beginPath()
    ctx.arc(x + cardHeight * 0.5, y + cardHeight / 2, r, 0, Math.PI * 2)
    ctx.fillStyle = selected ? palette.primary : palette.muted
    ctx.fill()
    roundedRect(ctx, x + cardHeight, y + cardHeight * 0.38, cardWidth * 0.45, cardHeight * 0.24, 3)
    ctx.fillStyle = selected ? palette.primary : palette.border
    ctx.fill()
    ctx.globalAlpha = 1
  }

  // Selected cards last, so they sit on top of anything passing.
  cards.filter((c) => c.outcome !== 'selected').forEach(drawCard)
  cards.filter((c) => c.outcome === 'selected').forEach(drawCard)
}

/**
 * The hiring pipeline, scrubbed by scroll.
 *
 * The canvas is pinned while the section scrolls past, and scroll progress
 * picks the frame, exactly as Apple's product pages do with image sequences.
 * Scrolling is never taken over: the page moves natively, and drawing
 * happens once per animation frame, only when the frame index changes.
 */
export function PipelineScrubSection() {
  const sectionRef = useRef<HTMLElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const canScrub = useCanScrub()
  const [beat, setBeat] = useState(BEATS.length - 1)

  useEffect(() => {
    const section = sectionRef.current
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!section || !canvas || !ctx) return

    let palette = readPalette()
    let width = 0
    let height = 0
    let drawn = -1
    let pending = 0

    const frameForScroll = () => {
      if (!canScrub) return FRAME_COUNT - 1
      const rect = section.getBoundingClientRect()
      const travel = rect.height - window.innerHeight
      const progress = travel > 0 ? Math.min(1, Math.max(0, -rect.top / travel)) : 1
      return Math.min(FRAME_COUNT - 1, Math.floor(progress * FRAME_COUNT))
    }

    const render = (force = false) => {
      pending = 0
      const index = frameForScroll()
      if (!force && index === drawn) return
      drawn = index
      draw(ctx, width, height, index, palette)
      setBeat(phaseAt(index))
    }

    const schedule = () => {
      if (!pending) pending = requestAnimationFrame(() => render())
    }

    // Sharp on high-density screens, capped at 2x to keep fill cost sane.
    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, 2)
      width = canvas.clientWidth
      height = canvas.clientHeight
      canvas.width = Math.round(width * ratio)
      canvas.height = Math.round(height * ratio)
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      render(true)
    }

    const sizeObserver = new ResizeObserver(resize)
    sizeObserver.observe(canvas)

    // The theme switches by toggling a class on <html>; redraw in the new colours.
    const themeObserver = new MutationObserver(() => {
      palette = readPalette()
      render(true)
    })
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

    if (canScrub) {
      window.addEventListener('scroll', schedule, { passive: true })
    }

    return () => {
      sizeObserver.disconnect()
      themeObserver.disconnect()
      window.removeEventListener('scroll', schedule)
      if (pending) cancelAnimationFrame(pending)
    }
  }, [canScrub])

  return (
    <section
      ref={sectionRef}
      id="pipeline"
      aria-labelledby="pipeline-heading"
      className={canScrub ? 'relative h-[320vh] bg-background' : 'relative bg-background py-24'}
    >
      <div
        className={
          canScrub
            ? 'sticky top-0 flex h-screen flex-col items-center justify-center px-4 sm:px-6 lg:px-8'
            : 'flex flex-col items-center px-4 sm:px-6 lg:px-8'
        }
      >
        <div className="mb-8 flex min-h-[7.5rem] w-full max-w-3xl items-end justify-center text-center sm:mb-10">
          <AnimatePresence mode="wait" initial={false}>
            <motion.h2
              id="pipeline-heading"
              key={beat}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.35, ease: appleOut }}
              className="text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-5xl"
            >
              {canScrub ? BEATS[beat] : 'From one link to a decision.'}
            </motion.h2>
          </AnimatePresence>
        </div>

        <canvas
          ref={canvasRef}
          role="img"
          aria-label="Illustration: applicants move from Applied to Task, then to Interview, and a few are selected at Decision."
          className="h-[52vh] max-h-[560px] min-h-[320px] w-full max-w-5xl"
        />

        <p className="mt-6 text-center text-xs text-muted-foreground">
          Illustration of a drive. Recruiters invite and decide at every step.
        </p>
      </div>
    </section>
  )
}
