export function ReportDemoSection() {
  return (
    <section className="relative bg-white pb-20 lg:pb-28">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative -mt-4 lg:-mt-8">

          {/* Report card */}
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">

            {/* Header — report cover strip */}
            <div className="bg-gradient-to-r from-[#1B73E8] to-[#0D47A1] px-6 py-4 flex items-center gap-3">
              <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center flex-shrink-0">
                <img src="/favicon.png?v=5" alt="Pepperyn" className="w-9 h-9 object-contain" />
              </div>
              <div className="min-w-0">
                <p className="text-white font-semibold text-sm">Rapport d&apos;analyse financière</p>
                <p className="text-blue-200 text-xs truncate">P&amp;L_Q3_2024.xlsx · Généré en 52 secondes</p>
              </div>
              <div className="ml-auto hidden sm:flex items-center gap-2">
                <span className="text-[10px] text-blue-200 font-medium">Confiance IA · 92%</span>
                <div className="w-3 h-3 bg-green-400 rounded-full" />
              </div>
            </div>

            {/* Body */}
            <div className="p-5 sm:p-7 bg-[#F8FAFF] flex flex-col gap-5">

              {/* KPI row */}
              <div className="bg-white rounded-xl border border-gray-100 shadow-sm px-4 sm:px-6 py-4">
                <p className="text-[10px] font-semibold text-[#5F6368] uppercase tracking-wide mb-3">Indicateurs clés</p>
                <div className="grid grid-cols-3 gap-2 mb-3">
                  {[
                    { label: 'CA', value: '2,4M€', trend: '+12%', up: true },
                    { label: 'Marge brute', value: '67%', trend: '+3pp', up: true },
                    { label: 'EBITDA', value: '18%', trend: '-2pp', up: false },
                  ].map(m => (
                    <div key={m.label} className="text-center">
                      <p className="text-xs text-[#5F6368]">{m.label}</p>
                      <p className="text-lg sm:text-xl font-bold text-[#1A1A2E]">{m.value}</p>
                      <p className={`text-xs font-medium ${m.up ? 'text-green-600' : 'text-red-500'}`}>{m.trend}</p>
                    </div>
                  ))}
                </div>
                <div className="bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
                  <p className="text-xs text-amber-700">⚠️ 2 anomalies détectées sur les charges exceptionnelles</p>
                </div>
              </div>

              {/* Scores + Plan d'action + Projection */}
              <div className="bg-white rounded-xl border border-gray-100 shadow-sm px-4 sm:px-6 py-4 flex flex-col gap-4">

                {/* Scores /10 */}
                <div>
                  <p className="text-[10px] font-semibold text-[#5F6368] uppercase tracking-wide mb-2">Scores de santé financière</p>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: 'Rentabilité', score: '4/10', badge: 'FRAGILE', scoreColor: 'text-red-600', bg: 'bg-red-50', border: 'border-red-100', badgeBg: 'bg-red-100 text-red-700' },
                      { label: 'Risque', score: '6/10', badge: 'ÉLEVÉ', scoreColor: 'text-amber-500', bg: 'bg-amber-50', border: 'border-amber-100', badgeBg: 'bg-amber-100 text-amber-700' },
                      { label: 'Structure', score: '7/10', badge: 'STABLE', scoreColor: 'text-green-600', bg: 'bg-green-50', border: 'border-green-100', badgeBg: 'bg-green-100 text-green-700' },
                    ].map(s => (
                      <div key={s.label} className={`${s.bg} border ${s.border} rounded-lg p-2.5 text-center`}>
                        <p className={`text-base font-extrabold ${s.scoreColor}`}>{s.score}</p>
                        <p className="text-[10px] text-[#5F6368] leading-tight mb-1">{s.label}</p>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${s.badgeBg}`}>{s.badge}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="border-t border-gray-100" />

                {/* Plan d'action */}
                <div>
                  <p className="text-[10px] font-semibold text-[#5F6368] uppercase tracking-wide mb-2">Plan d&apos;action · Impact estimé</p>
                  <div className="flex flex-col gap-2">
                    {[
                      { dot: 'bg-red-500', text: 'Réduire charges fixes → +4,5pp EBITDA estimé' },
                      { dot: 'bg-amber-400', text: 'Accélérer le SaaS B2B — levier de marge n°1' },
                      { dot: 'bg-green-500', text: 'Couvrir le creux juillet-août (risque liquidité)' },
                    ].map((a, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${a.dot} flex-shrink-0 mt-1.5`} />
                        <p className="text-xs sm:text-sm text-[#1A1A2E] leading-snug">{a.text}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Projection */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-amber-50 border border-amber-100 rounded-lg px-3 py-2.5 text-center">
                    <p className="text-xs font-bold text-amber-700">⚡ 3 mois</p>
                    <p className="text-[10px] text-amber-600 leading-tight">Stabilisation si action avant juillet</p>
                  </div>
                  <div className="bg-green-50 border border-green-100 rounded-lg px-3 py-2.5 text-center">
                    <p className="text-xs font-bold text-green-700">✅ 6 mois</p>
                    <p className="text-[10px] text-green-600 leading-tight">Retour à l&apos;équilibre — budget 2026 atteignable</p>
                  </div>
                </div>
              </div>

              {/* Suite du rapport — signal de profondeur */}
              <div className="bg-white rounded-xl border border-gray-100 shadow-sm px-4 sm:px-6 py-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[10px] font-semibold text-[#5F6368] uppercase tracking-wide">Rapport complet</p>
                  <span className="text-[9px] font-bold text-white bg-[#1B73E8] px-1.5 py-0.5 rounded-full">9 sections</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex gap-0.5 flex-shrink-0">
                    <span className="w-1 h-1 rounded-full bg-gray-300" />
                    <span className="w-1 h-1 rounded-full bg-gray-300" />
                    <span className="w-1 h-1 rounded-full bg-gray-300" />
                  </div>
                  <p className="text-[11px] text-[#5F6368] italic leading-snug">
                    Copilote de décision · Avant/Après · Ce qui détruit votre rentabilité · Leviers de croissance...
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Caption */}
          <p className="text-center text-xs text-[#5F6368] italic mt-4">
            Extrait réel généré par Pepperyn à partir d&apos;un simple fichier Excel.
          </p>
        </div>
      </div>
    </section>
  );
}
