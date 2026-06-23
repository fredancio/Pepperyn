const rows = [
  { chatbot: 'Répond.', pepperyn: 'Décide.' },
  { chatbot: 'Explique.', pepperyn: 'Priorise.' },
  { chatbot: 'Attend vos questions.', pepperyn: 'Prend l’initiative.' },
  { chatbot: 'Oublie.', pepperyn: 'Construit la mémoire financière de votre entreprise.' },
];

export function PositioningSection() {
  return (
    <section className="py-20 lg:py-28 bg-white border-t border-gray-100">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="text-center mb-14">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight max-w-xl mx-auto">
            Pourquoi Pepperyn n&apos;est pas un chatbot.
          </h2>
        </div>

        {/* Comparatif */}
        <div className="rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
          {/* Header */}
          <div className="grid grid-cols-2">
            <div className="px-6 sm:px-8 py-4 bg-[#F8FAFF] border-b border-r border-gray-100">
              <p className="text-xs font-bold uppercase tracking-widest text-[#5F6368]">Chatbot</p>
            </div>
            <div className="px-6 sm:px-8 py-4 bg-[#0A2540] border-b border-gray-100">
              <p className="text-xs font-bold uppercase tracking-widest text-blue-300">Pepperyn</p>
            </div>
          </div>
          {/* Rows */}
          {rows.map((r, i) => (
            <div key={r.chatbot} className="grid grid-cols-2">
              <div className={`px-6 sm:px-8 py-5 bg-white border-r border-gray-100 ${i < rows.length - 1 ? 'border-b' : ''}`}>
                <p className="text-base text-[#5F6368]">{r.chatbot}</p>
              </div>
              <div className={`px-6 sm:px-8 py-5 bg-[#F8FAFF] ${i < rows.length - 1 ? 'border-b border-gray-100' : ''}`}>
                <p className="text-base font-semibold text-[#1A1A2E]">{r.pepperyn}</p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
