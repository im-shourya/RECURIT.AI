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
 * Light / dark / system, as a segmented control. Lives in the footer, the
 * way apple.com keeps its region and appearance settings out of the way.
 */
export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme()
  // The stored theme is only known after mount; until then nothing is
  // shown as selected, so the server and client render the same markup.
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <div role="radiogroup" aria-label="Appearance" className="inline-flex rounded-lg border p-0.5">
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const selected = mounted && theme === value
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={label}
            title={label}
            onClick={() => setTheme(value)}
            className={cn(
              'flex h-7 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors',
              selected ? 'bg-secondary text-foreground' : 'hover:text-foreground',
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
          </button>
        )
      })}
    </div>
  )
}
