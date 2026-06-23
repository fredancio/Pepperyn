const problems = [
  "Elles ne disposent pas des bonnes informations au bon moment.",
  "Elles n'ont pas le temps de tout analyser.",
  "Les dérives sont découvertes trop tard.",
];

const flow = ['Pepperyn', 'Décisions', 'Priorités', 'Suivi'];

export function WhyBadDecisionsSection() {
  return (
    <section className="py-20 lg:py-24 bg-[#F8FAFF] border-t border-[#1B73E8]/10">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="text-center mb-14">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight max-w-2xl mx-auto">
            Pourquoi les entreprises prennent-elles de mauvaises décisions ?
          </h2>
        </div>

        {/* 3 cartes du problème, reliées par une flèche descendante */}
        <div className="flex flex-col gap-3 max-w-xl mx-auto mb-16">
          {problems.map((p, i) => (
            <div key={p}>
              <div className="bg-white border border-gray-100 rounded-2xl shadow-sm px-6 py-5 text-center">
                <p className="text-base text-[#1A1A2E] font-medium">{p}</p>
              </div>
              {i < problems.length - 1 && (
                <div className="flex justify-center py-2">
                  <svg className="w-4 h-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Pepperyn -> Décisions -> Priorités -> Suivi */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          {flow.map((step, i) => (
            <div key={step} className="flex items-center gap-3">
              <div
                className={`px-5 py-3 rounded-xl text-sm font-bold ${
                  i === 0
                    ? 'bg-[#0A2540] text-white'
                    : 'bg-white border border-[#1B73E8]/20 text-[#1A1A2E]'
                }`}
              >
                {step}
              </div>
              {i < flow.length - 1 && (
                <svg className="w-4 h-4 text-[#1B73E8]/50 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              )}
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
