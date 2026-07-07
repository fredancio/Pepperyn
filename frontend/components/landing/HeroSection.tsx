import Link from 'next/link';

/* ─────────────────────────────────────────────────────────────────────────
   SUB-COMPONENTS
───────────────────────────────────────────────────────────────────────── */

/** Sparkline trend arrow — wider for metric mini-cards */
function Sparkline({ color = '#16a34a', w = 80, h = 30 }: { color?: string; w?: number; h?: number }) {
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none" aria-hidden="true">
      <polyline
        points={`0,${h - 4} ${w * 0.22},${h * 0.62} ${w * 0.45},${h * 0.48} ${w * 0.68},${h * 0.28} ${w * 0.88},${h * 0.1}`}
        stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"
      />
      {/* arrowhead */}
      <polyline
        points={`${w * 0.76},${h * 0.06} ${w * 0.88},${h * 0.1} ${w * 0.84},${h * 0.4}`}
        stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"
      />
    </svg>
  );
}

/** Waterfall bar chart — 6 bars with full labels */
function WaterfallChart() {
  const bars = [
    { label: 'EBITDA\nInitial',   value: '2,1M€',  h: 88,  color: '#1B73E8', pos: true  },
    { label: 'Achats',            value: '-0,6M€', h: 30,  color: '#e07b2a', pos: false },
    { label: 'Frais fixes',       value: '-0,4M€', h: 22,  color: '#e07b2a', pos: false },
    { label: 'Sous-traitance',    value: '-0,3M€', h: 15,  color: '#e87070', pos: false },
    { label: 'Autres',            value: '-0,2M€', h: 11,  color: '#DC2626', pos: false },
    { label: 'EBITDA\nCible',     value: '2,6M€',  h: 106, color: '#16a34a', pos: true  },
  ];
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 7, height: 148, padding: '0 2px' }}>
      {bars.map((b, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
          <span style={{ fontSize: 8.5, fontWeight: 700, color: b.color, lineHeight: 1.2, textAlign: 'center' }}>
            {b.value}
          </span>
          <div style={{
            width: '100%', borderRadius: 4, marginTop: 2,
            height: b.h * 0.9, background: b.color, opacity: b.pos ? 1 : 0.85,
          }} />
          <span style={{ fontSize: 7, color: '#9ca3af', textAlign: 'center', whiteSpace: 'pre-line', lineHeight: 1.3, marginTop: 3 }}>
            {b.label}
          </span>
        </div>
      ))}
    </div>
  );
}

/** 90-day timeline */
function Timeline() {
  const steps = [
    { days: '30 JOURS', label: 'Lancer',    bg: '#1B73E8', border: '#1B73E8', dot: '#fff' },
    { days: '60 JOURS', label: 'Accélérer', bg: '#4E95EF', border: '#4E95EF', dot: '#fff' },
    { days: '90 JOURS', label: 'Mesurer',   bg: '#fff',    border: '#16a34a', dot: '#16a34a' },
  ];
  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 14px', marginTop: 4 }}>
      {/* track */}
      <div style={{ position: 'absolute', left: 22, right: 22, top: 12, height: 2, background: '#e5e7eb' }} />
      {/* active segment */}
      <div style={{ position: 'absolute', left: 22, right: '33%', top: 12, height: 2, background: '#1B73E8' }} />
      {steps.map((s, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, zIndex: 1 }}>
          <div style={{ width: 24, height: 24, borderRadius: '50%', border: `2.5px solid ${s.border}`, background: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: s.dot }} />
          </div>
          <span style={{ fontSize: 7.5, fontWeight: 700, color: '#9ca3af', letterSpacing: '0.07em', textTransform: 'uppercase' as const }}>
            {s.days}
          </span>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#1a1a2e' }}>{s.label}</span>
        </div>
      ))}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────
   HERO SECTION
───────────────────────────────────────────────────────────────────────── */

export function HeroSection() {
  return (
    <section className="relative bg-white overflow-hidden">

      {/* ── Backgrounds ── */}
      <div className="absolute inset-0 pointer-events-none" style={{ background: 'linear-gradient(160deg, #f5f9ff 0%, #ffffff 45%)' }} />
      <div className="absolute pointer-events-none" style={{
        top: -120, right: -140, width: 860, height: 660,
        background: 'radial-gradient(ellipse at 60% 25%, rgba(27,115,232,0.1) 0%, rgba(219,234,254,0.12) 40%, transparent 65%)',
        borderRadius: '50%',
      }} />

      {/* ── Container ── */}
      <div className="relative max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-16 pt-20 lg:pt-[90px]">

        {/* ── Two-column grid ── */}
        <div className="grid lg:grid-cols-[43%_1fr] gap-8 lg:gap-10 xl:gap-16 items-center">

          {/* ╔══════════╗
              ║  LEFT    ║
              ╚══════════╝ */}
          <div className="flex flex-col gap-6 lg:gap-7">

            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full w-fit">
              <span className="w-1.5 h-1.5 rounded-full bg-[#1B73E8]" />
              <span className="text-sm font-medium text-[#1B73E8]">Copilote Financier Exécutif</span>
            </div>

            <h1 style={{ fontSize: 'clamp(38px, 4.8vw, 68px)', fontWeight: 900, lineHeight: 1.0, letterSpacing: '-0.025em', color: '#0c1524' }}>
              Ne prenez plus seul vos décisions financières.
            </h1>

            <p style={{ fontSize: 'clamp(16px, 1.35vw, 20px)', lineHeight: 1.65, color: '#4a5878', maxWidth: 580 }}>
              Pepperyn transforme vos données financières en décisions exécutives, rapports de
              direction et plans d&apos;action priorisés en quelques minutes.
            </p>

            <div className="border-t border-gray-100 pt-5">
              <p style={{ fontSize: 15, fontWeight: 600, lineHeight: 1.65, color: '#1a1a2e' }}>
                Le meilleur Directeur Financier n&apos;est plus celui qui travaille le plus.{' '}
                C&apos;est celui qui prend les meilleures décisions, au bon moment.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-start gap-3">
              <Link
                href="/register"
                className="inline-flex items-center gap-2.5 bg-[#1B73E8] text-white font-semibold rounded-[14px] px-7 hover:bg-[#0D47A1] transition-all duration-200 whitespace-nowrap flex-shrink-0"
                style={{ height: 56, fontSize: 15, boxShadow: '0 4px 16px rgba(27,115,232,0.38)' }}
              >
                Analyser mon premier fichier gratuitement
                <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <Link
                href="#livrables"
                className="inline-flex items-center justify-center px-7 text-[#1a1a2e] font-semibold rounded-[14px] border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all duration-200 whitespace-nowrap"
                style={{ height: 56, fontSize: 15 }}
              >
                Découvrir un rapport exécutif
              </Link>
            </div>

            <div className="flex items-center gap-2" style={{ fontSize: 13, color: '#8a9bb0' }}>
              <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Sans carte bancaire&nbsp;·&nbsp;Résultats en quelques minutes&nbsp;·&nbsp;Données anonymisées
            </div>
          </div>

          {/* ╔══════════════════════╗
              ║  RIGHT — mockup      ║
              ╚══════════════════════╝ */}
          <div className="relative lg:overflow-visible flex items-start justify-center lg:justify-end pb-16 lg:pb-20">

            {/* Wrapper — positions ghost + main card */}
            <div className="relative w-full lg:w-[720px] lg:flex-shrink-0">

              {/* ── Ghost card behind (deeper angle, offset up-right) ── */}
              <div style={{
                position: 'absolute',
                inset: 0,
                background: '#ffffff',
                border: '1px solid rgba(200,218,238,0.55)',
                borderRadius: 22,
                transform: 'rotate(5deg) translateX(16px) translateY(-24px)',
                transformOrigin: 'center top',
                zIndex: 0,
                opacity: 0.7,
                boxShadow: '0 8px 32px rgba(27,115,232,0.07)',
              }} />

              {/* ── Main dashboard card ── */}
              <div
                className="bg-white rounded-[22px] overflow-hidden w-full"
                style={{
                  position: 'relative',
                  zIndex: 1,
                  border: '1px solid rgba(27,115,232,0.13)',
                  boxShadow: [
                    'inset 0 1.5px 0 rgba(255,255,255,0.95)',
                    '0 0 0 5px rgba(27,115,232,0.04)',
                    '0 4px 12px rgba(0,0,0,0.07)',
                    '0 18px 56px -8px rgba(27,115,232,0.22)',
                    '0 40px 100px -20px rgba(27,115,232,0.13)',
                  ].join(', '),
                  transform: 'rotate(1.5deg) translateY(-10px)',
                  transformOrigin: 'center top',
                }}
              >

                {/* ═══ TOP: two panels side by side ═══ */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid #eef2f8' }}>

                  {/* ── Panel L: DÉCISION PRIORITAIRE ── */}
                  <div style={{ padding: '22px 22px 20px', borderRight: '1px solid #eef2f8', display: 'flex', flexDirection: 'column', gap: 14 }}>

                    <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.09em', color: '#1B73E8', textTransform: 'uppercase' as const }}>
                      Décision prioritaire
                    </p>

                    <p style={{ fontSize: 18, fontWeight: 700, fontStyle: 'italic', color: '#0c1524', lineHeight: 1.25, marginTop: -4 }}>
                      Réduire les achats indirects
                    </p>

                    {/* Impact + ROI */}
                    <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
                      <div>
                        <p style={{ fontSize: 9, color: '#94a3b8', marginBottom: 4, fontStyle: 'italic' }}>Impact annuel estimé</p>
                        <p style={{ fontSize: 32, fontWeight: 800, color: '#16a34a', lineHeight: 1 }}>+480 K€</p>
                      </div>
                      <div>
                        <p style={{ fontSize: 9, color: '#94a3b8', marginBottom: 6 }}>ROI</p>
                        {/* GREEN stars — not amber */}
                        <div style={{ display: 'flex', gap: 2 }}>
                          {[1,2,3,4,5].map(i => (
                            <svg key={i} width="15" height="15" viewBox="0 0 20 20" fill="#22c55e">
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* MARGE / EBITDA / CASH — each in a mini-card */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, paddingTop: 4 }}>
                      {[
                        { label: 'MARGE',  value: '+1,8 pt',  check: false },
                        { label: 'EBITDA', value: '+480 K€',  check: true  },
                        { label: 'CASH',   value: '+320 K€',  check: false },
                      ].map(m => (
                        <div
                          key={m.label}
                          style={{
                            background: '#f7fafd',
                            border: '1px solid #e2ecf7',
                            borderRadius: 10,
                            padding: '10px 10px 8px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 3,
                          }}
                        >
                          {/* Label row — with optional checkmark for EBITDA */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                            {m.check && (
                              <svg width="10" height="10" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                                <path d="M1.5 6l3 3 6-6" stroke="#1B73E8" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                            )}
                            <p style={{ fontSize: 8, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.07em', textTransform: 'uppercase' as const }}>
                              {m.label}
                            </p>
                          </div>
                          <p style={{ fontSize: 13, fontWeight: 800, color: '#16a34a' }}>{m.value}</p>
                          <Sparkline color="#16a34a" w={76} h={28} />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* ── Panel R: 5 DÉCISIONS + PLAN 90 JOURS ── */}
                  <div style={{ padding: '22px 22px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>

                    <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.09em', color: '#94a3b8', textTransform: 'uppercase' as const }}>
                      5 Décisions prioritaires
                    </p>

                    <WaterfallChart />

                    <div style={{ borderTop: '1px solid #eef2f8', paddingTop: 14 }}>
                      <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.09em', color: '#94a3b8', textTransform: 'uppercase' as const, marginBottom: 12 }}>
                        Plan 90 jours
                      </p>
                      <Timeline />
                    </div>
                  </div>
                </div>

                {/* ═══ BOTTOM: Recommandations clés ═══ */}
                <div style={{ padding: '18px 22px 20px', background: '#f8fbff', borderTop: '1px solid #eef2f8' }}>
                  <p style={{ fontSize: 13, fontWeight: 700, fontStyle: 'italic', color: '#3d4f6a', marginBottom: 12 }}>
                    Recommandations clés
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 28px' }}>
                    {[
                      'Concentration client à risque',
                      'Nouveau segment à fort potentiel',
                      'BFR en dégradation structurelle',
                      'Dérive de la masse salariale',
                    ].map((rec, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="#22c55e" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span style={{ fontSize: 11.5, color: '#4a5878' }}>{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>

              </div>{/* end main card */}
            </div>{/* end wrapper */}
          </div>{/* end right col */}
        </div>{/* end grid */}

        {/* ╔══════════════════════════════════════════════════╗
            ║  FEATURE BAR — card with 4 items                ║
            ╚══════════════════════════════════════════════════╝ */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          background: 'rgba(248,251,255,0.97)',
          border: '1px solid rgba(27,115,232,0.12)',
          borderRadius: 18,
          boxShadow: '0 2px 16px rgba(27,115,232,0.07), 0 1px 3px rgba(0,0,0,0.04)',
          minHeight: 92,
          marginTop: 44,
        }}>
          {[
            {
              title: 'Sécurisé & confidentiel',
              desc: 'Vos données restent les vôtres',
              icon: (
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              ),
            },
            {
              title: 'Résultats en quelques minutes',
              desc: "Fini les semaines d'analyse",
              icon: (
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              ),
            },
            {
              title: '100% orienté décision',
              desc: 'Clair, chiffré, priorisé',
              icon: (
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <circle cx="12" cy="12" r="10" />
                  <circle cx="12" cy="12" r="6" />
                  <circle cx="12" cy="12" r="2" />
                </svg>
              ),
            },
            {
              title: 'Impact mesurable',
              desc: 'Suivez vos gains dans le temps',
              icon: (
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              ),
            },
          ].map((item, i) => (
            <div
              key={i}
              style={{
                display: 'flex', alignItems: 'center', gap: 14,
                padding: '0 28px',
                borderRight: i < 3 ? '1px solid rgba(27,115,232,0.1)' : 'none',
              }}
            >
              <div style={{ width: 38, height: 38, borderRadius: 11, background: 'rgba(27,115,232,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1B73E8', flexShrink: 0 }}>
                {item.icon}
              </div>
              <div>
                <p style={{ fontSize: 13, fontWeight: 700, color: '#0c1524', lineHeight: 1.3 }}>{item.title}</p>
                <p style={{ fontSize: 12, color: '#6b7c8f', lineHeight: 1.3 }}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
