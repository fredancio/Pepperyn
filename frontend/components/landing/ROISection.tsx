export function ROISection() {
  return (
    <section className="py-20 lg:py-28 bg-[#F8FAFF] border-t border-[#1B73E8]/10">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Retour sur investissement</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight">
            Une décision qui se rembourse dès la première analyse.
          </h2>
        </div>

        {/* Avant / Après */}
        <div className="grid md:grid-cols-2 gap-6 mb-10">
          <div className="bg-white border border-gray-100 rounded-2xl p-7 shadow-sm flex flex-col gap-4">
            <p className="text-xs font-bold uppercase tracking-widest text-red-500">Sans diagnostic</p>
            <ul className="flex flex-col gap-3">
              {[
                'Des dérives de marge qui passent inaperçues pendant des mois',
                'Des décisions prises à l’instinct, sans estimation d’impact',
                'Un reporting manuel qui consomme des heures chaque mois',
              ].map((t) => (
                <li key={t} className="flex items-start gap-2.5 text-sm text-[#1A1A2E]">
                  <svg className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  {t}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-[#0A2540] rounded-2xl p-7 shadow-sm flex flex-col gap-4">
            <p className="text-xs font-bold uppercase tracking-widest text-blue-300">Avec Pepperyn</p>
            <ul className="flex flex-col gap-3">
              {[
                'Un diagnostic complet de votre rentabilité en moins de 2 minutes',
                'Des actions priorisées par impact chiffré, pas par intuition',
                'Le suivi de l’effet réel de chaque décision prise',
              ].map((t) => (
                <li key={t} className="flex items-start gap-2.5 text-sm text-white">
                  <svg className="w-4 h-4 text-[#60A5FA] flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                  {t}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Exemple chiffré */}
        <div className="bg-white border border-[#1B73E8]/20 rounded-2xl p-7 sm:p-8 text-center">
          <p className="text-sm font-semibold text-[#1B73E8] mb-2">Exemple réel</p>
          <p className="text-lg sm:text-xl text-[#1A1A2E] font-bold leading-snug max-w-2xl mx-auto">
            Une dérive de marge de 2 points sur 2,4M€ de chiffre d&apos;affaires représente
            près de <span className="text-[#1B73E8]">48 000 € par an</span> non détectés.
          </p>
          <p className="text-sm text-[#5F6368] mt-3">
            Le plan PRO coûte 79€ par mois.
          </p>
        </div>
      </div>
    </section>
  );
}
