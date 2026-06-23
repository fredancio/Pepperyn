const results = [
  { value: '3', label: 'décisions priorisées en moyenne par analyse' },
  { value: '~30h', label: 'gagnées par semaine pour une équipe financière de 4 personnes' },
  { value: '< 3 mois', label: 'pour un retour sur investissement positif' },
  { value: '100%', label: 'des comités de direction préparés sans retravail' },
];

export function ProofSection() {
  return (
    <section className="py-20 lg:py-24 bg-[#F8FAFF] border-t border-[#1B73E8]/10">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="text-center mb-14">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight max-w-2xl mx-auto">
            Ce que Pepperyn améliore réellement.
          </h2>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-gray-100 rounded-2xl overflow-hidden shadow-sm mb-10">
          {results.map((r) => (
            <div key={r.label} className="bg-white px-6 py-9 flex flex-col items-center text-center gap-2">
              <span className="text-4xl font-extrabold text-[#1B73E8] tracking-tight">{r.value}</span>
              <span className="text-xs text-[#5F6368] leading-snug max-w-[160px]">{r.label}</span>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3">
          {['Décisions priorisées', 'Temps économisé', 'Valeur potentielle créée', 'Risque réduit', 'CODIR préparés'].map((tag) => (
            <span
              key={tag}
              className="px-4 py-2 bg-white border border-gray-100 rounded-full text-sm font-medium text-[#1A1A2E] shadow-sm"
            >
              {tag}
            </span>
          ))}
        </div>

      </div>
    </section>
  );
}
