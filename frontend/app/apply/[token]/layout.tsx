import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Apply | RECRUIT.AI',
}

export default function ApplyLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
