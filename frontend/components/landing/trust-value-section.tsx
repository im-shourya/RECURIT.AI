import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

import { Reveal } from './motion'

/**
 * The one-line case for the product, straight after the pipeline scrub.
 *
 * It used to be pinned for two screens of scrolling with a parallax shrink
 * and a second ambient glow. One statement does not need a pin; it needs to
 * be read once, so it is an ordinary section now.
 */
export function TrustValueSection() {
  return (
    <section className="bg-background py-28 sm:py-36">
      <div className="mx-auto flex max-w-5xl flex-col items-center px-4 text-center sm:px-6 lg:px-8">
        <Reveal>
          <h2 className="section-title mb-8 text-foreground">
            Hire smarter.
            <br />
            Interview less.
          </h2>
        </Reveal>

        <Reveal delay={0.1}>
          <p className="body-large mx-auto mb-12 max-w-3xl text-balance text-muted-foreground">
            Applications, submissions, interviews and decisions in one place, instead of
            a form, a spreadsheet and a group chat.
          </p>
        </Reveal>

        <Reveal delay={0.18}>
          <Link
            href="/#how-it-works"
            className="group inline-flex items-center font-medium text-primary transition-colors hover:text-primary-hover"
          >
            See how it works
            <ArrowRight
              className="ml-1.5 size-4 transition-transform duration-300 group-hover:translate-x-0.5"
              aria-hidden="true"
            />
          </Link>
        </Reveal>
      </div>
    </section>
  )
}
