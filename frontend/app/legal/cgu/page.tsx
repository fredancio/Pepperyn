import Link from 'next/link';
import { Footer } from '@/components/landing/Footer';

export default function CGUPage() {
  return (
    <div className="bg-white min-h-screen flex flex-col">
      {/* Header */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <img src="/favicon.png?v=4" alt="Pepperyn" className="w-12 h-12 object-contain" />
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
        <h1 className="text-3xl font-extrabold text-[#1B73E8] mb-2">
          Conditions Générales d'Utilisation (CGU)
        </h1>
        <p className="text-sm text-[#5F6368] mb-10">Finflate SRL — Pepperyn</p>

        <div className="prose prose-sm max-w-none text-[#1A1A2E]">

          <h2 className="text-xl font-bold mt-8 mb-3">1. Objet</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Les présentes CGU régissent l'accès et l'utilisation du service Pepperyn, édité par Finflate SRL.
            Pepperyn est un outil d'analyse de données financières permettant aux utilisateurs d'obtenir
            des insights et recommandations à partir de leurs données.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">2. Accès au service</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Le service est accessible via le site : www.finflate.com.
            L'utilisateur doit créer un compte pour accéder aux fonctionnalités.
            Certaines fonctionnalités peuvent être limitées dans une version gratuite.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">3. Utilisation du service</h2>
          <p className="text-[#5F6368] leading-relaxed mb-2">L'utilisateur s'engage à :</p>
          <ul className="list-disc pl-6 text-[#5F6368] space-y-1">
            <li>fournir des données exactes</li>
            <li>ne pas utiliser le service à des fins illégales</li>
            <li>ne pas tenter de perturber ou compromettre le service</li>
          </ul>

          <h2 className="text-xl font-bold mt-8 mb-3">4. Responsabilité</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Pepperyn fournit des analyses automatisées à titre informatif.
            L'utilisateur reste seul responsable des décisions prises sur la base des analyses fournies.
            Finflate SRL ne saurait être tenue responsable des pertes financières résultant de
            l'utilisation du service.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">5. Données</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Les données fournies par l'utilisateur restent sa propriété.
            Finflate SRL s'engage à ne pas exploiter ces données à des fins commerciales sans consentement.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">6. Disponibilité</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Le service est fourni "tel quel".
            Finflate SRL ne garantit pas une disponibilité continue ou sans erreur.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">7. Modification des CGU</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Finflate SRL se réserve le droit de modifier les présentes CGU à tout moment.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">8. Droit applicable</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Les présentes CGU sont régies par le droit belge.
            Tout litige relève des tribunaux compétents de Belgique.
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}
