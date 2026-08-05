/**
 * Isolation réseau du mode démo — External User Testing Prototype
 * (2026-08-05), Mission 9, cas 1 à 3.
 *
 * Preuve directe : en mode démo, fetchPortfolio / fetchReviewBriefing /
 * abandonArc ne construisent jamais de fetch() — donc ne peuvent jamais
 * atteindre Supabase, le backend, ni un appel LLM (qui transite toujours
 * par une requête HTTP vers le backend). global.fetch est mocké et sa
 * non-invocation est l'assertion centrale de ce fichier.
 */
jest.mock('@/lib/demo-mode', () => ({
  ...jest.requireActual('@/lib/demo-mode'),
  isDemoModeEnabled: jest.fn(),
}));

import { fetchPortfolio, fetchReviewBriefing, abandonArc } from '../arc-api';
import { isDemoModeEnabled } from '../demo-mode';

const mockedIsDemoModeEnabled = isDemoModeEnabled as jest.Mock;

describe('Mode démo activé (cas 1) — isolation réseau totale', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedIsDemoModeEnabled.mockReturnValue(true);
    global.fetch = jest.fn();
  });

  it('fetchPortfolio() ne construit jamais de fetch() (cas 2 : aucun accès Supabase possible)', async () => {
    const result = await fetchPortfolio();
    expect(global.fetch).not.toHaveBeenCalled();
    expect(result.length).toBeGreaterThan(0);
  });

  it('fetchReviewBriefing() ne construit jamais de fetch() (cas 2 : aucun accès Supabase possible)', async () => {
    await fetchReviewBriefing('e1');
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('abandonArc() ne construit jamais de fetch() — aucune écriture réelle ou simulée côté serveur', async () => {
    const result = await abandonArc('arc-1', 'raison');
    expect(global.fetch).not.toHaveBeenCalled();
    expect(result).toEqual({ abandoned: true, arc_id: 'arc-1' });
  });

  it('aucune de ces fonctions ne peut donc déclencher un appel LLM (cas 3) — le LLM est toujours servi via une requête HTTP au backend, jamais invoquée ici', async () => {
    await fetchPortfolio();
    await fetchReviewBriefing();
    await abandonArc('arc-2');
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
