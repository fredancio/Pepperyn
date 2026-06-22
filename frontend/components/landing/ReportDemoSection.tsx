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
            D&apos;une feuille Excel à une décision{' '}
            <span className="text-[#1B73E8]">stratégique en moins d&apos;une minute.</span>
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto mt-4">
            Pepperyn transforme vos données financières en décisions concrètes,
            prêtes à être présentées et exécutées.
          </p>
        </div>

        {/* 3 colonnes — Excel → PDF → PowerPoint */}
        <div className="grid md:grid-cols-3 gap-6 mb-14">

          {/* Colonne 1 — Excel */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-green-50 border border-green-100 flex items-center justify-center text-base flex-shrink-0">📗</span>
              <div>
                <p className="text-[11px] font-bold text-[#1A1A2E] uppercase tracking-wide">1. Vos données</p>
                <p className="text-xs text-[#5F6368]">Fichier Excel</p>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 shadow-lg p-3 flex flex-col gap-2">
              <p className="text-[9px] font-bold text-[#1A1A2E] border-b border-gray-100 pb-1.5">P&amp;L — Prévisionnel 2025</p>
              <div className="grid grid-cols-5 gap-1 text-[7px] font-semibold text-[#5F6368] border-b border-gray-100 pb-1">
                <span className="col-span-2">Compte de résultat</span>
                <span className="text-right">2024</span>
                <span className="text-right">2025</span>
                <span className="text-right">Écart</span>
              </div>
              {[
                ["Chiffre d'affaires", '44 629', '46 530', '-2,0%'],
                ['Marge brute', '39 842', '41 770', '-2,4%'],
                ['Charges de personnel', '-5 821', '-6 180', '+10,4%'],
                ['EBITDA', '-7 521', '-4 962', '-90,1%'],
                ['Résultat net', '-6 847', '-5 231', '-93,7%'],
              ].map((row, i) => (
                <div key={i} className="grid grid-cols-5 gap-1 text-[7.5px] text-[#1A1A2E]">
                  <span className="col-span-2 truncate">{row[0]}</span>
                  <span className="text-right text-[#5F6368]">{row[1]}</span>
                  <span className="text-right text-[#5F6368]">{row[2]}</span>
                  <span className="text-right text-red-500 font-medium">{row[3]}</span>
                </div>
              ))}
              <p className="text-[9px] font-bold text-[#1A1A2E] border-t border-gray-100 pt-1.5 mt-0.5">Indicateurs clés</p>
              <div className="grid grid-cols-2 gap-1.5">
                {[
                  ['Marge brute', '89,8%'],
                  ["Taux d'occupation", '82%'],
                  ['Turn-over', '22%'],
                  ['Dette nette / EBITDA', '4,2x'],
                ].map((kpi, i) => (
                  <div key={i} className="bg-[#F8FAFF] rounded px-1.5 py-1">
                    <p className="text-[6.5px] text-[#5F6368] truncate">{kpi[0]}</p>
                    <p className="text-[9px] font-bold text-[#1A1A2E]">{kpi[1]}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Colonne 2 — PDF Rapport Exécutif */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center text-base flex-shrink-0">📄</span>
              <div>
                <p className="text-[11px] font-bold text-[#1A1A2E] uppercase tracking-wide">2. Rapport exécutif</p>
                <p className="text-xs text-[#5F6368]">PDF · Décisionnel</p>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 shadow-lg p-3 flex flex-col gap-2">
              <p className="text-[9px] font-bold text-[#1A1A2E] uppercase tracking-wide">Rapport exécutif</p>
              <p className="text-[7px] text-[#5F6368] border-b border-gray-100 pb-1.5">Société Cliente · Mai 2025</p>

              <div className="bg-red-50 border border-red-100 rounded-md px-2 py-1.5">
                <p className="text-[7px] font-bold text-red-700 uppercase">Décision prioritaire</p>
                <p className="text-[7px] text-red-600">Risque critique</p>
                <p className="text-[12px] font-extrabold text-red-700 leading-tight mt-0.5">Vous perdez 2,4 M€/an</p>
                <p className="text-[7px] text-red-600 mt-0.5">Agissez cette semaine.</p>
              </div>

              <div>
                <p className="text-[7.5px] font-bold text-[#1A1A2E]">Résumé exécutif</p>
                <p className="text-[7px] text-[#5F6368] leading-snug mt-0.5">
                  CA 2025 à 46,5M€, en retard de 971K€ sur le budget. La masse
                  salariale et les charges fixes dépassent la marge brute.
                </p>
              </div>

              <p className="text-[8px] font-bold text-[#1A1A2E] border-t border-gray-100 pt-1.5">Plan d&apos;action prioritaire</p>
              {[
                { n: '1', t: 'Réduire les coûts fixes', i: '+1,8M€', c: 'bg-red-50 border-red-100 text-red-700' },
                { n: '2', t: "Améliorer le taux d'occupation", i: '+1,1M€', c: 'bg-amber-50 border-amber-100 text-amber-700' },
                { n: '3', t: 'Accélérer le SaaS / ARR', i: '+0,9M€', c: 'bg-green-50 border-green-100 text-green-700' },
              ].map((a) => (
                <div key={a.n} className={`rounded-md border px-1.5 py-1 ${a.c}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1">
                      <span className="w-3 h-3 rounded-full bg-white/70 flex items-center justify-center text-[6px] font-bold">{a.n}</span>
                      <p className="text-[6.5px] font-semibold">{a.t}</p>
                    </div>
                    <p className="text-[8px] font-bold">{a.i}</p>
                  </div>
                </div>
              ))}

              <div className="bg-[#0A2540] rounded-md px-2 py-1.5 mt-0.5">
                <p className="text-[6.5px] text-blue-200 uppercase tracking-wide">Impact financier total</p>
                <div className="flex items-center justify-between mt-0.5">
                  <p className="text-[9px] font-extrabold text-white">Gain +3,8M€</p>
                  <p className="text-[6.5px] text-blue-200">Équilibre en 6 à 8 mois</p>
                </div>
              </div>
            </div>
          </div>

          {/* Colonne 3 — PowerPoint Codir */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-orange-50 border border-orange-100 flex items-center justify-center text-base flex-shrink-0">📊</span>
              <div>
                <p className="text-[11px] font-bold text-[#1A1A2E] uppercase tracking-wide">3. Présentation Codir</p>
                <p className="text-xs text-[#5F6368]">PowerPoint · Prêt à présenter</p>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 shadow-lg p-3 flex gap-2">
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
                  {['Coûts fixes', 'Occupation', 'SaaS'].map((t) => (
                    <div key={t} className="bg-white/10 border border-white/15 rounded px-1 py-1 text-center">
                      <p className="text-[6px] text-white truncate">{t}</p>
                    </div>
                  ))}
                </div>
                <div className="flex items-end gap-0.5 h-5 mt-1">
                  {[30, 45, 40, 60, 70, 85].map((h, i) => (
                    <div key={i} className="flex-1 bg-[#1B73E8]/50 rounded-t-sm" style={{ height: `${h}%` }} />
                  ))}
                </div>
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
