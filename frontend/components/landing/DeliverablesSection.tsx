const deliverables = [
  {
    name: 'Executive Financial Model',
    why: 'Une structuration rigoureuse de vos données financières, fiabilisée et prête à servir de base à toute décision.',
    decision: 'Sert de fondation chiffrée à chaque recommandation — rien n’est avancé sans calcul vérifiable.',
    when: 'En amont de toute analyse.',
  },
  {
    name: 'Executive Report',
    why: 'Un diagnostic clair de ce qui crée ou détruit votre rentabilité, et des décisions priorisées par impact.',
    decision: 'Répond à la question : que faire maintenant, et dans quel ordre ?',
    when: 'Dès l’import de vos données, en quelques minutes.',
  },
  {
    name: 'Executive Board Deck',
    why: 'Une synthèse exécutive prête à être présentée, sans retravail, sans mise en forme supplémentaire.',
    decision: 'Permet au Comité de Direction de décider en réunion, pas la semaine suivante.',
    when: 'Avant chaque comité de direction.',
  },
];

export function DeliverablesSection() {
  return (
    <section id="livrables" className="py-20 lg:py-28 bg-white border-t border-gray-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-5">
            <span className="text-sm font-medium text-[#1B73E8]">Les livrables d&apos;une mission de conseil</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight max-w-2xl mx-auto">
            Ce que produit chaque analyse.
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {deliverables.map((d) => (
            <div key={d.name} className="flex flex-col gap-5 bg-white border border-gray-100 rounded-2xl shadow-sm p-7">
              <h3 className="text-lg font-bold text-[#1A1A2E] leading-snug">{d.name}</h3>
              <div className="h-px bg-gray-100" />
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-[#5F6368] mb-1.5">Pourquoi ce livrable existe</p>
                <p className="text-sm text-[#1A1A2E] leading-relaxed">{d.why}</p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-[#5F6368] mb-1.5">À quelle décision il sert</p>
                <p className="text-sm text-[#1A1A2E] leading-relaxed">{d.decision}</p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-[#5F6368] mb-1.5">À quel moment</p>
                <p className="text-sm text-[#1B73E8] font-semibold leading-relaxed">{d.when}</p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
