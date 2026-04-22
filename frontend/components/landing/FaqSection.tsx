'use client';
import { useState } from 'react';

interface FaqItem {
  question: string;
  answer: React.ReactNode;
}

const firstAnswer = (
  <div className="text-[#5F6368] leading-relaxed text-sm flex flex-col gap-4">
    <p>Les versions payantes offriront :</p>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-1">Pour la version PRO :</p>
      <p>des analyses et requêtes illimitées ainsi qu&apos;une mémoire persistante.</p>
    </div>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-1">Et pour la version PREMIUM :</p>
      <p>une automatisation sur mesure basée sur vos process et systèmes internes, l&apos;intégration de n&apos;importe quel système déjà en place (ERP, CRM, Agendas, etc.), une logique multi-agentique reposant sur différentes IA spécialisées, un développement sur-mesure selon les besoins et process de votre entreprise, du benchmarking sectoriel, la budgétisation, des alertes proactives, des projections et analyses financières fines, un onboarding complet &amp; la formation de votre équipe financière, ainsi qu&apos;un support à vie.</p>
    </div>

    <p><span className="font-semibold text-[#1A1A2E]">En résumé :</span> une infrastructure IA entièrement dédiée à votre entreprise.</p>

    <p>Vous possèderez ainsi un système métier IA propriétaire qui pourra évoluer au gré de l&apos;évolution des LLM (GPT 6… / Claude 5… / Gemini 4… etc.) et qui s&apos;autoaméliorera sur vos données propres et vos process grâce à la mémoire persistante !</p>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-2">Pepperyn sait :</p>
      <ul className="flex flex-col gap-1 pl-4">
        {['Que la marge brute baisse depuis 4 mois', 'Que tel fournisseur a augmenté ses prix', 'Que ça a ou non dégradé votre rentabilité', 'Que le BFR se dégrade', 'Que le même problème revient', '…'].map(item => (
          <li key={item} className="flex items-start gap-2">
            <span className="text-[#1B73E8] font-bold flex-shrink-0">·</span>
            {item}
          </li>
        ))}
      </ul>
      <p className="mt-2 italic">Un LLM générique ne fait pas naturellement ça.</p>
    </div>

    <div className="bg-[#EFF6FF] border border-[#1B73E8]/20 rounded-xl p-4">
      <p className="font-semibold text-[#1A1A2E] mb-2">La vraie différence : Pepperyn ne répond pas simplement à une question, il suit votre entreprise.</p>
      <p className="mb-2">Il peut dire — non pas :</p>
      <p className="text-[#5F6368] line-through pl-3 mb-1">&ldquo;vos coûts ont augmenté&rdquo;</p>
      <p className="mb-1">Mais :</p>
      <p className="font-semibold text-[#1A1A2E] pl-3">&ldquo;Réduisez immédiatement la ligne marketing de 12% avant fin de mois&rdquo;</p>
      <p className="mt-2 text-[#1B73E8] font-semibold">→ Passage de chatbot IA à copilote stratégique et opérationnel !</p>
    </div>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-2">Il va :</p>
      <ul className="flex flex-col gap-1 pl-4">
        {['Analyser', 'Proposer', 'Générer un plan', 'Créer un reporting', 'Préparer un board pack', 'Suivre l\'impact le mois suivant', '…'].map(item => (
          <li key={item} className="flex items-start gap-2">
            <span className="text-[#1B73E8] font-bold flex-shrink-0">·</span>
            {item}
          </li>
        ))}
      </ul>
    </div>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-2">Ce qui restera difficile pour les grands modèles :</p>
      <p className="mb-2">Les gros modèles de LLM restent horizontaux alors que Pepperyn est vertical.</p>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="font-semibold text-[#5F6368] mb-1 text-xs uppercase tracking-wide">Les LLM classiques font :</p>
          <p>Tout pour tout le monde</p>
        </div>
        <div className="bg-[#EFF6FF] rounded-lg p-3">
          <p className="font-semibold text-[#1B73E8] mb-1 text-xs uppercase tracking-wide">Pepperyn fait :</p>
          <ul className="flex flex-col gap-1">
            {['Une seule chose (la finance d\'entreprise)', 'Pour les problèmes qui concernent votre entreprise uniquement', 'Extrêmement bien'].map(item => (
              <li key={item} className="flex items-start gap-1.5">
                <span className="text-[#1B73E8] font-bold flex-shrink-0">·</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>

    <div className="bg-gray-50 rounded-xl p-4">
      <p className="font-semibold text-[#1A1A2E] mb-3">Concrètement :</p>
      <div className="flex flex-col gap-2">
        <div>
          <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-wide mb-1">ChatGPT dira :</p>
          <p className="pl-3 text-[#5F6368] italic">&ldquo;vos coûts ont augmenté de 18%&rdquo;</p>
        </div>
        <div>
          <p className="text-xs font-semibold text-[#1B73E8] uppercase tracking-wide mb-1">Pepperyn dira :</p>
          <p className="pl-3 font-medium text-[#1A1A2E]">&ldquo;vos coûts augmentent depuis 3 analyses malgré votre hausse de prix — votre stratégie actuelle ne fonctionne pas. Essayons ceci…&rdquo;</p>
        </div>
      </div>
      <p className="mt-2 font-bold text-[#1B73E8]">Ça, c&apos;est différent !!!</p>
    </div>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-2">Les gagnants de demain ne sont pas ceux qui &ldquo;ont un modèle puissant&rdquo;, mais ceux qui possèdent :</p>
      <ul className="flex flex-col gap-1 pl-4">
        {['Le contexte', 'La mémoire métier', 'Les workflows', "L'intégration aux systèmes du client"].map(item => (
          <li key={item} className="flex items-start gap-2">
            <span className="text-[#1B73E8] font-bold flex-shrink-0">·</span>
            {item}
          </li>
        ))}
      </ul>
    </div>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-2">Si Pepperyn se branche à :</p>
      <div className="flex flex-wrap gap-2">
        {['Sage', 'Odoo', 'Exact', 'Winbooks', 'HubSpot', 'Stripe', 'Banques'].map(s => (
          <span key={s} className="px-2.5 py-1 bg-[#EFF6FF] border border-[#1B73E8]/20 rounded-full text-xs font-medium text-[#1B73E8]">{s}</span>
        ))}
      </div>
      <p className="mt-2">Il est un vrai <span className="font-semibold text-[#1A1A2E]">system of record</span> + un <span className="font-semibold text-[#1A1A2E]">« decision layer »</span></p>
    </div>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-2">Le futur : &ldquo;l&apos;IA vous alerte avant que le problème n&apos;explose&rdquo;</p>
      <ul className="flex flex-col gap-1 pl-4">
        {['Cash runway < 90 jours', 'Marge brute en baisse 3 mois', 'Dérive coûts acquisition', 'DSO qui explose', '…'].map(item => (
          <li key={item} className="flex items-start gap-2">
            <span className="text-[#1B73E8] font-bold flex-shrink-0">·</span>
            {item}
          </li>
        ))}
      </ul>
    </div>

    <div>
      <p className="font-semibold text-[#1A1A2E] mb-2">Ce que Pepperyn sait :</p>
      <ul className="flex flex-col gap-1 pl-4">
        {["L'historique complet de vos analyses, de vos échanges et de vos actions", "L'évolution des marges", 'Les décisions prises', 'Les effets réels des décisions', 'Votre saisonnalité', 'Votre structure coûts / revenus', '…'].map(item => (
          <li key={item} className="flex items-start gap-2">
            <span className="text-[#1B73E8] font-bold flex-shrink-0">·</span>
            {item}
          </li>
        ))}
      </ul>
    </div>

    <div className="bg-[#EFF6FF] border border-[#1B73E8]/20 rounded-xl p-4">
      <p className="font-semibold text-[#1A1A2E] mb-2">Ce que ça donne :</p>
      <p className="italic mb-3">&ldquo;Tu as augmenté tes prix en janvier → aucun impact → problème de volume ou d&apos;élasticité&rdquo;</p>
      <p className="font-semibold text-[#1A1A2E] mb-1">Pepperyn va tracker :</p>
      <ul className="flex flex-col gap-1 pl-4 mb-3">
        {['Les décisions prises', 'Le statut (en cours / appliqué)', "L'impact réel"].map(item => (
          <li key={item} className="flex items-start gap-2">
            <span className="text-[#1B73E8] font-bold flex-shrink-0">·</span>
            {item}
          </li>
        ))}
      </ul>
      <p className="italic">&ldquo;Tu as décidé de réduire les coûts → aucune baisse détectée → action inefficace&rdquo;</p>
      <p className="mt-2 font-semibold text-[#1A1A2E]">ET ça, aucun LLM généraliste ne le fait nativement et proprement.</p>
    </div>

    <p>Dès lors, Pepperyn se positionne comme un <span className="font-semibold text-[#1A1A2E]">système de pilotage financier décisionnel avec mémoire persistante</span>, capacité d&apos;auto-amélioration continue — bref, le <span className="font-semibold text-[#1B73E8]">copilote financier du dirigeant</span>.</p>
  </div>
);

const faqs: FaqItem[] = [
  {
    question: 'Quelles différences entre cette version gratuite et les versions payantes à venir ?',
    answer: firstAnswer,
  },
  {
    question: 'Combien de temps dure une analyse ?',
    answer: "En version gratuite, l'analyse prend quelques secondes. Les analyses avancées (multi-fichiers, croisement ERP) sont disponibles dans les versions payantes à venir.",
  },
  {
    question: 'Quels formats de fichiers sont acceptés ?',
    answer: "Excel (.xlsx), CSV, PDF et exports ERP. Envoyez simplement votre fichier — Pepperyn s'occupe du reste.",
  },
  {
    question: 'Mes données financières sont-elles sécurisées ?',
    answer: "Oui. Les fichiers sont traités en temps réel et ne sont pas stockés de façon permanente. Vos analyses sont conservées dans votre espace sécurisé.",
  },
  {
    question: "Combien d'analyses puis-je faire gratuitement ?",
    answer: "3 analyses par mois, sans carte bancaire. Pour des analyses illimitées, un accès équipe et des exports enrichis, rendez-vous dans les versions payantes à venir.",
  },
  {
    question: 'Comment fonctionne le système de PIN pour mon équipe ?',
    answer: "Le partage d'accès équipe via code PIN sera disponible dans les versions payantes qui suivront le MVP. En version gratuite, l'accès est individuel.",
  },
];

export function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className="py-20 lg:py-28 bg-[#EFF6FF]" id="faq">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Questions fréquentes</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] mb-4">
            Tout ce que vous voulez savoir
          </h2>
          <p className="text-lg text-[#5F6368]">
            Une question non couverte ici ? Contactez-nous.
          </p>
        </div>

        {/* FAQ items */}
        <div className="flex flex-col gap-3">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full flex items-center justify-between p-6 text-left gap-4 hover:bg-gray-50/50 transition-colors duration-200"
              >
                <span className="text-base font-semibold text-[#1A1A2E] pr-4">{faq.question}</span>
                <div className={`flex-shrink-0 w-8 h-8 rounded-full ${openIndex === index ? 'bg-[#1B73E8]' : 'bg-gray-100'} flex items-center justify-center transition-all duration-200`}>
                  <svg
                    className={`w-4 h-4 transition-transform duration-200 ${openIndex === index ? 'rotate-180 text-white' : 'rotate-0 text-[#5F6368]'}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>
              {openIndex === index && (
                <div className="px-6 pb-6">
                  {typeof faq.answer === 'string' ? (
                    <p className="text-[#5F6368] leading-relaxed text-sm">{faq.answer}</p>
                  ) : (
                    faq.answer
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Contact CTA */}
        <div className="mt-12 text-center bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
          <p className="text-[#1A1A2E] font-semibold mb-2">Vous avez d&apos;autres questions ?</p>
          <p className="text-[#5F6368] text-sm mb-5">Notre équipe répond en moins de 24h</p>
          <a
            href="mailto:info@finflate.com"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#1B73E8] text-white rounded-xl font-medium text-sm hover:bg-[#0D47A1] transition-colors duration-200"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Nous contacter
          </a>
        </div>
      </div>
    </section>
  );
}
