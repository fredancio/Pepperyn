import Link from 'next/link';

type PlanExtras = {
  label: string;
  detail: string;
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
    price: '0€',
    period: '',
    tagline: 'Idéal pour tester Pepperyn sur vos propres données.',
    highlighted: false,
    badge: null,
    color: 'green',
    features: [
      '1 analyse / mois',
      'Export PDF',
      'Mémoire légère',
      '3 interactions contextuelles incluses',
    ],
    extras: null,
    microcopy: 'Parfait pour tester Pepperyn sur vos propres données.',
    cta: 'Commencer gratuitement',
    ctaHref: '/register',
  },
  {
    name: 'PRO',
    subtitle: 'Pour dirigeants de PME, CFO et experts-comptables',
    price: '79€',
    period: '/mois',
    tagline: 'Votre copilote financier complet.',
    highlighted: true,
    badge: '⭐ LE PLUS POPULAIRE',
    color: 'blue',
    features: [
      '15 analyses / mois',
      '75 interactions contextuelles / mois',
      'Exports Excel, PDF et PowerPoint',
      'Mémoire persistante complète',
      'Multi-entités (clients, filiales, dossiers)',
      'Simulateur de décisions financières',
      'Analyse multi-périodes & comparaisons',
      'Projections et alertes automatiques',
      'Crédits supplémentaires disponibles à la demande',
    ],
    extras: null,
    microcopy: 'Gérez plusieurs clients ou entités depuis un seul outil.',
    cta: 'Passer à PRO',
    ctaHref: '/register',
  },
  {
    name: 'SCALE',
    subtitle: 'Pour départements financiers, cabinets & groupes multi-entités',
    price: '349€',
    period: '/mois',
    tagline: 'Votre AI Financial Operating System sur-mesure.',
    highlighted: false,
    badge: null,
    color: 'purple',
    features: [
      '250 analyses / mois',
      '500 interactions contextuelles / mois',
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
      label: '🔧 Implémentation sur-mesure incluse',
      detail: 'Chaque déploiement SCALE fait l\'objet d\'un onboarding personnalisé : cartographie de vos systèmes, intégrations, formation équipe et suivi continu. Devis d\'implémentation fourni à la signature.',
      services: {
        title: 'SERVICES DISPONIBLES SUR DEVIS',
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

const addons = [
  { name: 'Starter Pack', desc: '+10 analyses', price: '19€' },
  { name: 'Growth Pack', desc: '+50 analyses', price: '69€' },
  { name: 'Scale Pack', desc: '+200 analyses', price: '199€' },
];

const colorMap: Record<string, { ring: string; badge: string; bg: string; text: string; cta: string; ctaText: string }> = {
  green:  { ring: 'border-green-200',  badge: 'bg-green-100 text-green-700',   bg: 'bg-white',     text: 'text-[#1A1A2E]', cta: 'bg-green-600 text-white hover:bg-green-700',  ctaText: 'text-white' },
  blue:   { ring: 'border-[#1B73E8]',  badge: 'bg-amber-400 text-white',       bg: 'bg-[#0A2540]', text: 'text-white',     cta: 'bg-white text-[#1B73E8] hover:bg-blue-50',   ctaText: 'text-[#1B73E8]' },
  purple: { ring: 'border-purple-200', badge: 'bg-purple-100 text-purple-700', bg: 'bg-white',     text: 'text-[#1A1A2E]', cta: 'bg-[#7C3AED] text-white hover:bg-[#6D28D9]', ctaText: 'text-white' },
};

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
            Votre copilote financier IA
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto mb-2">
            Pepperyn ne se contente pas d'analyser. Il vous indique quoi faire.
          </p>
          <p className="text-sm text-[#5F6368] italic">Chaque mois d'inaction détruit de la valeur.</p>
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

                {/* ERP/CRM extras block (SCALE only) */}
                {plan.extras && (
                  <div className="rounded-xl border border-purple-200 bg-purple-50 p-4 space-y-3">
                    <div>
                      <p className="text-sm font-bold text-purple-900 mb-1">{plan.extras.label}</p>
                      <p className="text-xs text-purple-700 leading-relaxed">{plan.extras.detail}</p>
                    </div>
                    {plan.extras.services && (
                      <div className="border-t border-purple-200 pt-3">
                        <p className="text-xs font-bold text-purple-900 uppercase tracking-widest mb-2">
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
              <div key={a.name} className="flex items-center justify-between p-4 bg-[#EFF6FF] border border-blue-100 rounded-xl">
                <div>
                  <p className="text-sm font-bold text-[#1A1A2E]">{a.name}</p>
                  <p className="text-xs text-[#5F6368]">{a.desc}</p>
                </div>
                <span className="text-lg font-extrabold text-[#1B73E8]">{a.price}</span>
              </div>
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
