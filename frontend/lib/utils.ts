import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * The URL, if it is an http(s) link, otherwise undefined.
 *
 * Candidate-supplied links are validated by the API, but rows written before
 * that check existed may still hold a `javascript:` URL, which would run in
 * the recruiter's session if used as an href.
 */
export function safeExternalUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined
  try {
    const { protocol } = new URL(url)
    return protocol === 'http:' || protocol === 'https:' ? url : undefined
  } catch {
    return undefined
  }
}
