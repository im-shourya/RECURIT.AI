import { Navbar } from '@/components/navbar'
import { Footer } from '@/components/footer'
import { HeroSection } from '@/components/landing/hero-section'
import { TrustValueSection } from '@/components/landing/trust-value-section'
import { ProductStorySection } from '@/components/landing/product-story-section'
import { CapabilitiesSection } from '@/components/landing/capabilities-section'
import { OrganizationWorkflowSection } from '@/components/landing/organization-workflow-section'
import { ApplicantWorkflowSection } from '@/components/landing/applicant-workflow-section'
import { DecisionMomentSection } from '@/components/landing/decision-moment-section'
import { CTASection } from '@/components/landing/cta-section'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Home | RECRUIT.AI',
}

export default function HomePage() {
  return (
    <div className="relative min-h-screen bg-background">
      <Navbar />
      <main>
        <HeroSection />
        <TrustValueSection />
        <ProductStorySection />
        <CapabilitiesSection />
        <OrganizationWorkflowSection />
        <ApplicantWorkflowSection />
        <DecisionMomentSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}
