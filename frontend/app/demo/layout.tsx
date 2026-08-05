'use client';

/**
 * Layout des routes /demo/* — External User Testing Prototype (2026-08-05).
 *
 * Aucune authentification (à la différence de app/app/layout.tsx) : ce
 * prototype doit être utilisable sans compte, sans PIN, sans connexion
 * réelle. En contrepartie, garde-fou explicite en profondeur (Mission 2) :
 * si isDemoModeEnabled() est faux — drapeau absent, ou build en
 * production quel que soit le drapeau — ces routes n'affichent jamais
 * l'interface Portfolio/Chat, uniquement un message neutre. Ceci évite
 * qu'un déploiement mal configuré ne tente des appels réseau réels sans
 * authentification.
 */
import { isDemoModeEnabled } from '@/lib/demo-mode';

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  if (!isDemoModeEnabled()) {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex items-center justify-center px-4">
        <div className="max-w-sm text-center">
          <p className="text-sm text-[#5F6368]">
            Ce prototype de démonstration n&apos;est pas disponible sur cet environnement.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
