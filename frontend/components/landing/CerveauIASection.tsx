export function CerveauIASection() {
  return (
    <section className="py-24 bg-[#F8FAFF] border-t border-[#1B73E8]/20">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col gap-16">

        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-5">
            <span className="text-sm font-medium text-[#1B73E8]">Pourquoi Pepperyn</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight mb-4">
            Votre département financier mérite{' '}
            <em className="not-italic text-[#1B73E8] italic">son propre cerveau IA</em>
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto">
            Ce que font les CFO les plus avancés en 2026 —
            et pourquoi la majorité de leurs concurrents ne le sait pas encore.
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[#1B73E8]/10 rounded-2xl overflow-hidden shadow-sm">
          {[
            { value: '~30h', label: 'gagnées par semaine pour une équipe financière de 4 personnes' },
            { value: '60 sec', label: "pour une analyse complète de vos données financières" },
            { value: '< 3 mois', label: "pour un ROI positif sur l'investissement" },
          ].map((stat, i) => (
            <div key={i} className="bg-[#0A2540] px-8 py-10 flex flex-col items-center text-center gap-3">
              <span className="text-5xl font-extrabold text-white tracking-tight">{stat.value}</span>
              <span className="text-blue-300 text-sm leading-snug max-w-[180px]">{stat.label}</span>
            </div>
          ))}
        </div>

        {/* Two-column problem block */}
        <div className="grid md:grid-cols-2 gap-6">

          {/* LLM génériques */}
          <div className="bg-white border border-gray-100 rounded-2xl p-8 shadow-sm flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div>
              <h4 className="text-base font-bold text-[#1A1A2E] mb-2">
                Le problème avec les LLM génériques
              </h4>
              <p className="text-sm text-[#5F6368] leading-relaxed">
                ChatGPT, Copilot, Gemini — ces outils ne connaissent pas votre Plan Comptable,
                vos BU, vos marges par produit, vos règles de gestion interne. Chaque réponse
                est une estimation. Chaque chiffre doit être vérifié. Vous avez investi dans
                un outil de productivité qui vous crée de la friction.
              </p>
            </div>
          </div>

          {/* La vérité */}
          <div className="bg-white border border-gray-100 rounded-2xl p-8 shadow-sm flex flex-col gap-4">
            <div className="w-10 h-10 rounded-xl bg-[#1B73E8]/10 border border-[#1B73E8]/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h4 className="text-base font-bold text-[#1A1A2E] mb-2">
                Ce qui rend un copilote financier réellement utile
              </h4>
              <p className="text-sm text-[#5F6368] leading-relaxed">
                Le problème n&apos;est pas le modèle d&apos;IA.<br />
                Le problème est qu&apos;un modèle générique ne comprend ni votre entreprise, ni votre logique financière.<br />
                Un copilote financier réellement utile s&apos;appuie sur vos données, votre historique et votre contexte métier pour produire des analyses pertinentes, cohérentes et actionnables.
              </p>
            </div>
          </div>
        </div>

        {/* Mémoire persistante — bloc signature */}
        <div className="relative bg-[#0A2540] rounded-2xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-[#1B73E8]/20 to-transparent pointer-events-none" />
          <div className="relative px-10 py-10 flex flex-col md:flex-row items-start md:items-center gap-8">
            <div className="flex-shrink-0">
              <div className="w-14 h-14 rounded-2xl bg-[#1B73E8]/20 border border-[#1B73E8]/30 flex items-center justify-center">
                <svg className="w-7 h-7 text-[#60A5FA]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
            </div>
            <div className="flex-1">
              <p className="text-white font-semibold text-base mb-2">
                La mémoire persistante — le vrai game changer
              </p>
              <p className="text-blue-200 text-sm leading-relaxed">
                Pepperyn connaît votre historique financier, vos décisions passées, et vérifie
                automatiquement ses propres analyses — zéro hallucination. Il ne répond pas à vos
                questions. Il devient votre <strong className="text-white">copilote financier</strong>.
              </p>
            </div>
            <div className="flex-shrink-0 hidden md:block">
              <span className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#1B73E8]/20 border border-[#1B73E8]/30 rounded-xl text-xs font-semibold text-blue-200 whitespace-nowrap">
                Plans PRO & SCALE
              </span>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
