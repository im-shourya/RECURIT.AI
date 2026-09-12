'use client'

import React, { useEffect, useRef, useState } from 'react'
import { getSvgPath } from 'figma-squircle'
import { cn } from '@/lib/utils'
import { Slot } from '@radix-ui/react-slot'

export interface SquircleProps extends React.HTMLAttributes<HTMLElement> {
  cornerRadius?: number
  cornerSmoothing?: number
  borderClassName?: string
  asChild?: boolean
}

export function useSquircle({ cornerRadius = 16, cornerSmoothing = 1, borderClassName }: Omit<SquircleProps, 'asChild'>) {
  const internalRef = useRef<HTMLElement>(null)
  const [size, setSize] = useState({ width: 0, height: 0 })

  const ref = (node: HTMLElement | null) => {
    internalRef.current = node
  }

  useEffect(() => {
    if (!internalRef.current) return

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const box = entry.borderBoxSize?.[0]
        if (box) {
          setSize({ width: box.inlineSize, height: box.blockSize })
        } else {
          const rect = entry.target.getBoundingClientRect()
          setSize({ width: rect.width, height: rect.height })
        }
      }
    })

    observer.observe(internalRef.current)
    return () => observer.disconnect()
  }, [])

  const path = size.width > 0 && size.height > 0
    ? getSvgPath({
        width: size.width,
        height: size.height,
        cornerRadius,
        cornerSmoothing,
      })
    : ''

  const isReady = path !== ''
  const clipStyle = {
    clipPath: isReady ? `path('${path}')` : undefined,
    WebkitClipPath: isReady ? `path('${path}')` : undefined,
  }

  const svgOverlay = borderClassName && isReady ? (
    <svg className="absolute inset-0 pointer-events-none z-50" width={size.width} height={size.height}>
      <path d={path} className={cn("fill-transparent", borderClassName)} strokeWidth="2" />
    </svg>
  ) : null

  return { ref, clipStyle, svgOverlay, isReady }
}

export const Squircle = React.forwardRef<HTMLElement, SquircleProps>(
  ({ className, cornerRadius = 16, cornerSmoothing = 1, borderClassName, asChild, children, style, ...props }, forwardedRef) => {
    const { ref: hookRef, clipStyle, svgOverlay } = useSquircle({ cornerRadius, cornerSmoothing, borderClassName })
    
    const ref = (node: HTMLElement) => {
      hookRef(node)
      if (typeof forwardedRef === 'function') forwardedRef(node)
      else if (forwardedRef) forwardedRef.current = node
    }

    if (asChild && React.isValidElement(children)) {
      const childProps = children.props as any;
      return (
        <Slot
          {...props}
          ref={ref as React.RefObject<HTMLElement>}
          className={cn("relative overflow-hidden", className, childProps.className)}
          style={{ ...style, ...childProps.style, ...clipStyle }}
        >
          {svgOverlay ? (
            React.cloneElement(children, {
              children: (
                <>
                  {svgOverlay}
                  {childProps.children}
                </>
              )
            })
          ) : (
            children
          )}
        </Slot>
      )
    }
    
    return (
      <div
        ref={ref as React.RefObject<HTMLDivElement>}
        className={cn("relative overflow-hidden", className)}
        style={{ ...style, ...clipStyle }}
        {...props}
      >
        {svgOverlay}
        {children}
      </div>
    )
  }
)

Squircle.displayName = 'Squircle'
