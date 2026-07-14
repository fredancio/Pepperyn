import Link from 'next/link';
import { EXECUTIVE_CAPACITY_PACKS, getCommercialPlan } from '@/lib/plans-config';
// WP4A — plans et addons chargés depuis plans-config.ts (source canonique unique).
// Aucune constante commerciale (prix, quotas) n'est dupliquée dans ce fichier.

// Données commerciales issues de la source canonique — product_catalog.py via plans-config.ts
const FREE_CFG  = getCommercialPlan('free');
const PRO_CFG   = getCommercialPlan('pro');
const SCALE_CFG = getCommercialPlan('scale');

type PlanPhase = {
  number: string;
  title: string;
  badge: string;
  badgeStyle: 'devis' | 'price';
  description: string;
  items: string[];
  note: string | null;
};

type PlanExtras = {
  label: string;
  detail: string;
  phases?: PlanPhase[];
  services?: {
    title: string;
    items: string[];
  };
};

const plans: {
  name: string;
  subtitle: string;
  price: string;
  period: string;
  tagline: string;
  highlighted: boolean;
  badge: string | null;
  color: string;
  features: string[];
  extras: PlanExtras | null;
  microcopy: string;
  cta: string;
  ctaHref: string;
}[] = [
  {
    name: 'FREE',
    subtitle: 'Découvrez Pepperyn',
    price: FREE_CFG.priceLabel,
    period: FREE_CFG.period,
    tagline: 'Idéal pour tester Pepperyn sur vos propres données.',
    highlighted: false,
    badge: null,
    color: 'green',
    features: [
      `${FREE_CFG.analysesPerMonth} analyse / mois`,
      'Export PDF',
      'Mémoire légère',
      `${FREE_CFG.interactionsPerMonth} échanges de suivi inclus`,
    ],
    extras: null,
    microcopy: 'Parfait pour tester Pepperyn sur vos propres données.',
    cta: 'Commencer gratuitement',
    ctaHref: '/register',
  },
  {
    name: 'PRO',
    subtitle: 'CFO, CEO, CFO de transition, dirigeants PME & startups, experts-comptables…',
    price: PRO_CFG.priceLabel,
    period: PRO_CFG.period,
    tagline: 'Votre copilote financier complet.',
    highlighted: true,
    badge: '⭐ LE PLUS POPULAIRE',
    color: 'blue',
    features: [
      `${PRO_CFG.analysesPerMonth} analyses / mois`,
      `${PRO_CFG.interactionsPerMonth} échanges de suivi / mois`,
      'Exports Excel, PDF et PowerPoint',
      'Mémoire persistante complète',
      'Multi-entités (clients, filiales, dossiers)',
      'Simulateur de décisions financières',
      'Analyse multi-périodes & comparaisons',
      'Projections financières',
      'Executive Capacity Packs disponibles à la demande',
    ],
    extras: null,
    microcopy: 'Gérez plusieurs clients ou entités depuis un seul outil.',
    cta: 'Passer à PRO',
    ctaHref: '/register?plan=pro',
  },
  {
    name: 'SCALE',
    subtitle: 'Pour les entreprises souhaitant intégrer Pepperyn directement à leur ERP, CRM et processus financiers.',
    price: SCALE_CFG.priceLabel,
    period: SCALE_CFG.period,
    tagline: 'Votre AI Financial Operating System sur-mesure.',
    highlighted: false,
    badge: null,
    color: 'purple',
    features: [
      `${SCALE_CFG.analysesPerMonth} analyses / mois`,
      `${SCALE_CFG.interactionsPerMonth} échanges de suivi / mois`,
      '✦ Tout le plan PRO inclus',
      'Workspace multi-utilisateurs & rôles',
      'Permissions & gouvernance des analyses',
      'Architecture multi-filiales & consolidation',
      'Intégrations ERP, CRM & logiciels comptables',
      'Workflows financiers personnalisés',
      'Reporting automatisé & tableaux de bord',
      'Hébergement dédié / déploiement on-premise',
      'LLM privé / open-source en option',
      'Onboarding dédié & SLA support prioritaire',
    ],
    extras: {
      label: '🚀 Déploiement en 2 étapes',
      detail: '',
      phases: [
        {
          number: '1',
          title: 'Projet d\'implémentation',
          badge: 'Sur devis — facturé une seule fois',
          badgeStyle: 'devis',
          description: 'Chaque entreprise possède un environnement différent. Nous réalisons un déploiement personnalisé comprenant :',
          items: [
            'audit de vos systèmes',
            'connexions ERP / CRM',
            'intégrations comptables',
            'workflows sur mesure',
            'onboarding des équipes',
            'formation',
            'mise en production',
          ],
          note: 'Cette phase est chiffrée sur devis et facturée une seule fois.',
        },
        {
          number: '2',
          title: 'Exploitation de Pepperyn',
          badge: '349 €/mois',
          badgeStyle: 'price',
          description: 'Une fois votre environnement opérationnel :',
          items: [
            'toutes les fonctionnalités SCALE',
            'maintenance & mises à jour',
            'support prioritaire',
            'exploitation continue',
          ],
          note: null,
        },
      ],
      services: {
        title: 'Prestations pouvant être intégrées à votre projet',
        items: [
          'Connexions ERP/CRM',
          'Intégrations comptables',
          'Workflows personnalisés',
          'Reporting automatisé',
          'Dashboards consolidés',
          'Hébergement dédié',
          'VPS privé',
          'Déploiement on-premise',
          'LLM privé / open-source',
        ],
      },
    },
    microcopy: 'Industrialisez votre pilotage financier à l\'échelle de votre organisation.',
    cta: 'Nous contacter',
    ctaHref: '/contact',
  },
];

// WP4A — Packs chargés depuis plans-config.ts (source canonique unique).
const addons = EXECUTIVE_CAPACITY_PACKS.map(pack => ({
  name: pack.name,
  desc: `+${pack.analysesAdded} analyses`,
  price: pack.priceLabel,
}));

const colorMap: Record<string, { ring: string; badge: string; bg: string; text: string; cta: string; ctaText: string }> = {
  green:  { ring: 'border-green-200',  badge: 'bg-green-100 text-green-700',   bg: 'bg-white',     text: 'text-[#1A1A2E]', cta: 'bg-green-600 text-white hover:bg-green-700',  ctaText: 'text-white' },
  blue:   { ring: 'border-[#1B73E8]',  badge: 'bg-amber-400 text-white',       bg: 'bg-[#0A2540]', text: 'text-white',     cta: 'bg-white text-[#1B73E8] hover:bg-blue-50',   ctaText: 'text-[#1B73E8]' },
  purple: { ring: 'border-purple-200', badge: 'bg-purple-100 text-purple-700', bg: 'bg-white',     text: 'text-[#1A1A2E]', cta: 'bg-[#7C3AED] text-white hover:bg-[#6D28D9]', ctaText: 'text-white' },
};

const costComparison = [
  { label: 'Recruter un CFO senior', value: '90 000 € – 150 000 € / an', tone: 'default' as const },
  { label: 'Cabinet de conseil', value: '1 500 € – 3 000 € / jour', tone: 'default' as const },
  { label: 'Mission ponctuelle', value: '15 000 € – 50 000 €', tone: 'default' as const },
  { label: 'Pepperyn', value: 'À partir de 0 €, puis 149 € / mois', tone: 'highlight' as const },
];

export function PricingPlans() {
  return (
    <section className="py-20 lg:py-28 bg-[#EFF6FF]" id="tarifs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Tarification transparente</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] mb-4">
            Moins cher qu&apos;une décision manquée
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto mb-2">
            Pepperyn ne se contente pas d'analyser. Il vous indique quoi faire.
          </p>
          <p className="text-sm text-[#5F6368] italic">Chaque mois d'inaction détruit de la valeur.</p>
        </div>

        {/* Combien coûte réellement une mauvaise décision ? */}
        <div className="max-w-3xl mx-auto mb-16">
          <p className="text-center text-sm font-bold uppercase tracking-widest text-[#5F6368] mb-6">
            Combien coûte réellement une mauvaise décision ?
          </p>
          <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
            {costComparison.map((c, i) => (
              <div
                key={c.label}
                className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-4 px-6 sm:px-8 py-4 sm:py-5 ${
                  i < costComparison.length - 1 ? 'border-b border-gray-100' : ''
                } ${c.tone === 'highlight' ? 'bg-[#EFF6FF]' : ''}`}
              >
                <p className={`text-sm ${c.tone === 'highlight' ? 'font-bold text-[#1A1A2E]' : 'text-[#5F6368]'}`}>
                  {c.label}
                </p>
                <p className={`text-sm font-bold flex-shrink-0 ${c.tone === 'highlight' ? 'text-[#1B73E8]' : 'text-[#1A1A2E]'}`}>
                  {c.value}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Plans grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch mt-12">
          {plans.map((plan) => {
            const c = colorMap[plan.color];
            const isHighlighted = plan.highlighted;
            return (
              <div
                key={plan.name}
                className={`relative flex flex-col gap-5 p-6 rounded-2xl border-2 shadow-sm transition-all duration-200 ${c.ring} ${c.bg} ${
                  isHighlighted ? 'shadow-2xl shadow-blue-500/20 scale-[1.02]' : ''
                }`}
              >
                {/* Badge */}
                {plan.badge && (
                  <div className={`absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-1 text-xs font-bold rounded-full shadow-md whitespace-nowrap ${c.badge}`}>
                    {plan.badge}
                  </div>
                )}

                {/* Header */}
                <div>
                  <p className={`text-xs font-bold uppercase tracking-widest mb-1 ${isHighlighted ? 'text-blue-300' : 'text-[#5F6368]'}`}>
                    {plan.name}
                  </p>
                  <p className={`text-xs mb-3 ${isHighlighted ? 'text-slate-300' : 'text-[#5F6368]'}`}>
                    {plan.subtitle}
                  </p>
                  <div className="flex items-end gap-1 mb-1">
                    <span className={`text-4xl font-extrabold ${isHighlighted ? 'text-white' : 'text-[#1A1A2E]'}`}>
                      {plan.price}
                    </span>
                    {plan.period && (
                      <span className={`text-sm mb-1 ${isHighlighted ? 'text-slate-300' : 'text-[#5F6368]'}`}>
                        {plan.period}
                      </span>
                    )}
                  </div>
                  <p className={`text-xs font-semibold ${isHighlighted ? 'text-blue-200' : 'text-[#1B73E8]'}`}>
                    {plan.tagline}
                  </p>
                </div>

                <div className={`h-px ${isHighlighted ? 'bg-white/15' : 'bg-gray-100'}`} />

                {/* Features */}
                <ul className="flex flex-col gap-2 flex-1">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <svg
                        className={`w-4 h-4 flex-shrink-0 mt-0.5 ${isHighlighted ? 'text-blue-300' : 'text-green-500'}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className={isHighlighted ? 'text-slate-200' : 'text-[#1A1A2E]'}>{f}</span>
                    </li>
                  ))}
                </ul>

                {/* Déploiement 2 étapes block (SCALE only) */}
                {plan.extras && (
                  <div className="rounded-xl border border-purple-200 bg-purple-50 p-4 space-y-3">
                    {/* Header */}
                    <p className="text-sm font-bold text-purple-900">{plan.extras.label}</p>

                    {/* Phases */}
                    {plan.extras.phases && plan.extras.phases.map((phase, pi) => (
                      <div key={pi}>
                        {/* Arrow between phases */}
                        {pi > 0 && (
                          <div className="flex items-center justify-center py-1">
                            <div className="flex flex-col items-center gap-0.5">
                              <div className="w-px h-3 bg-purple-300" />
                              <svg className="w-3 h-3 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 3a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V4a1 1 0 011-1z" clipRule="evenodd" />
                              </svg>
                            </div>
                          </div>
                        )}
                        <div className={`rounded-lg p-3 ${pi === 0 ? 'bg-white border border-purple-200' : 'bg-purple-100 border border-purple-200'}`}>
                          {/* Phase header */}
                          <div className="flex items-start justify-between gap-2 mb-1.5">
                            <p className="text-xs font-bold text-purple-900">
                              {phase.number}. {phase.title}
                            </p>
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full whitespace-nowrap flex-shrink-0 ${
                              phase.badgeStyle === 'devis'
                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                : 'bg-purple-700 text-white'
                            }`}>
                              {phase.badge}
                            </span>
                          </div>
                          <p className="text-xs text-purple-700 leading-relaxed mb-1.5">{phase.description}</p>
                          <ul className="space-y-0.5">
                            {phase.items.map((item, ii) => (
                              <li key={ii} className="text-xs text-purple-800 flex items-center gap-1.5">
                                <span className="text-purple-400">•</span>{item}
                              </li>
                            ))}
                          </ul>
                          {phase.note && (
                            <p className="text-xs font-semibold text-purple-800 mt-2 pt-2 border-t border-purple-200">
                              {phase.note}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* Services */}
                    {plan.extras.services && (
                      <div className="border-t border-purple-200 pt-3">
                        <p className="text-xs font-semibold text-purple-700 mb-2">
                          {plan.extras.services.title}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {plan.extras.services.items.map((s, i) => (
                            <span
                              key={i}
                              className="text-xs px-2 py-0.5 bg-white text-purple-800 rounded-full border border-purple-300 font-medium"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Microcopy */}
                <p className={`text-xs italic leading-snug ${isHighlighted ? 'text-slate-400' : 'text-[#5F6368]'}`}>
                  &ldquo;{plan.microcopy}&rdquo;
                </p>

                {/* Price summary visual (SCALE only) */}
                {plan.extras?.phases && (
                  <div className="rounded-xl border border-purple-200 overflow-hidden text-xs font-semibold">
                    <div className="flex items-center justify-between px-3 py-2 bg-amber-50 border-b border-purple-200">
                      <span className="text-purple-900">Projet d&apos;implémentation</span>
                      <span className="text-amber-700">Sur devis · une seule fois</span>
                    </div>
                    <div className="flex justify-center py-1 bg-white border-b border-purple-100">
                      <svg className="w-3.5 h-3.5 text-purple-300" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 3a1 1 0 011 1v10.586l2.293-2.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V4a1 1 0 011-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex items-center justify-between px-3 py-2 bg-purple-700">
                      <span className="text-purple-100">Pepperyn déployé</span>
                      <span className="text-white font-bold">349 €/mois</span>
                    </div>
                  </div>
                )}

                {/* CTA */}
                <Link
                  href={plan.ctaHref}
                  className={`w-full py-3 rounded-xl font-bold text-sm text-center transition-all duration-200 ${c.cta}`}
                >
                  {plan.cta}
                </Link>
              </div>
            );
          })}
        </div>

        {/* Add-ons section */}
        <div className="mt-14 bg-white border border-gray-100 rounded-2xl p-8 shadow-sm">
          <div className="text-center mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#EFF6FF] border border-blue-100 rounded-full mb-3">
              <span className="text-xs font-semibold text-[#1B73E8]">Disponible sur les plans PRO et SCALE</span>
            </div>
            <h3 className="text-xl font-bold text-[#1A1A2E] mb-1">Besoin de plus de capacité ce mois-ci ?</h3>
            <p className="text-sm text-[#5F6368]">
              Achetez des analyses supplémentaires à la demande — sans changer de plan, sans engagement.
            </p>
          </div>
          <div className="grid sm:grid-cols-3 gap-4">
            {addons.map((a) => (
              <Link
                key={a.name}
                href="/register"
                className="flex items-center justify-between p-4 bg-[#EFF6FF] border border-blue-100 rounded-xl hover:border-[#1B73E8] hover:shadow-sm transition-all group"
              >
                <div>
                  <p className="text-sm font-bold text-[#1A1A2E]">{a.name}</p>
                  <p className="text-xs text-[#5F6368]">{a.desc}</p>
                </div>
                <span className="text-lg font-extrabold text-[#1B73E8] group-hover:text-[#0D47A1]">{a.price}</span>
              </Link>
            ))}
          </div>
          <p className="text-center text-xs text-[#5F6368] italic mt-4">
            Conçu pour absorber les pics d&apos;activité sans bloquer votre travail.
          </p>
        </div>

        {/* Enterprise section */}
        <div className="mt-8 bg-[#0A2540] rounded-2xl p-7 text-white">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Besoins ultra-spécifiques ?</span>
              <h3 className="text-lg font-bold text-white mt-1 mb-1">
                Architecture IA financière 100% privée & sur-mesure
              </h3>
              <p className="text-sm text-slate-300 max-w-xl">
                Déploiement isolé dans votre infrastructure, LLM open-source sur vos serveurs,
                intégrations propriétaires, conformité RGPD renforcée, SLA entreprise.
                Au-delà du plan SCALE — devis sur demande.
              </p>
            </div>
            <div className="flex-shrink-0">
              <Link
                href="/contact"
                className="inline-flex items-center gap-2 px-6 py-3.5 bg-white text-[#1B73E8] font-bold text-sm rounded-xl hover:bg-blue-50 transition-colors whitespace-nowrap"
              >
                Parler à un expert →
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom microcopy */}
        <div className="mt-10 text-center">
          <p className="text-sm text-[#5F6368]">
            Transformez vos données financières en décisions business.{' '}
            <span className="font-semibold text-[#1A1A2E]">Détectez les problèmes avant qu&apos;ils impactent votre rentabilité.</span>
          </p>
        </div>

      </div>
    </section>
  );
}
