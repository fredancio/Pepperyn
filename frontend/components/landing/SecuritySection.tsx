import Link from 'next/link';

const pillars = [
  {
    icon: (
      <svg className="w-6 h-6 text-[#60A5FA]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 11-12 0 6 6 0 0112 0zM6 21v-2a4 4 0 014-4h0" />
      </svg>
    ),
    title: 'Anonymisation avant analyse',
    desc: 'Vos données sensibles (clients, fournisseurs, IBAN) sont remplacées par des alias avant tout traitement par l’IA.',
  },
  {
    icon: (
      <svg className="w-6 h-6 text-[#60A5FA]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3M4 7h16" />
      </svg>
    ),
    title: 'Fichier jamais conservé',
    desc: 'Votre fichier source est traité en mémoire et supprimé immédiatement après l’analyse — jamais stocké sur nos serveurs.',
  },
  {
    icon: (
      <svg className="w-6 h-6 text-[#60A5FA]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
    title: 'Suppression totale sur demande',
    desc: 'Compte, rapports et historique supprimés définitivement, conformément au RGPD, sur simple demande.',
  },
  {
    icon: (
      <svg className="w-6 h-6 text-[#60A5FA]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: 'Jamais utilisé pour entraîner une IA',
    desc: 'Vos données ne servent jamais à entraîner un modèle, ni le nôtre, ni celui d’un tiers.',
  },
];

export function SecuritySection() {
  return (
    <section id="securite" className="py-20 lg:py-28 bg-[#0A2540]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/20 border border-[#1B73E8]/30 rounded-full mb-4">
            <span className="text-sm font-medium text-blue-200">Sécurité &amp; conformité</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-white leading-tight">
            Vos données vous appartiennent. Point final.
          </h2>
        </div>

        {/* Pillars */}
        <div className="grid sm:grid-cols-2 gap-5">
          {pillars.map((p) => (
            <div key={p.title} className="bg-white/5 border border-white/10 rounded-2xl p-6 flex gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#1B73E8]/20 border border-[#1B73E8]/30 flex items-center justify-center flex-shrink-0">
                {p.icon}
              </div>
              <div>
                <h3 className="text-sm font-bold text-white mb-1.5">{p.title}</h3>
                <p className="text-sm text-blue-200/80 leading-relaxed">{p.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Link */}
        <div className="text-center mt-10">
          <Link href="/legal/donnees-securisees" className="text-sm text-blue-300 hover:text-white underline transition-colors">
            En savoir plus sur notre politique de sécurité
          </Link>
        </div>
      </div>
    </section>
  );
}
