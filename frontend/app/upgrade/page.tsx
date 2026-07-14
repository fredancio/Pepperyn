'use client';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { normalizePlan } from '@/lib/featureGate';
import { EXECUTIVE_CAPACITY_PACKS } from '@/lib/plans-config';
// WP4A — addons chargés depuis plans-config.ts (source canonique unique).

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// WP4A — Valeurs alignées sur product_catalog.py via plans-config.ts.
const PLANS_DATA = [
  {
    id: 'free', name: 'FREE', subtitle: 'Découvrez Pepperyn', price: '0€', period: '',
    tagline: 'Idéal pour tester Pepperyn sur vos propres données.',
    color: 'green', highlighted: false, badge: null,
    features: ['1 analyse / mois', 'Export PDF', 'Mémoire légère', '3 échanges de suivi inclus'],
    microcopy: '"Parfait pour tester Pepperyn sur vos propres données."',
    ctaHref: null, ctaAction: null,
  },
  {
    id: 'pro', name: 'PRO', subtitle: 'CFO, CEO, CFO de transition, dirigeants PME & startups, experts-comptables…', price: '149€', period: '/mois',
    tagline: 'Votre copilote financier complet.',
    color: 'blue', highlighted: true, badge: '⭐ LE PLUS POPULAIRE',
    features: ['30 analyses / mois', '75 échanges de suivi / mois', 'Exports Excel, PDF et PowerPoint', 'Mémoire persistante complète', 'Multi-entités (clients, filiales, dossiers)', 'Simulateur de décisions financières', 'Analyse multi-périodes & comparaisons', 'Projections financières', 'Executive Capacity Packs disponibles à la demande'],
    microcopy: '"Gérez plusieurs clients ou entités depuis un seul outil."',
    ctaHref: null, ctaAction: 'stripe',
  },
  {
    id: 'scale', name: 'SCALE', subtitle: 'Pour départements financiers, cabinets & groupes multi-entités', price: '349€', period: '/mois',
    tagline: 'Votre AI Financial Operating System sur-mesure.',
    color: 'purple', highlighted: false, badge: null,
    features: ['100 analyses / mois', '500 échanges de suivi / mois', '✦ Tout le plan PRO inclus', 'Workspace multi-utilisateurs & rôles', 'Permissions & gouvernance des analyses', 'Architecture multi-filiales & consolidation', 'Intégrations ERP, CRM & logiciels comptables', 'Workflows financiers personnalisés', 'Reporting automatisé & tableaux de bord', 'Hébergement dédié / déploiement on-premise', 'LLM privé / open-source en option', 'Onboarding dédié & SLA support prioritaire'],
    microcopy: '"Industrialisez votre pilotage financier à l\'échelle de votre organisation."',
    ctaHref: '/contact', ctaAction: null,
  },
];

// WP4A — Packs chargés depuis plans-config.ts (source canonique unique).
const addons = EXECUTIVE_CAPACITY_PACKS.map(pack => ({
  id:   pack.id,
  name: pack.name,
  desc: `+${pack.analysesAdded} analyses`,
  price: pack.priceLabel,
}));

const colorMap: Record<string, { ring: string; bg: string; ctaUpgrade: string; ctaCurrent: string }> = {
  green:  { ring: 'border-green-200',  bg: 'bg-white',     ctaUpgrade: 'bg-green-600 text-white hover:bg-green-700', ctaCurrent: 'bg-gray-100 text-gray-400 cursor-default' },
  blue:   { ring: 'border-[#1B73E8]',  bg: 'bg-[#0A2540]', ctaUpgrade: 'bg-white text-[#1B73E8] hover:bg-blue-50',  ctaCurrent: 'bg-white/20 text-white/70 cursor-default' },
  purple: { ring: 'border-purple-200', bg: 'bg-white',     ctaUpgrade: 'bg-[#7C3AED] text-white hover:bg-[#6D28D9]', ctaCurrent: 'bg-gray-100 text-gray-400 cursor-default' },
};

export default function UpgradePage() {
  const [currentPlan, setCurrentPlan] = useState<string>('free');
  const [loadingPlan, setLoadingPlan] = useState(true);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadPlan() {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) { setLoadingPlan(false); return; }
        const { data: profile } = await supabase
          .from('profiles')
          .select('company:companies(plan)')
          .eq('id', user.id)
          .single();
        const companyData = (profile as { company?: { plan?: string } } | null)?.company;
        if (companyData?.plan) setCurrentPlan(normalizePlan(companyData.plan));
      } catch {
        // ignore
      } finally {
        setLoadingPlan(false);
      }
    }
    loadPlan();
  }, []);

  const handleUpgrade = async (planId: string) => {
    setLoading(planId);
    setError('');
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const { data: { user } } = await supabase.auth.getUser();
      if (!session) {
        // Redirect to login with return URL
        window.location.href = '/login?redirect=/upgrade';
        return;
      }

      const res = await fetch(`${API_URL}/api/billing/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          plan_or_addon: planId,
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
      setLoading(null);
    }
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

      <div className="max-w-5xl mx-auto px-4 py-10">
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
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Plans grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 items-stretch mb-12">
          {PLANS_DATA.map((plan) => {
            const c = colorMap[plan.color];
            const isHighlighted = plan.highlighted;
            const isCurrent = !loadingPlan && currentPlan === plan.id;
            const isUpgrade = !loadingPlan && plan.id !== 'free' && currentPlan !== plan.id && plan.id !== 'scale';

            return (
              <div
                key={plan.id}
                className={`relative flex flex-col gap-4 p-5 rounded-2xl border-2 shadow-sm ${c.ring} ${c.bg} ${
                  isHighlighted ? 'shadow-2xl shadow-blue-500/20 scale-[1.02]' : ''
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-1 text-xs font-bold rounded-full bg-amber-400 text-white shadow-md whitespace-nowrap">
                    {plan.badge}
                  </div>
                )}
                <div>
                  <p className={`text-xs font-bold uppercase tracking-widest mb-1 ${isHighlighted ? 'text-blue-300' : 'text-[#5F6368]'}`}>
                    {plan.name}
                    {isCurrent && (
                      <span className="ml-2 px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-semibold normal-case tracking-normal">
                        Plan actuel
                      </span>
                    )}
                  </p>
                  <p className={`text-xs mb-2 ${isHighlighted ? 'text-slate-300' : 'text-[#5F6368]'}`}>{plan.subtitle}</p>
                  <div className="flex items-end gap-1">
                    <span className={`text-3xl font-extrabold ${isHighlighted ? 'text-white' : 'text-[#1A1A2E]'}`}>{plan.price}</span>
                    {plan.period && <span className={`text-sm mb-0.5 ${isHighlighted ? 'text-slate-300' : 'text-[#5F6368]'}`}>{plan.period}</span>}
                  </div>
                  {plan.tagline && (
                    <p className={`text-xs mt-1 font-medium ${isHighlighted ? 'text-blue-200' : 'text-[#1B73E8]'}`}>{plan.tagline}</p>
                  )}
                </div>

                <div className={`h-px ${isHighlighted ? 'bg-white/15' : 'bg-gray-100'}`} />

                <ul className="flex flex-col gap-1.5 flex-1">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs">
                      <svg className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${isHighlighted ? 'text-blue-300' : 'text-green-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className={isHighlighted ? 'text-slate-200' : 'text-[#1A1A2E]'}>{f}</span>
                    </li>
                  ))}
                </ul>

                {plan.microcopy && (
                  <p className={`text-xs italic ${isHighlighted ? 'text-slate-400' : 'text-[#5F6368]'}`}>{plan.microcopy}</p>
                )}

                {/* CTA */}
                {isCurrent ? (
                  <div className={`w-full py-2.5 rounded-xl font-bold text-sm text-center ${c.ctaCurrent}`}>
                    ✓ Plan actuel
                  </div>
                ) : plan.ctaHref ? (
                  <Link
                    href={plan.ctaHref}
                    className={`w-full py-2.5 rounded-xl font-bold text-sm text-center transition-all block ${c.ctaUpgrade}`}
                  >
                    Nous contacter
                  </Link>
                ) : plan.ctaAction === 'stripe' ? (
                  <button
                    onClick={() => handleUpgrade(plan.id)}
                    disabled={loading === plan.id}
                    className={`w-full py-2.5 rounded-xl font-bold text-sm text-center transition-all block disabled:opacity-70 ${c.ctaUpgrade}`}
                  >
                    {loading === plan.id ? 'Redirection…' : 'Passer à PRO'}
                  </button>
                ) : null}
              </div>
            );
          })}
        </div>

        {/* Add-ons */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm mb-8">
          <div className="text-center mb-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#EFF6FF] border border-blue-100 rounded-full mb-3">
              <span className="text-xs font-semibold text-[#1B73E8]">Disponible sur les plans PRO et SCALE</span>
            </div>
            <h2 className="text-lg font-bold text-[#1A1A2E] mb-1">Besoin de plus de capacité ce mois-ci ?</h2>
            <p className="text-sm text-[#5F6368]">Achetez des analyses supplémentaires à la demande — sans changer de plan, sans engagement.</p>
          </div>
          <div className="grid sm:grid-cols-3 gap-3">
            {addons.map((a) => (
              <button
                key={a.id}
                onClick={() => handleUpgrade(a.id)}
                disabled={loading === a.id}
                className="flex items-center justify-between p-4 bg-[#EFF6FF] border border-blue-100 rounded-xl hover:border-[#1B73E8] hover:shadow-sm transition-all w-full text-left disabled:opacity-70 group"
              >
                <div>
                  <p className="text-sm font-bold text-[#1A1A2E]">{a.name}</p>
                  <p className="text-xs text-[#5F6368]">{a.desc}</p>
                </div>
                <span className="text-lg font-extrabold text-[#1B73E8] group-hover:text-[#0D47A1] ml-3">
                  {loading === a.id ? '…' : a.price}
                </span>
              </button>
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
              href="/contact"
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
