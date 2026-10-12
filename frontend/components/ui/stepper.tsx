import { Check } from 'lucide-react'

import { cn } from '@/lib/utils'

export type Step = { id: number; title: string; description?: string }

/**
 * A horizontal progress indicator for multi-step forms.
 *
 * Steps sit in equal columns with their circles on one line, so a title that
 * wraps never pushes its circle out of alignment, and the connectors run
 * between circle centres rather than between whole columns.
 *
 * Every colour comes from the theme tokens, so it reads the same in light and
 * dark. Below `sm` the labels give way to a single "Step 2 of 4" line.
 */
export function Stepper({ steps, current }: { steps: Step[]; current: number }) {
  const active = steps.find((s) => s.id === current)

  return (
    <nav aria-label="Progress">
      <ol
        className="grid"
        style={{ gridTemplateColumns: `repeat(${steps.length}, minmax(0, 1fr))` }}
      >
        {steps.map((step, index) => {
          const done = step.id < current
          const isCurrent = step.id === current
          return (
            <li
              key={step.id}
              aria-current={isCurrent ? 'step' : undefined}
              className="relative flex flex-col items-center text-center"
            >
              {index < steps.length - 1 && (
                <span
                  aria-hidden="true"
                  className={cn(
                    // From just right of this circle to just left of the next.
                    'absolute top-5 left-[calc(50%+1.75rem)] right-[calc(-50%+1.75rem)] h-px transition-colors duration-500',
                    done ? 'bg-primary' : 'bg-border',
                  )}
                />
              )}

              <span
                className={cn(
                  'relative flex size-10 items-center justify-center rounded-full text-sm font-semibold transition-all duration-300',
                  done && 'bg-primary text-primary-foreground',
                  isCurrent && 'bg-primary text-primary-foreground ring-4 ring-primary/20',
                  !done && !isCurrent && 'border bg-card text-muted-foreground',
                )}
              >
                {done ? <Check className="size-5" aria-hidden="true" /> : step.id}
                <span className="sr-only">
                  {done ? ', completed' : isCurrent ? ', current step' : ''}
                </span>
              </span>

              <span className="mt-3 hidden px-2 sm:block">
                <span
                  className={cn(
                    'block text-sm font-medium',
                    done || isCurrent ? 'text-foreground' : 'text-muted-foreground',
                  )}
                >
                  {step.title}
                </span>
                {step.description && (
                  <span className="mt-0.5 block text-xs text-muted-foreground">
                    {step.description}
                  </span>
                )}
              </span>
            </li>
          )
        })}
      </ol>

      {active && (
        <p className="mt-4 text-center text-sm sm:hidden">
          <span className="text-muted-foreground">
            Step {active.id} of {steps.length} ·{' '}
          </span>
          <span className="font-medium text-foreground">{active.title}</span>
        </p>
      )}
    </nav>
  )
}
