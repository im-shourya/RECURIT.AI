import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Submit Application | RECRUIT.AI',
}

export default function SubmitLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
