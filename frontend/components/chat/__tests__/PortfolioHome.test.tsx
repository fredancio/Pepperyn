/**
 * Tests — PortfolioHome (Portfolio Intelligence, Incréments 1 + 2, Capability 7).
 *
 * Couvre le périmètre de l'Incrément 2 (voir GO IMPLEMENT — PORTFOLIO
 * INTELLIGENCE INCREMENT 2 et docs/Product/portfolio-card-review/) :
 *   - rendu d'une carte par client (nom + titre du point prioritaire)
 *   - tri des cartes tel que retourné par le backend (déjà trié)
 *   - contexte temporel toujours affiché, jamais d'injonction non prouvable
 *   - compteur affiché uniquement si other_active_count > 0
 *   - why_it_matters affiché uniquement quand why_it_matters_display est fourni
 *   - état vide honnête / échec réseau traités proprement
 *   - "Préparer cette revue" navigue vers /app/chat?entity=<id>
 *   - aucun élément hors périmètre (menu, filtre, score, bouton d'abandon…)
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
      temporal_context: 'Sans décision depuis 45 jours',
      why_it_matters: 'Toujours sans décision confirmée après au moins une revue.',
      questions_to_ask: ['Avez-vous pris une décision sur ce point ?'],
      age_days: 45,
    },
    other_active_count: 0,
    why_it_matters_display: null,
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('PortfolioHome — rendu de base', () => {
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
});

describe('PortfolioHome — contexte temporel (Mission 1)', () => {
  test('le contexte temporel est affiché sur la carte', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard()]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    expect(screen.getByTestId('portfolio-temporal-entity-1')).toHaveTextContent(
      'Sans décision depuis 45 jours'
    );
  });

  test('aucune injonction non prouvable ("à traiter aujourd\'hui", "urgent maintenant") n\'est rendue', async () => {
    mockedFetchPortfolio.mockResolvedValue([
      makeCard(),
      makeCard({
        entity_id: 'e2',
        entity_name: 'Client B',
        top_item: { ...makeCard().top_item, arc_id: 'arc-2' },
      }),
    ]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    const bodyText = document.body.textContent?.toLowerCase() || '';
    for (const forbidden of ['à traiter aujourd\'hui', 'priorité du jour', 'urgent maintenant']) {
      expect(bodyText).not.toContain(forbidden);
    }
  });
});

describe('PortfolioHome — compteur (Mission 2)', () => {
  test('aucun compteur affiché quand other_active_count est 0', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard({ other_active_count: 0 })]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    expect(screen.queryByTestId('portfolio-counter-entity-1')).not.toBeInTheDocument();
  });

  test('compteur affiché et correctement formaté pour plusieurs points', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard({ other_active_count: 2 })]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    expect(screen.getByTestId('portfolio-counter-entity-1')).toHaveTextContent(
      '+2 autres points à suivre'
    );
  });

  test('compteur au singulier pour un seul autre point', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard({ other_active_count: 1 })]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    expect(screen.getByTestId('portfolio-counter-entity-1')).toHaveTextContent(
      '+1 autre point à suivre'
    );
  });
});

describe('PortfolioHome — why_it_matters filtré (Mission 3)', () => {
  test('why_it_matters affiché lorsque why_it_matters_display est fourni (distinct)', async () => {
    mockedFetchPortfolio.mockResolvedValue([
      makeCard({ why_it_matters_display: 'Effet pas encore confirmé dans une analyse.' }),
    ]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    expect(screen.getByTestId('portfolio-why-entity-1')).toHaveTextContent(
      'Effet pas encore confirmé dans une analyse.'
    );
  });

  test('why_it_matters masqué lorsque why_it_matters_display est null (redondant)', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard({ why_it_matters_display: null })]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    expect(screen.queryByTestId('portfolio-why-entity-1')).not.toBeInTheDocument();
    // Le texte brut (non filtré) ne doit pas non plus apparaître par un autre biais.
    expect(
      screen.queryByText('Toujours sans décision confirmée après au moins une revue.')
    ).not.toBeInTheDocument();
  });
});

describe('PortfolioHome — périmètre strict de la carte (Mission 6)', () => {
  test('aucun élément hors périmètre (menu, filtre, score, bouton d\'abandon)', async () => {
    mockedFetchPortfolio.mockResolvedValue([makeCard()]);
    render(<PortfolioHome />);
    await screen.findByText('Client A');

    expect(screen.queryByText('Ne plus suivre')).not.toBeInTheDocument();
    expect(screen.queryByRole('searchbox')).not.toBeInTheDocument();
    // Une seule action doit exister sur la carte.
    expect(screen.getAllByRole('button')).toHaveLength(1);
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
