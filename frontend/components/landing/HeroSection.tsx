import Link from 'next/link';

/* ─────────────────────────────────────────────────────────────────────────
   HERO SECTION
   Fond : gradient unifié blanc → navy (classe .hero-section dans globals.css)
   Mobile  : colonne gauche = fond clair, colonne droite = fond sombre
   Desktop : les deux colonnes transparentes → gradient section visible
   Démarcation : overlay 240px sur le bord gauche de la colonne droite,
                 couleur #aecde7 = gradient à ~40% (frontière des colonnes)
───────────────────────────────────────────────────────────────────────── */

const FEATURES = [
  {
    title: 'Sécurisé & confidentiel',
    desc: 'Vos données restent les vôtres',
    icon: (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
        <path strokeLinecap="round" strokeLinejoin="round"
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
        />
      </svg>
    ),
  },
  {
    title: 'Résultats en quelques minutes',
    desc: "Fini les semaines d'analyse",
    icon: (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    title: '100% orienté décision',
    desc: 'Clair, chiffré, priorisé',
    icon: (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
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
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
];

export function HeroSection() {
  return (
    <section
      /* hero-section → globals.css applique le gradient unifié sur desktop */
      className="hero-section flex flex-col lg:flex-row w-full overflow-hidden"
      style={{ minHeight: 'calc(100vh - 64px)' }}
    >

      {/* ═══════════════════════════════════════════════════════════════
          COLONNE GAUCHE
          Mobile  : fond blanc → bleu très clair (inline style)
          Desktop : transparent (hero-left-col override !important)
      ═══════════════════════════════════════════════════════════════ */}
      <div
        className="hero-left-col flex flex-col justify-center overflow-hidden
                   w-full lg:w-[44%]
                   px-8 sm:px-14 lg:pl-20 xl:pl-28 lg:pr-10
                   py-16 lg:py-24"
        /* fond mobile uniquement — overridé par .hero-left-col sur desktop */
        style={{ background: 'linear-gradient(160deg, #f8fafc 0%, #eaf3fb 100%)' }}
      >

        {/* ── Badge ── */}
        <div
          className="inline-flex items-center gap-2 px-3.5 py-1.5 mb-8 w-fit rounded-full"
          style={{
            background: 'rgba(255,255,255,0.80)',
            border: '1.5px solid rgba(27,115,232,0.30)',
            backdropFilter: 'blur(4px)',
          }}
        >
          <svg className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#1B73E8' }}
            fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
          <span style={{ fontSize: 13, fontWeight: 500, color: '#0A1628', letterSpacing: '0.01em' }}>
            Copilote Financier Exécutif
          </span>
        </div>

        {/* ── H1 ── */}
        <h1 className="mb-6" style={{
          fontSize: 'clamp(36px, 3.6vw, 56px)', fontWeight: 900,
          lineHeight: 1.06, letterSpacing: '-0.028em', color: '#0A1628',
        }}>
          Ne prenez plus seul vos{' '}
          <span style={{
            color: '#1B73E8',
            textDecoration: 'underline',
            textDecorationColor: '#1B73E8',
            textDecorationThickness: '3px',
            textUnderlineOffset: '8px',
          }}>
            décisions
          </span>
          {' '}financières.
        </h1>

        {/* ── Paragraphe ── */}
        <p className="mb-9" style={{
          fontSize: 'clamp(15px, 1vw, 17px)', lineHeight: 1.7,
          color: '#334155', maxWidth: 460,
        }}>
          Pepperyn transforme un simple fichier Excel en{' '}
          <strong style={{ fontWeight: 700, color: '#1B73E8' }}>décisions exécutives</strong>
          , rapports de direction et plans d&apos;action priorisés en quelques minutes.
        </p>

        {/* ── Feature icons — 4 colonnes ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-5 gap-y-6 mb-10">
          {FEATURES.map((f) => (
            <div key={f.title} className="flex flex-col gap-1.5">
              <div style={{ color: '#1B73E8' }}>{f.icon}</div>
              <p style={{ fontSize: 12, fontWeight: 700, color: '#0A1628', lineHeight: 1.3 }}>{f.title}</p>
              <p style={{ fontSize: 11, color: '#5f7a8f', lineHeight: 1.3 }}>{f.desc}</p>
            </div>
          ))}
        </div>

        {/* ── CTA — côte à côte si la place le permet, empilés sinon ── */}
        <div className="flex flex-wrap gap-3 mb-7">
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2
                       bg-[#1B73E8] text-white font-semibold rounded-[14px] px-5
                       hover:bg-[#0D47A1] transition-all duration-200 whitespace-nowrap"
            style={{ height: 52, fontSize: 15, boxShadow: '0 4px 20px rgba(27,115,232,0.42)' }}
          >
            Analyser mon premier fichier gratuitement
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <Link
            href="#livrables"
            className="inline-flex items-center justify-center px-5
                       font-semibold rounded-[14px] hover:bg-white/60 transition-all duration-200 whitespace-nowrap"
            style={{
              height: 52, fontSize: 15, color: '#0A1628',
              border: '1.5px solid rgba(10,22,40,0.20)',
              background: 'rgba(255,255,255,0.50)',
            }}
          >
            Découvrir un rapport exécutif
          </Link>
        </div>

        {/* ── Réassurance ── */}
        <div className="flex items-center gap-2" style={{ fontSize: 12.5, color: '#6b8099' }}>
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
          Sans carte bancaire&nbsp;·&nbsp;Résultats en quelques minutes&nbsp;·&nbsp;Données anonymisées
        </div>

      </div>

      {/* ═══════════════════════════════════════════════════════════════
          COLONNE DROITE
          Mobile  : fond sombre (inline style)
          Desktop : transparent (hero-right-col override !important)
                    → gradient section visible derrière l'image
          Overlay 240px : masque le bord gauche de l'image et assure
                          la continuité avec le gradient section (#aecde7)
      ═══════════════════════════════════════════════════════════════ */}
      <div
        className="hero-right-col relative flex-1 w-full min-h-[400px] lg:min-h-0"
        /* fond mobile uniquement */
        style={{ background: '#0A1528' }}
      >
        {/* Fondu gauche — couleur = gradient section à ~40% (#aecde7) */}
        <div
          className="hidden lg:block absolute inset-y-0 left-0 pointer-events-none"
          style={{
            width: '240px',
            background: 'linear-gradient(to right, #aecde7 0%, rgba(174,205,231,0) 100%)',
            zIndex: 1,
          }}
        />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/hero/hero-image.png"
          alt="Pepperyn Hero"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'left center',
            display: 'block',
          }}
        />
      </div>

    </section>
  );
}
