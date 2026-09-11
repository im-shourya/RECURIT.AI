'use client'

import { Error500 } from '@/components/error-pages'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  // Log the error for server-side capture
  console.error(error)

  return <Error500 onRetry={reset} />
}
