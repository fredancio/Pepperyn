'use client';
import Link from 'next/link';
import { useState } from 'react';

const plans = [
  {
    id: 'free', name: 'FREE', subtitle: 'Découvrez Pepperyn', price: '0€', period: '',
    color: 'green', highlighted: false, badge: null,
    features: ['1 analyse / mois', 'Export PDF', 'Mémoire légère', 'Données anonymisées', '3 interactions contextuelles incluses'],
    cta: 'Plan actuel', ctaDisabled: true,
  },
  {
    id: 'pro', name: 'PRO', subtitle: 'Pour dirigeants de PME', price: '59€', period: '/mois',
    color: 'blue', highlighted: false, badge: null,
    features: ['15 analyses / mois', 'Usage conversationnel inclus', 'Exports Excel, PDF et PowerPoint', 'Mémoire persistante', 'Suivi des tendances financières', 'Alertes et dérives automatiques', 'Analyse multi-périodes', 'Projections simples'],
    cta: 'Choisir PRO', ctaDisabled: false,
  },
  {
    id: 'power', name: 'POWER', subtitle: 'Pour CFO, consultants et experts-comptables', price: '129€', period: '/mois',
    color: 'red', highlighted: true, badge: '⭐ LE PLUS UTILISÉ',
    features: ['75 analyses / mois', 'Usage avancé inclus', 'Multi-entités', 'Mémoire persistante par entité', 'Simulateur de décisions', 'Projections avancées', 'Comparaison périodes', 'Exports premium', 'Historique enrichi'],
    cta: 'Choisir POWER', ctaDisabled: false,
  },
  {
    id: 'scale', name: 'SCALE', subtitle: 'Pour départements financiers et cabinets', price: '349€', period: '/mois',
    color: 'purple', highlighted: false, badge: null,
    features: ['250 analyses / mois', 'Usage intensif inclus', 'Multi-users', 'Multi-entités avancé', 'Permissions utilisateurs', 'Workspace collaboratif', 'Support prioritaire', 'Gouvernance des analyses'],
    cta: 'Choisir SCALE', ctaDisabled: false,
  },
];

const addons = [
  { id: 'addon_starter', name: 'Starter Pack', desc: '+10 analyses', price: '19€' },
  { id: 'addon_growth',  name: 'Growth Pack',  desc: '+50 analyses', price: '69€' },
  { id: 'addon_scale',   name: 'Scale Pack',   desc: '+200 analyses', price: '199€' },
];

const colorMap: Record<string, { ring: string; bg: string; text: string; cta: string }> = {
  green:  { ring: 'border-green-200',  bg: 'bg-white',     text: 'text-[#1A1A2E]', cta: 'bg-gray-100 text-gray-400 cursor-default' },
  blue:   { ring: 'border-blue-200',   bg: 'bg-white',     text: 'text-[#1A1A2E]', cta: 'bg-[#1B73E8] text-white hover:bg-[#0D47A1]' },
  red:    { ring: 'border-[#1B73E8]',  bg: 'bg-[#0A2540]', text: 'text-white',     cta: 'bg-white text-[#1B73E8] hover:bg-blue-50' },
  purple: { ring: 'border-purple-200', bg: 'bg-white',     text: 'text-[#1A1A2E]', cta: 'bg-[#7C3AED] text-white hover:bg-[#6D28D9]' },
};

function ComingSoonBadge() {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-semibold rounded-full">
      ⚡ Bientôt disponible
    </span>
  );
}

export default function UpgradePage() {
  const [clicked, setClicked] = useState<string | null>(null);

  const handleUpgrade = (planId: string) => {
    setClicked(planId);
    // TODO demain : appel POST /api/billing/checkout avec planId
    // const res = await fetch('/api/billing/checkout', { method: 'POST', body: JSON.stringify({ plan_or_addon: planId }) })
    // const { data } = await res.json()
    // if (data.checkout_url) window.location.href = data.checkout_url
  };

  return (
    <div className="min-h-screen bg-[#EFF6FF]">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-4 py-4 flex items-center gap-3">
        <Link href="/app/chat" className="text-[#5F6368] hover:text-[#1A1A2E] transition-colors">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div className="flex items-center gap-2">
          <img src="/favicon.png?v=4" alt="Pepperyn" className="w-8 h-8 object-contain" />
          <span className="font-bold text-[#1A1A2E]">Choisissez votre plan</span>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-10">
        {/* Hero */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Tarification transparente</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[#1A1A2E] mb-2">
            Votre copilote financier IA
          </h1>
          <p className="text-[#5F6368]">Pepperyn ne se contente pas d'analyser. Il vous indique quoi faire.</p>
          <p className="text-sm text-[#5F6368] italic mt-1">Chaque mois d'inaction détruit de la valeur.</p>

          {/* Stripe coming soon notice */}
          <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-xl">
            <span className="text-amber-600">⚡</span>
            <span className="text-sm text-amber-700 font-medium">
              Paiement en ligne disponible très prochainement — contactez-nous pour activer votre plan dès maintenant
            </span>
            <Link href="mailto:contact@pepperyn.com" className="text-amber-700 font-bold underline hover:no-underline">
              contact@pepperyn.com
            </Link>
          </div>
        </div>

        {/* Plans grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-12">
          {plans.map((plan) => {
            const c = colorMap[plan.color];
            return (
              <div
                key={plan.id}
                className={`relative flex flex-col gap-4 p-5 rounded-2xl border-2 shadow-sm ${c.ring} ${c.bg} ${
                  plan.highlighted ? 'shadow-2xl shadow-blue-500/20 scale-[1.02]' : ''
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-1 text-xs font-bold rounded-full bg-amber-400 text-white shadow-md whitespace-nowrap">
                    {plan.badge}
                  </div>
                )}
                <div>
                  <p className={`text-xs font-bold uppercase tracking-widest mb-1 ${plan.highlighted ? 'text-blue-300' : 'text-[#5F6368]'}`}>
                    {plan.name}
                  </p>
                  <p className={`text-xs mb-2 ${plan.highlighted ? 'text-slate-300' : 'text-[#5F6368]'}`}>{plan.subtitle}</p>
                  <div className="flex items-end gap-1">
                    <span className={`text-3xl font-extrabold ${plan.highlighted ? 'text-white' : 'text-[#1A1A2E]'}`}>{plan.price}</span>
                    {plan.period && <span className={`text-sm mb-0.5 ${plan.highlighted ? 'text-slate-300' : 'text-[#5F6368]'}`}>{plan.period}</span>}
                  </div>
                </div>

                <div className={`h-px ${plan.highlighted ? 'bg-white/15' : 'bg-gray-100'}`} />

                <ul className="flex flex-col gap-1.5 flex-1">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs">
                      <svg className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${plan.highlighted ? 'text-blue-300' : 'text-green-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className={plan.highlighted ? 'text-slate-200' : 'text-[#1A1A2E]'}>{f}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => !plan.ctaDisabled && handleUpgrade(plan.id)}
                  disabled={plan.ctaDisabled}
                  className={`w-full py-2.5 rounded-xl font-bold text-sm text-center transition-all ${c.cta}`}
                >
                  {plan.ctaDisabled
                    ? plan.cta
                    : clicked === plan.id
                      ? '⚡ Bientôt disponible...'
                      : plan.cta
                  }
                </button>

                {!plan.ctaDisabled && (
                  <p className="text-center text-xs text-[#5F6368]/60">
                    Contactez <a href="mailto:contact@pepperyn.com" className="underline">contact@pepperyn.com</a>
                  </p>
                )}
              </div>
            );
          })}
        </div>

        {/* Add-ons */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm mb-8">
          <div className="text-center mb-5">
            <h2 className="text-lg font-bold text-[#1A1A2E] mb-1">Besoin de plus de capacité ?</h2>
            <p className="text-sm text-[#5F6368]">Ajoutez des analyses supplémentaires à la demande, sans changer de plan.</p>
          </div>
          <div className="grid sm:grid-cols-3 gap-3">
            {addons.map((a) => (
              <div key={a.id} className="flex items-center justify-between p-4 bg-[#EFF6FF] border border-blue-100 rounded-xl">
                <div>
                  <p className="text-sm font-bold text-[#1A1A2E]">{a.name}</p>
                  <p className="text-xs text-[#5F6368]">{a.desc}</p>
                  <ComingSoonBadge />
                </div>
                <button
                  onClick={() => handleUpgrade(a.id)}
                  className="text-lg font-extrabold text-[#1B73E8] hover:text-[#0D47A1] transition-colors ml-3"
                >
                  {a.price}
                </button>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-[#5F6368] italic mt-3">
            Conçu pour absorber les pics d&apos;activité sans interruption.
          </p>
        </div>

        {/* Enterprise */}
        <div className="bg-[#0A2540] rounded-2xl p-6 text-white">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">Enterprise & Private AI</p>
              <h3 className="text-lg font-bold mb-1">Pour entreprises souhaitant intégrer Pepperyn à leurs systèmes internes</h3>
              <p className="text-sm text-slate-300">Connexions ERP/CRM, hébergement dédié, LLM privé, architecture multi-filiales — sur devis.</p>
            </div>
            <Link
              href="mailto:contact@pepperyn.com"
              className="flex-shrink-0 px-5 py-3 bg-white text-[#1B73E8] font-bold text-sm rounded-xl hover:bg-blue-50 transition-colors whitespace-nowrap"
            >
              Parler à un expert →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
