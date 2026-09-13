import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Login | RECRUIT.AI',
}

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
