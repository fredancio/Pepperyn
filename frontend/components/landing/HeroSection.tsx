import Link from 'next/link';

export function HeroSection() {
  return (
    <section className="relative bg-white overflow-hidden">

      {/* Background gradient — UNCHANGED */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-indigo-50 pointer-events-none" />
      <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[640px] h-[320px] bg-[#1B73E8]/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 lg:pt-28 lg:pb-20 flex flex-col items-center text-center gap-7">

        {/* Badge — UNCHANGED */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-[#1B73E8]" />
          <span className="text-sm font-medium text-[#1B73E8]">Copilote Financier Exécutif</span>
        </div>

        {/* Headline — UNCHANGED */}
        <h1 className="text-4xl lg:text-5xl xl:text-6xl font-extrabold text-[#1A1A2E] leading-tight max-w-3xl">
          Ne prenez plus seul vos décisions financières.
        </h1>

        {/* Subtitle — UNCHANGED */}
        <p className="text-lg lg:text-xl text-[#5F6368] leading-relaxed max-w-2xl">
          Pepperyn transforme vos données financières en décisions exécutives, rapports de
          direction et plans d&apos;action priorisés en quelques minutes.
        </p>

        {/* Phrase signature — UNCHANGED */}
        <p className="text-base lg:text-lg text-[#1A1A2E] font-semibold leading-snug max-w-xl border-t border-gray-100 pt-6 mt-1">
          Le meilleur Directeur Financier n&apos;est plus celui qui travaille le plus.
          <br className="hidden sm:block" />
          {' '}C&apos;est celui qui prend les meilleures décisions, au bon moment.
        </p>

        {/* CTAs — UNCHANGED */}
        <div className="flex flex-col sm:flex-row items-center gap-3 mt-1">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 px-8 py-4 bg-[#1B73E8] text-white rounded-xl font-semibold text-base hover:bg-[#0D47A1] transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5"
          >
            Obtenir mon diagnostic
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <Link
            href="#livrables"
            className="inline-flex items-center gap-2 px-8 py-4 bg-transparent text-[#1A1A2E] rounded-xl font-semibold text-base border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all duration-200"
          >
            Découvrir un rapport exécutif
          </Link>
        </div>

        {/* ── Hero visual ── */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/hero-workflow.png"
          alt="Pepperyn — De vos données à vos décisions exécutives"
          className="w-full h-auto mt-9"
        />

        {/* Trust line — UNCHANGED */}
        <p className="text-xs text-[#5F6368] mt-2">
          Sans carte bancaire · Résultats en quelques minutes · Données anonymisées avant analyse
        </p>
      </div>
    </section>
  );
}
