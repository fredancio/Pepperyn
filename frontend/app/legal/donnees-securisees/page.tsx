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
        <h1 className="text-3xl font-extrabold text-[#1B73E8] mb-2">Données sécurisées</h1>
        <p className="text-sm text-[#5F6368] mb-10">Finflate SRL — Pepperyn</p>

        <div className="prose prose-sm max-w-none text-[#1A1A2E]">

          <div className="mb-8">
            <p className="text-xl font-bold text-[#1A1A2E] mb-2">🔒 Vos données sont sécurisées. Point.</p>
            <p className="text-lg font-semibold text-[#1A1A2E] mb-3">Vous manipulez des données sensibles. Nous aussi.</p>
            <p className="text-[#5F6368] leading-relaxed mb-2">
              Pepperyn analyse des données financières critiques.
            </p>
            <p className="text-[#5F6368] leading-relaxed">
              Nous avons conçu l&apos;infrastructure pour qu&apos;elles restent <strong className="text-[#1A1A2E]">sécurisées, privées et sous votre contrôle</strong>.
            </p>
          </div>

          <h2 className="text-xl font-bold mt-10 mb-5 text-[#1A1A2E]">Ce que nous garantissons</h2>

          <div className="flex flex-col gap-6">

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">🔒 Vos données ne sont jamais revendues</h3>
              <p className="text-[#5F6368] leading-relaxed">Zéro revente.</p>
              <p className="text-[#5F6368] leading-relaxed">Zéro exploitation marketing.</p>
              <p className="text-[#5F6368] leading-relaxed">Zéro partage à des tiers.</p>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">🔒 Sécurité de niveau professionnel</h3>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>Chiffrement HTTPS (TLS)</li>
                <li>Données protégées au repos</li>
                <li>Accès strictement contrôlé</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">👤 Vous gardez le contrôle</h3>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>Accès à vos données à tout moment</li>
                <li>Suppression sur demande</li>
                <li>Export complet possible</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">🗂️ Infrastructure fiable</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Construit sur des technologies reconnues :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>Supabase (base de données sécurisée)</li>
                <li>Vercel (infrastructure fiable)</li>
                <li>Modèles IA contrôlés</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">🤖 IA maîtrisée (pas un chatbot approximatif)</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Contrairement aux outils génériques :</p>
              <ul className="text-[#5F6368] leading-relaxed space-y-1">
                <li>✔ Pas d&apos;invention de données</li>
                <li>✔ Analyse basée uniquement sur vos inputs</li>
                <li>✔ Résultats structurés et vérifiables</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">📊 Fiabilité des analyses</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Chaque analyse est conçue pour être :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>directe</li>
                <li>compréhensible en quelques secondes</li>
                <li>immédiatement actionnable</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">🧠 Mémoire intelligente (différenciation)</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn ne se contente pas d&apos;analyser. Il apprend :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>évolution de vos marges</li>
                <li>tendances de vos coûts</li>
                <li>impact de vos décisions</li>
              </ul>
              <div className="mt-3 bg-[#EFF6FF] border-l-4 border-[#1B73E8] pl-4 pr-3 py-3 rounded-r-lg">
                <p className="text-xs font-semibold text-[#1A1A2E] mb-1">Exemple</p>
                <p className="text-sm text-[#5F6368] italic">
                  &ldquo;Votre marge a baissé de 4% depuis votre dernière analyse malgré votre réduction de coûts.&rdquo;
                </p>
              </div>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">⭐ Ce que disent nos premiers utilisateurs</h3>
              <div className="flex flex-col gap-3">
                <div className="bg-gray-50 rounded-xl px-4 py-3">
                  <p className="text-sm text-[#5F6368] italic">&ldquo;Pour la première fois, je comprends vraiment mes chiffres.&rdquo;</p>
                  <p className="text-xs text-[#1A1A2E] font-semibold mt-1">— CEO, PME</p>
                </div>
                <div className="bg-gray-50 rounded-xl px-4 py-3">
                  <p className="text-sm text-[#5F6368] italic">&ldquo;C&apos;est comme avoir un CFO en instantané.&rdquo;</p>
                  <p className="text-xs text-[#1A1A2E] font-semibold mt-1">— Founder SaaS</p>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">🔍 Transparence totale</h3>
              <p className="text-[#5F6368] leading-relaxed mb-2">Pepperyn est un outil d&apos;aide à la décision. Il ne remplace pas :</p>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>un expert-comptable</li>
                <li>un conseiller financier</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">📋 Conformité</h3>
              <ul className="list-disc list-inside text-[#5F6368] leading-relaxed space-y-1">
                <li>Conforme RGPD</li>
                <li>Données hébergées en Europe</li>
                <li>Respect des standards de sécurité</li>
              </ul>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">💬 Une question ?</h3>
              <a href="mailto:info@finflate.com" className="text-[#1B73E8] hover:underline">info@finflate.com</a>
            </div>

            <div className="border-t border-gray-100 pt-5">
              <h3 className="text-base font-bold text-[#1A1A2E] mb-2">💙 Notre engagement</h3>
              <p className="text-[#5F6368] leading-relaxed">Construire un outil fiable.</p>
              <p className="text-[#5F6368] leading-relaxed">Pas un gadget.</p>
              <p className="text-[#5F6368] leading-relaxed">
                Pas un simple chatbot de plus mais un véritable outil métier.
                Un système qui vous aide à piloter votre business en toute confiance.
              </p>
            </div>

          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
