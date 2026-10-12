import Link from 'next/link'
import { Github, Globe, Linkedin, Twitter } from 'lucide-react'

import { ThemeSwitcher } from '@/components/theme-switcher'
import { version } from '../package.json'

const REPOSITORY = 'https://github.com/im-shourya/RECURIT.AI'
const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@shouryaparashar.in'

type FooterLink = { label: string; href: string; external?: boolean }

/** Every href here resolves: an existing route, a section id, or a public URL. */
const COLUMNS: { title: string; links: FooterLink[] }[] = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '/#features' },
      { label: 'How it works', href: '/#how-it-works' },
      { label: 'The pipeline', href: '/#pipeline' },
      { label: 'For organizations', href: '/#for-organizations' },
    ],
  },
  {
    title: 'Account',
    links: [
      { label: 'Create an account', href: '/auth/register' },
      { label: 'Sign in', href: '/auth/login' },
      { label: 'Reset your password', href: '/auth/forgot-password' },
      { label: 'Dashboard', href: '/dashboard' },
    ],
  },
  {
    title: 'For candidates',
    links: [
      { label: 'How applying works', href: '/#for-candidates' },
      { label: 'Contact support', href: `mailto:${SUPPORT_EMAIL}`, external: true },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Source code', href: REPOSITORY, external: true },
      { label: 'Release notes', href: `${REPOSITORY}/releases`, external: true },
      { label: 'Report an issue', href: `${REPOSITORY}/issues`, external: true },
    ],
  },
]

const LEGAL: FooterLink[] = [
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Terms of Service', href: '/terms' },
  { label: 'Cookie Policy', href: '/cookies' },
]

const SOCIAL = [
  { icon: Github, href: 'https://github.com/im-shourya', label: 'GitHub' },
  { icon: Twitter, href: 'https://x.com/im_SParashar/', label: 'X (Twitter)' },
  { icon: Linkedin, href: 'https://www.linkedin.com/in/im-shourya/', label: 'LinkedIn' },
  { icon: Globe, href: 'https://www.shouryaparashar.in/', label: 'Personal website' },
]

function FooterAnchor({ link, className }: { link: FooterLink; className: string }) {
  if (link.external) {
    const isMail = link.href.startsWith('mailto:')
    return (
      <a
        href={link.href}
        className={className}
        {...(isMail ? {} : { target: '_blank', rel: 'noopener noreferrer' })}
      >
        {link.label}
      </a>
    )
  }
  return (
    <Link href={link.href} className={className}>
      {link.label}
    </Link>
  )
}

export function Footer() {
  const linkClass =
    'text-[13px] text-muted-foreground transition-colors duration-200 hover:text-foreground hover:underline underline-offset-4'

  return (
    <footer className="border-t bg-muted/60" aria-labelledby="footer-heading">
      <h2 id="footer-heading" className="sr-only">
        Footer
      </h2>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Brand and directory */}
        <div className="grid gap-10 py-12 lg:grid-cols-[1.2fr_3fr] lg:gap-16 lg:py-16">
          <div>
            <Link href="/" className="inline-flex items-center gap-0.5" aria-label="RECRUIT.AI home">
              <span className="text-base font-extrabold tracking-tight text-foreground">RECRUIT</span>
              <span className="text-primary">.</span>
              <span className="text-base font-extrabold tracking-tight text-foreground">AI</span>
            </Link>
            <p className="mt-4 max-w-xs text-[13px] leading-relaxed text-muted-foreground">
              Recruitment drives for college clubs and small teams: one apply link, task
              submissions, recorded interviews and your decision.
            </p>
            <ul className="mt-6 flex gap-1" aria-label="Social links">
              {SOCIAL.map(({ icon: Icon, href, label }) => (
                <li key={label}>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={label}
                    className="flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  >
                    <Icon className="size-4.5" aria-hidden="true" />
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <nav aria-label="Footer" className="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-4">
            {COLUMNS.map((column) => (
              <div key={column.title}>
                <h3 className="text-[13px] font-semibold text-foreground">{column.title}</h3>
                <ul className="mt-4 space-y-3">
                  {column.links.map((link) => (
                    <li key={link.label}>
                      <FooterAnchor link={link} className={linkClass} />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>
        </div>

        {/* Bottom bar: copyright, policies, version and appearance */}
        <div className="flex flex-col gap-4 border-t py-6 text-xs text-muted-foreground md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
            <p>&copy; {new Date().getFullYear()} RECRUIT.AI. All rights reserved.</p>
            <ul className="flex flex-wrap gap-x-4 gap-y-1">
              {LEGAL.map((link) => (
                <li key={link.label}>
                  <FooterAnchor link={link} className="transition-colors hover:text-foreground" />
                </li>
              ))}
            </ul>
          </div>

          <div className="flex items-center justify-between gap-4 md:justify-end">
            <a
              href={`${REPOSITORY}/releases`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono transition-colors hover:text-foreground"
            >
              v{version}
            </a>
            <span>
              Made by{' '}
              <a
                href="https://shouryaparashar.in"
                target="_blank"
                rel="me noopener noreferrer"
                className="text-foreground hover:underline underline-offset-4"
              >
                Shourya Parashar
              </a>
            </span>
            <ThemeSwitcher />
          </div>
        </div>
      </div>
    </footer>
  )
}
