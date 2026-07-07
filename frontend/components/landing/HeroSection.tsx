import Link from 'next/link';
import Image from 'next/image';

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
              ║  RIGHT — illustration ║
              ╚══════════════════════╝ */}
          <div className="flex items-center justify-center lg:justify-end">
            <Image
              src="/hero-mockup.jpg"
              alt="Pepperyn — dashboard d'analyse financière"
              width={886}
              height={740}
              priority
              className="w-full max-w-[720px] h-auto"
            />
          </div>
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
