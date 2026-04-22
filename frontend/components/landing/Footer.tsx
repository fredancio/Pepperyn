import Link from 'next/link';

export function Footer() {
  return (
    <footer className="bg-[#1A1A2E] text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10 lg:gap-16 mb-12">

          {/* Brand column */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              <img src="/favicon.png?v=4" alt="Pepperyn" className="w-12 h-12 object-contain" />
              <span className="text-base font-bold">Pepperyn — Financial Control Center</span>
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">
              Scanner financier IA pour équipes financières.
            </p>
          </div>

          {/* Entreprise */}
          <div className="flex flex-col gap-3">
            <p className="text-sm font-semibold text-white">Entreprise</p>
            <p className="text-sm text-gray-400">Finflate SRL</p>
            <p className="text-sm text-gray-400">6 Chemin du Cyclotron, 1348 LLN, Belgique</p>
            <p className="text-sm text-gray-400">BE 0753796205</p>
            <a href="mailto:info@finflate.com" className="text-sm text-[#1B73E8] hover:text-blue-300 transition-colors">
              info@finflate.com
            </a>
            <a href="https://www.finflate.com" target="_blank" rel="noopener noreferrer" className="text-sm text-[#1B73E8] hover:text-blue-300 transition-colors">
              www.finflate.com
            </a>
          </div>

          {/* Légal */}
          <div className="flex flex-col gap-3">
            <p className="text-sm font-semibold text-white">Légal</p>
            <Link href="/legal/mentions-legales" className="text-sm text-gray-400 hover:text-white transition-colors">
              Mentions légales
            </Link>
            <Link href="/legal/confidentialite" className="text-sm text-gray-400 hover:text-white transition-colors">
              Politique de confidentialité
            </Link>
            <Link href="/legal/cgu" className="text-sm text-gray-400 hover:text-white transition-colors">
              CGU
            </Link>
            <Link href="/legal/rgpd" className="text-sm text-gray-400 hover:text-white transition-colors">
              RGPD
            </Link>
            <Link href="/legal/donnees-securisees" className="text-sm text-gray-400 hover:text-white transition-colors">
              Données sécurisées
            </Link>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500">
            © 2026 Pepperyn — Finflate SRL. Tous droits réservés.
          </p>
          <p className="text-xs text-gray-500">
            Powered by Finflate, 2026®
          </p>
        </div>
      </div>
    </footer>
  );
}
