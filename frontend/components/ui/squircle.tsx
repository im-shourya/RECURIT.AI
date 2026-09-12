'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'
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
  const internalRef = useRef<HTMLElement | null>(null)
  const [size, setSize] = useState({ width: 0, height: 0 })

  const ref = useCallback((node: HTMLElement | null) => {
    internalRef.current = node
  }, [])

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
  const clipStyle: React.CSSProperties = {
    clipPath: isReady ? `path('${path}')` : undefined,
    WebkitClipPath: isReady ? `path('${path}')` : undefined,
  }

  const svgOverlay = borderClassName && isReady ? (
    <svg className="absolute inset-0 pointer-events-none z-50 overflow-visible" width="100%" height="100%" viewBox={`0 0 ${size.width} ${size.height}`}>
      <path d={path} className={cn("fill-transparent", borderClassName)} strokeWidth="2" />
    </svg>
  ) : null

  return { ref, clipStyle, svgOverlay, isReady }
}

export const Squircle = React.forwardRef<HTMLElement, SquircleProps>(
  ({ className, cornerRadius = 16, cornerSmoothing = 1, borderClassName, asChild, children, style, ...props }, forwardedRef) => {
    const { ref: hookRef, clipStyle, svgOverlay } = useSquircle({ cornerRadius, cornerSmoothing, borderClassName })

    const combinedRef = useCallback(
      (node: HTMLElement | null) => {
        hookRef(node)
        if (typeof forwardedRef === 'function') forwardedRef(node)
        else if (forwardedRef) (forwardedRef as React.MutableRefObject<HTMLElement | null>).current = node
      },
      [hookRef, forwardedRef]
    )

    if (asChild && React.isValidElement(children)) {
      const childProps = children.props as Record<string, unknown>;
      return (
        <Slot
          {...props}
          ref={combinedRef}
          className={cn("relative overflow-hidden", className, childProps.className as string | undefined)}
          style={{ ...style, ...(childProps.style as React.CSSProperties | undefined), ...clipStyle }}
        >
          {svgOverlay ? (
            React.cloneElement(children as React.ReactElement<{ children?: React.ReactNode }>, {
              children: (
                <>
                  {svgOverlay}
                  {childProps.children as React.ReactNode}
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
        ref={combinedRef as React.Ref<HTMLDivElement>}
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

