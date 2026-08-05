import { PortfolioHome } from '@/components/chat/PortfolioHome';
import { DemoBanner } from '@/components/demo/DemoBanner';

/**
 * Portfolio Home — External User Testing Prototype (2026-08-05).
 *
 * Réutilise PortfolioHome.tsx à l'identique (aucune redéfinition du
 * Portfolio) : hiérarchie de carte, tri, densité, why_it_matters — tout
 * est inchangé par rapport à l'écran validé (PORTFOLIO_HOME_FINAL_VALIDATION.md).
 * Seule différence : fetchPortfolio() lit lib/demo-data.ts au lieu de
 * l'API réelle (isDemoModeEnabled(), voir lib/arc-api.ts).
 */
export default function DemoPortfolioPage() {
  return (
    <>
      <DemoBanner />
      <PortfolioHome />
    </>
  );
}
