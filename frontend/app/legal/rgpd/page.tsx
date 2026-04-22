import Link from 'next/link';
import { Footer } from '@/components/landing/Footer';

export default function RGPDPage() {
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
        <h1 className="text-3xl font-extrabold text-[#1B73E8] mb-2">Conformité RGPD</h1>
        <p className="text-sm text-[#5F6368] mb-10">Finflate SRL — Pepperyn</p>

        <div className="prose prose-sm max-w-none text-[#1A1A2E]">

          <h2 className="text-xl font-bold mt-8 mb-3">Engagement</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Finflate SRL s'engage à respecter le Règlement Général sur la Protection des Données (RGPD).
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">Données traitées</h2>
          <p className="text-[#5F6368] mb-2">
            Nous traitons uniquement les données nécessaires au fonctionnement du service :
          </p>
          <ul className="list-disc pl-6 text-[#5F6368] space-y-1">
            <li>données de compte</li>
            <li>données financières fournies volontairement</li>
          </ul>

          <h2 className="text-xl font-bold mt-8 mb-3">Finalité</h2>
          <p className="text-[#5F6368] mb-2">Les données sont utilisées exclusivement pour :</p>
          <ul className="list-disc pl-6 text-[#5F6368] space-y-1">
            <li>fournir les analyses</li>
            <li>améliorer le service</li>
            <li>assurer la sécurité</li>
          </ul>

          <h2 className="text-xl font-bold mt-8 mb-3">Base légale</h2>
          <p className="text-[#5F6368] mb-2">Le traitement repose sur :</p>
          <ul className="list-disc pl-6 text-[#5F6368] space-y-1">
            <li>l'exécution du service</li>
            <li>le consentement de l'utilisateur</li>
          </ul>

          <h2 className="text-xl font-bold mt-8 mb-3">Sous-traitants</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Nous utilisons des prestataires techniques (hébergement, IA) conformes aux standards de sécurité.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">Droits des utilisateurs</h2>
          <p className="text-[#5F6368] mb-2">Vous pouvez à tout moment :</p>
          <ul className="list-disc pl-6 text-[#5F6368] space-y-1">
            <li>demander l'accès à vos données</li>
            <li>demander leur suppression</li>
            <li>retirer votre consentement</li>
          </ul>

          <h2 className="text-xl font-bold mt-8 mb-3">Contact</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Pour toute demande RGPD : <a href="mailto:info@finflate.com" className="text-[#1B73E8] hover:underline">info@finflate.com</a>
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}
