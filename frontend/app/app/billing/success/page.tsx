'use client';
import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';

const PLAN_LABELS: Record<string, string> = {
  pro:   'PRO',
  scale: 'SCALE',
  addon_starter: 'Starter Pack (+10 analyses)',
  addon_growth:  'Growth Pack (+50 analyses)',
  addon_scale:   'Scale Pack (+200 analyses)',
};

export default function BillingSuccessPage() {
  const params = useSearchParams();
  const router = useRouter();
  const plan   = params.get('plan') || 'pro';
  const isAddon = plan.startsWith('addon_');
  const [countdown, setCountdown] = useState(8);

  useEffect(() => {
    const t = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) { clearInterval(t); router.push('/app/chat'); }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [router]);

  return (
    <div className="min-h-screen bg-[#EFF6FF] flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl p-10 max-w-md w-full text-center">

        {/* Icône succès */}
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-5">
          <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-2xl font-extrabold text-[#1A1A2E] mb-2">
          {isAddon ? 'Crédits ajoutés !' : 'Bienvenue sur le plan ' + (PLAN_LABELS[plan] || plan) + ' !'}
        </h1>

        <p className="text-[#5F6368] mb-6">
          {isAddon
            ? `Votre achat "${PLAN_LABELS[plan]}" a bien été pris en compte. Les analyses supplémentaires sont disponibles immédiatement.`
            : `Votre abonnement est actif. Toutes les fonctionnalités du plan ${PLAN_LABELS[plan] || plan} sont maintenant disponibles.`
          }
        </p>

        <div className="bg-[#EFF6FF] rounded-xl p-4 mb-6">
          <p className="text-sm text-[#1B73E8] font-medium">
            ✉️ Un reçu de paiement vous a été envoyé par email.
          </p>
        </div>

        <Link
          href="/app/chat"
          className="block w-full py-3.5 bg-[#1B73E8] text-white rounded-xl font-bold text-sm hover:bg-[#0D47A1] transition-colors mb-3"
        >
          Commencer à analyser →
        </Link>

        <p className="text-xs text-[#5F6368]">
          Redirection automatique dans {countdown}s…
        </p>
      </div>
    </div>
  );
}
