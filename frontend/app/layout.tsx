import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Pepperyn — Copilote financier IA',
  description: 'Pepperyn est une IA de décision financière qui permet aux dirigeants de PME d\'améliorer durablement leur rentabilité, leur trésorerie et leur croissance en identifiant et en priorisant les décisions qui créeront ou protégeront le plus de valeur pour leur entreprise.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Pepperyn',
  },
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
    ],
    apple: '/icon-192.png',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#1B73E8',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#1B73E8" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Pepperyn" />
        <link rel="apple-touch-icon" href="/favicon.png" />
      </head>
      <body>
        {children}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistrations().then(function(registrations) {
                  for (var r of registrations) { r.unregister(); }
                });
                caches.keys().then(function(names) {
                  for (var name of names) { caches.delete(name); }
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
