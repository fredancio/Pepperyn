'use client';
import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';

/**
 * Page de callback après confirmation d'email (Supabase).
 * Le client supabase-js détecte automatiquement la session présente
 * dans l'URL (detectSessionInUrl: true) et l'enregistre.
 *
 * Une fois la session établie, on redirige vers `next` :
 * - PRO (depuis la landing) : /checkout/pro → Stripe directement,
 *   sans passer par la page de connexion.
 * - FREE : /app/chat
 *
 * Si aucune session n'a pu être établie (lien expiré, etc.),
 * on retombe sur /login en conservant la destination.
 */
function AuthCallbackInner() {
  const searchParams = useSearchParams();
  const next = searchParams.get('next') || '/app/chat';
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function finalize() {
      // Laisse le temps au client supabase-js de parser le hash de l'URL
      // et d'établir la session (detectSessionInUrl: true).
      for (let i = 0; i < 20; i++) {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          if (!cancelled) window.location.replace(next);
          return;
        }
        await new Promise((r) => setTimeout(r, 150));
      }
      if (!cancelled) setError(true);
    }

    finalize();
    return () => { cancelled = true; };
  }, [next]);

  if (error) {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex flex-col items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 max-w-md w-full text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-[#1A1A2E] mb-2">Lien invalide ou expiré</h2>
          <p className="text-sm text-[#5F6368] mb-6">
            Veuillez vous connecter pour continuer.
          </p>
          <button
            onClick={() => window.location.href = `/login?redirect=${encodeURIComponent(next)}`}
            className="w-full py-3 rounded-xl bg-[#1B73E8] text-white font-bold text-sm hover:bg-[#1557B0] transition-colors"
          >
            Se connecter →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#EFF6FF] flex flex-col items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 max-w-md w-full text-center">
        <img src="/favicon.png?v=4" alt="Pepperyn" className="w-16 h-16 mx-auto mb-4 object-contain" />
        <div className="w-8 h-8 border-2 border-[#1B73E8] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-bold text-[#1A1A2E] mb-2">Confirmation en cours…</h2>
        <p className="text-sm text-[#5F6368]">Un instant, on vous redirige.</p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#EFF6FF] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#1B73E8] border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <AuthCallbackInner />
    </Suspense>
  );
}
