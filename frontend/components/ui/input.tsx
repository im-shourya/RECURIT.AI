import * as React from 'react'

import { cn } from '@/lib/utils'
import { Squircle } from './squircle'

function Input({ className, type, style, ...props }: React.ComponentProps<'input'>) {
  return (
    <div
      className={cn(
        'relative flex h-9 w-full min-w-0 shadow-xs transition-[color,box-shadow]',
        'focus-within:border-ring focus-within:ring-ring/50 focus-within:ring-[3px]',
        'aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive',
        className
      )}
      style={style}
    >
      <Squircle
        cornerRadius={6}
        cornerSmoothing={1}
        borderClassName="stroke-input"
        className="absolute inset-0 z-[0] pointer-events-none bg-transparent dark:bg-input/30"
      />
      <input
        type={type}
        data-slot="input"
        className={cn(
          'relative z-10 w-full bg-transparent px-3 py-1 text-base outline-none',
          'file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium',
          'placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground',
          'disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm'
        )}
        {...props}
      />
    </div>
  )
}

export { Input }
