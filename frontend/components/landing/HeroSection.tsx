import Link from 'next/link';

const deliverables = [
  { verb: 'Préparer',   label: 'Executive Financial Model', primary: false, delay: 0 },
  { verb: 'Décider',    label: 'Executive Report',          primary: true,  delay: 150 },
  { verb: 'Convaincre', label: 'Executive Board Deck',      primary: false, delay: 300 },
];

export function HeroSection() {
  return (
    <section className="relative bg-white overflow-hidden">
      {/* ── Micro-animation keyframes ── */}
      <style>{`
        @keyframes heroFadeUp {
          from { opacity: 0; transform: translateY(18px); }
          to   { opacity: 1; transform: translateY(0);    }
        }
        .hero-doc {
          opacity: 0;
          animation: heroFadeUp 0.55s ease-out forwards;
        }
      `}</style>

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

        {/* ── Hero visual — REDESIGNED (V5.1) ── */}
        <div className="w-full max-w-3xl mt-16">

          {/* Three premium document objects */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-8 sm:gap-5">
            {deliverables.map((doc, i) => (
              <div
                key={doc.label}
                className="hero-doc flex flex-col items-center gap-3 w-full sm:w-auto"
                style={{ animationDelay: `${doc.delay}ms` }}
              >

                {/* Verb — primary navigation label */}
                <span
                  className="text-[10px] font-black uppercase tracking-[0.2em]"
                  style={{ color: doc.primary ? '#1B73E8' : '#94A3B8' }}
                >
                  {doc.verb}
                </span>

                {/* Document object */}
                <div
                  className="relative bg-white rounded-2xl overflow-hidden"
                  style={{
                    width: doc.primary ? '15rem' : '12.5rem',
                    border: doc.primary
                      ? '1px solid rgba(27,115,232,0.14)'
                      : '1px solid #F1F5F9',
                    boxShadow: doc.primary
                      ? '0 24px 60px rgba(27,115,232,0.15), 0 8px 24px rgba(27,115,232,0.10), 0 2px 6px rgba(0,0,0,0.04)'
                      : '0 8px 28px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04)',
                    transform: i === 0
                      ? 'rotate(-1.5deg) translateY(8px)'
                      : i === 2
                        ? 'rotate(1.5deg) translateY(8px)'
                        : 'translateY(-8px)',
                  }}
                >
                  {/* Top accent strip */}
                  <div
                    className="h-1 w-full"
                    style={{ background: doc.primary ? '#1B73E8' : '#E2E8F0' }}
                  />

                  {/* Document body */}
                  <div className="px-4 pt-4 pb-5">

                    {/* Simulated heading line */}
                    <div
                      className="h-2 rounded-full mb-3"
                      style={{
                        width: doc.primary ? '68%' : '58%',
                        background: doc.primary ? 'rgba(27,115,232,0.22)' : '#E2E8F0',
                      }}
                    />

                    {/* Simulated text paragraphs */}
                    <div className="flex flex-col gap-1.5">
                      {(doc.primary
                        ? ['100%', '88%', '95%', '82%', '90%']
                        : ['100%', '88%', '94%']
                      ).map((w, j) => (
                        <div
                          key={j}
                          className="h-1.5 rounded-full"
                          style={{
                            width: w,
                            background: doc.primary ? 'rgba(27,115,232,0.07)' : '#F1F5F9',
                          }}
                        />
                      ))}
                    </div>

                    {/* Simulated data chart */}
                    <div className="flex items-end gap-1 mt-4" style={{ height: '28px' }}>
                      {(doc.primary
                        ? [38, 56, 44, 72, 52, 80, 62]
                        : [30, 50, 38]
                      ).map((h, j) => (
                        <div
                          key={j}
                          className="flex-1 rounded-sm"
                          style={{
                            height: `${h}%`,
                            background: doc.primary
                              ? `rgba(27,115,232,${0.12 + j * 0.05})`
                              : '#E2E8F0',
                          }}
                        />
                      ))}
                    </div>

                    {/* Document name */}
                    <div
                      className="mt-4 pt-3 border-t"
                      style={{ borderColor: doc.primary ? 'rgba(27,115,232,0.09)' : '#F1F5F9' }}
                    >
                      <span
                        className="text-[9px] font-black uppercase tracking-wide leading-none"
                        style={{ color: doc.primary ? '#1B73E8' : '#CBD5E1' }}
                      >
                        {doc.label}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Legend */}
          <p className="text-sm text-[#5F6368] leading-relaxed text-center max-w-lg mx-auto mt-10 px-4">
            Les mêmes livrables que ceux attendus d&apos;un cabinet de conseil stratégique.
            Générés en quelques minutes à partir de vos propres données.
          </p>

          {/* Vos données → Pepperyn → Décisions exécutives — UNCHANGED */}
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

        {/* Trust line — UNCHANGED */}
        <p className="text-xs text-[#5F6368] mt-2">
          Sans carte bancaire · Résultats en quelques minutes · Données anonymisées avant analyse
        </p>
      </div>
    </section>
  );
}
