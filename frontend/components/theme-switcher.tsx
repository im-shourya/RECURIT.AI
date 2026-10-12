'use client'

import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'
import { Monitor, Moon, Sun } from 'lucide-react'

import { cn } from '@/lib/utils'

const OPTIONS = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
] as const

/**
 * Light / dark / system, as a segmented control.
 *
 * Compact (icons only) in the footer and the account menu; labelled on the
 * settings page, where there is room to say what each option is.
 */
export function ThemeSwitcher({ labelled = false }: { labelled?: boolean }) {
  const { theme, setTheme } = useTheme()
  // The stored theme is only known after mount; until then nothing is
  // shown as selected, so the server and client render the same markup.
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <div
      role="radiogroup"
      aria-label="Appearance"
      className={cn('inline-flex rounded-lg border p-0.5', labelled && 'bg-muted')}
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const selected = mounted && theme === value
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={labelled ? undefined : label}
            title={labelled ? undefined : label}
            onClick={() => setTheme(value)}
            className={cn(
              'flex items-center justify-center gap-2 rounded-md text-muted-foreground transition-colors',
              labelled ? 'h-9 px-4 text-sm font-medium' : 'h-7 w-8',
              selected
                ? labelled
                  ? 'bg-card text-foreground shadow-elevation-1'
                  : 'bg-secondary text-foreground'
                : 'hover:text-foreground',
            )}
          >
            <Icon className="size-4" aria-hidden="true" />
            {labelled && label}
          </button>
        )
      })}
    </div>
  )
}
