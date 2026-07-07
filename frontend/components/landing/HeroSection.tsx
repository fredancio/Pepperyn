import Link from 'next/link';

/* ── Mini sparkline ────────────────────────────────────────────────── */
function Sparkline({ color = '#16a34a' }: { color?: string }) {
  return (
    <svg width="48" height="22" viewBox="0 0 48 22" fill="none" aria-hidden="true">
      <polyline points="0,18 10,14 20,12 30,8 40,5 48,2" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Waterfall bar chart ────────────────────────────────────────────── */
function WaterfallChart() {
  const bars = [
    { label: 'EBITDA\nInitial', value: '+2,1M€', h: 72, color: '#1B73E8', positive: true },
    { label: 'Achats',         value: '-0,6M€', h: 25, color: '#e07b2a', positive: false },
    { label: 'Frais fixes',    value: '-0,4M€', h: 17, color: '#e07b2a', positive: false },
    { label: 'Sous-\ntraitance', value: '-0,3M€', h: 13, color: '#e07b2a', positive: false },
    { label: 'Autres',         value: '-0,2M€', h: 9,  color: '#DC2626', positive: false },
    { label: 'EBITDA\nCible',  value: '+2,6M€', h: 88, color: '#16a34a', positive: true },
  ];
  return (
    <div className="flex items-end gap-1.5 h-24 px-1">
      {bars.map((b, i) => (
        <div key={i} className="flex flex-col items-center gap-0.5 flex-1">
          <span className="text-[7px] font-bold leading-tight" style={{ color: b.color }}>{b.value}</span>
          <div className="w-full rounded-sm" style={{ height: b.h * 0.7, background: b.color, opacity: b.positive ? 1 : 0.75 }} />
          <span className="text-[6.5px] text-gray-400 text-center whitespace-pre-line leading-tight">{b.label}</span>
        </div>
      ))}
    </div>
  );
}

/* ── 90-day timeline ────────────────────────────────────────────────── */
function Timeline() {
  const steps = [
    { days: '30 JOURS', label: 'Lancer',    active: true  },
    { days: '60 JOURS', label: 'Accélérer', active: true  },
    { days: '90 JOURS', label: 'Mesurer',   active: false },
  ];
  return (
    <div className="relative flex items-center justify-between px-2 mt-1">
      <div className="absolute left-4 right-4 top-2.5 h-0.5 bg-gray-200 -z-0" />
      <div className="absolute left-4 right-1/3 top-2.5 h-0.5 bg-[#1B73E8] z-0" />
      {steps.map((s, i) => (
        <div key={i} className="flex flex-col items-center gap-1 z-10">
          <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
            i === 2 ? 'border-[#16a34a] bg-white' : 'border-[#1B73E8] bg-[#1B73E8]'
          }`}>
            {i < 2 && <span className="w-2 h-2 rounded-full bg-white" />}
            {i === 2 && <span className="w-2 h-2 rounded-full bg-[#16a34a]" />}
          </div>
          <span className="text-[6.5px] font-bold text-gray-400 tracking-widest">{s.days}</span>
          <span className="text-[8px] font-semibold text-[#1A1A2E]">{s.label}</span>
        </div>
      ))}
    </div>
  );
}

/* ── Feature badge ──────────────────────────────────────────────────── */
function FeatureBadge({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-[#1B73E8]/10 flex items-center justify-center text-[#1B73E8]">
        {icon}
      </div>
      <div>
        <p className="text-sm font-bold text-[#1A1A2E] leading-tight">{title}</p>
        <p className="text-xs text-[#5F6368] leading-snug mt-0.5">{desc}</p>
      </div>
    </div>
  );
}

/* ── Hero ───────────────────────────────────────────────────────────── */
export function HeroSection() {
  return (
    <section className="relative bg-white overflow-hidden">

      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-indigo-50 pointer-events-none" />
      <div className="absolute top-10 left-1/4 w-[560px] h-[280px] bg-[#1B73E8]/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-14 lg:pt-16 pb-0">

        {/* ── Two-column row ── */}
        <div className="grid lg:grid-cols-2 gap-10 xl:gap-16 items-center pb-12 lg:pb-16">

          {/* ── Left: text ── */}
          <div className="flex flex-col gap-5">

            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full w-fit">
              <span className="w-1.5 h-1.5 rounded-full bg-[#1B73E8]" />
              <span className="text-sm font-medium text-[#1B73E8]">Copilote Financier Exécutif</span>
            </div>

            <h1 className="text-4xl lg:text-5xl xl:text-6xl font-extrabold text-[#1A1A2E] leading-tight">
              Ne prenez plus seul vos décisions financières.
            </h1>

            <p className="text-lg text-[#5F6368] leading-relaxed">
              Pepperyn transforme vos données financières en décisions exécutives, rapports de
              direction et plans d&apos;action priorisés en quelques minutes.
            </p>

            <p className="text-base text-[#1A1A2E] font-semibold leading-snug border-t border-gray-100 pt-5">
              Le meilleur Directeur Financier n&apos;est plus celui qui travaille le plus.
              <br className="hidden sm:block" />
              {' '}C&apos;est celui qui prend les meilleures décisions, au bon moment.
            </p>

            <div className="flex flex-col sm:flex-row items-start gap-3 mt-1">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-[#1B73E8] text-white rounded-xl font-semibold text-base hover:bg-[#0D47A1] transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5"
              >
                Analyser mon premier fichier gratuitement
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <Link
                href="#livrables"
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-transparent text-[#1A1A2E] rounded-xl font-semibold text-base border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all duration-200"
              >
                Découvrir un rapport exécutif
              </Link>
            </div>

            <p className="text-xs text-[#5F6368] flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Sans carte bancaire · Résultats en quelques minutes · Données anonymisées
            </p>
          </div>

          {/* ── Right: product mockup ── */}
          <div className="relative flex items-start justify-center lg:justify-end">
            <div
              className="w-full max-w-[520px] bg-white rounded-2xl overflow-hidden"
              style={{
                border: '1px solid #e2e8f0',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.04), 0 20px 60px -8px rgba(27,115,232,0.14), 0 8px 24px -4px rgba(0,0,0,0.07)',
              }}
            >
              {/* Top row: two panels */}
              <div className="grid grid-cols-2 divide-x divide-gray-100">

                {/* Left panel: Décision prioritaire */}
                <div className="p-4 flex flex-col gap-3">
                  <p className="text-[8.5px] font-bold uppercase tracking-widest text-[#1B73E8]">Décision prioritaire</p>
                  <p className="text-[13px] font-bold text-[#1A1A2E] leading-tight">Réduire les achats indirects</p>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-green-50 rounded-lg p-2.5">
                      <p className="text-[8px] text-gray-500 leading-tight mb-1">Impact annuel estimé</p>
                      <p className="text-base font-extrabold text-green-600 leading-none">+480 K€</p>
                    </div>
                    <div className="bg-amber-50 rounded-lg p-2.5">
                      <p className="text-[8px] text-gray-500 leading-tight mb-1">ROI</p>
                      <div className="flex gap-px">
                        {[1,2,3,4,5].map(i => (
                          <svg key={i} className="w-2.5 h-2.5 text-amber-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Metrics with sparklines */}
                  <div className="grid grid-cols-3 gap-1 pt-1 border-t border-gray-100">
                    {[
                      { label: 'MARGE',  value: '+1,8pt' },
                      { label: 'EBITDA', value: '+480 K€' },
                      { label: 'CASH',   value: '+320 K€' },
                    ].map(m => (
                      <div key={m.label} className="flex flex-col gap-0.5">
                        <p className="text-[7px] font-bold text-gray-400 tracking-widest">{m.label}</p>
                        <p className="text-[10px] font-extrabold text-green-600">{m.value}</p>
                        <Sparkline />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right panel: 5 decisions chart + 90-day plan */}
                <div className="p-4 flex flex-col gap-3">
                  <p className="text-[8.5px] font-bold uppercase tracking-widest text-gray-400">5 Décisions prioritaires</p>
                  <WaterfallChart />

                  <div className="border-t border-gray-100 pt-3">
                    <p className="text-[8.5px] font-bold uppercase tracking-widest text-gray-400 mb-2">Plan 90 jours</p>
                    <Timeline />
                  </div>
                </div>
              </div>

              {/* Bottom: Recommandations clés */}
              <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
                <p className="text-[8.5px] font-bold text-gray-600 mb-2 italic">Recommandations clés</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                  {[
                    'Concentration client à risque',
                    'Nouveau segment à fort potentiel',
                    'BFR en dégradation structurelle',
                    'Dérive de la masse salariale',
                  ].map((rec, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <svg className="w-3 h-3 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-[9px] text-gray-600 leading-tight">{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Feature badges ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8 py-10 border-t border-gray-100">
          <FeatureBadge
            icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>}
            title="Sécurisé & confidentiel"
            desc="Vos données restent les vôtres"
          />
          <FeatureBadge
            icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
            title="Résultats en quelques minutes"
            desc="Fini les semaines d'analyse"
          />
          <FeatureBadge
            icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>}
            title="100% orienté décision"
            desc="Clair, chiffré, priorisé"
          />
          <FeatureBadge
            icon={<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
            title="Impact mesurable"
            desc="Suivez vos gains dans le temps"
          />
        </div>

      </div>
    </section>
  );
}
