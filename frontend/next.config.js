/** @type {import('next').NextConfig} */
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
