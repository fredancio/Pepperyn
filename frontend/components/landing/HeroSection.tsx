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
            {/* Headline — all blue */}
            <h1 className="text-4xl lg:text-5xl xl:text-6xl font-extrabold text-[#1B73E8] leading-tight">
              Le copilote financier IA de votre entreprise
            </h1>

            {/* Subtitle */}
            <p className="text-xl lg:text-2xl text-[#1A1A2E] font-bold leading-snug">
              Transformez vos données financières en décisions business
            </p>
            <p className="text-base text-[#5F6368] font-medium leading-snug">
              Analyse vos chiffres &amp; vous conseille. Apprend de vos décisions. S&apos;améliore avec votre entreprise.
            </p>

            {/* Description */}
            <p className="text-base text-[#5F6368] leading-relaxed max-w-lg">
              En quelques secondes, identifiez ce qui fonctionne,
              ce qui vous coûte et les décisions à prioriser —
              revenus, coûts, marges, anomalies et recommandations activables.
              Le premier assistant financier qui se souvient de votre entreprise
              et apprend de vos décisions.
            </p>

            {/* Bullets — bulles rondes bleues */}
            <ul className="flex flex-col gap-2">
              {[
                'les leviers de rentabilité',
                'les dérives qui impactent vos marges',
                'les actions prioritaires à forte valeur',
                'Recommandations qui s’améliorent dans le temps',
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
                <strong>Une mémoire persistante, une IA qui apprend de vos décisions et s&apos;améliore</strong>
              </li>
            </ul>

            {/* Mémoire & apprentissage — précision discrète */}
            <p className="text-xs text-[#5F6368] italic leading-relaxed max-w-lg">
              Pepperyn conserve l&apos;historique de vos analyses, suit les actions réellement
              mises en œuvre et améliore progressivement ses recommandations.
            </p>

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
                Données 100% sécurisées et anonymisées avant analyse
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
                <span className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 text-[#1B73E8] font-bold text-xs">1</span>
                analyse gratuite · sans CB
              </span>
              <span className="w-1 h-1 rounded-full bg-gray-300 hidden sm:block" />
              <span className="flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-3 h-3 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5C21.27 7.61 17 4.5 12 4.5z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15a3 3 0 100-6 3 3 0 000 6z" />
                  </svg>
                </span>
                Apprend de votre entreprise
              </span>
              <span className="w-1 h-1 rounded-full bg-gray-300 hidden sm:block" />
              <span className="flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                  <svg className="w-3 h-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </span>
                Recommandations qui s&apos;améliorent dans le temps
              </span>
            </div>
          </div>

          {/* Right column - Chat preview mockup */}
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
                  <div className="ml-auto flex items-center gap-2">
                    <span className="text-[10px] text-blue-200 font-medium">Confiance IA · 92%</span>
                    <div className="w-3 h-3 bg-green-400 rounded-full" />
                  </div>
                </div>

                {/* Messages */}
                <div className="p-4 bg-[#EFF6FF] flex flex-col gap-3">

                  {/* Bot intro */}
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

                  {/* KPI analysis card */}
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

                  {/* Pepperyn — Scores /10 + Plan d'action + Projection */}
                  <div className="flex items-start gap-2 max-w-[95%]">
                    <div className="w-7 h-7 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">P</span>
                    </div>
                    <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm w-full flex flex-col gap-3">

                      {/* Scores /10 */}
                      <div>
                        <p className="text-[10px] font-semibold text-[#5F6368] uppercase tracking-wide mb-2">Scores de santé financière</p>
                        <div className="grid grid-cols-3 gap-1.5">
                          {[
                            { label: 'Rentabilité', score: '4/10', badge: 'FRAGILE', scoreColor: 'text-red-600', bg: 'bg-red-50', border: 'border-red-100', badgeBg: 'bg-red-100 text-red-700' },
                            { label: 'Risque', score: '6/10', badge: 'ÉLEVÉ', scoreColor: 'text-amber-500', bg: 'bg-amber-50', border: 'border-amber-100', badgeBg: 'bg-amber-100 text-amber-700' },
                            { label: 'Structure', score: '7/10', badge: 'STABLE', scoreColor: 'text-green-600', bg: 'bg-green-50', border: 'border-green-100', badgeBg: 'bg-green-100 text-green-700' },
                          ].map(s => (
                            <div key={s.label} className={`${s.bg} border ${s.border} rounded-lg p-2 text-center`}>
                              <p className={`text-sm font-extrabold ${s.scoreColor}`}>{s.score}</p>
                              <p className="text-[9px] text-[#5F6368] leading-tight mb-1">{s.label}</p>
                              <span className={`text-[8px] font-bold px-1 py-0.5 rounded-full ${s.badgeBg}`}>{s.badge}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Divider */}
                      <div className="border-t border-gray-100" />

                      {/* Plan d'action chiffré */}
                      <div>
                        <p className="text-[10px] font-semibold text-[#5F6368] uppercase tracking-wide mb-2">Plan d&apos;action · Impact estimé</p>
                        <div className="flex flex-col gap-1.5">
                          {[
                            { dot: 'bg-red-500', text: 'Réduire charges fixes → +4.5pp EBITDA estimé' },
                            { dot: 'bg-amber-400', text: 'Accélérer SaaS B2B — levier de marge N°1' },
                            { dot: 'bg-green-500', text: 'Couvrir creux juillet-août (risque liquidité)' },
                          ].map((a, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <div className={`w-1.5 h-1.5 rounded-full ${a.dot} flex-shrink-0 mt-1.5`} />
                              <p className="text-xs text-[#1A1A2E] leading-snug">{a.text}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Projection temporelle */}
                      <div className="grid grid-cols-2 gap-1.5">
                        <div className="bg-amber-50 border border-amber-100 rounded-lg px-2.5 py-2 text-center">
                          <p className="text-[10px] font-bold text-amber-700">⚡ 3 mois</p>
                          <p className="text-[9px] text-amber-600 leading-tight">Stabilisation si action<br/>avant juillet</p>
                        </div>
                        <div className="bg-green-50 border border-green-100 rounded-lg px-2.5 py-2 text-center">
                          <p className="text-[10px] font-bold text-green-700">✅ 6 mois</p>
                          <p className="text-[9px] text-green-600 leading-tight">Retour à l&apos;équilibre —<br/>budget 2026 atteignable</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* User follow-up — hints at Simulateur de décision */}
                  <div className="flex justify-end">
                    <div className="bg-[#1B73E8] rounded-2xl rounded-tr-none px-4 py-3 max-w-[80%]">
                      <p className="text-sm text-white">Et si on réduit 15 ETP support ?</p>
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

              {/* Floating badge — top right */}
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

              {/* Floating badge — bottom left */}
              <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-lg border border-gray-100 px-3 py-2 flex items-center gap-2">
                <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#1A1A2E]">Simulateur de décision</p>
                  <p className="text-xs text-[#5F6368]">Impact chiffré par action</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
