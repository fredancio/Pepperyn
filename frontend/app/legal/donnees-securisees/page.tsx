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
        <h1 className="text-3xl font-extrabold text-[#1B73E8] mb-2">Sécurité &amp; confidentialité des données</h1>
        <p className="text-sm text-[#5F6368] mb-10">Finflate SRL — Pepperyn</p>

        <div className="prose prose-sm max-w-none text-[#1A1A2E]">

          <div className="mb-8">
            <p className="text-lg font-semibold text-[#1A1A2E] mb-3">Vos données financières méritent un haut niveau d&apos;exigence</p>
            <p className="text-[#5F6368] leading-relaxed mb-3">
              Pepperyn est conçu pour traiter des données financières sensibles avec une approche centrée sur :
            </p>
            <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
              <li>la confidentialité,</li>
              <li>la minimisation des données,</li>
              <li>la sécurité,</li>
              <li>le cloisonnement des informations,</li>
              <li>et le contrôle utilisateur.</li>
            </ul>
            <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn n&apos;est pas un simple accès direct à un modèle IA.</p>
            <p className="text-[#5F6368] leading-relaxed">
              La plateforme agit comme une couche intermédiaire de structuration, de sécurisation et de contrôle entre vos données et les modèles IA utilisés pour produire les analyses.
            </p>
          </div>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Comment Pepperyn traite vos données</h2>

          <div className="flex flex-col gap-6">

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Une architecture conçue pour limiter l&apos;exposition des données</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Avant tout traitement IA :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>les fichiers transmis sont analysés localement par Pepperyn,</li>
                <li>les données sont structurées,</li>
                <li>les informations inutiles à l&apos;analyse peuvent être supprimées,</li>
                <li>certaines données identifiantes peuvent être anonymisées ou exclues du traitement,</li>
                <li>seuls les éléments nécessaires au raisonnement financier sont utilisés.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed mt-3">
                Pepperyn est conçu pour éviter l&apos;envoi inutile de données personnelles ou sensibles aux modèles IA.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Les fichiers bruts ne sont pas directement transmis aux modèles IA</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Pepperyn est conçu pour fonctionner comme une couche de traitement intermédiaire.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Les modèles IA utilisés par Pepperyn ne sont pas destinés à recevoir directement :
              </p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>vos fichiers Excel complets,</li>
                <li>vos exports comptables bruts,</li>
                <li>vos données nominatives,</li>
                <li>vos informations personnelles inutiles à l&apos;analyse.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed mb-2">Avant tout appel IA, Pepperyn peut notamment :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>structurer les données,</li>
                <li>agréger certains éléments financiers,</li>
                <li>filtrer certaines informations,</li>
                <li>supprimer certains champs sensibles,</li>
                <li>limiter les données transmises au strict nécessaire.</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Cloisonnement des données par entité</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn fonctionne avec un système d&apos;entités cloisonnées.</p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Chaque société, client, filiale ou organisation dispose de son propre contexte :
              </p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-3">
                <li>historique,</li>
                <li>fichiers,</li>
                <li>analyses,</li>
                <li>mémoire,</li>
                <li>conversations,</li>
                <li>rapports.</li>
              </ul>
              <p className="text-[#5F6368] leading-relaxed">
                Pepperyn est conçu pour limiter les risques de mélange de données entre plusieurs clients ou entités.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Contrôle utilisateur</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Les utilisateurs conservent le contrôle de leurs données.</p>
              <p className="text-[#5F6368] leading-relaxed mb-2">Selon les fonctionnalités disponibles dans leur plan :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>ils peuvent accéder à leurs historiques,</li>
                <li>exporter leurs rapports,</li>
                <li>supprimer certaines données,</li>
                <li>demander la clôture de leur compte,</li>
                <li>demander la suppression de leur historique lorsque cela est applicable.</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Suppression des fichiers sources</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Pepperyn est conçu pour limiter la conservation inutile des fichiers transmis.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">Selon la configuration du service :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>certains fichiers temporaires ou sources peuvent être automatiquement supprimés après traitement,</li>
                <li>seuls certains résultats d&apos;analyse, historiques ou rapports peuvent être conservés afin de permettre les fonctionnalités de suivi et de mémoire analytique.</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">Utilisation de modèles IA professionnels</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Pepperyn utilise des APIs professionnelles de fournisseurs IA reconnus.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                Les traitements IA sont réalisés via des environnements professionnels disposant de politiques de sécurité et de confidentialité adaptées aux usages B2B.
              </p>
              <p className="text-[#5F6368] leading-relaxed mb-2">
                À notre connaissance et selon les politiques commerciales communiquées par ces fournisseurs :
              </p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>les données transmises via les APIs professionnelles ne sont pas utilisées pour entraîner les modèles publics,</li>
                <li>certains traitements techniques temporaires (logs, monitoring, sécurité, détection d&apos;abus, rétention limitée) peuvent néanmoins exister selon les politiques des fournisseurs concernés.</li>
              </ul>
            </div>

          </div>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Ce que Pepperyn ne fait pas</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn n&apos;a pas pour objectif :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>de revendre vos données,</li>
            <li>d&apos;exploiter vos données à des fins publicitaires,</li>
            <li>de partager volontairement vos données financières avec des tiers non nécessaires au fonctionnement du service.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed mb-2">Les données sont utilisées uniquement dans le cadre :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
            <li>des analyses demandées,</li>
            <li>du fonctionnement de la plateforme,</li>
            <li>de la sécurité du service,</li>
            <li>de l&apos;amélioration technique de Pepperyn.</li>
          </ul>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Infrastructure &amp; sécurité</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn s&apos;appuie sur des technologies et infrastructures reconnues.</p>
          <p className="text-[#5F6368] leading-relaxed mb-2">Les mesures de sécurité mises en œuvre peuvent inclure :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>chiffrement des communications (HTTPS / TLS),</li>
            <li>contrôle des accès,</li>
            <li>cloisonnement logique des données,</li>
            <li>limitation des accès administratifs,</li>
            <li>suppression automatique de certains fichiers temporaires,</li>
            <li>surveillance technique de l&apos;infrastructure,</li>
            <li>journalisation de sécurité,</li>
            <li>limitation des permissions internes.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed mb-2">Aucun système informatique ne peut garantir un risque zéro.</p>
          <p className="text-[#5F6368] leading-relaxed">
            Pepperyn met toutefois en œuvre des mesures techniques et organisationnelles raisonnables destinées à réduire les risques de perte, d&apos;accès non autorisé ou d&apos;utilisation inappropriée des données.
          </p>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Transparence sur les analyses IA</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn est un outil d&apos;aide à la décision.</p>
          <p className="text-[#5F6368] leading-relaxed mb-2">Les analyses générées :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>reposent sur les données fournies,</li>
            <li>peuvent inclure des estimations, projections ou hypothèses,</li>
            <li>ne constituent pas un conseil comptable, fiscal, juridique ou financier professionnel.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed mb-2">Les utilisateurs restent responsables :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>de la validation des décisions prises,</li>
            <li>de l&apos;interprétation des analyses,</li>
            <li>de la vérification des informations importantes.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed">
            Lorsque certaines données sont incomplètes ou indisponibles, Pepperyn est conçu pour signaler les limites des analyses ou afficher des niveaux de confiance.
          </p>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Conformité &amp; confidentialité</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">
            Pepperyn est développé avec une attention particulière portée à la confidentialité, à la sécurité et à la protection des données.
          </p>
          <p className="text-[#5F6368] leading-relaxed">
            Certaines données peuvent être traitées via des prestataires techniques, fournisseurs cloud ou services tiers nécessaires au fonctionnement de la plateforme.
          </p>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Vos droits</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Selon la réglementation applicable, vous pouvez notamment :</p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1 mb-4">
            <li>demander l&apos;accès à certaines données,</li>
            <li>demander leur suppression lorsque cela est applicable,</li>
            <li>exporter certaines informations disponibles dans la plateforme,</li>
            <li>demander la clôture de votre compte.</li>
          </ul>
          <p className="text-[#5F6368] leading-relaxed">
            Pour toute question relative à la confidentialité ou à la sécurité :{' '}
            <a href="mailto:info@finflate.com" className="text-[#1B73E8] hover:underline">info@finflate.com</a>
          </p>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Notre engagement</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">Construire un outil métier sérieux, transparent et fiable.</p>
          <p className="text-[#5F6368] leading-relaxed mb-2">
            Pepperyn n&apos;a pas vocation à remplacer les professionnels du chiffre ou du conseil, mais à aider les dirigeants et équipes financières à :
          </p>
          <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
            <li>mieux comprendre leurs données,</li>
            <li>mieux piloter leurs décisions,</li>
            <li>mieux anticiper leurs risques,</li>
            <li>et gagner du temps dans leurs analyses.</li>
          </ul>

        </div>
      </main>

      <Footer />
    </div>
  );
}
