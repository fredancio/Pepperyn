import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { FeedbackCard } from '../FeedbackCard';
import { submitV1GovernedIntention } from '@/lib/api';

jest.mock('@/lib/api', () => ({
  submitDecisionFeedback: jest.fn(),
  submitV1GovernedIntention: jest.fn(),
}));

const mockedSubmit = submitV1GovernedIntention as jest.Mock;

const recommendation = {
  id: 'governed-rec-1',
  text: 'Valider la marge avant toute action commerciale.',
  source: 'plan_action',
  priority: 'haute' as const,
  index: 0,
};

beforeEach(() => {
  jest.clearAllMocks();
  mockedSubmit.mockResolvedValue({ success: true, arc_created: false });
});

test('présente le feedback V1 comme une intention et jamais comme une décision confirmée', async () => {
  render(<FeedbackCard reportId="analysis-1" recommendations={[recommendation]} governedV1 />);

  expect(screen.getByText('Quelle est votre intention ?')).toBeInTheDocument();
  expect(screen.getByText(/jamais comme une décision confirmée/i)).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Je vais appliquer' }));

  await waitFor(() => expect(mockedSubmit).toHaveBeenCalledWith({
    analysis_id: 'analysis-1',
    recommendation_id: 'governed-rec-1',
    status: 'planned',
    comment: undefined,
  }));
  expect(await screen.findByText('Intention enregistrée — aucune décision confirmée.')).toBeInTheDocument();
  expect(screen.queryByText('Décision tracée')).not.toBeInTheDocument();
});

test('réaffiche une intention gouvernée persistée sans la transformer en décision', () => {
  render(<FeedbackCard
    reportId="analysis-1"
    recommendations={[{ ...recommendation, status: 'planned' }]}
    governedV1
  />);

  expect(screen.getByText('Intention enregistrée — aucune décision confirmée.')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Je vais appliquer' })).not.toBeInTheDocument();
  expect(screen.queryByText('Décision tracée')).not.toBeInTheDocument();
});
