import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Cookie Policy - RECRUIT.AI',
  description: 'Learn about how RECRUIT.AI uses cookies and similar technologies to provide, protect, and improve our services.',
}

export default function CookiesPage() {
  return (
    <div className="min-h-screen bg-background relative selection:bg-primary/20">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-background to-background" />
      
      <div className="container relative z-10 px-4 py-16 mx-auto max-w-3xl space-y-8">
        <Button variant="ghost" asChild className="mb-4 -ml-4">
          <Link href="/">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Link>
        </Button>
        
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">Cookie Policy</h1>
          <p className="text-muted-foreground">Last updated: {new Date().toLocaleDateString()}</p>
        </div>
        
        <div className="prose prose-slate dark:prose-invert max-w-none space-y-6 text-muted-foreground">
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">1. What Are Cookies</h2>
            <p>
              Cookies are small text files stored on your device when you visit websites. They help the website remember your actions and preferences (such as authentication state, interface theme, and session tokens) over a period of time.
            </p>
          </section>
          
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">2. How We Use Cookies</h2>
            <p>
              RECRUIT.AI uses cookies strictly for functional and security purposes:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong className="text-foreground">Authentication & Session Management:</strong> To identify you when you log in and keep you authenticated as you navigate through your organization dashboard or applicant portal.
              </li>
              <li>
                <strong className="text-foreground">Preferences:</strong> To remember your selected display settings such as Dark/Light theme mode.
              </li>
              <li>
                <strong className="text-foreground">Security:</strong> To protect against CSRF attacks, fraud, and abuse across assessment drives and interview sessions.
              </li>
            </ul>
          </section>
          
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">3. Third-Party Cookies</h2>
            <p>
              We do not sell data to data brokers or use invasive third-party cross-site advertising trackers. Any external services integrated into RECRUIT.AI (such as AI audio/video APIs or authentication providers) operate under strict enterprise confidentiality standards.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">4. Managing Your Cookie Preferences</h2>
            <p>
              Most web browsers allow you to control cookies through their browser settings. Note that disabling essential cookies may prevent you from logging into your account, creating recruitment drives, or completing scheduled AI assessments.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">5. Contact Us</h2>
            <p>
              If you have any questions about our use of cookies or privacy practices, please contact us at support@shouryaparashar.in.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
