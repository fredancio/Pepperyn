import Link from 'next/link';
import { Footer } from '@/components/landing/Footer';

export default function GuideDonneesPage() {
  return (
    <div className="bg-white min-h-screen flex flex-col">
      {/* Header */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <img src="/favicon.png?v=5" alt="Pepperyn" className="w-10 h-10 object-contain" />
            <div>
              <span className="text-base font-bold text-[#1A1A2E] block leading-none">Pepperyn IA</span>
              <span className="text-xs text-[#5F6368] block">Financial Control Center</span>
            </div>
          </Link>
          <Link href="/register" className="text-sm font-medium text-[#1B73E8] hover:underline">
            Essai gratuit →
          </Link>
        </div>
      </nav>

      <main className="flex-1 max-w-3xl mx-auto px-4 sm:px-8 py-14">

        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Bonnes pratiques</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[#1A1A2E] mb-3">
            Préparer vos données pour une analyse optimale
          </h1>
          <p className="text-[#5F6368] text-lg leading-relaxed">
            La qualité de l&apos;analyse Pepperyn dépend directement de la clarté et de la structure du fichier uploadé.
            Ce guide vous explique comment préparer vos données pour obtenir des résultats fiables et exploitables.
          </p>
        </div>

        {/* Astuce Copilot — en avant */}
        <div className="bg-[#1B73E8]/5 border border-[#1B73E8]/20 rounded-2xl p-6 mb-10">
          <div className="flex items-start gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <p className="font-bold text-[#1A1A2E] mb-1">Astuce : utilisez l&apos;IA pour nettoyer vos fichiers</p>
              <p className="text-[#5F6368] text-sm leading-relaxed">
                Si votre fichier Excel est complexe, désorganisé ou difficile à lire,
                une première passe via <strong>Microsoft Copilot</strong> (intégré à Excel 365) ou
                <strong> ChatGPT</strong> peut le restructurer en quelques secondes.
                Demandez-lui : <em>&ldquo;Restructure ce tableau en un P&L mensuel clair avec des en-têtes explicites&rdquo;</em>.
                Vous obtiendrez un fichier propre, prêt pour Pepperyn.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-8 text-[#1A1A2E]">

          {/* Section 1 */}
          <section>
            <h2 className="text-xl font-bold mb-3 flex items-center gap-2">
              <span className="w-7 h-7 bg-[#1B73E8] text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">1</span>
              Ce qui fait un bon fichier
            </h2>
            <div className="grid sm:grid-cols-2 gap-3">
              {[
                ['✅', 'En-têtes de colonnes claires', 'CA, Charges, Marge, Janvier, Février…'],
                ['✅', '1 à 3 onglets maximum', 'Un onglet P&L, un onglet Budget si nécessaire'],
                ['✅', 'Données numériques présentes', 'Les cellules contiennent de vrais chiffres, pas des formules cassées'],
                ['✅', 'Structure cohérente', 'Les lignes ont une signification homogène de haut en bas'],
                ['✅', 'Pas de lignes totalement vides', 'Évitez les grandes zones blanches entre les sections'],
                ['✅', 'Noms de lignes lisibles', '"Charges de personnel" plutôt que "CPT_4200_A"'],
              ].map(([icon, title, desc]) => (
                <div key={title} className="flex items-start gap-3 p-3 bg-green-50 border border-green-100 rounded-xl">
                  <span className="text-lg flex-shrink-0">{icon}</span>
                  <div>
                    <p className="text-sm font-semibold text-[#1A1A2E]">{title}</p>
                    <p className="text-xs text-[#5F6368] mt-0.5">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Section 2 */}
          <section>
            <h2 className="text-xl font-bold mb-3 flex items-center gap-2">
              <span className="w-7 h-7 bg-red-500 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">2</span>
              Ce qui pose problème
            </h2>
            <div className="grid sm:grid-cols-2 gap-3">
              {[
                ['❌', 'Plus de 15 onglets', 'Seuls les 5 premiers seront analysés — supprimez les onglets inutiles'],
                ['❌', 'Cellules fusionnées en masse', 'Elles compliquent la lecture automatique des données'],
                ['❌', 'Colonnes sans en-tête', 'Pepperyn ne peut pas deviner ce que représente une colonne vide'],
                ['❌', 'Codes internes cryptiques', '"CPT_4200" n\'est pas interprétable sans référentiel'],
                ['❌', 'Formules non calculées', 'Si les cellules affichent "=SUM(A1:A10)" au lieu du résultat'],
                ['❌', 'Plus de 60% de cellules vides', 'Un fichier creux ne donne pas assez de matière à analyser'],
              ].map(([icon, title, desc]) => (
                <div key={title} className="flex items-start gap-3 p-3 bg-red-50 border border-red-100 rounded-xl">
                  <span className="text-lg flex-shrink-0">{icon}</span>
                  <div>
                    <p className="text-sm font-semibold text-[#1A1A2E]">{title}</p>
                    <p className="text-xs text-[#5F6368] mt-0.5">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Section 3 */}
          <section>
            <h2 className="text-xl font-bold mb-3 flex items-center gap-2">
              <span className="w-7 h-7 bg-amber-500 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">3</span>
              Comment nettoyer un fichier complexe
            </h2>
            <ol className="space-y-3 text-sm text-[#5F6368] leading-relaxed">
              <li className="flex gap-3">
                <span className="font-bold text-[#1A1A2E] flex-shrink-0">Étape 1.</span>
                <span>Ouvrez le fichier dans Excel et identifiez l&apos;onglet le plus pertinent (P&L, compte de résultat, budget).</span>
              </li>
              <li className="flex gap-3">
                <span className="font-bold text-[#1A1A2E] flex-shrink-0">Étape 2.</span>
                <span>Supprimez les onglets vides, les tableaux de bord graphiques et les données non financières.</span>
              </li>
              <li className="flex gap-3">
                <span className="font-bold text-[#1A1A2E] flex-shrink-0">Étape 3.</span>
                <span>Ajoutez des en-têtes claires à chaque colonne. Renommez les lignes codifiées en termes compréhensibles.</span>
              </li>
              <li className="flex gap-3">
                <span className="font-bold text-[#1A1A2E] flex-shrink-0">Étape 4.</span>
                <span>Copiez-collez les données en <strong>valeurs uniquement</strong> (Ctrl+C → Collage spécial → Valeurs) pour éliminer les formules cassées.</span>
              </li>
              <li className="flex gap-3">
                <span className="font-bold text-[#1A1A2E] flex-shrink-0">Étape 5.</span>
                <span>Sauvegardez en <strong>.xlsx</strong> et uploadez dans Pepperyn.</span>
              </li>
            </ol>
          </section>

          {/* Section 4 */}
          <section>
            <h2 className="text-xl font-bold mb-3 flex items-center gap-2">
              <span className="w-7 h-7 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">4</span>
              Formats idéaux par type d&apos;analyse
            </h2>
            <div className="space-y-3">
              {[
                {
                  type: 'Compte de résultat (P&L)',
                  format: 'Lignes = postes comptables, Colonnes = mois ou périodes. En-tête en ligne 1.',
                  example: 'CA | Jan | Fév | Mar | ... | Total',
                },
                {
                  type: 'Budget vs Réel',
                  format: '3 colonnes : Poste | Budget | Réel (ou Prévisionnel | Réalisé). Écart calculable.',
                  example: 'Poste | Budget 2024 | Réel 2024 | Écart',
                },
                {
                  type: 'Trésorerie / Cash Flow',
                  format: 'Dates en colonnes, flux entrants/sortants en lignes. Solde cumulé idéalement présent.',
                  example: 'Catégorie | Semaine 1 | Semaine 2 | ...',
                },
                {
                  type: 'Export ERP / Comptable',
                  format: 'Format tabulaire avec colonnes : Date, Compte, Libellé, Débit, Crédit, Solde.',
                  example: 'Date | Compte | Libellé | Débit | Crédit',
                },
              ].map((item) => (
                <div key={item.type} className="p-4 border border-gray-100 rounded-xl">
                  <p className="font-semibold text-sm text-[#1A1A2E] mb-1">{item.type}</p>
                  <p className="text-xs text-[#5F6368] mb-2">{item.format}</p>
                  <code className="text-xs bg-gray-50 px-2 py-1 rounded text-[#1B73E8] font-mono">{item.example}</code>
                </div>
              ))}
            </div>
          </section>

        </div>

        {/* CTA */}
        <div className="mt-12 bg-[#0A2540] rounded-2xl p-7 text-white text-center">
          <h3 className="text-lg font-bold mb-2">Votre fichier est prêt ?</h3>
          <p className="text-slate-300 text-sm mb-5">Lancez votre analyse financière IA en 60 secondes.</p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#1B73E8] text-white rounded-xl font-bold text-sm hover:bg-[#0D47A1] transition-colors"
          >
            Analyser mes données gratuitement →
          </Link>
        </div>

      </main>

      <Footer />
    </div>
  );
}
