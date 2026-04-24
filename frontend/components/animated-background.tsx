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
      // Just draw a subtle static gradient
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
      gradient.addColorStop(0, 'rgba(45, 139, 139, 0.025)')
      gradient.addColorStop(1, 'rgba(241, 250, 238, 0)')
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
      time += 0.0015
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const centerX = canvas.width / 2 + Math.sin(time * 0.4) * 40
      const centerY = canvas.height / 3 + Math.cos(time * 0.25) * 25

      const gradient = ctx.createRadialGradient(
        centerX,
        centerY,
        0,
        centerX,
        centerY,
        canvas.width * 0.5
      )
      
      gradient.addColorStop(0, 'rgba(45, 139, 139, 0.04)')
      gradient.addColorStop(0.5, 'rgba(45, 139, 139, 0.015)')
      gradient.addColorStop(1, 'rgba(241, 250, 238, 0)')

      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      const center2X = canvas.width * 0.7 + Math.cos(time * 0.3) * 35
      const center2Y = canvas.height * 0.6 + Math.sin(time * 0.5) * 25

      const gradient2 = ctx.createRadialGradient(
        center2X,
        center2Y,
        0,
        center2X,
        center2Y,
        canvas.width * 0.3
      )
      
      gradient2.addColorStop(0, 'rgba(168, 218, 220, 0.025)')
      gradient2.addColorStop(1, 'rgba(241, 250, 238, 0)')

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
