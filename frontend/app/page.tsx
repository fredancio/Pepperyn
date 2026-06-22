import { HeroSection } from '@/components/landing/HeroSection';
import { ReportDemoSection } from '@/components/landing/ReportDemoSection';
import { DetectionSection } from '@/components/landing/DetectionSection';
import { ROISection } from '@/components/landing/ROISection';
import { CerveauIASection } from '@/components/landing/CerveauIASection';
import { SecuritySection } from '@/components/landing/SecuritySection';
import { PricingPlans } from '@/components/landing/PricingPlans';
import { FaqSection } from '@/components/landing/FaqSection';
import { Footer } from '@/components/landing/Footer';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="bg-white">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5">
            <img src="/favicon.png?v=5" alt="Pepperyn" className="w-10 h-10 object-contain" />
            <div>
              <span className="text-base font-bold text-[#1A1A2E] block leading-none">Pepperyn IA</span>
              <span className="text-xs text-[#5F6368] block">Financial Control Center</span>
            </div>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-6">
            <Link href="#securite" className="text-sm text-[#5F6368] hover:text-[#1A1A2E] transition-colors">
              Sécurité
            </Link>
            <Link href="#tarifs" className="text-sm text-[#5F6368] hover:text-[#1A1A2E] transition-colors">
              Tarifs
            </Link>
            <Link href="#faq" className="text-sm text-[#5F6368] hover:text-[#1A1A2E] transition-colors">
              FAQ
            </Link>
          </div>

          {/* CTA buttons */}
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="inline-flex items-center px-4 py-2 border border-[#1B73E8] text-[#1B73E8] text-sm font-semibold rounded-xl hover:bg-blue-50 transition-all duration-200"
            >
              Se connecter
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#1B73E8] text-white text-sm font-semibold rounded-xl hover:bg-[#0D47A1] transition-all duration-200 shadow-sm"
            >
              Essai gratuit
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </nav>

      {/* Page content */}
      <main>
        <HeroSection />
        <ReportDemoSection />
        <DetectionSection />
        <ROISection />
        <CerveauIASection />
        <SecuritySection />
        <PricingPlans />
        <FaqSection />

        {/* CTA section */}
        <section className="py-20 bg-[#EFF6FF]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center gap-6">
            <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E]">
              Prêt à reprendre le contrôle de votre rentabilité ?
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
