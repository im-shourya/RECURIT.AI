import { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * There is a stray, empty `package-lock.json` at the repository root (no
 * package.json and no node_modules beside it). Turbopack infers the workspace
 * root from lockfiles, picks that directory, and then fails to resolve
 * `tailwindcss` for the `@import 'tailwindcss'` in app/globals.css.
 * Pinning the root to this app keeps resolution inside frontend/node_modules.
 */
const appRoot = dirname(fileURLToPath(import.meta.url))

const isDev = process.env.NODE_ENV !== 'production'

// The only origin besides this one that the browser talks to.
const apiOrigin = new URL(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').origin

/**
 * Scripts still need 'unsafe-inline': next-themes and the JSON-LD block are
 * inline, and Next.js bootstraps with inline scripts unless every page is
 * rendered with a nonce. The policy still stops scripts loading from any
 * other origin, and limits where data can be sent to this app and the API.
 *
 * Images and media accept any https source because logos and interview
 * recordings are served from object storage through presigned URLs.
 */
const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ''}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https:",
  "media-src 'self' blob: https:",
  "font-src 'self' data:",
  `connect-src 'self' ${apiOrigin}${isDev ? ' ws:' : ''}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  // Only when the API is already https: upgrading a local http API breaks
  // a production build run on localhost.
  ...(!isDev && apiOrigin.startsWith('https:') ? ['upgrade-insecure-requests'] : []),
].join('; ')

const securityHeaders = [
  { key: 'Content-Security-Policy', value: contentSecurityPolicy },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  // Submission, interview and status links carry a token in the path.
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  // The interview page needs camera and microphone; nothing embedded may.
  {
    key: 'Permissions-Policy',
    value: 'camera=(self), microphone=(self), geolocation=(), payment=(), usb=()',
  },
  ...(isDev
    ? []
    : [{ key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains' }]),
]

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: appRoot,
  },
  images: {
    unoptimized: true,
  },
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }]
  },
}

export default nextConfig
