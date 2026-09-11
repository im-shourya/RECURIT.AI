'use client'

import { useEffect, useRef } from 'react'

export function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      const gradient = ctx.createRadialGradient(
        canvas.width / 2,
        canvas.height / 3,
        0,
        canvas.width / 2,
        canvas.height / 3,
        canvas.width * 0.6
      )
      // P0341 blue — extremely subtle static wash
      gradient.addColorStop(0, 'rgba(44, 82, 186, 0.02)')
      gradient.addColorStop(1, 'rgba(247, 248, 247, 0)')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      return
    }

    let animationFrameId: number
    let time = 0

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    const draw = () => {
      time += 0.0012
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Primary blue ambient glow — very subtle
      const centerX = canvas.width / 2 + Math.sin(time * 0.35) * 30
      const centerY = canvas.height / 3 + Math.cos(time * 0.2) * 20

      const gradient = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, canvas.width * 0.5
      )
      // #2C52BA at extremely low opacity
      gradient.addColorStop(0, 'rgba(44, 82, 186, 0.025)')
      gradient.addColorStop(0.5, 'rgba(44, 82, 186, 0.01)')
      gradient.addColorStop(1, 'rgba(247, 248, 247, 0)')

      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Secondary blue accent wash
      const center2X = canvas.width * 0.7 + Math.cos(time * 0.25) * 25
      const center2Y = canvas.height * 0.6 + Math.sin(time * 0.4) * 20

      const gradient2 = ctx.createRadialGradient(
        center2X, center2Y, 0,
        center2X, center2Y, canvas.width * 0.3
      )
      // #2552D0 at extremely low opacity
      gradient2.addColorStop(0, 'rgba(37, 82, 208, 0.015)')
      gradient2.addColorStop(1, 'rgba(247, 248, 247, 0)')

      ctx.fillStyle = gradient2
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      animationFrameId = requestAnimationFrame(draw)
    }

    resize()
    draw()

    window.addEventListener('resize', resize)

    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 -z-10 pointer-events-none"
      aria-hidden="true"
    />
  )
}
