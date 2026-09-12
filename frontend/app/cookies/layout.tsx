import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Cookies Policy | RECRUIT.AI',
}

export default function CookiesLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
