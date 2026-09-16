import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ChatContainer } from '../ChatContainer';
import * as api from '@/lib/api';
jest.mock('@/lib/api');
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), useSearchParams: () => ({ get: () => null }) }));
jest.mock('@/lib/auth', () => ({ getCurrentAuthMode: async () => 'guest', getGuestPlan: () => 'pro' }));
jest.mock('@/lib/supabase', () => ({ supabase: {} }));
jest.mock('../MessageBubble', () => ({ MessageBubble: () => null, TypingIndicator: () => null }));
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
