import { HeroSection } from '@/components/landing/HeroSection';
import { ForWhom } from '@/components/landing/ForWhom';
import { CerveauIASection } from '@/components/landing/CerveauIASection';
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
            <Link href="#pour-qui" className="text-sm text-[#5F6368] hover:text-[#1A1A2E] transition-colors">
              Pour qui ?
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
        <ForWhom />
        <CerveauIASection />
        <FaqSection />

        {/* CTA section */}
        <section className="py-20 bg-[#EFF6FF]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center gap-6">
            <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E]">
              Prêt à gagner du temps sur vos analyses ?
            </h2>

            <img src="/favicon.png?v=5" alt="Pepperyn" className="w-20 h-20 object-contain" />

            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#1B73E8] text-white rounded-xl font-bold text-base hover:bg-[#0D47A1] transition-all duration-200 shadow-lg"
            >
              Analyser mes données
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>

            <a
              href="https://www.linkedin.com/in/fr%C3%A9d%C3%A9ric-anciaux-7192405a/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 border border-[#1B73E8] text-[#1B73E8] rounded-xl font-medium text-sm hover:bg-[#1B73E8] hover:text-white transition-all duration-200"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
              </svg>
              Me contacter sur LinkedIn
            </a>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
