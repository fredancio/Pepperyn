import Link from 'next/link';

/* ─────────────────────────────────────────────────────────────────────────
   SUB-COMPONENTS — scaled for the large 720 px mockup
───────────────────────────────────────────────────────────────────────── */

function Sparkline({ color = '#16a34a' }: { color?: string }) {
  return (
    <svg width="62" height="24" viewBox="0 0 62 24" fill="none" aria-hidden="true">
      <polyline
        points="0,20 14,15 28,12 42,8 56,3"
        stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      />
      {/* arrowhead */}
      <polyline
        points="48,1 56,3 54,11"
        stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      />
    </svg>
  );
}

function WaterfallChart() {
  const bars = [
    { label: 'EBITDA\nInitial',  value: '2,1M€',  h: 86,  color: '#1B73E8', pos: true  },
    { label: 'Achats',           value: '-0,6M€', h: 29,  color: '#e07b2a', pos: false },
    { label: 'Frais\nfixes',     value: '-0,4M€', h: 21,  color: '#e07b2a', pos: false },
    { label: 'Sous-\ntrait.',    value: '-0,3M€', h: 15,  color: '#e87070', pos: false },
    { label: 'Autres',           value: '-0,2M€', h: 11,  color: '#DC2626', pos: false },
    { label: 'EBITDA\nCible',    value: '2,6M€',  h: 104, color: '#16a34a', pos: true  },
  ];
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 5, height: 136, padding: '0 2px' }}>
      {bars.map((b, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
          <span style={{ fontSize: 8, fontWeight: 700, color: b.color, lineHeight: 1.2, textAlign: 'center' }}>
            {b.value}
          </span>
          <div
            style={{
              width: '100%', borderRadius: 3, marginTop: 2,
              height: b.h * 0.88, background: b.color, opacity: b.pos ? 1 : 0.82,
            }}
          />
          <span style={{ fontSize: 6.5, color: '#9ca3af', textAlign: 'center', whiteSpace: 'pre-line', lineHeight: 1.3, marginTop: 3 }}>
            {b.label}
          </span>
        </div>
      ))}
    </div>
  );
}

function Timeline() {
  const steps = [
    { days: '30 JOURS', label: 'Lancer',    bg: '#1B73E8', border: '#1B73E8', dot: '#ffffff' },
    { days: '60 JOURS', label: 'Accélérer', bg: '#4E95EF', border: '#4E95EF', dot: '#ffffff' },
    { days: '90 JOURS', label: 'Mesurer',   bg: '#ffffff', border: '#16a34a', dot: '#16a34a' },
  ];
  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 12px', marginTop: 4 }}>
      {/* track */}
      <div style={{ position: 'absolute', left: 20, right: 20, top: 12, height: 2, background: '#e5e7eb' }} />
      {/* active segment */}
      <div style={{ position: 'absolute', left: 20, right: '33%', top: 12, height: 2, background: '#1B73E8' }} />
      {steps.map((s, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, zIndex: 1 }}>
          <div style={{
            width: 24, height: 24, borderRadius: '50%', border: `2px solid ${s.border}`,
            background: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: s.dot }} />
          </div>
          <span style={{ fontSize: 7.5, fontWeight: 700, color: '#9ca3af', letterSpacing: '0.07em', textTransform: 'uppercase' }}>
            {s.days}
          </span>
          <span style={{ fontSize: 10, fontWeight: 600, color: '#1a1a2e' }}>{s.label}</span>
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

      {/* ── Background glows ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'linear-gradient(160deg, #f5f9ff 0%, #ffffff 45%, #ffffff 100%)' }}
      />
      <div
        className="absolute pointer-events-none"
        style={{
          top: -120, right: -140, width: 860, height: 660,
          background: 'radial-gradient(ellipse at 60% 25%, rgba(27,115,232,0.1) 0%, rgba(219,234,254,0.12) 40%, transparent 65%)',
          borderRadius: '50%',
        }}
      />

      {/* ── Main container ── */}
      <div className="relative max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-16 pt-20 lg:pt-[90px]">

        {/* ── Two-column grid — 43 / 57 ── */}
        <div className="grid lg:grid-cols-[43%_1fr] gap-8 lg:gap-10 xl:gap-16 items-center">

          {/* ╔══════════════════════════════╗
              ║  LEFT — text                 ║
              ╚══════════════════════════════╝ */}
          <div className="flex flex-col gap-6 lg:gap-7">

            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full w-fit">
              <span className="w-1.5 h-1.5 rounded-full bg-[#1B73E8]" />
              <span className="text-sm font-medium text-[#1B73E8]">Copilote Financier Exécutif</span>
            </div>

            {/* Title — 68 px, weight 900 */}
            <h1
              style={{
                fontSize: 'clamp(38px, 4.8vw, 68px)',
                fontWeight: 900,
                lineHeight: 1.0,
                letterSpacing: '-0.025em',
                color: '#0c1524',
              }}
            >
              Ne prenez plus seul vos décisions financières.
            </h1>

            {/* Subtitle */}
            <p style={{ fontSize: 'clamp(16px, 1.35vw, 20px)', lineHeight: 1.65, color: '#4a5878', maxWidth: 580 }}>
              Pepperyn transforme vos données financières en décisions exécutives, rapports de
              direction et plans d&apos;action priorisés en quelques minutes.
            </p>

            {/* Separator + conviction */}
            <div className="border-t border-gray-100 pt-5">
              <p style={{ fontSize: 15, fontWeight: 600, lineHeight: 1.65, color: '#1a1a2e' }}>
                Le meilleur Directeur Financier n&apos;est plus celui qui travaille le plus.{' '}
                C&apos;est celui qui prend les meilleures décisions, au bon moment.
              </p>
            </div>

            {/* CTAs */}
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

            {/* Trust */}
            <div className="flex items-center gap-2" style={{ fontSize: 13, color: '#8a9bb0' }}>
              <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Sans carte bancaire&nbsp;·&nbsp;Résultats en quelques minutes&nbsp;·&nbsp;Données anonymisées
            </div>
          </div>

          {/* ╔══════════════════════════════╗
              ║  RIGHT — premium mockup      ║
              ╚══════════════════════════════╝ */}
          <div className="relative lg:overflow-visible flex items-start justify-center lg:justify-end pb-14 lg:pb-16">

            {/* ── The large card ── */}
            <div
              className="w-full bg-white rounded-[22px] overflow-hidden lg:w-[720px] lg:flex-shrink-0"
              style={{
                border: '1px solid rgba(27,115,232,0.15)',
                boxShadow: [
                  'inset 0 1.5px 0 rgba(255,255,255,0.95)',
                  '0 0 0 6px rgba(27,115,232,0.04)',
                  '0 4px 10px rgba(0,0,0,0.06)',
                  '0 16px 52px -8px rgba(27,115,232,0.24)',
                  '0 40px 100px -20px rgba(27,115,232,0.14)',
                ].join(', '),
                transform: 'rotate(1.5deg) translateY(-12px)',
                transformOrigin: 'center top',
              }}
            >

              {/* ── Upper two panels ── */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid #f0f4f8' }}>

                {/* Panel L : Décision prioritaire */}
                <div style={{ padding: 24, borderRight: '1px solid #f0f4f8', display: 'flex', flexDirection: 'column', gap: 12 }}>

                  <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#1B73E8', textTransform: 'uppercase' }}>
                    Décision prioritaire
                  </p>
                  <p style={{ fontSize: 16, fontWeight: 700, fontStyle: 'italic', color: '#0c1524', lineHeight: 1.3 }}>
                    Réduire les achats indirects
                  </p>

                  {/* Impact + ROI */}
                  <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
                    <div>
                      <p style={{ fontSize: 8.5, color: '#94a3b8', marginBottom: 4 }}>Impact annuel estimé</p>
                      <p style={{ fontSize: 28, fontWeight: 800, color: '#16a34a', lineHeight: 1 }}>+480 K€</p>
                    </div>
                    <div>
                      <p style={{ fontSize: 8.5, color: '#94a3b8', marginBottom: 6 }}>ROI</p>
                      <div style={{ display: 'flex', gap: 2 }}>
                        {[1,2,3,4,5].map(i => (
                          <svg key={i} width="14" height="14" viewBox="0 0 20 20" fill="#f59e0b">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* MARGE / EBITDA / CASH */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, paddingTop: 14, borderTop: '1px solid #f0f4f8' }}>
                    {[
                      { label: 'MARGE',  value: '+1,8pt'  },
                      { label: 'EBITDA', value: '+480 K€' },
                      { label: 'CASH',   value: '+320 K€' },
                    ].map(m => (
                      <div key={m.label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <p style={{ fontSize: 8, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.07em', textTransform: 'uppercase' }}>
                          {m.label}
                        </p>
                        <p style={{ fontSize: 12, fontWeight: 800, color: '#16a34a' }}>{m.value}</p>
                        <Sparkline />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Panel R : 5 décisions + Plan 90 jours */}
                <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#94a3b8', textTransform: 'uppercase' }}>
                    5 Décisions prioritaires
                  </p>
                  <WaterfallChart />
                  <div style={{ borderTop: '1px solid #f0f4f8', paddingTop: 14 }}>
                    <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: '#94a3b8', textTransform: 'uppercase', marginBottom: 12 }}>
                      Plan 90 jours
                    </p>
                    <Timeline />
                  </div>
                </div>
              </div>

              {/* ── Recommandations clés ── */}
              <div style={{ padding: '18px 24px', background: '#f8fbff', borderTop: '1px solid #f0f4f8' }}>
                <p style={{ fontSize: 11.5, fontWeight: 600, fontStyle: 'italic', color: '#4a5878', marginBottom: 12 }}>
                  Recommandations clés
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '9px 28px' }}>
                  {[
                    'Concentration client à risque',
                    'Nouveau segment à fort potentiel',
                    'BFR en dégradation structurelle',
                    'Dérive de la masse salariale',
                  ].map((rec, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="#22c55e" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span style={{ fontSize: 11, color: '#4a5878' }}>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ╔══════════════════════════════════════════════════════╗
            ║  FEATURE BAR — card, border-radius 18, height ~92  ║
            ╚══════════════════════════════════════════════════════╝ */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            background: 'rgba(248,251,255,0.97)',
            border: '1px solid rgba(27,115,232,0.12)',
            borderRadius: 18,
            boxShadow: '0 2px 16px rgba(27,115,232,0.07), 0 1px 3px rgba(0,0,0,0.04)',
            minHeight: 92,
            marginTop: 48,
            marginBottom: 0,
          }}
        >
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
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '0 28px',
                borderRight: i < 3 ? '1px solid rgba(27,115,232,0.1)' : 'none',
              }}
            >
              <div
                style={{
                  width: 38, height: 38, borderRadius: 11,
                  background: 'rgba(27,115,232,0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#1B73E8', flexShrink: 0,
                }}
              >
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
