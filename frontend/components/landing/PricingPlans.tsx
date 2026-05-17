import Link from 'next/link';

const plans = [
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
      'Données anonymisées',
      '3 interactions contextuelles incluses',
    ],
    microcopy: 'Parfait pour tester Pepperyn sur vos propres données.',
    cta: 'Commencer gratuitement',
    ctaHref: '/register',
  },
  {
    name: 'PRO',
    subtitle: 'Pour dirigeants de PME',
    price: '59€',
    period: '/mois',
    tagline: 'Votre copilote financier personnel.',
    highlighted: false,
    badge: null,
    color: 'blue',
    features: [
      '15 analyses / mois',
      'Usage conversationnel inclus',
      'Exports Excel, PDF et PowerPoint',
      'Mémoire persistante',
      'Suivi des tendances financières',
      'Alertes et dérives automatiques',
      'Analyse multi-périodes',
      'Projections simples',
      'Priorisation intelligente',
    ],
    microcopy: 'Détectez les problèmes avant qu\'ils impactent votre rentabilité.',
    cta: 'Commencer',
    ctaHref: '/register',
  },
  {
    name: 'POWER',
    subtitle: 'Pour CFO, consultants et experts-comptables',
    price: '129€',
    period: '/mois',
    tagline: 'Pilotage financier multi-entités.',
    highlighted: true,
    badge: '⭐ LE PLUS UTILISÉ',
    color: 'red',
    features: [
      '75 analyses / mois',
      'Usage avancé inclus',
      'Multi-entités',
      'Mémoire persistante par entité',
      'Simulateur de décisions',
      'Projections avancées',
      'Comparaison de périodes',
      'Analyse comparative',
      'Exports premium',
      'Historique enrichi',
      'Détection des tendances récurrentes',
    ],
    microcopy: 'Transformez vos données financières en décisions rapides et actionnables.',
    cta: 'Passer à Power',
    ctaHref: '/register',
  },
  {
    name: 'SCALE',
    subtitle: 'Pour départements financiers et cabinets',
    price: '349€',
    period: '/mois',
    tagline: 'AI Financial Operating System.',
    highlighted: false,
    badge: null,
    color: 'purple',
    features: [
      '250 analyses / mois',
      'Usage intensif inclus',
      'Multi-users',
      'Multi-entités avancé',
      'Permissions utilisateurs',
      'Workspace collaboratif',
      'Historique avancé',
      'Gouvernance des analyses',
      'Support prioritaire',
      'Collaboration équipe finance',
      'Gestion avancée des entités',
    ],
    microcopy: 'Industrialisez votre pilotage financier sans alourdir votre organisation.',
    cta: 'Passer à Scale',
    ctaHref: '/register',
  },
];

const addons = [
  { name: 'Starter Pack', desc: '+10 analyses', price: '19€' },
  { name: 'Growth Pack', desc: '+50 analyses', price: '69€' },
  { name: 'Scale Pack', desc: '+200 analyses', price: '199€' },
];

const colorMap: Record<string, { ring: string; badge: string; bg: string; text: string; cta: string; ctaText: string }> = {
  green:  { ring: 'border-green-200',  badge: 'bg-green-100 text-green-700',   bg: 'bg-white',          text: 'text-[#1A1A2E]', cta: 'bg-green-600 text-white hover:bg-green-700',  ctaText: 'text-white' },
  blue:   { ring: 'border-blue-200',   badge: 'bg-blue-100 text-blue-700',     bg: 'bg-white',          text: 'text-[#1A1A2E]', cta: 'bg-[#1B73E8] text-white hover:bg-[#0D47A1]', ctaText: 'text-white' },
  red:    { ring: 'border-[#1B73E8]',  badge: 'bg-amber-400 text-white',       bg: 'bg-[#0A2540]',      text: 'text-white',     cta: 'bg-white text-[#1B73E8] hover:bg-blue-50',   ctaText: 'text-[#1B73E8]' },
  purple: { ring: 'border-purple-200', badge: 'bg-purple-100 text-purple-700', bg: 'bg-white',          text: 'text-[#1A1A2E]', cta: 'bg-[#7C3AED] text-white hover:bg-[#6D28D9]', ctaText: 'text-white' },
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
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch mt-12">
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
            <h3 className="text-xl font-bold text-[#1A1A2E] mb-1">Besoin de plus de capacité ?</h3>
            <p className="text-sm text-[#5F6368]">
              Ajoutez des analyses supplémentaires à la demande, sans changer de plan.
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
            Conçu pour absorber les pics d&apos;activité sans interruption.
          </p>
        </div>

        {/* Enterprise section */}
        <div className="mt-8 bg-[#0A2540] rounded-2xl p-8 text-white">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Enterprise & Private AI</span>
              </div>
              <h3 className="text-xl font-bold text-white mb-1">
                Pour entreprises souhaitant intégrer Pepperyn à leurs systèmes internes
              </h3>
              <p className="text-sm text-slate-300 mb-4">
                Une architecture IA financière privée, sécurisée et adaptée à vos processus.
              </p>
              <div className="grid sm:grid-cols-2 gap-x-8 gap-y-1.5">
                {[
                  'Connexions ERP / CRM',
                  'Intégrations comptables',
                  'Workflows personnalisés',
                  'Reporting automatisé',
                  'Hébergement dédié / VPS privé',
                  'Déploiement on-premise',
                  'LLM privé / open-source',
                  'Architecture multi-filiales',
                ].map((item) => (
                  <div key={item} className="flex items-center gap-2 text-sm text-slate-300">
                    <svg className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    {item}
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-4">
                👉 Ces services nécessitent onboarding, configuration et intégration spécifique —{' '}
                et font l&apos;objet d&apos;un devis personnalisé avec frais d&apos;implémentation.
              </p>
            </div>
            <div className="flex-shrink-0">
              <Link
                href="mailto:contact@pepperyn.com"
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
