import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Application Status | RECRUIT.AI',
  description: 'Track the progress of your application.',
  // The URL carries a capability token. robots.txt is advisory and easy to
  // miss, so the page also refuses indexing in its own metadata.
  robots: { index: false, follow: false },
}

export default function StatusLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
