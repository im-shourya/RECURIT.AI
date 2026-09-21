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

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: appRoot,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
