import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ChatContainer } from '../ChatContainer';
import * as api from '@/lib/api';
import { supabase } from '@/lib/supabase';
jest.mock('@/lib/api');
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), useSearchParams: () => ({ get: () => null }) }));
jest.mock('@/lib/auth', () => ({ getCurrentAuthMode: async () => 'guest', getGuestPlan: () => 'pro' }));
jest.mock('@/lib/supabase', () => ({ supabase: { from: jest.fn() } }));
jest.mock('../MessageBubble', () => {
  process.env.NEXT_PUBLIC_ENABLE_SYNTHETIC_V1_DEMO = '1';
  return { MessageBubble: ({ message }: { message: { content: string; content_type: string; metadata?: { id?: string } } }) =>
    <div data-testid={message.content_type}>{message.metadata?.id || message.content}</div>, TypingIndicator: () => null };
});
jest.mock('../InputBar', () => ({ InputBar: () => null }));
jest.mock('../ReviewBriefing', () => ({ ReviewBriefing: () => null }));
jest.mock('@/components/ui/PwaInstallButton', () => ({ PwaInstallButton: () => null }));
jest.mock('@/components/ui/UpgradeModal', () => ({ UpgradeModal: () => null }));
jest.mock('@/components/ui/CreditsModal', () => ({ CreditsModal: () => null }));

beforeEach(() => {
  jest.resetAllMocks();
  Element.prototype.scrollIntoView = jest.fn();
  (api.fetchAnalysesHistory as jest.Mock).mockResolvedValue([]);
  (api.fetchBillingUsage as jest.Mock).mockResolvedValue(null);
});

test('unavailable list has no fictitious primary client and retry only reads', async () => {
  (api.fetchEntities as jest.Mock).mockRejectedValueOnce(new Error('private')).mockResolvedValueOnce([]);
  render(<ChatContainer />);
  expect(await screen.findByText(/Liste des clients indisponible/)).toBeInTheDocument();
  expect(screen.queryByText('Entreprise principale')).not.toBeInTheDocument();
  fireEvent.click(screen.getByText('Réessayer la lecture'));
  expect(await screen.findByText('Aucun client enregistré.')).toBeInTheDocument();
  expect(api.createEntity).not.toHaveBeenCalled();
});

test('confirmed creation followed by failed refresh closes creation form and retry cannot recreate', async () => {
  (api.fetchEntities as jest.Mock).mockResolvedValueOnce([]).mockRejectedValueOnce(new Error('unavailable')).mockResolvedValueOnce([]);
  (api.createEntity as jest.Mock).mockResolvedValue({ id: 'synthetic', name: 'Synthetic' });
  render(<ChatContainer />);
  await screen.findByText('Aucun client enregistré.');
  fireEvent.click(screen.getByText('Ajouter un client ou une entreprise'));
  fireEvent.change(screen.getByPlaceholderText("Nom du client ou de l'entreprise..."), { target: { value: 'Synthetic' } });
  fireEvent.click(screen.getByText('Client suivi'));
  fireEvent.click(screen.getByText('Créer'));
  await screen.findByText(/Liste des clients indisponible/);
  expect(screen.queryByText('Créer')).not.toBeInTheDocument();
  fireEvent.click(screen.getByText('Réessayer la lecture'));
  await waitFor(() => expect(api.fetchEntities).toHaveBeenCalledTimes(3));
  expect(api.createEntity).toHaveBeenCalledTimes(1);
});

const history = [
  { id: 'a', fichier_nom: 'Analysis A', created_at: '2026-01-01' },
  { id: 'b', fichier_nom: 'Analysis B', created_at: '2026-01-02' },
];

test('late governed result cannot replace the newly opened analysis', async () => {
  let resolveA!: (value: unknown) => void;
  (api.fetchEntities as jest.Mock).mockResolvedValue([]);
  (api.fetchAnalysesHistory as jest.Mock).mockResolvedValue(history);
  (api.fetchV1GovernedAnalysis as jest.Mock).mockImplementation((id: string) => id === 'a'
    ? new Promise(resolve => { resolveA = resolve; }) : Promise.resolve({ analyse_id: 'b', result: {} }));
  render(<ChatContainer />);
  fireEvent.click(await screen.findByText('Analysis A'));
  fireEvent.click(screen.getByText('Analysis B'));
  expect(await screen.findByTestId('analysis')).toHaveTextContent('b');
  await act(async () => { resolveA({ analyse_id: 'a', result: {} }); });
  expect(screen.getByTestId('analysis')).toHaveTextContent('b');
});

test('failed governed read never falls back to legacy messages', async () => {
  (api.fetchEntities as jest.Mock).mockResolvedValue([]);
  (api.fetchAnalysesHistory as jest.Mock).mockResolvedValue(history);
  (api.fetchV1GovernedAnalysis as jest.Mock).mockRejectedValue(new Error('private database detail'));
  render(<ChatContainer />);
  fireEvent.click(await screen.findByText('Analysis A'));
  expect(await screen.findByTestId('error')).toHaveTextContent('aucun résultat de remplacement');
  expect(supabase.from).not.toHaveBeenCalled();
  expect(screen.queryByText('private database detail')).not.toBeInTheDocument();
});

test('late failed read cannot erase a successful newer analysis', async () => {
  let rejectA!: (reason: Error) => void;
  (api.fetchEntities as jest.Mock).mockResolvedValue([]);
  (api.fetchAnalysesHistory as jest.Mock).mockResolvedValue(history);
  (api.fetchV1GovernedAnalysis as jest.Mock).mockImplementation((id: string) => id === 'a'
    ? new Promise((_, reject) => { rejectA = reject; }) : Promise.resolve({ analyse_id: 'b', result: {} }));
  render(<ChatContainer />);
  fireEvent.click(await screen.findByText('Analysis A'));
  fireEvent.click(screen.getByText('Analysis B'));
  expect(await screen.findByTestId('analysis')).toHaveTextContent('b');
  await act(async () => { rejectA(new Error('late private error')); });
  expect(screen.getByTestId('analysis')).toHaveTextContent('b');
  expect(screen.queryByTestId('error')).not.toBeInTheDocument();
  expect(supabase.from).not.toHaveBeenCalled();
});

test('new analysis invalidates a pending stored result without new writes', async () => {
  let resolve!: (value: unknown) => void;
  (api.fetchEntities as jest.Mock).mockResolvedValue([]);
  (api.fetchAnalysesHistory as jest.Mock).mockResolvedValue(history);
  (api.fetchV1GovernedAnalysis as jest.Mock).mockImplementation(() => new Promise(r => { resolve = r; }));
  render(<ChatContainer />);
  fireEvent.click(await screen.findByText('Analysis A'));
  fireEvent.click(screen.getByText('Nouvelle analyse'));
  await act(async () => { resolve({ analyse_id: 'a', result: {} }); });
  expect(screen.queryByTestId('analysis')).not.toBeInTheDocument();
  expect(api.analyzeV1SyntheticWorkbook).not.toHaveBeenCalled();
});

test('switching client suppresses an in-flight mock result without repeating the analysis', async () => {
  let resolve!: (value: unknown) => void;
  (api.fetchEntities as jest.Mock).mockResolvedValue([{ id: 'client-b', name: 'Client B', is_primary: false }]);
  (api.analyzeV1SyntheticWorkbook as jest.Mock).mockImplementation(() => new Promise(r => { resolve = r; }));
  render(<ChatContainer />);
  await screen.findByText('Client B');
  const button = screen.getByText('Analyser le classeur English via le fournisseur simulé');
  const input = button.previousElementSibling as HTMLInputElement;
  expect(input.type).toBe('file');
  fireEvent.change(input, { target: { files: [new File(['synthetic'], 'fixture.xlsx')] } });
  fireEvent.click(screen.getByText('Client B'));
  await act(async () => { resolve({ analyse_id: 'old-client-analysis', result: {} }); });
  expect(screen.queryByTestId('analysis')).not.toBeInTheDocument();
  expect(api.analyzeV1SyntheticWorkbook).toHaveBeenCalledTimes(1);
  expect(api.analyzeV1SyntheticWorkbook).toHaveBeenCalledWith(expect.any(File), undefined);
});

test.each(['demo', 'inspection'])('new conversation suppresses pending %s result', async kind => {
  let resolve!: (value: unknown) => void;
  (api.fetchEntities as jest.Mock).mockResolvedValue([]);
  const operation = (kind === 'demo' ? api.runV1SyntheticDemo : api.inspectV1SyntheticWorkbook) as jest.Mock;
  operation.mockImplementation(() => new Promise(r => { resolve = r; }));
  render(<ChatContainer />);
  await screen.findByText('Aucun client enregistré.');
  if (kind === 'demo') {
    fireEvent.click(screen.getByText('Lancer la démonstration V1 synthétique'));
  } else {
    const input = screen.getByText('Tester un classeur synthétique V1 enregistré').previousElementSibling as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['synthetic'], 'fixture.xlsx')] } });
  }
  fireEvent.click(screen.getByText('Nouvelle analyse'));
  await act(async () => { resolve(kind === 'demo' ? { analyse_id: 'old-demo', result: {} }
    : { status: 'UNDERSTOOD', current_period: '2025', facts: [] }); });
  expect(screen.queryByTestId('analysis')).not.toBeInTheDocument();
  expect(screen.queryByText(/Inspection synthétique V1 —/)).not.toBeInTheDocument();
  expect(operation).toHaveBeenCalledTimes(1);
});
