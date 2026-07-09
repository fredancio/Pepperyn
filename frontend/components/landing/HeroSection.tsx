import Link from 'next/link';

/* ─────────────────────────────────────────────────────────────────────────
   HERO SECTION — deux colonnes 50/50
   Fond : gradient direct sur chaque colonne (pas de surcharge CSS externe)
     • Colonne gauche : blanc → #DCE5EE (couleur exacte du bord gauche de l'image)
     • Colonne droite : image en position:absolute, parent relative SANS overflow-hidden
   Jonction : couleur identique des deux côtés → aucune ligne visible.
   Overlay 120px : lisse les légères variations verticales du bord de l'image.
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
      className="flex flex-col lg:flex-row w-full overflow-hidden"
      style={{ minHeight: 'calc(100vh - 64px)' }}
    >

      {/* ═══════════════════════════════════════════════════════════════
          COLONNE GAUCHE — fond gradient blanc → #DCE5EE (bord de l'image)
          La couleur finale (#DCE5EE) = couleur mesurée du bord gauche de
          hero-image.png → jonction optiquement invisible sur desktop.
      ═══════════════════════════════════════════════════════════════ */}
      <div
        className="flex flex-col justify-center overflow-hidden
                   w-full lg:w-1/2
                   px-8 sm:px-14 lg:pl-20 xl:pl-28 lg:pr-10
                   py-16 lg:py-24"
        style={{
          /* Gradient calibré sur la couleur mesurée du bord gauche de l'image :
             x=0→20 de hero-image.png = #e3e2e6 (gris neutre).
             Le gradient se termine sur cette couleur exacte → jonction invisible. */
          background: 'linear-gradient(to right, #f8fafc 0%, #eaf3fb 45%, #e3e2e6 100%)',
        }}
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

        {/* ── CTA ── */}
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
          COLONNE DROITE — image produit via background-image CSS
          Approche background-image : aucun problème de résolution de hauteur
          (contrairement à <img height:100%> ou position:absolute qui dépendent
          d'une hauteur explicite sur le parent — non garantie en flex layout).
          Le div remplit son espace flex naturellement ; background-size:cover
          fait le reste. Fallback fond #0A1528 si l'image ne charge pas.
      ═══════════════════════════════════════════════════════════════ */}
      <div
        className="relative flex-1 w-full min-h-[400px] lg:min-h-0"
        role="img"
        aria-label="Illustration produit Pepperyn"
        style={{
          backgroundColor: '#0A1528',
          backgroundImage: "url('/hero/hero-image.png')",
          backgroundSize: 'cover',
          backgroundPosition: 'left center',
          backgroundRepeat: 'no-repeat',
        }}
      >
        {/*
          Overlay 120px : lisse les variations verticales du bord gauche de
          l'image (top #C9D9E1 / center #EAEFF7 / bottom #E2E8F3 ≠ #DCE5EE).
          absolute + inset-y-0 = s'étire sur toute la hauteur sans height:100%.
        */}
        {/* Overlay gauche 220px — même couleur que le bord droit du gradient
            de la colonne gauche (#e3e2e6), lisse les variations verticales */}
        <div
          className="hidden lg:block absolute inset-y-0 left-0 pointer-events-none"
          style={{
            width: '220px',
            background: 'linear-gradient(to right, rgba(227,226,230,0.72) 0%, rgba(227,226,230,0) 100%)',
            zIndex: 2,
          }}
        />
        {/* Overlay haut — masque les 2 lignes noires (#1e2023) mesurées
            en haut de hero-image.png. Fondu de 90px vers le bas. */}
        <div
          className="absolute inset-x-0 top-0 pointer-events-none"
          style={{
            height: '90px',
            background: 'linear-gradient(to bottom, rgba(232,234,237,0.92) 0%, rgba(232,234,237,0) 100%)',
            zIndex: 3,
          }}
        />
      </div>

    </section>
  );
}
