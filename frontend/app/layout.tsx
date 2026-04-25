import type { Metadata, Viewport } from 'next'
import { Inter, Playfair_Display, JetBrains_Mono } from 'next/font/google'

import { ThemeProvider } from '@/components/theme-provider'
import { Providers } from '@/components/providers'
import { Toaster } from '@/components/ui/sonner'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
  weight: ['400', '500', '600', '700', '800'],
})

const playfairDisplay = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-playfair',
  display: 'swap',
  weight: ['600', '700'],
})

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
        url: '/favicon.ico',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/favicon.ico',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/favicon.ico',
        type: 'image/x-icon',
      },
    ],
    apple: '/favicon.ico',
  },
}

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FBFBFD' },
    { media: '(prefers-color-scheme: dark)', color: '#0A0A0B' },
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
          <body className={`${inter.variable} ${playfairDisplay.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
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
                  logo: "https://recuritai.shouryaparashar.in/favicon.ico",
                }),
              }}
            />
          </body>
        </html>
  )
}
