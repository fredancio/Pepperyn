import Link from 'next/link';

export function HeroSection() {
  return (
    <section className="relative bg-white overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-indigo-50 pointer-events-none" />

      {/* Decorative circles */}
      <div className="absolute top-20 right-20 w-72 h-72 bg-[#1B73E8]/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-20 left-10 w-96 h-96 bg-indigo-200/20 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 lg:pt-32 lg:pb-36">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left column */}
          <div className="flex flex-col items-start gap-4">
            {/* Beta banner — petite pill transparente */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full">
              <span className="w-2 h-2 bg-[#1B73E8] rounded-full" />
              <span className="text-sm font-medium text-[#1B73E8]">Accès bêta ouvert — places limitées</span>
            </div>

            {/* Headline — all blue */}
            <h1 className="text-4xl lg:text-5xl xl:text-6xl font-extrabold text-[#1B73E8] leading-tight">
              Scanner financier pour entreprises
            </h1>

            {/* Subtitle */}
            <p className="text-lg text-[#1A1A2E] font-medium leading-snug">
              Transformez vos données financières en décisions business
            </p>

            {/* Description */}
            <p className="text-base text-[#5F6368] leading-relaxed max-w-lg">
              En quelques secondes, identifiez ce qui fonctionne,
              ce qui vous coûte et ce que vous devez faire ensuite —
              revenus, coûts, marges, anomalies et recommandations activables.
            </p>

            {/* Bullets — bulles rondes bleues */}
            <ul className="flex flex-col gap-2">
              {[
                'ce qui vous fait gagner de l\'argent',
                'ce qui vous en fait perdre',
                'les actions à prioriser',
              ].map((item) => (
                <li key={item} className="flex items-center gap-2.5 text-sm text-[#1A1A2E]">
                  <span className="w-5 h-5 rounded-full bg-[#1B73E8] flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                  {item}
                </li>
              ))}
              <li className="flex items-center gap-2.5 text-sm text-[#1A1A2E]">
                <span className="w-5 h-5 rounded-full bg-[#1B73E8] flex items-center justify-center flex-shrink-0">
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </span>
                <strong>et surtout une mémoire persistante !</strong>
              </li>
            </ul>

            {/* Signature produit — surlignage bleu, sans trait */}
            <div className="py-0.5">
              <span className="text-base text-[#1B73E8] italic font-semibold tracking-tight border-b-2 border-[#1B73E8]/40 pb-0.5">
                &ldquo;Un raccourci vers la décision&rdquo;
              </span>
            </div>

            {/* Formats acceptés — badges pills colorés */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-[#5F6368] mr-1">Compatible :</span>
              {[
                { label: 'Excel',  bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', icon: '📊' },
                { label: 'CSV',    bg: 'bg-gray-50',    text: 'text-gray-600',    border: 'border-gray-200',    icon: '📋' },
                { label: 'PDF',    bg: 'bg-red-50',     text: 'text-red-600',     border: 'border-red-200',     icon: '📄' },
                { label: 'ERP',    bg: 'bg-blue-50',    text: 'text-[#1B73E8]',  border: 'border-blue-200',    icon: '⚙️' },
              ].map(f => (
                <span key={f.label}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg border text-xs font-semibold ${f.bg} ${f.text} ${f.border}`}>
                  <span className="text-sm">{f.icon}</span>
                  {f.label}
                </span>
              ))}
            </div>

            {/* Single CTA */}
            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#1B73E8] text-white rounded-xl font-semibold text-base hover:bg-[#0D47A1] transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5"
            >
              Analyser mes données
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>

            {/* Social proof strip — Données sécurisées cliquable */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-[#5F6368]">
              <Link href="/legal/donnees-securisees" className="flex items-center gap-1.5 hover:text-[#1B73E8] transition-colors">
                <span className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </span>
                Données sécurisées
              </Link>
              <span className="w-1 h-1 rounded-full bg-gray-300 hidden sm:block" />
              <span className="flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-3 h-3 text-amber-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                </span>
                Résultats en 60s
              </span>
              <span className="w-1 h-1 rounded-full bg-gray-300 hidden sm:block" />
              <span className="flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 text-[#1B73E8] font-bold text-xs">3</span>
                analyses gratuites · sans CB
              </span>
            </div>
          </div>

          {/* Right column - Chat preview mockup — conserver exactement */}
          <div className="hidden lg:block">
            <div className="relative">
              {/* Main card */}
              <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-[#1B73E8] to-[#0D47A1] px-4 py-3 flex items-center gap-3">
                  <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                    <img src="/favicon.png?v=5" alt="Pepperyn" className="w-8 h-8 object-contain" />
                  </div>
                  <div>
                    <p className="text-white font-semibold text-sm">Pepperyn IA</p>
                    <p className="text-blue-200 text-xs">Financial Control Center</p>
                  </div>
                  <div className="ml-auto flex gap-1.5">
                    <div className="w-3 h-3 bg-green-400 rounded-full" />
                  </div>
                </div>

                {/* Messages */}
                <div className="p-4 bg-[#EFF6FF] flex flex-col gap-3 min-h-[280px]">
                  {/* Bot message */}
                  <div className="flex items-start gap-2 max-w-[85%]">
                    <div className="w-7 h-7 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">P</span>
                    </div>
                    <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
                      <p className="text-sm text-[#1A1A2E]">
                        Bonjour ! J&apos;ai analysé votre fichier <strong>P&L_Q3_2024.xlsx</strong>. Voici les points clés :
                      </p>
                    </div>
                  </div>

                  {/* Analysis card */}
                  <div className="flex items-start gap-2 max-w-[90%]">
                    <div className="w-7 h-7 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">P</span>
                    </div>
                    <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm w-full">
                      <div className="grid grid-cols-3 gap-2 mb-3">
                        {[
                          { label: 'CA', value: '2.4M€', trend: '+12%', up: true },
                          { label: 'Marge brute', value: '67%', trend: '+3pp', up: true },
                          { label: 'EBITDA', value: '18%', trend: '-2pp', up: false },
                        ].map(m => (
                          <div key={m.label} className="text-center">
                            <p className="text-xs text-[#5F6368]">{m.label}</p>
                            <p className="text-sm font-bold text-[#1A1A2E]">{m.value}</p>
                            <p className={`text-xs font-medium ${m.up ? 'text-green-600' : 'text-red-500'}`}>{m.trend}</p>
                          </div>
                        ))}
                      </div>
                      <div className="bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
                        <p className="text-xs text-amber-700">⚠️ 2 anomalies détectées sur les charges exceptionnelles</p>
                      </div>
                    </div>
                  </div>

                  {/* User message */}
                  <div className="flex justify-end">
                    <div className="bg-[#1B73E8] rounded-2xl rounded-tr-none px-4 py-3 max-w-[75%]">
                      <p className="text-sm text-white">Quelles sont les recommandations prioritaires ?</p>
                    </div>
                  </div>

                  {/* Typing */}
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">P</span>
                    </div>
                    <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
                      <div className="flex gap-1 items-center">
                        <span className="typing-dot" />
                        <span className="typing-dot" />
                        <span className="typing-dot" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Input bar */}
                <div className="px-4 py-3 bg-white border-t border-gray-100 flex items-center gap-2">
                  <div className="flex-1 bg-gray-50 rounded-xl px-3 py-2.5 text-sm text-[#5F6368]">
                    Posez votre question...
                  </div>
                  <button className="w-9 h-9 bg-[#1B73E8] rounded-xl flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Floating badges */}
              <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-lg border border-gray-100 px-3 py-2 flex items-center gap-2">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#1A1A2E]">Analyse complète</p>
                  <p className="text-xs text-green-600">En quelques secondes</p>
                </div>
              </div>

              <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-lg border border-gray-100 px-3 py-2 flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#1A1A2E]">Données chiffrées</p>
                  <p className="text-xs text-[#5F6368]">Export Excel inclus</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
