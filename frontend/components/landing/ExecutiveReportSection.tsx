import Link from 'next/link';

export function ExecutiveReportSection() {
  return (
    <section className="py-20 lg:py-28 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Livrable</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] mb-4">
            Ce que reçoit votre direction
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto">
            Un document prêt à être partagé en comité de direction — pas un export brut de données.
          </p>
        </div>

        {/* PDF previews */}
        <div className="grid md:grid-cols-3 gap-6">

          {/* Page 1 — synthèse */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-lg overflow-hidden flex flex-col">
            <div className="aspect-[3/4] bg-[#F8FAFF] p-4 flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-[#1B73E8] rounded-md flex items-center justify-center">
                  <img src="/favicon.png?v=5" alt="" className="w-5 h-5 object-contain" />
                </div>
                <p className="text-[9px] font-bold text-[#1A1A2E] uppercase tracking-wide">Rapport exécutif</p>
              </div>
              <div>
                <p className="text-[8px] text-[#5F6368]">Société Cliente · Q3 2024</p>
                <div className="h-px bg-gray-200 mt-2 mb-3" />
              </div>
              <div className="bg-red-50 border border-red-100 rounded-md px-2 py-1.5">
                <p className="text-[8px] font-bold text-red-700">Diagnostic : rentabilité fragile</p>
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                {[
                  { l: 'CA', v: '2,4M€' },
                  { l: 'EBITDA', v: '18%' },
                  { l: 'Marge brute', v: '67%' },
                  { l: 'Score global', v: '5,6/10' },
                ].map((s) => (
                  <div key={s.l} className="bg-white rounded-md border border-gray-100 px-2 py-1.5 text-center">
                    <p className="text-[7px] text-[#5F6368]">{s.l}</p>
                    <p className="text-[10px] font-bold text-[#1A1A2E]">{s.v}</p>
                  </div>
                ))}
              </div>
              <div className="flex-1 flex flex-col gap-1 mt-1">
                {[60, 85, 40, 70].map((w, i) => (
                  <div key={i} className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-[#1B73E8]/30 rounded-full" style={{ width: `${w}%` }} />
                  </div>
                ))}
              </div>
            </div>
            <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
              <p className="text-xs font-semibold text-[#1A1A2E]">Page de synthèse</p>
              <span className="text-[10px] text-[#5F6368]">1 / 9</span>
            </div>
          </div>

          {/* Page 2 — plan d'action chiffré */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-lg overflow-hidden flex flex-col">
            <div className="aspect-[3/4] bg-[#F8FAFF] p-4 flex flex-col gap-3">
              <p className="text-[9px] font-bold text-[#1A1A2E] uppercase tracking-wide">Plan d&apos;action prioritaire</p>
              <div className="h-px bg-gray-200" />
              <div className="flex flex-col gap-2">
                {[
                  { n: '1', t: 'Réduire charges fixes', i: '+4,5pp EBITDA', c: 'bg-red-50 border-red-100 text-red-700' },
                  { n: '2', t: 'Accélérer le SaaS B2B', i: '+180k€ /an', c: 'bg-amber-50 border-amber-100 text-amber-700' },
                  { n: '3', t: 'Couvrir le creux estival', i: 'Risque cash évité', c: 'bg-green-50 border-green-100 text-green-700' },
                ].map((a) => (
                  <div key={a.n} className={`rounded-md border px-2 py-2 ${a.c}`}>
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className="w-3.5 h-3.5 rounded-full bg-white/70 flex items-center justify-center text-[7px] font-bold">{a.n}</span>
                      <p className="text-[8px] font-semibold">{a.t}</p>
                    </div>
                    <p className="text-[10px] font-bold">{a.i}</p>
                  </div>
                ))}
              </div>
              <div className="flex-1 flex items-end">
                <p className="text-[7px] text-[#5F6368] italic">Impact estimé sur 12 mois, par action.</p>
              </div>
            </div>
            <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
              <p className="text-xs font-semibold text-[#1A1A2E]">Plan d&apos;action chiffré</p>
              <span className="text-[10px] text-[#5F6368]">3 / 9</span>
            </div>
          </div>

          {/* Page 3 — projection */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-lg overflow-hidden flex flex-col">
            <div className="aspect-[3/4] bg-[#F8FAFF] p-4 flex flex-col gap-3">
              <p className="text-[9px] font-bold text-[#1A1A2E] uppercase tracking-wide">Projection — trajectoire</p>
              <div className="h-px bg-gray-200" />
              <div className="flex-1 flex items-end gap-1.5 pb-1">
                {[30, 38, 35, 50, 62, 58, 74, 88].map((h, i) => (
                  <div key={i} className="flex-1 bg-[#1B73E8]/15 rounded-t-sm relative" style={{ height: `${h}%` }}>
                    {i === 7 && <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-green-500" />}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                <div className="bg-amber-50 border border-amber-100 rounded-md px-2 py-1.5 text-center">
                  <p className="text-[8px] font-bold text-amber-700">3 mois</p>
                  <p className="text-[7px] text-amber-600">Stabilisation</p>
                </div>
                <div className="bg-green-50 border border-green-100 rounded-md px-2 py-1.5 text-center">
                  <p className="text-[8px] font-bold text-green-700">6 mois</p>
                  <p className="text-[7px] text-green-600">Retour à l&apos;équilibre</p>
                </div>
              </div>
            </div>
            <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
              <p className="text-xs font-semibold text-[#1A1A2E]">Projection 3-6-12 mois</p>
              <span className="text-[10px] text-[#5F6368]">7 / 9</span>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-12">
          <p className="text-sm text-[#5F6368] mb-4">Recevez ce rapport pour votre propre entreprise.</p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-[#1B73E8] text-white rounded-xl font-semibold text-sm hover:bg-[#0D47A1] transition-all duration-200 shadow-md"
          >
            Obtenir mon diagnostic
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  );
}
