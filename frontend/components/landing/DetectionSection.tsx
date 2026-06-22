const items = [
  {
    icon: '💸',
    title: 'Pertes cachées',
    desc: 'Des charges ou des dérives qui grignotent votre résultat sans que personne ne les ait isolées.',
  },
  {
    icon: '📉',
    title: 'Dérive des marges',
    desc: 'Une marge qui se dégrade progressivement, masquée dans le détail des lignes comptables.',
  },
  {
    icon: '⚠️',
    title: 'Anomalies',
    desc: 'Des écarts inhabituels dans vos charges ou vos revenus, détectés automatiquement.',
  },
  {
    icon: '🧾',
    title: 'Problèmes de trésorerie',
    desc: 'Un risque de tension de cash à venir, identifié avant qu’il ne devienne critique.',
  },
  {
    icon: '🚀',
    title: 'Leviers de croissance',
    desc: 'Les actions à plus fort impact pour accélérer votre rentabilité.',
  },
];

export function DetectionSection() {
  return (
    <section className="py-20 lg:py-24 bg-[#F8FAFF] border-t border-[#1B73E8]/10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Diagnostic automatique</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight">
            En moins de 2 minutes, Pepperyn peut détecter :
          </h2>
        </div>

        {/* Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {items.map((item) => (
            <div
              key={item.title}
              className="flex flex-col gap-3 p-5 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-300"
            >
              <div className="w-11 h-11 rounded-xl bg-[#1B73E8]/10 border border-[#1B73E8]/20 flex items-center justify-center text-xl">
                {item.icon}
              </div>
              <h3 className="text-sm font-bold text-[#1A1A2E]">{item.title}</h3>
              <p className="text-xs text-[#5F6368] leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
