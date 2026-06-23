import Link from 'next/link';

const documents = [
  { label: 'Executive Financial Model', sub: 'Le modèle' },
  { label: 'Executive Report', sub: 'La décision' },
  { label: 'Executive Board Deck', sub: 'Le comité' },
];

export function HeroSection() {
  return (
    <section className="relative bg-white overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-indigo-50 pointer-events-none" />
      <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[640px] h-[320px] bg-[#1B73E8]/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 lg:pt-28 lg:pb-20 flex flex-col items-center text-center gap-7">

        {/* Eyebrow */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-[#1B73E8]" />
          <span className="text-sm font-medium text-[#1B73E8]">Copilote Financier Exécutif</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl lg:text-5xl xl:text-6xl font-extrabold text-[#1A1A2E] leading-tight max-w-3xl">
          Ne prenez plus seul vos décisions financières.
        </h1>

        {/* Subtitle */}
        <p className="text-lg lg:text-xl text-[#5F6368] leading-relaxed max-w-2xl">
          Pepperyn transforme vos données financières en décisions exécutives, rapports de
          direction et plans d&apos;action priorisés en quelques minutes.
        </p>

        {/* Phrase signature */}
        <p className="text-base lg:text-lg text-[#1A1A2E] font-semibold leading-snug max-w-xl border-t border-gray-100 pt-6 mt-1">
          Le meilleur Directeur Financier n&apos;est plus celui qui travaille le plus.
          <br className="hidden sm:block" />
          {' '}C&apos;est celui qui prend les meilleures décisions, au bon moment.
        </p>

        {/* CTAs */}
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

        {/* Hero visual — transformation, pas une interface */}
        <div className="w-full max-w-3xl mt-10">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-0">
            {documents.map((doc, i) => (
              <div key={doc.label} className="flex items-center gap-3 sm:gap-0 w-full sm:w-auto">
                <div className="flex-1 sm:flex-initial flex flex-col items-center gap-2 bg-white border border-gray-100 rounded-2xl shadow-sm px-6 py-7 sm:w-52">
                  <span className="text-[11px] font-bold text-[#1B73E8] uppercase tracking-wide">{doc.sub}</span>
                  <span className="text-sm font-bold text-[#1A1A2E] text-center leading-snug">{doc.label}</span>
                </div>
                {i < documents.length - 1 && (
                  <div className="hidden sm:flex items-center justify-center px-2 flex-shrink-0">
                    <svg className="w-5 h-5 text-[#1B73E8]/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </div>
                )}
                {i < documents.length - 1 && (
                  <svg className="sm:hidden w-5 h-5 text-[#1B73E8]/50 rotate-90 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                )}
              </div>
            ))}
          </div>

          {/* Vos données → Pepperyn → Décisions exécutives */}
          <div className="flex items-center justify-center gap-3 sm:gap-5 mt-8 text-xs sm:text-sm font-semibold text-[#5F6368]">
            <span>Vos données</span>
            <svg className="w-4 h-4 text-gray-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
            <span className="text-[#1B73E8]">Pepperyn</span>
            <svg className="w-4 h-4 text-gray-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
            <span className="text-[#1A1A2E]">Décisions exécutives</span>
          </div>
        </div>

        {/* Micro trust line */}
        <p className="text-xs text-[#5F6368] mt-2">
          Sans carte bancaire · Résultats en quelques minutes · Données anonymisées avant analyse
        </p>
      </div>
    </section>
  );
}
