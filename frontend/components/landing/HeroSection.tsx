import Link from 'next/link';

export function HeroSection() {
  return (
    <section className="relative bg-white overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-indigo-50 pointer-events-none" />

      {/* Decorative circles */}
      <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[640px] h-[320px] bg-[#1B73E8]/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-10 right-10 w-72 h-72 bg-indigo-200/20 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 lg:pt-28 lg:pb-20 flex flex-col items-center text-center gap-6">

        {/* Eyebrow */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-[#1B73E8]" />
          <span className="text-sm font-medium text-[#1B73E8]">Diagnostic financier instantané</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl lg:text-5xl xl:text-6xl font-extrabold text-[#1A1A2E] leading-tight max-w-3xl">
          Découvrez en quelques minutes ce qui détruit votre{' '}
          <span className="text-[#1B73E8]">rentabilité</span>.
        </h1>

        {/* Subtitle */}
        <p className="text-lg lg:text-xl text-[#5F6368] leading-relaxed max-w-2xl">
          Importez simplement votre fichier Excel. Pepperyn identifie immédiatement
          les problèmes financiers, estime leur impact et propose les décisions
          qui auront le plus d&apos;effet.
        </p>

        {/* CTA */}
        <Link
          href="/register"
          className="inline-flex items-center gap-2 px-8 py-4 bg-[#1B73E8] text-white rounded-xl font-semibold text-base hover:bg-[#0D47A1] transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5 mt-2"
        >
          Obtenir mon diagnostic
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </Link>

        {/* Micro trust line */}
        <p className="text-xs text-[#5F6368]">
          Sans carte bancaire · Résultats en moins de 2 minutes · Données anonymisées avant analyse
        </p>

        {/* Formats acceptés */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-1">
          <span className="text-xs font-medium text-[#5F6368] mr-1">Compatible :</span>
          {[
            { label: 'Excel', bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', icon: '📊' },
            { label: 'CSV', bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200', icon: '📋' },
            { label: 'PDF', bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200', icon: '📄' },
            { label: 'ERP', bg: 'bg-blue-50', text: 'text-[#1B73E8]', border: 'border-blue-200', icon: '⚙️' },
          ].map(f => (
            <span key={f.label}
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg border text-xs font-semibold ${f.bg} ${f.text} ${f.border}`}>
              <span className="text-sm">{f.icon}</span>
              {f.label}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
