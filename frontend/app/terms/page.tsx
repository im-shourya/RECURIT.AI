import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function TermsPage() {
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
          <h1 className="text-4xl font-bold tracking-tight mb-2">Terms of Service</h1>
          <p className="text-muted-foreground">Last updated: {new Date().toLocaleDateString()}</p>
        </div>
        
        <div className="prose prose-slate dark:prose-invert max-w-none space-y-6 text-muted-foreground">
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">1. Acceptance of Terms</h2>
            <p>
              By accessing and using RECRUIT.AI, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our service.
            </p>
          </section>
          
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">2. Description of Service</h2>
            <p>
              RECRUIT.AI provides an AI-powered platform for technical recruitment, including technical task evaluations and AI-conducted interviews. We reserve the right to modify or discontinue the service at any time.
            </p>
          </section>
          
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">3. User Responsibilities</h2>
            <p>
              When using the platform, you agree to provide accurate information and maintain the confidentiality of any interview links or tokens provided. You are responsible for all activities that occur under your applicant ID.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">4. Intellectual Property</h2>
            <p>
              The platform, including its original content, features, AI models, and functionality, are owned by RECRUIT.AI and are protected by international copyright, trademark, and other intellectual property laws.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold text-foreground">5. Academic Integrity</h2>
            <p>
              For candidates, strict adherence to academic integrity is required during technical assessments and AI interviews. Any detection of malpractice will result in immediate disqualification and notification to the respective organisation.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
