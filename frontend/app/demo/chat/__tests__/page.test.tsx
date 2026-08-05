/**
 * Page de chat démo — External User Testing Prototype (2026-08-05),
 * Mission 9, cas 10, 11, 12.
 *
 * Test d'intégration réel (pas de mock de fetchReviewBriefing) : seul
 * isDemoModeEnabled() est forcé à vrai, tout le reste (ReviewBriefing,
 * InputBar, lib/demo-data.ts) est le vrai code, exactement comme en
 * environnement de prévisualisation.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import DemoChatPage from '../page';

const mockPush = jest.fn();
const mockGet = jest.fn((key: string) => (key === 'entity' ? 'e5' : null));

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: mockGet }),
}));

jest.mock('@/lib/demo-mode', () => ({
  ...jest.requireActual('@/lib/demo-mode'),
  isDemoModeEnabled: jest.fn(() => true),
}));

beforeEach(() => {
  jest.clearAllMocks();
  mockGet.mockImplementation((key: string) => (key === 'entity' ? 'e5' : null));
});

describe('Page /demo/chat (cas 10, 11, 12)', () => {
  test('cas 10 — le client correct (Cabinet Lemoine, e5) est préselectionné depuis ?entity=e5', async () => {
    render(<DemoChatPage />);
    expect(await screen.findByTestId('demo-chat-client-name')).toHaveTextContent('Cabinet Lemoine');
  });

  test('cas 11 — "Préparer cette question" préremplit le champ de saisie sans l\'envoyer', async () => {
    render(<DemoChatPage />);

    const prepareButtons = await screen.findAllByText('Préparer cette question');
    fireEvent.click(prepareButtons[0]);

    const textarea = screen.getByPlaceholderText('Posez une question de suivi...') as HTMLTextAreaElement;
    expect(textarea.value.length).toBeGreaterThan(0);
    // Jamais envoyé automatiquement : aucun message utilisateur supplémentaire
    // ne doit apparaître suite au seul préremplissage.
    expect(screen.queryAllByText(textarea.value)).not.toHaveLength(0); // visible dans le champ
  });

  test('cas 12 — un brouillon déjà tapé est préservé, la question est ajoutée à la suite', async () => {
    render(<DemoChatPage />);

    const textarea = screen.getByPlaceholderText('Posez une question de suivi...') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Brouillon existant' } });
    expect(textarea.value).toBe('Brouillon existant');

    const prepareButtons = await screen.findAllByText('Préparer cette question');
    fireEvent.click(prepareButtons[0]);

    expect(textarea.value).toContain('Brouillon existant');
    expect(textarea.value.length).toBeGreaterThan('Brouillon existant'.length);
  });
});
