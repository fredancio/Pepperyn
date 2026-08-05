/**
 * Tests — PortfolioHome (Portfolio Intelligence, Incrément 1, Capability 7).
 *
 * Couvre le périmètre strict de l'Incrément 1 (voir
 * PORTFOLIO_HOME_IMPLEMENTATION_PLAN.md et BACKLOG_ITEM.md) :
 *   - rendu d'une carte par client (nom + titre du point prioritaire)
 *   - tri des cartes tel que retourné par le backend (déjà trié par priorité)
 *   - état vide honnête (aucun bandeau alarmant, pas de plantage)
 *   - échec réseau traité proprement (message sobre, pas de crash)
 *   - "Préparer cette revue" navigue vers /app/chat?entity=<id>
 *   - aucun contenu hors périmètre (why_it_matters / temporal_context /
 *     compteur) affiché — réservé à l'Incrément 2
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

const mockedFetchPortfolio = arcApi.fetchPortfolio as jest.Mock;

function makeCard(overrides: Partial<PortfolioCard> = {}): PortfolioCard {
  return {
    entity_id: 'entity-1',
    entity_name: 'Client A',
    top_item: {
      arc_id: 'arc-1',
      source_type: 'decision_arc',
      entity_id: 'entity-1',
      priority: 'urgent',
      title: 'Renégocier le contrat assurance',
      temporal_context: 'il y a 45 jours',
      why_it_matters: 'Cette décision est en attente depuis plus de 3 semaines.',
      questions_to_ask: ['Avez-vous pris une décision sur ce point ?'],
    },
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('PortfolioHome — rendu', () => {
  test('rendu d\'une carte par client avec nom + titre du point prioritaire', async () => {
    mockedFetchPortfolio.mockResolvedValue([
      makeCard({ entity_id: 'e1', entity_name: 'Client A', top_item: makeCard().top_item }),
    ]);

    render(<PortfolioHome />);

    expect(await screen.findByText('Client A')).toBeInTheDocument();
    expect(screen.getByText('Renégocier le contrat assurance')).toBeInTheDocument();
    expect(screen.getByText('Préparer cette revue')).toBeInTheDocument();
  });

  test('plusieurs clients — une carte chacun, ordre préservé tel que renvoyé par le backend', async () => {
    mockedFetchPortfolio.mockResolvedValue([
      makeCard({ entity_id: 'e1', entity_name: 'Client A' }),
      makeCard({
        entity_id: 'e2',
        entity_name: 'Client B',
        top_item: { ...makeCard().top_item, arc_id: 'arc-2', priority: 'to_check' },
      }),
    ]);

    render(<PortfolioHome />);
    await screen.findByText('Client A');

    const cards = screen.getAllByTestId(/^portfolio-card-/);
    expect(cards.map((c) => c.getAttribute('data-testid'))).toEqual([
      'portfolio-card-e1',
      'portfolio-card-e2',
    ]);
  });

  test('état vide (aucun client actif) affiche un message sobre, pas d\'erreur', async () => {
    mockedFetchPortfolio.mockResolvedValue([]);
    render(<PortfolioHome />);

    expect(await screen.findByTestId('portfolio-empty')).toBeInTheDocument();
    expect(screen.getByText("Aucun point actif à traiter pour l'instant.")).toBeInTheDocument();
  });

  test('un échec réseau affiche un message sobre sans planter le composant', async () => {
    mockedFetchPortfolio.mockRejectedValue(new Error('network error'));
    render(<PortfolioHome />);

    expect(await screen.findByTestId('portfolio-error')).toBeInTheDocument();
  });

  test('aucun contenu hors périmètre Incrément 1 (why_it_matters / temporal_context) affiché', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard()]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    expect(
      screen.queryByText('Cette décision est en attente depuis plus de 3 semaines.')
    ).not.toBeInTheDocument();
    expect(screen.queryByText('il y a 45 jours')).not.toBeInTheDocument();
  });
});

describe('PortfolioHome — "Préparer cette revue"', () => {
  test('navigue vers /app/chat avec le client pré-sélectionné en paramètre', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard({ entity_id: 'entity-42' })]);

    render(<PortfolioHome />);
    await screen.findByText('Client A');

    fireEvent.click(screen.getByText('Préparer cette revue'));

    expect(mockPush).toHaveBeenCalledWith('/app/chat?entity=entity-42');
  });
});
