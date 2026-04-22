import Link from 'next/link';
import { Footer } from '@/components/landing/Footer';

export default function ConfidentialitePage() {
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
          Politique de Confidentialité
        </h1>
        <p className="text-sm text-[#5F6368] mb-10">Finflate SRL — Pepperyn</p>

        <div className="prose prose-sm max-w-none text-[#1A1A2E]">

          <h2 className="text-xl font-bold mt-8 mb-3">1. Responsable du traitement</h2>
          <div className="text-[#5F6368] leading-relaxed space-y-1">
            <p>Finflate SRL</p>
            <p>6 Chemin du Cyclotron, 1348 Louvain-la-Neuve, Belgique</p>
            <p>BE 0753796205</p>
            <p>Email : <a href="mailto:info@finflate.com" className="text-[#1B73E8] hover:underline">info@finflate.com</a></p>
          </div>

          <h2 className="text-xl font-bold mt-8 mb-3">2. Données collectées</h2>
          <p className="text-[#5F6368] mb-2">Nous collectons les données suivantes :</p>
          <ul className="list-disc pl-6 text-[#5F6368] space-y-1">
            <li>données d'identification (email)</li>
            <li>données d'utilisation</li>
            <li>données financières fournies par l'utilisateur</li>
          </ul>

          <h2 className="text-xl font-bold mt-8 mb-3">3. Finalités</h2>
          <p className="text-[#5F6368] mb-2">Les données sont utilisées pour :</p>
          <ul className="list-disc pl-6 text-[#5F6368] space-y-1">
            <li>fournir le service Pepperyn</li>
            <li>améliorer les analyses</li>
            <li>assurer la sécurité</li>
          </ul>

          <h2 className="text-xl font-bold mt-8 mb-3">4. Conservation</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Les données sont conservées uniquement le temps nécessaire au service.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">5. Partage des données</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Les données ne sont pas vendues.
            Elles peuvent être traitées par des sous-traitants techniques (hébergement, IA).
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">6. Sécurité</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Nous mettons en œuvre des mesures techniques et organisationnelles pour protéger les données.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">7. Droits des utilisateurs</h2>
          <p className="text-[#5F6368] mb-2">Conformément au RGPD, vous disposez de :</p>
          <ul className="list-disc pl-6 text-[#5F6368] space-y-1">
            <li>droit d'accès</li>
            <li>droit de rectification</li>
            <li>droit de suppression</li>
            <li>droit d'opposition</li>
          </ul>

          <h2 className="text-xl font-bold mt-8 mb-3">8. Contact</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Pour toute demande : <a href="mailto:info@finflate.com" className="text-[#1B73E8] hover:underline">info@finflate.com</a>
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}
