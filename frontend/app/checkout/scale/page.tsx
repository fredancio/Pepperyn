'use client';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Page de checkout direct pour le plan SCALE. (WP4B)
 * Lancée après login depuis le flow d'inscription SCALE.
 * — Si pas de session : redirige vers /login?redirect=/checkout/scale
 * — Si session : crée la session Stripe et redirige directement
 * L'utilisateur ne voit jamais la page /upgrade avec tous les plans.
 */
export default function CheckoutScalePage() {
  const [error, setError] = useState('');

  useEffect(() => {
    async function startCheckout() {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          window.location.href = '/login?redirect=/checkout/scale';
          return;
        }

        const { data: { user } } = await supabase.auth.getUser();

        const res = await fetch(`${API_URL}/api/billing/checkout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            plan_or_addon: 'scale',
            customer_email: user?.email,
          }),
        });

        const data = await res.json();
        if (data.success && data.data?.checkout_url) {
          window.location.href = data.data.checkout_url;
        } else {
          throw new Error(data.detail || 'Impossible de créer la session de paiement.');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Une erreur est survenue.');
      }
    }

    startCheckout();
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex flex-col items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 max-w-md w-full text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-[#1A1A2E] mb-2">Une erreur est survenue</h2>
          <p className="text-sm text-[#5F6368] mb-6">{error}</p>
          <button
            onClick={() => window.location.href = '/upgrade'}
            className="w-full py-3 rounded-xl bg-[#7C3AED] text-white font-bold text-sm hover:bg-[#6D28D9] transition-colors"
          >
            Voir les plans →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#EFF6FF] flex flex-col items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 max-w-md w-full text-center">
        <img src="/favicon.png?v=4" alt="Pepperyn" className="w-16 h-16 mx-auto mb-4 object-contain" />
        <div className="w-8 h-8 border-2 border-[#7C3AED] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-bold text-[#1A1A2E] mb-2">Préparation de votre paiement SCALE…</h2>
        <p className="text-sm text-[#5F6368]">
          Vous allez être redirigé vers Stripe en quelques secondes.
        </p>
        <p className="text-xs text-[#5F6368] mt-3 italic">Paiement 100 % sécurisé via Stripe</p>
      </div>
    </div>
  );
}
