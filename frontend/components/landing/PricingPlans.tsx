import Link from 'next/link';

export function PricingPlans() {
  const plans = [
    {
      name: 'Gratuit',
      price: '0€',
      period: 'pour toujours',
      description: 'Pour découvrir Pepperyn',
      highlighted: false,
      badge: null,
      features: [
        { text: '3 analyses par mois', included: true },
        { text: 'Mode rapide uniquement', included: true },
        { text: 'Export PDF basique', included: true },
        { text: '1 utilisateur (PIN)', included: true },
        { text: 'Analyse complète approfondie', included: false },
        { text: 'Export Excel enrichi', included: false },
        { text: 'Historique des sessions', included: false },
        { text: 'Support prioritaire', included: false },
      ],
      cta: 'Commencer gratuitement',
      ctaHref: '/register',
      ctaVariant: 'secondary',
    },
    {
      name: 'Standard',
      price: '49€',
      period: 'par mois',
      description: 'Pour les équipes financières',
      highlighted: true,
      badge: 'Le plus populaire',
      features: [
        { text: '30 analyses par mois', included: true },
        { text: 'Modes rapide + complet', included: true },
        { text: 'Export Excel enrichi', included: true },
        { text: "Jusqu'à 5 utilisateurs (PIN)", included: true },
        { text: 'Historique des sessions', included: true },
        { text: 'Détection anomalies avancée', included: true },
        { text: 'Support prioritaire', included: false },
        { text: 'API access', included: false },
      ],
      cta: 'Choisir Standard',
      ctaHref: '/register',
      ctaVariant: 'primary',
    },
    {
      name: 'Premium',
      price: '149€',
      period: 'par mois',
      description: 'Pour les grandes entreprises',
      highlighted: false,
      badge: null,
      features: [
        { text: 'Analyses illimitées', included: true },
        { text: 'Modes rapide + complet', included: true },
        { text: 'Export Excel + PowerPoint', included: true },
        { text: 'Utilisateurs illimités (PIN)', included: true },
        { text: 'Historique illimité', included: true },
        { text: 'Détection anomalies avancée', included: true },
        { text: 'Support dédié 24/7', included: true },
        { text: 'API access + webhooks', included: true },
      ],
      cta: 'Contacter les ventes',
      ctaHref: '/register',
      ctaVariant: 'secondary',
    },
  ];

  return (
    <section className="py-20 lg:py-28 bg-[#EFF6FF]" id="tarifs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Tarification transparente</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] mb-4">
            Des prix adaptés à chaque équipe
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto">
            Commencez gratuitement. Passez à la vitesse supérieure quand vous êtes prêt.
          </p>
        </div>

        {/* Plans grid */}
        <div className="grid md:grid-cols-3 gap-8 items-center">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative flex flex-col gap-6 p-8 rounded-2xl ${
                plan.highlighted
                  ? 'bg-[#1B73E8] text-white shadow-2xl shadow-blue-500/30 scale-105'
                  : 'bg-white border border-gray-100 shadow-sm'
              }`}
            >
              {/* Badge */}
              {plan.badge && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-[#FF6B35] text-white text-xs font-bold rounded-full shadow-md whitespace-nowrap">
                  {plan.badge}
                </div>
              )}

              {/* Plan header */}
              <div>
                <p className={`text-sm font-semibold mb-1 ${plan.highlighted ? 'text-blue-200' : 'text-[#5F6368]'}`}>
                  {plan.name}
                </p>
                <div className="flex items-end gap-1 mb-1">
                  <span className={`text-4xl font-extrabold ${plan.highlighted ? 'text-white' : 'text-[#1A1A2E]'}`}>
                    {plan.price}
                  </span>
                  <span className={`text-sm mb-1 ${plan.highlighted ? 'text-blue-200' : 'text-[#5F6368]'}`}>
                    /{plan.period}
                  </span>
                </div>
                <p className={`text-sm ${plan.highlighted ? 'text-blue-100' : 'text-[#5F6368]'}`}>
                  {plan.description}
                </p>
              </div>

              {/* Divider */}
              <div className={`h-px ${plan.highlighted ? 'bg-white/20' : 'bg-gray-100'}`} />

              {/* Features */}
              <ul className="flex flex-col gap-3">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-sm">
                    {feature.included ? (
                      <svg className={`w-4 h-4 flex-shrink-0 ${plan.highlighted ? 'text-blue-200' : 'text-green-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className={`w-4 h-4 flex-shrink-0 ${plan.highlighted ? 'text-blue-400/50' : 'text-gray-300'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                    <span className={
                      feature.included
                        ? (plan.highlighted ? 'text-white' : 'text-[#1A1A2E]')
                        : (plan.highlighted ? 'text-blue-300/50' : 'text-gray-300')
                    }>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Link
                href={plan.ctaHref}
                className={`mt-auto w-full py-3.5 rounded-xl font-semibold text-sm text-center transition-all duration-200 ${
                  plan.highlighted
                    ? 'bg-white text-[#1B73E8] hover:bg-blue-50'
                    : plan.ctaVariant === 'primary'
                      ? 'bg-[#1B73E8] text-white hover:bg-[#0D47A1]'
                      : 'bg-[#EFF6FF] text-[#1B73E8] border border-[#1B73E8]/20 hover:bg-blue-50'
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* PIN note */}
        <div className="mt-12 text-center">
          <div className="inline-flex items-start gap-3 bg-white border border-blue-100 rounded-2xl px-6 py-4 shadow-sm max-w-2xl">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-[#1A1A2E]">Comment fonctionne le système de PIN ?</p>
              <p className="text-sm text-[#5F6368] mt-0.5">
                L&apos;administrateur crée le compte et reçoit un PIN à 4 chiffres unique.
                Il le partage avec son équipe pour permettre à tous de se connecter sans créer de compte individuel.
                Simple, rapide, sécurisé.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
