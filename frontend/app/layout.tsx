import type { Metadata, Viewport } from 'next'
import { JetBrains_Mono } from 'next/font/google'

import { ThemeProvider } from '@/components/theme-provider'
import { Providers } from '@/components/providers'
import { Toaster } from '@/components/ui/sonner'
import './globals.css'

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
  weight: ['400', '500'],
})

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'https://recuritai.shouryaparashar.in'),
  title: 'RECRUIT.AI',
  description: 'Streamline your recruitment process with AI-powered interviews, automated screening, and intelligent candidate evaluation for organizations of every scale.',
  keywords: ['recruitment', 'AI', 'interviews', 'hiring', 'organizations', 'automation', 'AI recruitment platform',
    'automated interviews',
    'AI hiring software',
    'candidate screening AI',
    'interview automation tool'],
  authors: [
    { name: 'Shourya Parashar', url: 'https://recuritai.shouryaparashar.in' }
  ],
  creator: 'Shourya Parashar',
  publisher: 'RECRUIT.AI',
  alternates: {
    canonical: 'https://recuritai.shouryaparashar.in',
  },
  openGraph: {
    title: 'RECRUIT.AI – AI Powered Recruitment & Interview Platform',
    description: 'Streamline your recruitment process with AI-powered interviews, automated screening, and intelligent candidate evaluation for organizations of every scale.',
    url: 'https://recuritai.shouryaparashar.in',
    siteName: 'RECRUIT.AI',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'RECRUIT.AI',
    description: 'AI-powered recruitment platform',
    images: ['/og-image.png'],
  },
  icons: {
    icon: [
      {
        url: '/icon.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.png',
        type: 'image/png',
      },
    ],
    apple: '/icon.png',
  },
}

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#F5F5F7' },
    { media: '(prefers-color-scheme: dark)', color: '#000000' },
  ],
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
          <body className={`${jetbrainsMono.variable} font-sans antialiased`}>
            <ThemeProvider
              attribute="class"
              defaultTheme="light"
              enableSystem
              disableTransitionOnChange
            >
              <Providers>{children}</Providers>
              <Toaster />
            </ThemeProvider>
            <script
              type="application/ld+json"
              dangerouslySetInnerHTML={{
                __html: JSON.stringify({
                  "@context": "https://schema.org",
                  "@type": "Organization",
                  name: "RECRUIT.AI",
                  url: "https://recuritai.shouryaparashar.in",
                  logo: "https://recuritai.shouryaparashar.in/icon.png",
                }),
              }}
            />
          </body>
        </html>
  )
}
