import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Drives | RECRUIT.AI',
}

export default function DrivesLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
