/** @type {import('next').NextConfig} */

// Garantie de COMPILATION (pas seulement d'exécution) — External User
// Testing Prototype, 2026-08-05, suite à la revue de Fred sur
// PORTFOLIO_EXTERNAL_PROTOTYPE_REVIEW.md section 7 : quand
// NEXT_PUBLIC_DEMO_MODE=true, aucune variable NEXT_PUBLIC_SUPABASE_* ne
// doit être inlinée dans le bundle client, quelle que soit la
// configuration d'environnement Vercel (une Preview Deployment peut
// hériter des mêmes valeurs que Production si le scope n'a pas été
// restreint côté tableau de bord Vercel — on ne dépend plus de cette
// configuration humaine, potentiellement fragile).
//
// .env.local (et les autres fichiers .env*) sont déjà chargés dans
// process.env au moment où Next.js exécute ce fichier (voir @next/env),
// mais AVANT que Next.js construise son webpack.DefinePlugin qui inline
// les variables NEXT_PUBLIC_*. Écraser ces clés dans process.env ici les
// rend donc indisponibles à cette étape ultérieure : toute référence à
// process.env.NEXT_PUBLIC_SUPABASE_URL / _ANON_KEY dans le code (client
// ET côté génération statique) reçoit alors cette valeur factice, jamais
// la vraie. Vérifié par inspection du bundle généré (grep sur
// .next/static après build avec NEXT_PUBLIC_DEMO_MODE=true) — voir
// Mission 10 (sécurité) du rapport.
//
// Une VALEUR FACTICE plutôt qu'une suppression : frontend/lib/supabase.ts
// appelle createClient(url, key) de façon inconditionnelle au chargement
// du module (frontend/lib/auth.ts, ChatContainer.tsx et les pages
// authentifiées /app/*, /login importent ce module, y compris pendant la
// génération statique de CE MÊME build — un seul `next build` produit tout
// le site, /demo/* et /app/* compris). supprimer purement la variable fait
// échouer createClient(undefined, undefined) et casse la génération
// statique de TOUTES les pages, pas seulement /demo/*. Une URL syntaxiquement
// valide mais inerte n'est jamais utilisée pour un appel réseau réel côté
// /demo/* (frontend/lib/supabase.ts n'est chargé, via l'import() dynamique
// de lib/api.ts::getAuthHeaders, que dans la branche non-démo — jamais
// atteinte quand isDemoModeEnabled() est vrai, voir lib/arc-api.ts et
// lib/api.ts) ; côté /app/* elle resterait un problème d'authentification
// réel si ces routes étaient visitées sur une Preview en mode démo — hors
// périmètre de ce prototype, dont le seul point d'entrée documenté est
// /demo/portfolio.
const isDemoBuild = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';
if (isDemoBuild) {
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://demo-mode-disabled.invalid';
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'demo-mode-disabled';
}

const nextConfig = {
  // Expose VERCEL_ENV côté client sous NEXT_PUBLIC_VERCEL_ENV — nécessaire
  // au garde-fou du mode démo (frontend/lib/demo-mode.ts), qui doit pouvoir
  // confirmer côté navigateur qu'une Preview Deployment n'est jamais
  // l'environnement Production (External User Testing Prototype, 2026-08-05).
  env: {
    NEXT_PUBLIC_VERCEL_ENV: process.env.VERCEL_ENV || '',
  },
  async headers() {
    return [
      // Ne jamais mettre en cache le HTML des pages
      {
        source: '/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=0, must-revalidate' },
        ],
      },
      // Service Worker
      {
        source: '/sw.js',
        headers: [
          { key: 'Service-Worker-Allowed', value: '/' },
          { key: 'Cache-Control', value: 'public, max-age=0, must-revalidate' },
        ],
      },
    ];
  },
};
module.exports = nextConfig;
