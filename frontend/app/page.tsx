import { HeroSection } from '@/components/landing/HeroSection';
import { StorytellingSection } from '@/components/landing/StorytellingSection';
import { WhyBadDecisionsSection } from '@/components/landing/WhyBadDecisionsSection';
import { ROISection } from '@/components/landing/ROISection';
import { DeliverablesSection } from '@/components/landing/DeliverablesSection';
import { CopilotSection } from '@/components/landing/CopilotSection';
import { PositioningSection } from '@/components/landing/PositioningSection';
import { ProofSection } from '@/components/landing/ProofSection';
import { SecuritySection } from '@/components/landing/SecuritySection';
import { PricingPlans } from '@/components/landing/PricingPlans';
import { FaqSection } from '@/components/landing/FaqSection';
import { Footer } from '@/components/landing/Footer';
import { Navbar } from '@/components/landing/Navbar';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="bg-white">
      <Navbar />

      {/* Page content — narration : je vois → je comprends → je mesure → je décide */}
      <main>
        <HeroSection />
        {/* 1. Je vois immédiatement ce que Pepperyn produit */}
        <DeliverablesSection />
        {/* 2. Je comprends le bénéfice opérationnel — avant/après */}
        <StorytellingSection />
        {/* 3. Je comprends pourquoi les entreprises prennent de mauvaises décisions */}
        <WhyBadDecisionsSection />
        {/* 4. Je mesure ce que coûte l'inaction */}
        <ROISection />
        {/* 5. Je découvre que Pepperyn ne s'arrête pas au rapport */}
        <CopilotSection />
        {/* 6. Je comprends pourquoi ce n'est pas un chatbot */}
        <PositioningSection />
        {/* 7. Je mesure les bénéfices réels */}
        <ProofSection />
        {/* 8. Je suis rassuré sur la sécurité */}
        <SecuritySection />
        {/* 9. Je découvre les tarifs */}
        <PricingPlans />
        <FaqSection />

        {/* CTA section */}
        <section className="py-20 bg-[#EFF6FF]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center gap-6">
            <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] max-w-xl">
              Prêt à prendre de meilleures décisions financières ?
            </h2>

            <img src="/favicon.png?v=5" alt="Pepperyn" className="w-20 h-20 object-contain" />

            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#1B73E8] text-white rounded-xl font-bold text-base hover:bg-[#0D47A1] transition-all duration-200 shadow-lg"
            >
              Obtenir mon diagnostic
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>

          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
