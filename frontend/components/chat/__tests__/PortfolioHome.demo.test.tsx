/**
 * PortfolioHome en mode démo — External User Testing Prototype (2026-08-05),
 * Mission 9, cas 9 (navigation Portfolio → Review Briefing).
 *
 * Seule différence testée ici par rapport à PortfolioHome.test.tsx : la
 * cible de navigation change vers /demo/chat quand isDemoModeEnabled() est
 * vrai. Tout le reste du composant (hiérarchie, tri, rendu) est
 * byte-identique et déjà couvert par PortfolioHome.test.tsx.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { PortfolioHome } from '../PortfolioHome';
import * as arcApi from '@/lib/arc-api';
import type { PortfolioCard } from '@/lib/types';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/lib/arc-api', () => {
  const actual = jest.requireActual('@/lib/arc-api');
  return {
    ...actual,
    fetchPortfolio: jest.fn(),
  };
});

jest.mock('@/lib/demo-mode', () => ({
  ...jest.requireActual('@/lib/demo-mode'),
  isDemoModeEnabled: jest.fn(() => true),
}));

const mockedFetchPortfolio = arcApi.fetchPortfolio as jest.Mock;

function makeCard(overrides: Partial<PortfolioCard> = {}): PortfolioCard {
  return {
    entity_id: 'e1',
    entity_name: 'Cabinet Lefèvre & Associés',
    top_item: {
      arc_id: 'l1',
      source_type: 'decision_arc',
      entity_id: 'e1',
      priority: 'urgent',
      title: 'Renégocier le contrat cadre',
      temporal_context: 'Sans décision depuis 92 jours',
      why_it_matters: 'Toujours sans décision confirmée après au moins une revue.',
      questions_to_ask: ['Où en êtes-vous ?'],
      age_days: 92,
    },
    other_active_count: 3,
    why_it_matters_display: null,
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('PortfolioHome — navigation en mode démo (cas 9)', () => {
  test('"Préparer cette revue" navigue vers /demo/chat?entity=<id> quand isDemoModeEnabled() est vrai', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard()]);
    render(<PortfolioHome />);

    const button = await screen.findByText('Préparer cette revue');
    fireEvent.click(button);

    expect(mockPush).toHaveBeenCalledWith('/demo/chat?entity=e1');
  });
});
