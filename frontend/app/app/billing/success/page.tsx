'use client';
import { useEffect, useState, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { packLabel } from '@/lib/plans-config';

// WP4A — PLAN_LABELS utilise packLabel() depuis plans-config.ts pour les packs.
// Aucune quantité ni nom de pack n'est dupliqué ici.
const PLAN_LABELS: Record<string, string> = {
  pro:           'PRO',
  scale:         'SCALE',
  addon_starter: packLabel('addon_starter'),  // 'Starter Capacity Pack (+10 analyses)'
  addon_growth:  packLabel('addon_growth'),   // 'Growth Capacity Pack (+20 analyses)'
  addon_scale:   packLabel('addon_scale'),    // 'Scale Capacity Pack (+80 analyses)'
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// WP4B.1 — Constantes de polling d'activation
// La page ne confirme JAMAIS un plan uniquement via le paramètre URL.
// Elle attend la confirmation réelle du backend (companies.plan via /api/billing/usage).
const POLL_INTERVAL_MS  = 3_000;   // 3 secondes entre chaque vérification
const MAX_POLL_ATTEMPTS = 20;      // 20 × 3 s = 60 secondes max avant timeout

type ActivationState = 'waiting' | 'confirmed' | 'timeout';

export default function BillingSuccessPage() {
  const params  = useSearchParams();
  const router  = useRouter();
  const plan    = params.get('plan') || 'pro';
  const isAddon = plan.startsWith('addon_');

  // WP4B.1 — Pour les plans (PRO/SCALE) : attendre la confirmation backend avant
  // d'afficher le succès. Pour les addons, le flux ne change pas de plan dans
  // companies.plan → pas de polling requis.
  const [activationState, setActivationState] = useState<ActivationState>(
    isAddon ? 'confirmed' : 'waiting'
  );
  const [countdown, setCountdown] = useState(8);
  const pollAttemptsRef = useRef(0);

  // ── Polling d'activation plan (PRO / SCALE uniquement) ───────────────────
  // Appelle /api/billing/usage toutes les POLL_INTERVAL_MS ms jusqu'à ce que
  // data.plan === plan (webhook Stripe reçu et appliqué) ou timeout.
  useEffect(() => {
    if (isAddon) return;  // addons : pas de changement de plan → pas de polling

    let pollId: ReturnType<typeof setInterval>;

    const poll = async () => {
      pollAttemptsRef.current += 1;

      if (pollAttemptsRef.current > MAX_POLL_ATTEMPTS) {
        clearInterval(pollId);
        setActivationState('timeout');
        return;
      }

      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session?.access_token) return;

        const resp = await fetch(`${API_URL}/api/billing/usage`, {
          headers: { 'Authorization': `Bearer ${session.access_token}` },
        });
        if (!resp.ok) return;

        const json = await resp.json();
        // Confirmation réelle : companies.plan a été mis à jour par le webhook Stripe
        if (json?.data?.plan === plan) {
          clearInterval(pollId);
          setActivationState('confirmed');
        }
      } catch {
        // Erreur réseau transitoire — continuer à poller
      }
    };

    // Premier appel immédiat, puis intervalles réguliers
    poll();
    pollId = setInterval(poll, POLL_INTERVAL_MS);

    return () => clearInterval(pollId);  // cleanup à l'unmount
  }, [plan, isAddon]);

  // ── Redirection automatique une fois confirmé ─────────────────────────────
  useEffect(() => {
    if (activationState !== 'confirmed') return;

    const t = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) { clearInterval(t); router.push('/app/chat'); }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [activationState, router]);

  // ── État : attente activation (plan en cours de provisioning) ─────────────
  if (activationState === 'waiting') {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-xl p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-5">
            <div className="w-8 h-8 border-[3px] border-[#1B73E8] border-t-transparent rounded-full animate-spin" />
          </div>
          <h1 className="text-2xl font-extrabold text-[#1A1A2E] mb-2">
            Paiement reçu
          </h1>
          <p className="text-[#5F6368] mb-6">
            Nous finalisons l&apos;activation de votre plan {PLAN_LABELS[plan] || plan}…
          </p>
          <div className="bg-[#EFF6FF] rounded-xl p-4">
            <p className="text-sm text-[#1B73E8] font-medium">
              ⏳ Vérification en cours, cela prend généralement moins d&apos;une minute.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── État : timeout (webhook non reçu dans le délai imparti) ──────────────
  if (activationState === 'timeout') {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-xl p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-5">
            <svg className="w-8 h-8 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-extrabold text-[#1A1A2E] mb-2">
            Activation en cours
          </h1>
          <p className="text-[#5F6368] mb-4">
            Votre paiement a bien été reçu, mais l&apos;activation de votre plan prend
            plus de temps que prévu.
          </p>
          <p className="text-[#5F6368] mb-6">
            Actualisez la page dans quelques minutes ou contactez-nous à{' '}
            <a href="mailto:info@finflate.com" className="text-[#1B73E8] underline">
              info@finflate.com
            </a>.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="block w-full py-3.5 bg-[#1B73E8] text-white rounded-xl font-bold text-sm hover:bg-[#0D47A1] transition-colors"
          >
            Actualiser →
          </button>
        </div>
      </div>
    );
  }

  // ── État : confirmé (plan activé par le webhook Stripe) ───────────────────
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
          {isAddon ? 'Analyses ajoutées !' : 'Bienvenue sur le plan ' + (PLAN_LABELS[plan] || plan) + ' !'}
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
