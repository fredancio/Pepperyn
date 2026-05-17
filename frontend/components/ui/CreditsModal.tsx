'use client';
import { useEffect } from 'react';
import Link from 'next/link';

interface CreditsModalProps {
  plan: string;
  analysesUsed: number;
  analysesLimit: number;
  onClose: () => void;
}

const ADDONS = [
  { id: 'addon_starter', name: 'Starter Pack', analyses: 10,  price: '19€', popular: false },
  { id: 'addon_growth',  name: 'Growth Pack',  analyses: 50,  price: '69€', popular: true  },
  { id: 'addon_scale',   name: 'Scale Pack',   analyses: 200, price: '199€', popular: false },
];

export function CreditsModal({ plan, analysesUsed, analysesLimit, onClose }: CreditsModalProps) {
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const remaining = Math.max(0, analysesLimit - analysesUsed);
  const pct = analysesLimit > 0 ? Math.min(100, (analysesUsed / analysesLimit) * 100) : 100;

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
          <div className="text-3xl mb-2">💳</div>
          <h2 className="text-white font-extrabold text-lg">Crédits d&apos;analyses</h2>
          <p className="text-slate-300 text-sm mt-0.5">Ajoutez de la capacité sans changer de plan</p>
        </div>

        {/* Quota actuel */}
        <div className="p-5 border-b border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-[#1A1A2E]">Quota ce mois</span>
            <span className={`text-sm font-bold ${remaining === 0 ? 'text-red-600' : 'text-[#1B73E8]'}`}>
              {analysesUsed}/{analysesLimit} analyses
            </span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${pct >= 100 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-400' : 'bg-[#1B73E8]'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          {remaining === 0 && (
            <p className="text-xs text-red-600 mt-1.5 font-medium">
              ⚠️ Quota épuisé — achetez des crédits pour continuer ce mois-ci
            </p>
          )}
        </div>

        {/* Add-on packs */}
        <div className="p-5">
          <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-widest mb-3">
            Packs de crédits supplémentaires
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
                      // TODO demain : POST /api/billing/checkout { plan_or_addon: addon.id }
                      window.location.href = 'mailto:contact@pepperyn.com?subject=Achat%20crédits%20Pepperyn&body=Je%20souhaite%20acheter%20le%20' + addon.name;
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
              pour activer vos crédits immédiatement.
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
