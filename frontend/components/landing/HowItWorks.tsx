export function HowItWorks() {
  const steps = [
    {
      number: '01',
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      ),
      title: 'Importez votre fichier',
      description: 'Glissez-déposez votre fichier Excel, CSV ou PDF. Pepperyn supporte les P&L, bilans, budgets, et tout tableau financier.',
      highlight: 'Excel, CSV, PDF',
      color: 'blue',
    },
    {
      number: '02',
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2" />
        </svg>
      ),
      title: "L'IA analyse vos données",
      description: "Notre moteur IA lit, structure et analyse vos chiffres en profondeur. Il détecte anomalies, tendances et opportunités comme un consultant senior.",
      highlight: 'Analyse IA en 60s',
      color: 'indigo',
    },
    {
      number: '03',
      icon: (
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      title: 'Recevez votre analyse',
      description: "Obtenez un rapport complet : KPIs, graphiques, alertes, recommandations prioritaires. Exportez en Excel ou discutez avec l'IA pour approfondir.",
      highlight: 'Rapport + Export Excel',
      color: 'green',
    },
  ];

  const colorMap = {
    blue: {
      bg: 'bg-blue-100',
      text: 'text-[#1B73E8]',
      badge: 'bg-[#1B73E8]/10 text-[#1B73E8] border-[#1B73E8]/20',
      number: 'text-[#1B73E8]',
    },
    indigo: {
      bg: 'bg-indigo-100',
      text: 'text-indigo-600',
      badge: 'bg-indigo-50 text-indigo-600 border-indigo-200',
      number: 'text-indigo-600',
    },
    green: {
      bg: 'bg-green-100',
      text: 'text-green-600',
      badge: 'bg-green-50 text-green-700 border-green-200',
      number: 'text-green-600',
    },
  };

  return (
    <section className="py-20 lg:py-28 bg-[#EFF6FF]" id="comment-ca-marche">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Simple comme bonjour</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] mb-4">
            Comment ça fonctionne ?
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto">
            Trois étapes simples pour obtenir une analyse financière de niveau consultant
          </p>
        </div>

        {/* Steps */}
        <div className="grid md:grid-cols-3 gap-8 relative">
          {/* Connector line */}
          <div className="hidden md:block absolute top-16 left-1/3 right-1/3 h-0.5 bg-gradient-to-r from-[#1B73E8]/30 via-indigo-300/50 to-green-300/50" />

          {steps.map((step, index) => {
            const colors = colorMap[step.color as keyof typeof colorMap];
            return (
              <div key={index} className="relative flex flex-col items-center text-center gap-5 p-8 bg-white rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow duration-200">
                {/* Number */}
                <div className={`text-5xl font-black opacity-10 absolute top-4 right-5 ${colors.number}`}>
                  {step.number}
                </div>

                {/* Icon */}
                <div className={`w-16 h-16 ${colors.bg} ${colors.text} rounded-2xl flex items-center justify-center`}>
                  {step.icon}
                </div>

                {/* Content */}
                <div>
                  <h3 className="text-xl font-bold text-[#1A1A2E] mb-3">{step.title}</h3>
                  <p className="text-[#5F6368] leading-relaxed text-sm">{step.description}</p>
                </div>

                {/* Badge */}
                <div className={`px-3 py-1 rounded-full border text-xs font-semibold ${colors.badge}`}>
                  {step.highlight}
                </div>
              </div>
            );
          })}
        </div>

        {/* CTA */}
        <div className="text-center mt-12">
          <a
            href="/register"
            className="inline-flex items-center gap-2 px-7 py-4 bg-[#1B73E8] text-white rounded-xl font-semibold hover:bg-[#0D47A1] transition-all duration-200 shadow-lg shadow-blue-500/25"
          >
            Essayer maintenant — c&apos;est gratuit
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </a>
          <p className="text-sm text-[#5F6368] mt-3">3 analyses gratuites • Sans carte bancaire</p>
        </div>
      </div>
    </section>
  );
}
