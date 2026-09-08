import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { FeedbackCard } from '../FeedbackCard';
import { submitV1GovernedDecision, submitV1GovernedIntention } from '@/lib/api';

jest.mock('@/lib/api', () => ({
  submitDecisionFeedback: jest.fn(),
  submitV1GovernedIntention: jest.fn(),
  submitV1GovernedDecision: jest.fn(),
}));

const mockedSubmit = submitV1GovernedIntention as jest.Mock;
const mockedDecision = submitV1GovernedDecision as jest.Mock;

const recommendation = {
  id: 'governed-rec-1',
  text: 'Valider la marge avant toute action commerciale.',
  rationale: 'La marge observée doit être rapprochée des écritures sources.',
  fact_ids: ['FACT-REVENUE-2025'],
  prerequisite_validation: ['Confirmer le périmètre de marge avec le Fondateur.'],
  source: 'plan_action',
  priority: 'haute' as const,
  index: 0,
};

beforeEach(() => {
  jest.clearAllMocks();
  mockedSubmit.mockResolvedValue({ success: true, arc_created: false });
  mockedDecision.mockResolvedValue({ success: true, decision_confirmed: true, arc_created: false });
});

test('présente le feedback V1 comme une intention et jamais comme une décision confirmée', async () => {
  render(<FeedbackCard reportId="analysis-1" recommendations={[recommendation]} governedV1 />);

  expect(screen.getByText('Quelle est votre intention ?')).toBeInTheDocument();
  expect(screen.getByText(/jamais comme une décision confirmée/i)).toBeInTheDocument();
  expect(screen.getByText(/La marge observée doit être rapprochée/)).toBeInTheDocument();
  expect(screen.getByText('Validations requises avant toute décision')).toBeInTheDocument();
  expect(screen.getByText('Confirmer le périmètre de marge avec le Fondateur.')).toBeInTheDocument();
  expect(screen.getByText(/FACT-REVENUE-2025/)).toBeInTheDocument();

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
  expect(screen.getByText('Formaliser une décision professionnelle')).toBeInTheDocument();
});

test('confirme explicitement une décision conditionnelle et conserve les validations', async () => {
  render(<FeedbackCard reportId="analysis-1" recommendations={[{ ...recommendation, status: 'unsure' }]} governedV1 />);
  fireEvent.click(screen.getByRole('button', { name: 'Retenir sous conditions' }));
  fireEvent.change(screen.getByLabelText('Motivation de la décision'), {
    target: { value: 'Retenir après rapprochement des écritures.' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Confirmer explicitement la décision' }));
  expect(screen.getByText('Confirmez que les validations restent requises.')).toBeInTheDocument();
  expect(mockedDecision).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: 'Confirmer explicitement la décision' }));
  await waitFor(() => expect(mockedDecision).toHaveBeenCalledWith({
    analysis_id: 'analysis-1',
    recommendation_id: 'governed-rec-1',
    decision_kind: 'accepted_conditional',
    decision_text: 'Retenir après rapprochement des écritures.',
    prerequisites_acknowledged: true,
  }));
  expect(await screen.findByText('Décision professionnelle confirmée explicitement')).toBeInTheDocument();
  expect(screen.getByText('Aucun arc décisionnel n’a été créé.')).toBeInTheDocument();
});

test('réaffiche une décision persistée sans contrôle de mutation', () => {
  render(<FeedbackCard reportId="analysis-1" recommendations={[{
    ...recommendation,
    status: 'decided',
    decision_kind: 'modified',
    decision_text: 'Adapter le calendrier après validation.',
    decision_confirmed_at: '2026-09-08T10:00:00Z',
    decision_confirmation_source: 'explicit',
    prerequisites_acknowledged: true,
  }]} governedV1 />);
  expect(screen.getByText('Décision professionnelle confirmée explicitement')).toBeInTheDocument();
  expect(screen.getByText('Adapter le calendrier après validation.')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Confirmer explicitement la décision' })).not.toBeInTheDocument();
});
