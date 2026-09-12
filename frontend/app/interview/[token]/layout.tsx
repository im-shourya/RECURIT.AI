import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Interview | RECRUIT.AI',
}

export default function InterviewLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
