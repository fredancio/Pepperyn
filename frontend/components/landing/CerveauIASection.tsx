export function CerveauIASection() {
  return (
    <section
      className="py-20 bg-[#F8FAFF]"
      style={{ borderTop: '2px solid #1B73E8' }}
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col gap-10">

        {/* Titre principal */}
        <div className="text-center">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight mb-4">
            Votre département financier mérite{' '}
            <em className="not-italic text-[#1B73E8] italic">son propre cerveau IA</em>
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto">
            Ce que font les CFO les plus avancés en 2026 —
            et pourquoi la majorité de leurs concurrents ne le sait pas encore.
          </p>
        </div>

        {/* Bloc titre intermédiaire */}
        <h3 className="text-2xl font-bold text-[#1A1A2E] text-center">
          Ce que ChatGPT ne fera jamais pour votre CFO
        </h3>

        {/* Grille de stats — fond bleu foncé */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 rounded-2xl overflow-hidden">
          <div className="bg-[#0D47A1] text-white p-8 flex flex-col items-center text-center gap-2">
            <span className="text-5xl font-extrabold text-white">~30h</span>
            <span className="text-blue-200 text-sm leading-snug">
              gagnées / semaine pour une équipe financière de 4 personnes
            </span>
          </div>
          <div className="bg-[#0D47A1] text-white p-8 flex flex-col items-center text-center gap-2">
            <span className="text-5xl font-extrabold text-white">60 sec</span>
            <span className="text-blue-200 text-sm leading-snug">
              pour une analyse multi-BU croisée ERP
            </span>
          </div>
          <div className="bg-[#0D47A1] text-white p-8 flex flex-col items-center text-center gap-2">
            <span className="text-5xl font-extrabold text-white">&lt; 3 mois</span>
            <span className="text-blue-200 text-sm leading-snug">
              pour un ROI positif sur l'investissement
            </span>
          </div>
        </div>

        {/* Bloc explicatif */}
        <div className="bg-[#EFF6FF] border-l-4 border-[#1B73E8] pl-6 pr-4 py-5 rounded-r-xl text-sm text-[#5F6368] leading-relaxed">
          Comment estimer les 30h ? Un CFO économise environ 8h/semaine (reporting, consolidation,
          préparation Codir). Un contrôleur de gestion : 10h. Deux collaborateurs financiers : 6h chacun.
          Soit 30h hebdomadaires pour une équipe de 4 — l'équivalent d'un collaborateur à mi-temps,
          sans charge sociale.
        </div>

        {/* Le problème avec les LLM génériques */}
        <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6">
          <h4 className="text-lg font-bold text-[#1A1A2E] mb-3">
            Le problème avec les LLM génériques
          </h4>
          <p className="text-sm text-[#5F6368] leading-relaxed">
            ChatGPT, Copilot, Gemini — ces outils ne connaissent pas votre Plan Comptable, vos BU,
            vos marges par produit, vos règles de gestion interne. Chaque réponse est une estimation.
            Chaque chiffre doit être vérifié. Vous avez investi dans un outil de productivité
            qui vous crée de la friction.
          </p>
        </div>

        {/* Bloc vérité */}
        <div className="bg-white border-l-4 border-[#FF6B35] pl-6 pr-4 py-5 rounded-r-xl">
          <p className="text-sm text-[#1A1A2E] leading-relaxed">
            <strong>La vérité que personne ne dit :</strong> le problème n'est pas le modèle d'IA.
            C'est que le modèle ne sait pas qui vous êtes. Un chatbot financier réellement utile,
            c'est un modèle entraîné sur <em>vos</em> données, avec <em>votre</em> logique métier,
            accessible uniquement par <em>vous</em>.
          </p>
        </div>

        {/* Section Codir */}
        <div className="flex flex-col gap-4">
          <h3 className="text-2xl font-bold text-[#1A1A2E] text-center">
            Vos Codirs de 4h ramenés à 1h.
          </h3>

          {/* Scénario — fond bleu foncé */}
          <div className="bg-[#0D47A1] text-white rounded-2xl p-8">
            <h4 className="text-lg font-bold mb-3">Le scénario que tout CFO a vécu</h4>
            <p className="text-blue-100 text-sm leading-relaxed mb-4">
              Un Codir d'un groupe multi-filiales. 4 heures de réunion. La moitié passée à chercher
              des chiffres. Un directeur de filiale incapable d'expliquer une baisse de marge de 3 points
              parce qu'il n'a pas les données sous la main. Le CEO qui relance. Le silence gêné.
            </p>
            <blockquote className="border-l-4 border-blue-300 pl-4 text-blue-200 italic text-sm">
              "On a tous vécu cette réunion. La question n'est plus de savoir si elle était utile —
              c'est de comprendre pourquoi elle a duré 4 heures pour rien."
            </blockquote>
          </div>
        </div>

        {/* Bloc mémoire persistante */}
        <div className="bg-[#1B73E8] text-white rounded-2xl p-8 flex flex-col gap-3">
          <p className="text-sm leading-relaxed">
            La mémoire persistante est le vrai Game Changer par rapport aux LLM classiques.
            Pepperyn connaît votre historique financier, vos décisions passées, et vérifie
            automatiquement ses propres analyses (zéro hallucination).
          </p>
          <p className="text-sm leading-relaxed">
            Ainsi Pepperyn devient un <strong>copilote financier</strong>.
          </p>
          <p className="text-xs text-blue-200 mt-1">
            ⚡ Fonctionnalités avancées disponibles dans les versions payantes à venir.
          </p>
        </div>
      </div>
    </section>
  );
}
