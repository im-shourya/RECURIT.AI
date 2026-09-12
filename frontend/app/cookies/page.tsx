import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function CookiesPolicyPage() {
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
          <h1 className="text-4xl font-bold tracking-tight mb-2">Cookies Policy</h1>
          <p className="text-muted-foreground">Last updated: {new Date().toLocaleDateString()}</p>
        </div>
        
        <div className="prose prose-slate dark:prose-invert max-w-none space-y-6 text-muted-foreground">
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">1. What Are Cookies</h2>
            <p>
              Cookies are small pieces of text sent to your web browser by a website you visit. A cookie file is stored in your web browser and allows the Service or a third-party to recognize you and make your next visit easier and the Service more useful to you.
            </p>
          </section>
          
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">2. How We Use Cookies</h2>
            <p>
              We use cookies to maintain your session when you log in, to remember your preferences, and to understand how you interact with our platform to improve your experience. Specifically, authentication tokens are securely stored to keep you logged in across pages.
            </p>
          </section>
          
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">3. Types of Cookies We Use</h2>
            <p>
              - <strong>Essential Cookies:</strong> We may use essential cookies to authenticate users and prevent fraudulent use of user accounts.<br />
              - <strong>Analytics Cookies:</strong> We may use analytics cookies to track information how the Service is used so that we can make improvements.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">4. Your Choices Regarding Cookies</h2>
            <p>
              If you'd like to delete cookies or instruct your web browser to delete or refuse cookies, please visit the help pages of your web browser. Please note, however, that if you delete cookies or refuse to accept them, you might not be able to use all of the features we offer, you may not be able to store your preferences, and some of our pages might not display properly.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
