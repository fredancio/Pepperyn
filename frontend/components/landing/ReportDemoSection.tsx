import Link from 'next/link';

const features = [
  {
    icon: (
      <svg className="w-5 h-5 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: 'Décisions prioritaires',
    desc: "L'IA identifie ce qui compte vraiment et ce qui doit être fait, maintenant.",
  },
  {
    icon: (
      <svg className="w-5 h-5 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm6 0V9a2 2 0 00-2-2h-2a2 2 0 00-2 2v10m6 0V5a2 2 0 00-2-2h-2a2 2 0 00-2 2v14" />
      </svg>
    ),
    title: 'Impact chiffré',
    desc: 'Chaque recommandation est quantifiée et reliée à votre P&L.',
  },
  {
    icon: (
      <svg className="w-5 h-5 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
    title: 'Risques maîtrisés',
    desc: "Anticipez les problèmes avant qu'ils n'impactent vos résultats.",
  },
  {
    icon: (
      <svg className="w-5 h-5 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 14l4-4 4 4 6-6m0 0h-4m4 0v4M4 19h16" />
      </svg>
    ),
    title: 'Prêt pour le Codir',
    desc: 'Des slides professionnelles prêtes à convaincre et décider.',
  },
  {
    icon: (
      <svg className="w-5 h-5 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: 'Gain de temps',
    desc: "De l'analyse à la décision en moins d'une minute.",
  },
];

export function ReportDemoSection() {
  return (
    <section className="bg-white pb-20 lg:pb-28">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 bg-white border border-[#1B73E8]/20 rounded-full mb-6 shadow-sm">
            <span className="text-[11px] font-bold text-[#1B73E8] tracking-wide">RAPIDE</span>
            <span className="w-1 h-1 rounded-full bg-gray-300" />
            <span className="text-[11px] font-bold text-[#1B73E8] tracking-wide">PRÉCIS</span>
            <span className="w-1 h-1 rounded-full bg-gray-300" />
            <span className="text-[11px] font-bold text-[#1B73E8] tracking-wide">DÉCISIONNEL</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight max-w-3xl mx-auto">
            D&apos;une feuille Excel à une décision
            <br />
            <span className="text-[#1B73E8]">stratégique en moins d&apos;une minute.</span>
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto mt-4">
            Pepperyn transforme vos données financières en décisions concrètes,
            prêtes à être présentées et exécutées.
          </p>
        </div>

        {/* 3 colonnes — Excel → PDF → PowerPoint */}
        <div className="flex flex-col md:flex-row md:items-center gap-8 md:gap-0 mb-14">

          {/* Colonne 1 — Excel */}
          <div className="flex-1 flex flex-col gap-3 min-w-0">
            <div className="flex items-center gap-2.5">
              <span className="w-9 h-9 rounded-lg bg-[#107C41] flex items-center justify-center flex-shrink-0 shadow-sm">
                <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 8.5l1.6 2.7L9.2 8.5h1.8L8.7 12l2.3 3.5H9.2l-1.6-2.7-1.6 2.7H4.2L6.5 12 4.2 8.5H6z" />
                </svg>
              </span>
              <div>
                <p className="text-[11px] font-bold text-[#1A1A2E] uppercase tracking-wide">1. Vos données</p>
                <p className="text-xs text-[#5F6368]">Fichier Excel</p>
              </div>
            </div>

            <div className="rounded-xl border-[5px] border-[#1A1A2E] shadow-xl overflow-hidden bg-white">
              {/* barre d'outils type Excel */}
              <div className="bg-[#F1F3F4] border-b border-gray-200 px-2 py-1 flex items-center gap-1.5">
                <span className="text-[7px] font-semibold text-[#5F6368] bg-white border border-gray-200 rounded px-1.5 py-0.5">A1</span>
                <span className="text-[7px] text-gray-400 italic px-1">fx</span>
                <span className="text-[7px] text-gray-400 flex-1 truncate">P&amp;L — Prévisionnel 2025</span>
              </div>
              <div className="p-2.5 flex flex-col gap-1.5">
                <div className="bg-[#107C41] rounded px-1.5 py-1">
                  <p className="text-[8px] font-bold text-white">P&amp;L — Prévisionnel 2025</p>
                </div>
                <div className="grid grid-cols-6 gap-1 text-[6px] font-semibold text-[#5F6368] border-b border-gray-100 pb-1">
                  <span className="col-span-2">Compte de résultat</span>
                  <span className="text-right">2024</span>
                  <span className="text-right">2025</span>
                  <span className="text-right">Budget</span>
                  <span className="text-right">Écart</span>
                </div>
                {[
                  ["Chiffre d'affaires", '44 629', '46 530', '47 500', '-2,0%'],
                  ['Marge brute', '39 842', '41 770', '42 800', '-2,4%'],
                  ['Charges de personnel', '-37 542', '-40 552', '-39 800', '+1,9%'],
                  ['Charges externes', '-5 821', '-6 180', '-5 600', '+10,4%'],
                  ['EBITDA', '-7 521', '-4 962', '-2 600', '-90,1%'],
                  ['Résultat net', '-6 847', '-5 231', '-2 700', '-93,7%'],
                ].map((row, i) => (
                  <div key={i} className={`grid grid-cols-6 gap-1 text-[6.5px] text-[#1A1A2E] py-0.5 ${i % 2 === 0 ? 'bg-[#F8FAFF]/60' : ''}`}>
                    <span className="col-span-2 truncate">{row[0]}</span>
                    <span className="text-right text-[#5F6368]">{row[1]}</span>
                    <span className="text-right text-[#5F6368]">{row[2]}</span>
                    <span className="text-right text-[#5F6368]">{row[3]}</span>
                    <span className="text-right text-red-500 font-medium">{row[4]}</span>
                  </div>
                ))}
                <p className="text-[8px] font-bold text-[#1A1A2E] border-t border-gray-100 pt-1.5 mt-0.5">Indicateurs clés</p>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    ['Marge brute', '89,8%', '-0,2pp'],
                    ["Taux d'occupation", '82%', '-3,0pp'],
                    ['Turn-over', '22%', '+7,0pp'],
                    ['Dette nette / EBITDA', '4,2x', '+1,2x'],
                  ].map((kpi, i) => (
                    <div key={i} className="bg-[#F8FAFF] rounded px-1.5 py-1">
                      <p className="text-[6px] text-[#5F6368] truncate">{kpi[0]}</p>
                      <div className="flex items-baseline justify-between gap-1">
                        <p className="text-[9px] font-bold text-[#1A1A2E]">{kpi[1]}</p>
                        <p className="text-[6px] font-semibold text-red-500">{kpi[2]}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {/* base "ordinateur portable" */}
            <div className="h-1.5 w-2/3 mx-auto bg-[#1A1A2E] rounded-b-lg opacity-70" />
          </div>

          {/* Flèche de connexion 1 → 2 */}
          <div className="hidden md:flex items-center justify-center px-1 flex-shrink-0">
            <div className="w-9 h-9 rounded-full bg-[#1B73E8]/10 border border-[#1B73E8]/30 flex items-center justify-center shadow-[0_0_18px_rgba(27,115,232,0.35)]">
              <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          {/* Colonne 2 — PDF Rapport Exécutif */}
          <div className="flex-1 flex flex-col gap-3 min-w-0">
            <div className="flex items-center gap-2.5">
              <span className="w-9 h-9 rounded-lg bg-[#DC2626] flex items-center justify-center flex-shrink-0 shadow-sm">
                <span className="text-white font-extrabold text-[9px] tracking-tight">PDF</span>
              </span>
              <div>
                <p className="text-[11px] font-bold text-[#1A1A2E] uppercase tracking-wide">2. Rapport exécutif</p>
                <p className="text-xs text-[#5F6368]">PDF · Décisionnel</p>
              </div>
            </div>

            <div className="rounded-xl shadow-xl overflow-hidden">
              {/* bord supérieur "papier déchiré" */}
              <div
                className="h-2 w-full"
                style={{
                  backgroundImage:
                    'linear-gradient(135deg, transparent 50%, #F8FAFF 50%), linear-gradient(45deg, #F8FAFF 50%, transparent 50%)',
                  backgroundSize: '8px 8px',
                  backgroundPosition: '0 0, 4px 0',
                  backgroundColor: 'white',
                }}
              />
              <div className="bg-white border border-gray-100 p-3 flex flex-col gap-2">
                <p className="text-[9px] font-bold text-[#1A1A2E] uppercase tracking-wide">Rapport exécutif</p>
                <p className="text-[7px] text-[#5F6368] border-b border-gray-100 pb-1.5">Société Cliente · Mai 2025</p>

                <div className="bg-red-50 border border-red-100 rounded-md px-2 py-1.5">
                  <p className="text-[7px] font-bold text-red-700 uppercase">Décision prioritaire</p>
                  <p className="text-[7px] text-red-600">Risque critique</p>
                  <p className="text-[7px] text-red-600 mt-0.5">Vous perdez actuellement</p>
                  <p className="text-[14px] font-extrabold text-red-700 leading-tight">2,4 M€</p>
                  <p className="text-[7px] text-red-600">par an. <span className="font-semibold">Agissez cette semaine.</span></p>
                </div>

                <div>
                  <p className="text-[7.5px] font-bold text-[#1A1A2E]">Résumé exécutif</p>
                  <div className="text-[6.5px] text-[#5F6368] leading-snug mt-1 space-y-1">
                    <p><span className="font-semibold text-[#1A1A2E]">Situation : </span>CA 2025 à 46,5M€, en retard de 971 K€ sur le budget.</p>
                    <p><span className="font-semibold text-[#1A1A2E]">Problème : </span>La masse salariale et les charges fixes dépassent la marge brute.</p>
                    <p><span className="font-semibold text-[#1A1A2E]">Action : </span>Couper 2M€ de coûts fixes et porter le taux d&apos;occupation au-delà de 85%.</p>
                  </div>
                </div>

                <p className="text-[8px] font-bold text-[#1A1A2E] border-t border-gray-100 pt-1.5">Plan d&apos;action prioritaire</p>
                {[
                  { n: '1', t: 'Réduire les coûts fixes', i: '+1,8M€', prio: 'CETTE SEMAINE', risk: 'FAIBLE', c: 'bg-red-50 border-red-100 text-red-700' },
                  { n: '2', t: "Améliorer le taux d'occupation", i: '+1,1M€', prio: 'CETTE SEMAINE', risk: 'MOYEN', c: 'bg-amber-50 border-amber-100 text-amber-700' },
                  { n: '3', t: 'Accélérer le SaaS / ARR', i: '+0,9M€', prio: '1 MOIS', risk: 'FAIBLE', c: 'bg-green-50 border-green-100 text-green-700' },
                ].map((a) => (
                  <div key={a.n} className={`rounded-md border px-1.5 py-1 ${a.c}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        <span className="w-3 h-3 rounded-full bg-white/70 flex items-center justify-center text-[6px] font-bold">{a.n}</span>
                        <p className="text-[6.5px] font-semibold">{a.t}</p>
                      </div>
                      <p className="text-[8px] font-bold">{a.i}</p>
                    </div>
                    <div className="flex items-center gap-2.5 mt-0.5 pl-4">
                      <div>
                        <p className="text-[5px] opacity-70 uppercase tracking-wide">Priorité</p>
                        <p className="text-[6px] font-bold">{a.prio}</p>
                      </div>
                      <div>
                        <p className="text-[5px] opacity-70 uppercase tracking-wide">Risque</p>
                        <p className="text-[6px] font-bold">{a.risk}</p>
                      </div>
                    </div>
                  </div>
                ))}

                <div className="bg-[#0A2540] rounded-md px-2 py-1.5 mt-0.5 flex items-center justify-between gap-2">
                  <div>
                    <p className="text-[6px] text-blue-200 uppercase tracking-wide">Impact financier total</p>
                    <p className="text-[10px] font-extrabold text-green-400">Gain +3,8M€</p>
                  </div>
                  <svg className="w-3 h-3 text-blue-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                  <div className="text-right">
                    <p className="text-[6px] text-blue-200">Retour à l&apos;équilibre</p>
                    <p className="text-[7px] font-bold text-white">en 6 à 8 mois</p>
                  </div>
                </div>

                <p className="text-[5.5px] text-[#5F6368] text-center mt-1 pt-1.5 border-t border-gray-100">
                  Pepperyn — Rapport généré le 04/05/2025 · Données analysées par l&apos;IA Pepperyn
                </p>
              </div>
            </div>
          </div>

          {/* Flèche de connexion 2 → 3 */}
          <div className="hidden md:flex items-center justify-center px-1 flex-shrink-0">
            <div className="w-9 h-9 rounded-full bg-[#1B73E8]/10 border border-[#1B73E8]/30 flex items-center justify-center shadow-[0_0_18px_rgba(27,115,232,0.35)]">
              <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          {/* Colonne 3 — PowerPoint Codir */}
          <div className="flex-1 flex flex-col gap-3 min-w-0">
            <div className="flex items-center gap-2.5">
              <span className="w-9 h-9 rounded-lg bg-[#D24726] flex items-center justify-center flex-shrink-0 shadow-sm">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 13v7M12 8v12M16 4v16" />
                </svg>
              </span>
              <div>
                <p className="text-[11px] font-bold text-[#1A1A2E] uppercase tracking-wide">3. Présentation Codir</p>
                <p className="text-xs text-[#5F6368]">PowerPoint · Prêt à présenter</p>
              </div>
            </div>

            <div className="relative rounded-2xl border-[6px] border-[#1A1A2E] shadow-xl bg-[#1A1A2E]">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-gray-500" />
              <div className="flex gap-2 p-2">
                <div className="flex flex-col gap-1 flex-shrink-0">
                  {['1', '2', '3', '4'].map((n) => (
                    <span key={n} className="w-4 h-4 rounded bg-[#F8FAFF] border border-gray-100 flex items-center justify-center text-[6px] font-bold text-[#5F6368]">{n}</span>
                  ))}
                </div>
                <div className="flex-1 bg-[#0A2540] rounded-md p-2 flex flex-col gap-1.5">
                  <p className="text-[7px] font-bold text-white uppercase tracking-wide">Executive Summary</p>
                  <div className="grid grid-cols-2 gap-1">
                    <div className="bg-red-500/20 border border-red-400/30 rounded px-1.5 py-1">
                      <p className="text-[6px] text-red-200">Situation actuelle</p>
                      <p className="text-[7px] font-bold text-white">Risque critique</p>
                      <p className="text-[6px] text-red-200">Perte 2,4M€/an</p>
                    </div>
                    <div className="bg-[#1B73E8]/25 border border-[#1B73E8]/40 rounded px-1.5 py-1">
                      <p className="text-[6px] text-blue-200">Notre recommandation</p>
                      <p className="text-[7px] font-bold text-white">3 actions prioritaires</p>
                      <p className="text-[6px] text-blue-200">Impact +3,8M€</p>
                    </div>
                  </div>
                  <p className="text-[6.5px] font-bold text-blue-200 uppercase tracking-wide mt-0.5">Plan d&apos;action</p>
                  <div className="grid grid-cols-3 gap-1">
                    {[
                      { t: 'Coûts fixes', v: '+1,8M€' },
                      { t: 'Occupation', v: '+1,1M€' },
                      { t: 'SaaS', v: '+0,9M€' },
                    ].map((c) => (
                      <div key={c.t} className="bg-white/10 border border-white/15 rounded px-1 py-1 text-center">
                        <p className="text-[6px] text-white truncate">{c.t}</p>
                        <p className="text-[6px] font-bold text-green-400 truncate">{c.v}</p>
                      </div>
                    ))}
                  </div>
                  <div className="flex items-end gap-0.5 h-5 mt-1">
                    {[30, 45, 40, 60, 70, 85].map((h, i) => (
                      <div key={i} className="flex-1 bg-[#1B73E8]/50 rounded-t-sm" style={{ height: `${h}%` }} />
                    ))}
                  </div>
                  <p className="text-[5.5px] text-blue-200 text-center">Retour à l&apos;équilibre · S2 2025</p>
                  <div className="flex items-center gap-1 mt-1">
                    <span className="w-2.5 h-2.5 bg-white rounded flex items-center justify-center">
                      <img src="/favicon.png?v=5" alt="" className="w-2 h-2 object-contain" />
                    </span>
                    <span className="text-[6px] text-blue-200">Pepperyn</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 5 features */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-12">
          {features.map((f) => (
            <div key={f.title} className="flex flex-col items-center text-center gap-2 px-2">
              <div className="w-10 h-10 rounded-xl bg-[#EFF6FF] border border-[#1B73E8]/20 flex items-center justify-center">
                {f.icon}
              </div>
              <p className="text-sm font-bold text-[#1A1A2E]">{f.title}</p>
              <p className="text-xs text-[#5F6368] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* CTA bar */}
        <div className="bg-[#EFF6FF] border border-[#1B73E8]/20 rounded-2xl p-5 sm:p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="w-9 h-9 bg-white rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
              <img src="/favicon.png?v=5" alt="Pepperyn" className="w-7 h-7 object-contain" />
            </span>
            <p className="text-sm font-medium text-[#1A1A2E]">
              Importez votre fichier Excel et obtenez votre rapport exécutif en moins d&apos;une minute.
            </p>
          </div>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#1B73E8] text-white rounded-xl font-semibold text-sm hover:bg-[#0D47A1] transition-all duration-200 shadow-md whitespace-nowrap"
          >
            Obtenir mon rapport
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  );
}
