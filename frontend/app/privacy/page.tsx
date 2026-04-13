import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function PrivacyPage() {
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
          <h1 className="text-4xl font-bold tracking-tight mb-2">Privacy Policy</h1>
          <p className="text-muted-foreground">Last updated: {new Date().toLocaleDateString()}</p>
        </div>
        
        <div className="prose prose-slate dark:prose-invert max-w-none space-y-6 text-muted-foreground">
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">1. Information We Collect</h2>
            <p>
              When applying for a role through RECRUIT.AI, we collect information necessary for the recruitment process including your name, email address, resume references, and GitHub portfolio links. During AI interviews, we capture transcripts and potentially audio recordings, which are solely shared with the hiring organisation.
            </p>
          </section>
          
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">2. How We Use It</h2>
            <p>
              Data is strictly used to evaluate your suitability for the recruitment drives you actively opt into. Your scores, GitHub analysis, and AI interview metrics are accessible only by the evaluating organisation. We do not sell your personal data to third parties.
            </p>
          </section>
          
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">3. Data Security</h2>
            <p>
              We implement industry-standard security measures to ensure your data is safe. Passwords and tokens are securely hashed, and communication between our servers and your device is encrypted.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">4. Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy, your data, or would like to request account deletion, please consult the organisation you applied to or contact us directly at privacy@recruit-ai.com.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
