import { fireEvent, render, screen } from '@testing-library/react';
import { ChatContainer } from '../ChatContainer';
import * as api from '@/lib/api';
import { supabase } from '@/lib/supabase';
jest.mock('@/lib/api');
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), useSearchParams: () => ({ get: () => null }) }));
jest.mock('@/lib/auth', () => ({ getCurrentAuthMode: async () => 'guest', getGuestPlan: () => 'pro' }));
jest.mock('@/lib/supabase', () => ({ supabase: { from: jest.fn() } }));
jest.mock('../MessageBubble', () => {
  process.env.NEXT_PUBLIC_ENABLE_SYNTHETIC_V1_DEMO = '0';
  return { MessageBubble: ({ message }: { message: { content: string } }) => <div>{message.content}</div>, TypingIndicator: () => null };
});
jest.mock('../InputBar', () => ({ InputBar: () => null }));
jest.mock('../ReviewBriefing', () => ({ ReviewBriefing: () => null }));
jest.mock('@/components/ui/PwaInstallButton', () => ({ PwaInstallButton: () => null }));
jest.mock('@/components/ui/UpgradeModal', () => ({ UpgradeModal: () => null }));
jest.mock('@/components/ui/CreditsModal', () => ({ CreditsModal: () => null }));

test.each([false, true])('legacy read stays available outside synthetic mode; failure=%s', async failed => {
  jest.resetAllMocks();
  Element.prototype.scrollIntoView = jest.fn();
  (api.fetchEntities as jest.Mock).mockResolvedValue([]);
  (api.fetchBillingUsage as jest.Mock).mockResolvedValue(null);
  (api.fetchAnalysesHistory as jest.Mock).mockResolvedValue([{ id: 'legacy', fichier_nom: 'Legacy history', created_at: '2026-01-01' }]);
  const order = jest.fn().mockResolvedValue(failed ? { data: null, error: { message: 'private' } }
    : { data: [{ id: 'm', content_type: 'text', content: 'Stored synthetic legacy message' }], error: null });
  (supabase.from as jest.Mock).mockReturnValue({ select: () => ({ eq: () => ({ order }) }) });
  render(<ChatContainer />);
  fireEvent.click(await screen.findByText('Legacy history'));
  if (failed) expect(await screen.findByText(/Analyse indisponible/)).toBeInTheDocument();
  else expect(await screen.findByText('Stored synthetic legacy message')).toBeInTheDocument();
  expect(supabase.from).toHaveBeenCalledWith('messages');
  expect(api.fetchV1GovernedAnalysis).not.toHaveBeenCalled();
});
