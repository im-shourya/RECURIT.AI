import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Dashboard | RECRUIT.AI',
}

export default function DashboardPageLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
