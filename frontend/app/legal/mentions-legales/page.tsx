import Link from 'next/link';
import { Footer } from '@/components/landing/Footer';

export default function MentionsLegalesPage() {
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
        <h1 className="text-3xl font-extrabold text-[#1B73E8] mb-2">Mentions Légales</h1>
        <p className="text-sm text-[#5F6368] mb-10">Finflate SRL — Pepperyn</p>

        <div className="prose prose-sm max-w-none text-[#1A1A2E]">

          <h2 className="text-xl font-bold mt-8 mb-3">Éditeur du site</h2>
          <div className="text-[#5F6368] leading-relaxed space-y-1">
            <p>Finflate SRL</p>
            <p>6 Chemin du Cyclotron</p>
            <p>1348 Louvain-la-Neuve, Belgique</p>
            <p>BE 0753796205</p>
            <p>Email : <a href="mailto:info@finflate.com" className="text-[#1B73E8] hover:underline">info@finflate.com</a></p>
          </div>

          <h2 className="text-xl font-bold mt-8 mb-3">Directeur de publication</h2>
          <p className="text-[#5F6368] leading-relaxed">Finflate SRL</p>

          <h2 className="text-xl font-bold mt-8 mb-3">Hébergement</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Le site est hébergé par Vercel Inc.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">Propriété intellectuelle</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Tous les contenus présents sur le site sont protégés.
            Toute reproduction est interdite sans autorisation.
          </p>

          <h2 className="text-xl font-bold mt-8 mb-3">Responsabilité</h2>
          <p className="text-[#5F6368] leading-relaxed">
            Finflate SRL ne garantit pas l'exactitude des informations fournies.
            L'utilisation du site se fait sous la responsabilité de l'utilisateur.
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}
