'use client';
import { useEffect } from 'react';
import Link from 'next/link';

// WP1D — Option B
// Section usage entièrement réécrite : quota mensuel d'abord, Executive Capacity Pack ensuite.
// Vocabulaire officiel : "Executive Capacity Pack" (jamais "bonus" ni "Crédits d'analyses").
// Toutes les valeurs viennent directement du backend (zéro recalcul côté frontend).
// La section packs (ADDONS) reste inchangée — périmètre WP4.

interface CreditsModalProps {
  plan: string;
  analysesUsed: number;              // analyses_monthly_used depuis BillingUsage
  analysesLimit: number;             // analyses_limit depuis BillingUsage
  analysesRemaining: number | null;  // analyses_monthly_remaining depuis BillingUsage
  bonusRemaining: number;            // analyses_bonus_remaining depuis BillingUsage
  bonusSuspended: boolean;           // analyses_bonus_suspended depuis BillingUsage
  renewalDate: string | null;        // renewal_date depuis BillingUsage (ISO8601)
  onClose: () => void;
}

// Packs inchangés — valeurs et prix seront chargés depuis GET /api/billing/plans en WP4.
const ADDONS = [
  { id: 'addon_starter', name: 'Starter Pack', analyses: 10,  price: '19€', popular: false },
  { id: 'addon_growth',  name: 'Growth Pack',  analyses: 50,  price: '69€', popular: true  },
  { id: 'addon_scale',   name: 'Scale Pack',   analyses: 200, price: '199€', popular: false },
];

export function CreditsModal({
  plan,
  analysesUsed,
  analysesLimit,
  analysesRemaining,
  bonusRemaining,
  bonusSuspended,
  renewalDate,
  onClose,
}: CreditsModalProps) {
  // Fermeture sur Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  // Calcul purement visuel pour la barre de progression (rendu uniquement)
  const pct = analysesLimit > 0 ? Math.min(100, (analysesUsed / analysesLimit) * 100) : 100;
  const isOver = analysesRemaining !== null ? analysesRemaining <= 0 : analysesUsed >= analysesLimit;

  const renewalLabel = renewalDate
    ? new Date(renewalDate).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })
    : null;

  const hasExecPack = bonusRemaining > 0;
  const totalRemaining = hasExecPack && !bonusSuspended
    ? (analysesRemaining ?? 0) + bonusRemaining
    : null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">

        {/* Header */}
        <div className="bg-[#0A2540] p-5 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-7 h-7 flex items-center justify-center text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <div className="text-3xl mb-2">⚡</div>
          <h2 className="text-white font-extrabold text-lg">Executive Capacity</h2>
          <p className="text-slate-300 text-sm mt-0.5">Gérez votre capacité d&apos;analyse</p>
        </div>

        {/* ── Quota mensuel (bloc principal) ────────────────────────────── */}
        <div className="p-5 border-b border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-[#1A1A2E]">Quota mensuel</span>
            <span className={`text-sm font-bold ${isOver ? 'text-red-600' : 'text-[#1B73E8]'}`}>
              {analysesUsed} / {analysesLimit} analyses
            </span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${pct >= 100 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-400' : 'bg-[#1B73E8]'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="mt-1.5 flex flex-col gap-0.5">
            {isOver ? (
              <p className="text-xs text-red-600 font-medium">⚠️ Quota mensuel épuisé</p>
            ) : (
              analysesRemaining !== null && (
                <p className="text-xs text-[#5F6368]">
                  {analysesRemaining} analyse{analysesRemaining > 1 ? 's' : ''} restante{analysesRemaining > 1 ? 's' : ''} ce mois
                </p>
              )
            )}
            {renewalLabel && (
              <p className="text-xs text-[#5F6368]">Renouvellement le {renewalLabel}</p>
            )}
          </div>

          {/* ── Executive Capacity Pack (bloc secondaire) ──────────────── */}
          {hasExecPack && (
            <div className={`mt-3 rounded-xl px-4 py-3 ${
              bonusSuspended
                ? 'bg-amber-50 border border-amber-100'
                : 'bg-green-50 border border-green-100'
            }`}>
              {bonusSuspended ? (
                <>
                  <p className="text-xs font-semibold text-amber-800 mb-1">⏸ Executive Capacity Pack</p>
                  <p className="text-sm font-bold text-amber-700">{bonusRemaining} analyses disponibles</p>
                  <p className="text-xs text-amber-600 mt-0.5">Conservées tant qu&apos;elles ne sont pas utilisées.</p>
                  <p className="text-xs text-amber-600 mt-0.5">
                    Suspendues sur plan FREE. Aucune analyse ne sera perdue.
                    Réactivées automatiquement dès votre passage à PRO ou SCALE.
                  </p>
                </>
              ) : (
                <>
                  <p className="text-xs font-semibold text-green-800 mb-1">♾️ Executive Capacity Pack</p>
                  <p className="text-sm font-bold text-green-700">{bonusRemaining} analyses disponibles</p>
                  <p className="text-xs text-green-600 mt-0.5">Conservées tant qu&apos;elles ne sont pas utilisées.</p>
                  <p className="text-xs text-green-600">Consommées en priorité avant le quota mensuel.</p>
                  {totalRemaining !== null && (
                    <p className="text-xs text-green-700 font-semibold mt-1.5">
                      {totalRemaining} analyse{totalRemaining > 1 ? 's' : ''} disponible{totalRemaining > 1 ? 's' : ''} au total
                    </p>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {/* ── Packs Executive Capacity — inchangés (WP4) ──────────────── */}
        <div className="p-5">
          <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-widest mb-3">
            Packs Executive Capacity supplémentaires
          </p>
          <div className="flex flex-col gap-2 mb-4">
            {ADDONS.map((addon) => (
              <div
                key={addon.id}
                className={`flex items-center justify-between p-3 rounded-xl border transition-colors ${
                  addon.popular
                    ? 'border-[#1B73E8] bg-[#EFF6FF]'
                    : 'border-gray-100 bg-gray-50 hover:bg-[#EFF6FF] hover:border-blue-100'
                }`}
              >
                <div className="flex items-center gap-3">
                  {addon.popular && (
                    <span className="text-xs bg-[#1B73E8] text-white px-2 py-0.5 rounded-full font-bold">
                      Populaire
                    </span>
                  )}
                  <div>
                    <p className="text-sm font-bold text-[#1A1A2E]">{addon.name}</p>
                    <p className="text-xs text-[#5F6368]">+{addon.analyses} analyses</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-lg font-extrabold text-[#1B73E8]">{addon.price}</span>
                  <button
                    onClick={() => {
                      // TODO WP4 : POST /api/billing/checkout { plan_or_addon: addon.id }
                      window.location.href = 'mailto:contact@pepperyn.com?subject=Achat%20Executive%20Capacity%20Pepperyn&body=Je%20souhaite%20acheter%20le%20' + addon.name;
                    }}
                    className="px-3 py-1.5 bg-[#1B73E8] text-white text-xs font-bold rounded-lg hover:bg-[#0D47A1] transition-colors whitespace-nowrap"
                  >
                    Acheter →
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Stripe coming soon */}
          <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 mb-4">
            <p className="text-xs text-amber-700 font-medium">
              ⚡ Paiement en ligne disponible très prochainement.
              En attendant, envoyez un email à{' '}
              <a href="mailto:contact@pepperyn.com" className="underline font-bold">
                contact@pepperyn.com
              </a>{' '}
              pour activer votre Executive Capacity Pack immédiatement.
            </p>
          </div>

          {/* Upgrade CTA */}
          <div className="flex flex-col gap-2">
            <Link
              href="/upgrade"
              onClick={onClose}
              className="w-full py-2.5 rounded-xl font-bold text-sm text-center bg-[#0A2540] text-white hover:bg-[#1B73E8] transition-colors"
            >
              Voir tous les plans →
            </Link>
            <button
              onClick={onClose}
              className="w-full py-2 text-xs text-[#5F6368] hover:text-[#1A1A2E] transition-colors"
            >
              Continuer avec mon plan actuel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
