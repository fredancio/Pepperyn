import Link from 'next/link';
import { Footer } from '@/components/landing/Footer';

export default function DonneesSécuriséesPage() {
  return (
    <div className="bg-white min-h-screen flex flex-col">
      {/* Header */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <img src="/favicon.png?v=5" alt="Pepperyn" className="w-12 h-12 object-contain" />
            <div>
              <span className="text-base font-bold text-[#1A1A2E] block leading-none">Pepperyn IA</span>
              <span className="text-xs text-[#5F6368] block">Financial Control Center</span>
            </div>
          </Link>
          <Link href="/register" className="text-sm font-medium text-[#1B73E8] hover:underline">
            Créer un compte
          </Link>
        </div>
      </nav>

      {/* Content */}
      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-8 lg:px-16 py-16">
        <h1 className="text-3xl font-extrabold text-[#1B73E8] mb-2">Sécurité &amp; Confidentialité des données</h1>
        <p className="text-sm text-[#5F6368] mb-10">Finflate SRL — Pepperyn</p>

        <div className="prose prose-sm max-w-none text-[#1A1A2E]">

          <div className="mb-8">
            <p className="text-lg font-semibold text-[#1A1A2E] mb-3">Vos données financières méritent un haut niveau d&apos;exigence</p>
            <p className="text-[#5F6368] leading-relaxed mb-3">
              Pepperyn a été conçu pour traiter des données financières sensibles avec une approche centrée sur :
            </p>
            <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
              <li>la confidentialité ;</li>
              <li>la sécurité ;</li>
              <li>la confidentialité des données ;</li>
              <li>le cloisonnement des informations ;</li>
              <li>le contrôle utilisateur ;</li>
              <li>la transparence.</li>
            </ul>
            <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn n&apos;est pas un simple accès à un modèle d&apos;intelligence artificielle.</p>
            <p className="text-[#5F6368] leading-relaxed mb-2">
              La plateforme agit comme une couche intermédiaire de structuration, de sécurisation et d&apos;anonymisation entre vos données et les modèles d&apos;IA utilisés pour produire les analyses.
            </p>
            <p className="text-[#5F6368] leading-relaxed">
              Cette architecture a été pensée pour permettre aux entreprises de bénéficier de la puissance de l&apos;intelligence artificielle tout en éliminant l&apos;exposition des informations sensibles.
            </p>
          </div>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Comment Pepperyn protège vos données confidentielles</h2>

          <div className="flex flex-col gap-6">

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Une architecture conçue pour limiter l&apos;exposition des données</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Avant tout traitement IA :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>les fichiers transmis sont analysés et structurés par Pepperyn ;</li>
                <li>les données inutiles à l&apos;analyse sont exclues ;</li>
                <li>les informations identifiantes sont supprimées ;</li>
                <li>les données sont agrégées lorsque cela est pertinent ;</li>
                <li>seules les informations nécessaires au raisonnement financier sont utilisées.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed mt-3">
                Pepperyn est conçu pour empêcher l&apos;envoi de données personnelles ou sensibles aux modèles d&apos;intelligence artificielle.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Anonymisation avant tout traitement IA</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                L&apos;une des fonctions essentielles de Pepperyn consiste à préparer et sécuriser les données avant toute analyse IA.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Avant tout appel à un modèle d&apos;intelligence artificielle, Pepperyn applique des mécanismes de filtrage, d&apos;anonymisation et de rationalisation des données.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">Selon la structure des données fournies, Pepperyn va notamment exclure ou anonymiser :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>le nom de votre entreprise ;</li>
                <li>les noms de clients ;</li>
                <li>les noms de fournisseurs ;</li>
                <li>les données personnelles ;</li>
                <li>les informations identifiantes ;</li>
                <li>les éléments non nécessaires à l&apos;analyse financière.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed">
                L&apos;objectif est que les modèles IA raisonnent sur des données financières anonymisées et non sur l&apos;identité des personnes ou des organisations concernées.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Un exemple concret</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Concrètement, avant qu&apos;une analyse ne soit réalisée par l&apos;intelligence artificielle, les noms réels présents dans vos fichiers sont remplacés par des identifiants anonymes. Par exemple :
              </p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>« Dupont SA » devient « CLIENT_001 » ;</li>
                <li>« ABC Logistics » devient « FOURNISSEUR_001 ».</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed">
                Une fois l&apos;analyse terminée, Pepperyn rétablit automatiquement les noms réels dans les résultats qui vous sont présentés. Vous obtenez ainsi des analyses précises et exploitables, tout en garantissant que l&apos;intelligence artificielle ne connaît jamais l&apos;identité réelle de vos clients, fournisseurs ou collaborateurs.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Qui peut voir vos données réelles ?</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Vous seul. La table de correspondance qui relie les identifiants anonymes à vos noms réels est stockée dans votre espace sécurisé et n&apos;est jamais transmise à l&apos;intelligence artificielle.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">Vos données nominatives ne sont accessibles :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>ni aux autres utilisateurs ;</li>
                <li>ni aux partenaires technologiques de Pepperyn ;</li>
                <li>ni aux modèles d&apos;intelligence artificielle utilisés pour l&apos;analyse.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed">
                Les administrateurs de Pepperyn n&apos;ont pas accès au contenu de vos données dans le cadre de l&apos;utilisation normale du service et ne peuvent consulter vos informations nominatives sans procédure exceptionnelle strictement encadrée.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Les modèles IA ne reçoivent pas vos fichiers bruts</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Pepperyn ne fonctionne pas comme un simple transfert de vos fichiers vers un modèle d&apos;intelligence artificielle.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Les fichiers sources transmis par les utilisateurs ne sont pas destinés à être envoyés directement aux modèles IA.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">Avant toute analyse, Pepperyn applique des mécanismes de :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>structuration ;</li>
                <li>filtrage ;</li>
                <li>agrégation ;</li>
                <li>anonymisation ;</li>
                <li>définition par nature des données.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Les modèles IA reçoivent uniquement les informations nécessaires à la réalisation des analyses demandées.
              </p>
              <p className="text-[#5F6368] leading-relaxed">
                Cette approche permet d&apos;éliminer l&apos;exposition des données sensibles tout en conservant la qualité et la pertinence des analyses produites.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Isolation des entreprises, filiales et clients</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn fonctionne avec un système de clients ou entreprises cloisonnés.</p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Chaque entreprise, client, filiale ou organisation dispose de son propre espace logique comprenant :
              </p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>son historique ;</li>
                <li>ses fichiers ;</li>
                <li>ses rapports ;</li>
                <li>ses analyses ;</li>
                <li>sa mémoire contextuelle ;</li>
                <li>ses conversations.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed">
                Cette séparation contribue à éviter les mélanges de contexte et à renforcer la confidentialité des données traitées dans la plateforme.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Contrôle total de vos données</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Vous conservez le contrôle entier de vos données directement depuis votre espace Pepperyn.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">Vous pouvez à tout moment :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>consulter vos analyses ;</li>
                <li>accéder à votre historique et le supprimer ;</li>
                <li>exporter vos rapports ;</li>
                <li>gérer vos paramètres ;</li>
                <li>modifier vos préférences ;</li>
                <li>clôturer votre compte.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed">
                La clôture du compte entraîne la suppression définitive de l&apos;entièreté des données associées au compte conformément aux règles de fonctionnement de la plateforme.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Suppression des fichiers sources</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Pepperyn est conçu pour éviter la conservation des fichiers transmis.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Les fichiers sources utilisés pour produire une analyse sont destinés à être supprimés après traitement par Pepperyn et avant l&apos;envoi à tout système IA.
              </p>
              <p className="text-[#5F6368] leading-relaxed">
                L&apos;objectif est de limiter la conservation des données aux seuls éléments nécessaires au fonctionnement des services, tels que les rapports générés ainsi qu&apos;à l&apos;historique.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Utilisation de modèles IA professionnels</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Pepperyn utilise des APIs professionnelles de fournisseurs d&apos;intelligence artificielle reconnus.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Les traitements IA sont réalisés via des environnements professionnels adaptés aux usages B2B.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Selon les politiques communiquées par ces fournisseurs pour leurs services API professionnels :
              </p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>les données transmises ne sont pas utilisées pour entraîner les modèles publics ;</li>
                <li>les traitements sont réalisés dans des environnements distincts des services grand public.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed">
                Comme pour tout service cloud professionnel, certains traitements techniques limités (sécurité, journalisation, monitoring ou détection d&apos;abus) peuvent exister conformément aux politiques applicables des fournisseurs concernés.
              </p>
            </div>

          </div>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Ce que Pepperyn ne fait pas</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn n&apos;a pas pour objectif :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>de revendre vos données ;</li>
            <li>d&apos;exploiter vos données à des fins publicitaires ;</li>
            <li>de partager volontairement vos données financières avec des tiers non nécessaires au fonctionnement du service.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed mb-2">Les données sont utilisées uniquement dans le cadre :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
            <li>des analyses demandées ;</li>
            <li>de la sécurité du service ;</li>
            <li>de l&apos;amélioration analytique de votre compte Pepperyn.</li>
          </ul>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Infrastructure &amp; sécurité</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn s&apos;appuie sur des technologies et infrastructures reconnues.</p>
          <p className="text-[#5F6368] leading-relaxed mb-2">Les mesures de sécurité mises en œuvre incluent :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>chiffrement des communications (HTTPS / TLS) ;</li>
            <li>contrôle des accès ;</li>
            <li>cloisonnement des données ;</li>
            <li>contrôle exclusif des accès administratifs par les utilisateurs autorisés ;</li>
            <li>maîtrise des droits d&apos;accès et des permissions administratives ;</li>
            <li>gestion centralisée des accès administratifs par votre organisation ;</li>
            <li>surveillance technique de l&apos;infrastructure ;</li>
            <li>journalisation de sécurité ;</li>
            <li>limitation des permissions internes.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed mb-2">
            Votre organisation conserve le contrôle exclusif des accès, des rôles et des permissions au sein de Pepperyn.
          </p>
          <p className="text-[#5F6368] leading-relaxed mb-2">
            Seuls les administrateurs désignés par votre organisation peuvent gérer les accès, les utilisateurs et les autorisations.
          </p>
          <p className="text-[#5F6368] leading-relaxed">
            Pepperyn met en œuvre des mesures techniques et organisationnelles destinées à réduire les risques de perte, d&apos;accès non autorisé ou d&apos;utilisation inappropriée des données.
          </p>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Transparence sur les analyses IA</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn est un outil d&apos;aide à la décision.</p>
          <p className="text-[#5F6368] leading-relaxed mb-2">Les analyses générées :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>reposent sur les données fournies ;</li>
            <li>peuvent inclure des estimations, projections ou hypothèses ;</li>
            <li>ne constituent pas un conseil comptable, fiscal, juridique ou financier professionnel.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed mb-2">Les utilisateurs restent responsables :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>de la validation des décisions prises ;</li>
            <li>de l&apos;interprétation des analyses ;</li>
            <li>de la vérification des informations importantes.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed">
            Lorsque certaines données sont incomplètes ou indisponibles, Pepperyn est conçu pour signaler les limites des analyses ou afficher des niveaux de confiance.
          </p>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Vos droits</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Vous pouvez à tout moment :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>accéder à vos données ;</li>
            <li>exporter vos rapports ;</li>
            <li>gérer vos préférences ;</li>
            <li>clôturer votre compte depuis votre espace personnel, incluant l&apos;effacement définitif de l&apos;entièreté de vos données.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed">
            Pour toute question relative à la confidentialité ou à la sécurité :{' '}
            <a href="mailto:info@finflate.com" className="text-[#1B73E8] hover:underline">info@finflate.com</a>
          </p>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Notre engagement</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Construire un outil métier sérieux, transparent et fiable.</p>
          <p className="text-[#5F6368] leading-relaxed mb-2">
            Pepperyn n&apos;a pas vocation à remplacer les professionnels du chiffre ou du conseil.
          </p>
          <p className="text-[#5F6368] leading-relaxed mb-2">
            Sa mission est d&apos;aider les dirigeants, CFO, contrôleurs de gestion et équipes financières à :
          </p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
            <li>mieux comprendre leurs données ;</li>
            <li>mieux piloter leurs décisions ;</li>
            <li>mieux anticiper leurs risques ;</li>
            <li>obtenir un gain de temps considérable dans leurs analyses ;</li>
            <li>exploiter la puissance de l&apos;intelligence artificielle tout en conservant un haut niveau de contrôle sur leurs informations.</li>
          </ul>

        </div>
      </main>

      <Footer />
    </div>
  );
}
