import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Analytics | RECRUIT.AI',
}

export default function AnalyticsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
