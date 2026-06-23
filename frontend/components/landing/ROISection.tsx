const examples = [
  { trigger: 'Une amélioration de marge de 1 %', value: '120 000 €' },
  { trigger: 'Une renégociation fournisseur', value: '80 000 €' },
  {
    trigger: 'Une décision retardée',
    value: 'Plusieurs centaines de milliers d’euros',
    note: 'potentiellement perdus',
  },
];

export function ROISection() {
  return (
    <section className="py-20 lg:py-28 bg-[#F8FAFF] border-t border-[#1B73E8]/10">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-14">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight max-w-2xl mx-auto">
            Chaque semaine d&apos;attente détruit de la valeur.
          </h2>
        </div>

        {/* Exemples */}
        <div className="flex flex-col gap-4 mb-14">
          {examples.map((ex) => (
            <div
              key={ex.trigger}
              className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 bg-white border border-gray-100 rounded-2xl shadow-sm px-7 py-6"
            >
              <p className="text-base text-[#1A1A2E] font-medium">{ex.trigger}</p>
              <div className="text-right">
                <p className="text-2xl font-extrabold text-[#1B73E8]">{ex.value}</p>
                {ex.note && <p className="text-xs text-[#5F6368]">{ex.note}</p>}
              </div>
            </div>
          ))}
        </div>

        {/* Comparaison abonnement */}
        <div className="bg-[#0A2540] rounded-2xl px-8 py-10 text-center">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-12">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-blue-300 mb-2">Abonnement Pepperyn</p>
              <p className="text-3xl font-extrabold text-white">Quelques centaines d&apos;euros</p>
              <p className="text-sm text-blue-200 mt-1">par mois</p>
            </div>
            <div className="hidden sm:block w-px h-16 bg-white/10" />
            <p className="text-sm text-blue-200 max-w-xs text-left sm:text-left">
              Face à des décisions dont l&apos;impact se compte en dizaines voire centaines de
              milliers d&apos;euros, la question n&apos;est plus &laquo;&nbsp;combien ça coûte&nbsp;&raquo;
              mais &laquo;&nbsp;combien coûte de ne pas l&apos;avoir&nbsp;&raquo;.
            </p>
          </div>
        </div>

      </div>
    </section>
  );
}
