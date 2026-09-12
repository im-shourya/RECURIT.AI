import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Register | RECRUIT.AI',
}

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
