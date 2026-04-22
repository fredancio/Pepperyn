export function ForWhom() {
  const profiles = [
    {
      emoji: '💼',
      role: 'CFO & Directeurs Financiers',
      lines: [
        'Obtenez des analyses structurées en secondes.',
        'Préparez vos CODIR sans ressaisie.',
      ],
    },
    {
      emoji: '📊',
      role: 'Contrôleurs de Gestion',
      lines: [
        'Automatisez vos analyses mensuelles.',
        'Détectez les anomalies instantanément.',
      ],
    },
    {
      emoji: '🏢',
      role: 'PME en croissance & Startups',
      lines: [
        'Le niveau d\'analyse d\'un grand groupe,',
        'à la portée d\'une PME.',
      ],
    },
  ];

  return (
    <section className="py-20 lg:py-28 bg-white" id="pour-qui">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Pour qui ?</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E]">
            À qui est destiné Pepperyn dans sa version finale{' '}
            <span className="text-[#1B73E8]">(coming soon)</span> ?
          </h2>
        </div>

        {/* Profile cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {profiles.map((profile) => (
            <div
              key={profile.role}
              className="flex flex-col gap-4 p-7 bg-[#EFF6FF] rounded-2xl border border-[#1B73E8]/20 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
            >
              {/* Emoji */}
              <div className="text-4xl">{profile.emoji}</div>

              {/* Role */}
              <h3 className="text-xl font-bold text-[#1A1A2E]">{profile.role}</h3>

              {/* Description */}
              <div className="flex flex-col gap-1">
                {profile.lines.map((line, i) => (
                  <p key={i} className="text-[#5F6368] text-sm leading-relaxed">{line}</p>
                ))}
              </div>

              {/* CTA */}
              <a
                href="/register"
                className="mt-auto text-sm font-semibold flex items-center gap-1 text-[#1B73E8] hover:underline"
              >
                Commencer maintenant
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
