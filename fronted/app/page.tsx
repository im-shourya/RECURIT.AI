import { Navbar } from '@/components/navbar'
import { Footer } from '@/components/footer'
import { AnimatedBackground } from '@/components/animated-background'
import { HeroSection } from '@/components/landing/hero-section'
import { TrustedBySection } from '@/components/landing/trusted-by-section'
import { FeaturesSection } from '@/components/landing/features-section'
import { HowItWorksSection } from '@/components/landing/how-it-works-section'
import { CTASection } from '@/components/landing/cta-section'

export default function HomePage() {
  return (
    <div className="relative min-h-screen">
      <AnimatedBackground />
      <Navbar />
      <main>
        <HeroSection />
        <TrustedBySection />
        <FeaturesSection />
        <HowItWorksSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}
