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

        {/* Titre */}
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Bonnes pratiques</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[#1A1A2E] mb-3">
            Préparer vos données pour une analyse optimale
          </h1>
          <p className="text-[#5F6368] text-lg leading-relaxed">
            La qualité de l&apos;analyse Pepperyn dépend directement de la clarté de votre fichier.
            Voici comment obtenir un résultat fiable, même si vous n&apos;êtes pas à l&apos;aise avec Excel.
          </p>
        </div>

        {/* ══════════════════════════════════════════════════════════
            SECTION COPILOT — EN VEDETTE
        ══════════════════════════════════════════════════════════ */}
        <section className="mb-12">
          <div className="rounded-2xl bg-[#0A2540] overflow-hidden">

            {/* Header Copilot */}
            <div className="px-6 py-5 border-b border-white/10">
              <div className="flex items-center gap-3 mb-1">
                <div className="w-10 h-10 bg-[#1B73E8] rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xl">✨</span>
                </div>
                <div>
                  <p className="font-bold text-white text-lg">La solution la plus rapide : Microsoft Copilot</p>
                  <p className="text-slate-400 text-sm">Intégré directement dans Excel — nettoie votre fichier en 30 secondes</p>
                </div>
              </div>
            </div>

            <div className="px-6 py-5 space-y-5">

              {/* C'est quoi Copilot */}
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-white text-sm font-semibold mb-1">🤔 C&apos;est quoi Microsoft Copilot ?</p>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Copilot est l&apos;assistant IA de Microsoft, intégré directement dans Excel 365.
                  Il comprend le contenu de votre feuille de calcul et peut la restructurer, la nettoyer
                  et la reformater sur simple demande en langage courant — comme si vous demandiez à un collègue.
                  <strong className="text-white"> La grande majorité des entreprises qui utilisent Windows ont déjà accès à Excel 365.</strong>
                </p>
              </div>

              {/* Comment y accéder */}
              <div>
                <p className="text-white text-sm font-bold mb-3">📍 Comment accéder à Copilot dans Excel</p>
                <div className="space-y-2">
                  {[
                    { num: '1', text: 'Ouvrez votre fichier Excel normalement' },
                    { num: '2', text: 'Regardez en haut à droite du ruban — vous verrez un bouton "Copilot" avec une icône ✨ (étoile colorée)' },
                    { num: '3', text: 'Cliquez dessus — un panneau s\'ouvre sur le côté droit de votre écran' },
                    { num: '4', text: 'Tapez votre demande en français dans le champ texte et appuyez sur Entrée' },
                  ].map(step => (
                    <div key={step.num} className="flex items-start gap-3">
                      <span className="w-6 h-6 bg-[#1B73E8] text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                        {step.num}
                      </span>
                      <p className="text-slate-200 text-sm leading-relaxed">{step.text}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-3 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3">
                  <p className="text-amber-300 text-xs">
                    💡 <strong>Vous ne voyez pas le bouton Copilot ?</strong> Votre abonnement Microsoft 365 ne l&apos;inclut peut-être pas encore.
                    Dans ce cas, utilisez <strong>ChatGPT</strong> (chatgpt.com) en mode &ldquo;Analyser un fichier&rdquo; — le résultat est identique.
                  </p>
                </div>
              </div>

              {/* Les prompts */}
              <div>
                <p className="text-white text-sm font-bold mb-3">💬 Les prompts exacts à copier-coller</p>
                <p className="text-slate-400 text-xs mb-3">Copiez l&apos;un de ces prompts selon votre situation :</p>

                <div className="space-y-3">

                  <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-4 py-2 bg-white/10 flex items-center gap-2">
                      <span className="text-xs font-bold text-[#1B73E8]">📊 Pour un compte de résultat ou P&L</span>
                    </div>
                    <div className="px-4 py-3">
                      <p className="text-slate-200 text-xs font-mono leading-relaxed italic">
                        &ldquo;Restructure ce tableau en compte de résultat mensuel lisible. Ligne 1 = en-têtes (noms des mois). Colonne A = noms des postes comptables en français compréhensible (pas de codes). Supprime les lignes et colonnes vides. Assure-toi que toutes les valeurs numériques sont en format nombre.&rdquo;
                      </p>
                    </div>
                  </div>

                  <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-4 py-2 bg-white/10 flex items-center gap-2">
                      <span className="text-xs font-bold text-[#1B73E8]">🎯 Pour un budget ou prévisionnel</span>
                    </div>
                    <div className="px-4 py-3">
                      <p className="text-slate-200 text-xs font-mono leading-relaxed italic">
                        &ldquo;Restructure ce tableau en budget avec 3 colonnes claires : Poste | Budget prévu | Réalisé. Ajoute une ligne de total par catégorie. Renomme les codes internes en libellés comptables compréhensibles. Supprime les onglets vides.&rdquo;
                      </p>
                    </div>
                  </div>

                  <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-4 py-2 bg-white/10 flex items-center gap-2">
                      <span className="text-xs font-bold text-[#1B73E8]">💰 Pour un fichier complexe ou non identifié</span>
                    </div>
                    <div className="px-4 py-3">
                      <p className="text-slate-200 text-xs font-mono leading-relaxed italic">
                        &ldquo;Ce fichier contient des données financières. Identifie les données utiles, supprime les onglets vides ou inutiles, ajoute des en-têtes clairs à chaque colonne, et restructure le tout en tableau propre avec des libellés lisibles. Garde uniquement ce qui est pertinent pour une analyse financière.&rdquo;
                      </p>
                    </div>
                  </div>

                  <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-4 py-2 bg-white/10 flex items-center gap-2">
                      <span className="text-xs font-bold text-[#1B73E8]">🏦 Pour un export ERP ou logiciel comptable</span>
                    </div>
                    <div className="px-4 py-3">
                      <p className="text-slate-200 text-xs font-mono leading-relaxed italic">
                        &ldquo;Ce fichier est un export de logiciel comptable. Restructure-le en tableau analytique lisible avec les colonnes : Date | Compte | Libellé | Montant. Remplace les codes de compte par des libellés compréhensibles. Supprime les en-têtes techniques et les lignes vides.&rdquo;
                      </p>
                    </div>
                  </div>

                </div>
              </div>

              {/* Ce que Copilot va faire */}
              <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4">
                <p className="text-green-300 text-sm font-bold mb-2">✅ Ce que Copilot va faire pour vous</p>
                <ul className="space-y-1.5">
                  {[
                    'Ajouter des en-têtes clairs à chaque colonne',
                    'Supprimer les lignes et colonnes vides',
                    'Renommer les codes internes en libellés lisibles',
                    'Réorganiser la structure pour la rendre cohérente',
                    'Convertir les formules en valeurs numériques',
                  ].map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-slate-200 text-xs">
                      <span className="text-green-400 flex-shrink-0">✓</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Étape finale */}
              <div className="border border-[#1B73E8]/30 rounded-xl p-4 flex items-start gap-3">
                <span className="text-2xl flex-shrink-0">🚀</span>
                <div>
                  <p className="text-white text-sm font-bold mb-1">Une fois Copilot terminé</p>
                  <p className="text-slate-300 text-sm leading-relaxed">
                    Sauvegardez le fichier modifié (Ctrl+S), retournez dans Pepperyn,
                    et uploadez ce nouveau fichier. L&apos;analyse sera complète et fiable en 60 secondes.
                  </p>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════════════════
            SECTION : CE QUI FAIT UN BON FICHIER
        ══════════════════════════════════════════════════════════ */}
        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-[#1A1A2E]">
            <span className="w-7 h-7 bg-[#1B73E8] text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">1</span>
            Ce qui fait un bon fichier
          </h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {[
              ['✅', 'En-têtes de colonnes claires', 'CA, Charges, Marge, Janvier, Février…'],
              ['✅', '1 à 3 onglets maximum', 'Un onglet P&L, un onglet Budget si nécessaire'],
              ['✅', 'Données numériques présentes', 'Les cellules contiennent de vrais chiffres'],
              ['✅', 'Structure cohérente', 'Les lignes ont une signification homogène'],
              ['✅', 'Pas de lignes totalement vides', 'Évitez les grandes zones blanches'],
              ['✅', 'Noms de lignes lisibles', '"Charges de personnel" plutôt que "CPT_4200_A"'],
            ].map(([icon, title, desc]) => (
              <div key={String(title)} className="flex items-start gap-3 p-3 bg-green-50 border border-green-100 rounded-xl">
                <span className="text-lg flex-shrink-0">{icon}</span>
                <div>
                  <p className="text-sm font-semibold text-[#1A1A2E]">{title}</p>
                  <p className="text-xs text-[#5F6368] mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ══════════════════════════════════════════════════════════
            SECTION : CE QUI POSE PROBLÈME
        ══════════════════════════════════════════════════════════ */}
        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-[#1A1A2E]">
            <span className="w-7 h-7 bg-red-500 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">2</span>
            Ce qui pose problème
          </h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {[
              ['❌', 'Plus de 15 onglets', 'Seuls les 5 premiers seront analysés'],
              ['❌', 'Cellules fusionnées en masse', 'Elles compliquent la lecture automatique'],
              ['❌', 'Colonnes sans en-tête', 'Pepperyn ne peut pas deviner ce que représente une colonne vide'],
              ['❌', 'Codes internes cryptiques', '"CPT_4200" n\'est pas interprétable sans référentiel'],
              ['❌', 'Formules non calculées', 'Les cellules affichent "=SUM(...)" au lieu du résultat'],
              ['❌', 'Plus de 60% de cellules vides', 'Pas assez de matière pour une analyse fiable'],
            ].map(([icon, title, desc]) => (
              <div key={String(title)} className="flex items-start gap-3 p-3 bg-red-50 border border-red-100 rounded-xl">
                <span className="text-lg flex-shrink-0">{icon}</span>
                <div>
                  <p className="text-sm font-semibold text-[#1A1A2E]">{title}</p>
                  <p className="text-xs text-[#5F6368] mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ══════════════════════════════════════════════════════════
            SECTION : FORMATS IDÉAUX
        ══════════════════════════════════════════════════════════ */}
        <section className="mb-10">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-[#1A1A2E]">
            <span className="w-7 h-7 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">3</span>
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
                format: '3 colonnes : Poste | Budget | Réel. Écart calculable automatiquement.',
                example: 'Poste | Budget 2024 | Réel 2024 | Écart',
              },
              {
                type: 'Trésorerie / Cash Flow',
                format: 'Dates en colonnes, flux entrants/sortants en lignes. Solde cumulé si possible.',
                example: 'Catégorie | Semaine 1 | Semaine 2 | ...',
              },
              {
                type: 'Export ERP / Comptable',
                format: 'Format tabulaire : Date, Compte, Libellé, Débit, Crédit, Solde.',
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

        {/* CTA */}
        <div className="bg-[#0A2540] rounded-2xl p-7 text-white text-center">
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
