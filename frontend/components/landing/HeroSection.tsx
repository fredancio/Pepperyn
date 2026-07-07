import Link from 'next/link';
import Image from 'next/image';

/* ─────────────────────────────────────────────────────────────────────────
   HERO SECTION — deux colonnes (texte gauche / image droite)
   Image droite : PNG statique, affichée telle quelle, jamais reconstruite.
───────────────────────────────────────────────────────────────────────── */

const FEATURES = [
  {
    title: 'Sécurisé & confidentiel',
    desc: 'Vos données restent les vôtres',
    icon: (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    title: 'Résultats en quelques minutes',
    desc: "Fini les semaines d'analyse",
    icon: (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    title: '100% orienté décision',
    desc: 'Clair, chiffré, priorisé',
    icon: (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
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
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
];

export function HeroSection() {
  return (
    <section
      className="flex flex-col lg:flex-row w-full overflow-hidden"
      style={{ minHeight: 'calc(100vh - 64px)' }}
    >
      {/* ═══════════════════════════════════════════════════════════════
          COLONNE GAUCHE — fond blanc, contenu texte
      ═══════════════════════════════════════════════════════════════ */}
      <div
        className="flex flex-col justify-center w-full lg:w-[55%]
                   px-8 sm:px-14 lg:pl-20 xl:pl-28 lg:pr-12
                   py-16 lg:py-24"
        style={{ background: 'linear-gradient(155deg, #f0f6ff 0%, #ffffff 55%)' }}
      >

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 mb-8 w-fit
                        bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full">
          <svg
            className="w-3.5 h-3.5 text-[#1B73E8] flex-shrink-0"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
          <span className="text-sm font-medium text-[#1B73E8] tracking-wide">
            Copilote Financier Exécutif
          </span>
        </div>

        {/* H1 */}
        <h1
          className="mb-6"
          style={{
            fontSize: 'clamp(38px, 3.8vw, 58px)',
            fontWeight: 900,
            lineHeight: 1.06,
            letterSpacing: '-0.025em',
            color: '#0A1628',
          }}
        >
          Ne prenez plus seul vos{' '}
          <span style={{ color: '#1B73E8', fontStyle: 'italic' }}>décisions</span>
          {' '}financières.
        </h1>

        {/* Paragraph */}
        <p
          className="mb-8"
          style={{
            fontSize: 'clamp(16px, 1.1vw, 18px)',
            lineHeight: 1.65,
            color: '#4a5878',
            maxWidth: 520,
          }}
        >
          Pepperyn transforme un simple fichier Excel en décisions exécutives,
          rapports de direction et plans d&apos;action priorisés en quelques minutes.
        </p>

        {/* Feature icons — 4 colonnes */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-5 gap-y-6 mb-10">
          {FEATURES.map((f) => (
            <div key={f.title} className="flex flex-col gap-1.5">
              <div className="text-[#1B73E8]">{f.icon}</div>
              <p style={{ fontSize: 12, fontWeight: 700, color: '#0A1628', lineHeight: 1.3 }}>
                {f.title}
              </p>
              <p style={{ fontSize: 11, color: '#6b7c8f', lineHeight: 1.3 }}>
                {f.desc}
              </p>
            </div>
          ))}
        </div>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-3 mb-7">
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2.5
                       bg-[#1B73E8] text-white font-semibold rounded-[14px] px-6
                       hover:bg-[#0D47A1] transition-all duration-200 whitespace-nowrap"
            style={{
              height: 56,
              fontSize: 15,
              boxShadow: '0 4px 20px rgba(27,115,232,0.40)',
            }}
          >
            Analyser mon premier fichier gratuitement
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <Link
            href="#livrables"
            className="inline-flex items-center justify-center px-6
                       text-[#0A1628] font-semibold rounded-[14px]
                       border border-gray-200 hover:border-gray-300 hover:bg-gray-50
                       transition-all duration-200 whitespace-nowrap"
            style={{ height: 56, fontSize: 15 }}
          >
            Découvrir un rapport exécutif
          </Link>
        </div>

        {/* Ligne de réassurance */}
        <div className="flex items-center gap-2" style={{ fontSize: 13, color: '#8a9bb0' }}>
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
          Sans carte bancaire&nbsp;·&nbsp;Résultats en quelques minutes&nbsp;·&nbsp;Données anonymisées
        </div>

      </div>

      {/* ═══════════════════════════════════════════════════════════════
          COLONNE DROITE — fond sombre, image PNG officielle
          L'image est un PNG statique — aucune reconstruction.
      ═══════════════════════════════════════════════════════════════ */}
      <div
        className="relative flex-1 w-full min-h-[400px] lg:min-h-0"
        style={{ background: 'linear-gradient(135deg, #0D1B2E 0%, #0A1628 100%)' }}
      >
        <Image
          src="/hero/hero-image.png"
          alt="Pepperyn Hero"
          priority
          fill
          sizes="(max-width: 1024px) 100vw, 45vw"
          style={{ objectFit: 'contain', objectPosition: 'center' }}
        />
      </div>

    </section>
  );
}
