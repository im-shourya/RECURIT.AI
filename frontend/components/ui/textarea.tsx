import * as React from 'react'

import { cn } from '@/lib/utils'
import { Squircle } from './squircle'

function Textarea({ className, style, ...props }: React.ComponentProps<'textarea'>) {
  return (
    <div
      className={cn(
        'relative flex w-full min-w-0 shadow-xs transition-[color,box-shadow]',
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
      <textarea
        data-slot="textarea"
        className={cn(
          'relative z-10 w-full bg-transparent px-3 py-2 text-base outline-none field-sizing-content min-h-16',
          'placeholder:text-muted-foreground',
          'disabled:cursor-not-allowed disabled:opacity-50 md:text-sm'
        )}
        {...props}
      />
    </div>
  )
}

export { Textarea }
