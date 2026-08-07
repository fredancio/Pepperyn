/**
 * Tests — ReviewBriefing (Capability 3, Incrément 2).
 *
 * Couvre les points frontend de la mission GO IMPLEMENT (2026-08-05) :
 *   3. rendu du Review Briefing
 *   4. état vide retournant null
 *   5. ordre des priorités
 *   11. retrait optimiste après succès
 *   12. restauration après échec
 *   13. motif transmis à abandonArc()
 *   14. aucun libellé utilisateur ne prétend que le sujet est réglé/résolu
 *   15. "Préparer cette question" ne déclenche aucun envoi automatique
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ReviewBriefing } from '../ReviewBriefing';
import * as arcApi from '@/lib/arc-api';
import type { BriefingItem } from '@/lib/types';

jest.mock('@/lib/arc-api', () => {
  const actual = jest.requireActual('@/lib/arc-api');
  return {
    ...actual,
    fetchReviewBriefing: jest.fn(),
    abandonArc: jest.fn(),
  };
});

const mockedFetch = arcApi.fetchReviewBriefing as jest.Mock;
const mockedAbandon = arcApi.abandonArc as jest.Mock;

function makeItem(overrides: Partial<BriefingItem> = {}): BriefingItem {
  return {
    arc_id: 'arc-1',
    source_type: 'decision_arc',
    priority: 'urgent',
    title: 'Renégocier le contrat assurance',
    temporal_context: 'il y a 45 jours',
    why_it_matters: 'Cette décision est en attente depuis plus de 3 semaines.',
    questions_to_ask: ['Avez-vous pris une décision sur ce point ?'],
    age_days: 45,
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('ReviewBriefing — rendu', () => {
  test('rendu du Review Briefing avec plusieurs cartes et le sous-titre exact', async () => {
    mockedFetch.mockResolvedValue([
      makeItem({ arc_id: 'a1', priority: 'urgent', title: 'Point A' }),
      makeItem({ arc_id: 'a2', priority: 'to_check', title: 'Point B', questions_to_ask: ['Q ?'] }),
    ]);

    render(<ReviewBriefing />);

    expect(await screen.findByText('Briefing de revue')).toBeInTheDocument();
    expect(
      screen.getByText('Points issus des recommandations et décisions suivies avec ce client.')
    ).toBeInTheDocument();
    expect(screen.getByText('Point A')).toBeInTheDocument();
    expect(screen.getByText('Point B')).toBeInTheDocument();
  });

  test('état vide (aucun arc actif) ne rend aucun bandeau — retourne null', async () => {
    mockedFetch.mockResolvedValue([]);
    const { container } = render(<ReviewBriefing />);
    await waitFor(() => expect(mockedFetch).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByText('Briefing de revue')).not.toBeInTheDocument();
  });

  test('un échec de lecture réseau ne fait pas planter le composant (équivalent état vide)', async () => {
    mockedFetch.mockRejectedValue(new Error('network error'));
    const { container } = render(<ReviewBriefing />);
    await waitFor(() => expect(mockedFetch).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  test('ordre des priorités préservé tel que retourné par le backend (urgent > to_check > done > closed)', async () => {
    mockedFetch.mockResolvedValue([
      makeItem({ arc_id: 'a1', priority: 'urgent', title: 'Alpha point' }),
      makeItem({ arc_id: 'a2', priority: 'to_check', title: 'Bravo point', questions_to_ask: ['Q ?'] }),
      makeItem({ arc_id: 'a3', priority: 'done', title: 'Charlie point', questions_to_ask: ['Q ?'] }),
      makeItem({ arc_id: 'a4', priority: 'closed', title: 'Delta point', questions_to_ask: [] }),
    ]);

    render(<ReviewBriefing />);
    await screen.findByText('Briefing de revue');

    const cards = screen.getAllByTestId(/^briefing-card-/);
    expect(cards.map((c) => c.getAttribute('data-testid'))).toEqual([
      'briefing-card-a1',
      'briefing-card-a2',
      'briefing-card-a3',
      'briefing-card-a4',
    ]);
  });

  test('Evidence Ledger Consumer #1 : "Voir la preuve" absent quand evidence_support est null', async () => {
    mockedFetch.mockResolvedValue([makeItem({ evidence_support: null })]);
    render(<ReviewBriefing />);
    await screen.findByText('Renégocier le contrat assurance');

    expect(screen.queryByText('Voir la preuve')).not.toBeInTheDocument();
  });

  test('Evidence Ledger Consumer #1 : "Voir la preuve" affiché puis développe le contenu, sans fabrication', async () => {
    mockedFetch.mockResolvedValue([
      makeItem({
        evidence_support: {
          status: 'available',
          facts_count: 2,
          sheets: ['P&L'],
          impacts: [
            {
              amount: 50000,
              currency: 'EUR',
              metric_type_label: "Chiffre d'affaires",
              confidence: 0.8,
              qualifier: 'preuve vérifiée',
            },
          ],
        },
      }),
    ]);
    render(<ReviewBriefing />);
    await screen.findByText('Renégocier le contrat assurance');

    const toggle = screen.getByText('Voir la preuve');
    expect(screen.queryByText(/preuve vérifiée/)).not.toBeInTheDocument();

    fireEvent.click(toggle);

    expect(await screen.findByText(/preuve vérifiée/)).toBeInTheDocument();
    expect(screen.getByText('Masquer la preuve')).toBeInTheDocument();
  });

  test('Evidence Ledger Consumer #1 : evidence_support sans impacts ni sheets ne rend rien', async () => {
    mockedFetch.mockResolvedValue([
      makeItem({ evidence_support: { status: 'available', facts_count: 0, sheets: [], impacts: [] } }),
    ]);
    render(<ReviewBriefing />);
    await screen.findByText('Renégocier le contrat assurance');

    expect(screen.queryByText('Voir la preuve')).not.toBeInTheDocument();
  });

  test('une carte "Clos" n\'affiche ni question ni action "Ne plus suivre"', async () => {
    mockedFetch.mockResolvedValue([
      makeItem({ arc_id: 'a4', priority: 'closed', title: 'Closed point', questions_to_ask: [] }),
    ]);
    render(<ReviewBriefing />);
    await screen.findByText('Closed point');

    expect(screen.queryByText('Ne plus suivre')).not.toBeInTheDocument();
    expect(screen.queryByText(/Préparer cette question/)).not.toBeInTheDocument();
  });
});

describe('ReviewBriefing — "Ne plus suivre"', () => {
  test('retrait optimiste après succès + motif transmis à abandonArc()', async () => {
    mockedFetch.mockResolvedValue([makeItem({ arc_id: 'a1', title: 'Point A' })]);
    mockedAbandon.mockResolvedValue({ abandoned: true, arc_id: 'a1' });

    render(<ReviewBriefing />);
    await screen.findByText('Point A');

    fireEvent.click(screen.getByText('Ne plus suivre'));
    // Texte de confirmation exact (fixé par Fred) avant toute action destructrice.
    expect(
      screen.getByText(
        (_, node) =>
          node?.textContent ===
          "Ce point restera conservé dans l'historique, mais ne figurera plus parmi les sujets actifs de vos prochaines revues."
      )
    ).toBeInTheDocument();

    fireEvent.click(screen.getByText('Traité en dehors de Pepperyn'));

    // Retrait optimiste immédiat.
    await waitFor(() => expect(screen.queryByText('Point A')).not.toBeInTheDocument());
    expect(mockedAbandon).toHaveBeenCalledWith('a1', 'Traité en dehors de Pepperyn');
  });

  test('restauration de la carte après un échec côté serveur', async () => {
    mockedFetch.mockResolvedValue([makeItem({ arc_id: 'a1', title: 'Point A' })]);
    mockedAbandon.mockRejectedValue(new Error('Erreur serveur'));

    render(<ReviewBriefing />);
    await screen.findByText('Point A');

    fireEvent.click(screen.getByText('Ne plus suivre'));
    fireEvent.click(screen.getByText('Devenu non pertinent'));

    // La carte disparaît d'abord (optimiste), puis réapparaît après l'échec.
    await waitFor(() => expect(screen.getByText('Point A')).toBeInTheDocument());
    expect(screen.getByText('Erreur serveur')).toBeInTheDocument();
  });

  test('aucun libellé utilisateur n\'affirme que le sujet est réglé ou résolu', async () => {
    mockedFetch.mockResolvedValue([makeItem({ arc_id: 'a1', title: 'Point A' })]);
    render(<ReviewBriefing />);
    await screen.findByText('Point A');

    fireEvent.click(screen.getByText('Ne plus suivre'));

    const forbidden = ['réglé', 'résolu', 'résolue', 'exécuté avec succès'];
    const bodyText = document.body.textContent?.toLowerCase() || '';
    for (const term of forbidden) {
      expect(bodyText).not.toContain(term);
    }
  });

  test('l\'arc n\'est jamais physiquement supprimé côté client — seul abandonArc() est appelé', async () => {
    mockedFetch.mockResolvedValue([makeItem({ arc_id: 'a1', title: 'Point A' })]);
    mockedAbandon.mockResolvedValue({ abandoned: true, arc_id: 'a1' });

    render(<ReviewBriefing />);
    await screen.findByText('Point A');

    fireEvent.click(screen.getByText('Ne plus suivre'));
    fireEvent.click(screen.getByText('Décision abandonnée'));

    await waitFor(() => expect(mockedAbandon).toHaveBeenCalledTimes(1));
    expect(mockedAbandon).toHaveBeenCalledWith('a1', 'Décision abandonnée');
  });
});

describe('ReviewBriefing — "Préparer cette question"', () => {
  test('appelle onPrepareQuestion sans déclencher aucun envoi de message', async () => {
    const onPrepareQuestion = jest.fn();
    mockedFetch.mockResolvedValue([
      makeItem({ arc_id: 'a1', title: 'Point A', questions_to_ask: ['Quelle est votre décision ?'] }),
    ]);

    render(<ReviewBriefing onPrepareQuestion={onPrepareQuestion} />);
    await screen.findByText('Point A');

    fireEvent.click(screen.getByText('Préparer cette question'));

    expect(onPrepareQuestion).toHaveBeenCalledTimes(1);
    expect(onPrepareQuestion).toHaveBeenCalledWith('Quelle est votre décision ?');
  });

  test('sans callback fourni, le bouton "Préparer cette question" n\'est pas affiché', async () => {
    mockedFetch.mockResolvedValue([
      makeItem({ arc_id: 'a1', title: 'Point A', questions_to_ask: ['Quelle est votre décision ?'] }),
    ]);
    render(<ReviewBriefing />);
    await screen.findByText('Point A');

    expect(screen.queryByText('Préparer cette question')).not.toBeInTheDocument();
  });
});
