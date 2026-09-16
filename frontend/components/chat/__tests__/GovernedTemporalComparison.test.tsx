import { render, screen, waitFor } from '@testing-library/react';
import { GovernedTemporalComparison } from '../GovernedTemporalComparison';
import { fetchGovernedTemporalComparison } from '@/lib/governed-temporal-api';
jest.mock('@/lib/governed-temporal-api', () => ({ fetchGovernedTemporalComparison: jest.fn() }));
const fetchComparison = fetchGovernedTemporalComparison as jest.Mock;
const base = { status: 'UNKNOWN', current_analysis_id: 'a', previous_analysis_id: null,
  previous_period: null, current_period: '2025', changes: [], unknowns: ['Aucune période antérieure'], contradictions: [] };
beforeEach(() => jest.resetAllMocks());

test('unknown is visible, without a numeric table', async () => {
  fetchComparison.mockResolvedValue(base);
  render(<GovernedTemporalComparison analysisId="a" />);
  expect(await screen.findByText(/non établie/)).toBeInTheDocument();
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
});

test('failure is not no change', async () => {
  fetchComparison.mockRejectedValue(new Error('private details'));
  render(<GovernedTemporalComparison analysisId="a" />);
  expect(await screen.findByRole('alert')).toHaveTextContent('indisponible');
  expect(screen.queryByText('private details')).not.toBeInTheDocument();
});

test('partial comparison retains unknowns and provenance', async () => {
  fetchComparison.mockResolvedValue({ ...base, status: 'PARTIALLY_COMPARABLE', previous_analysis_id: 'old',
    previous_period: '2024', unknowns: ['REVENUE absent'], changes: [{ metric: 'CASH', unit: 'EUR',
      previous_value: 20, current_value: 10, absolute_change: -10, previous_fact_id: 'FOLD', current_fact_id: 'FNEW' }] });
  render(<GovernedTemporalComparison analysisId="a" />);
  expect(await screen.findByRole('table')).toHaveTextContent('-10 EUR');
  expect(screen.getByText('REVENUE absent')).toBeInTheDocument();
  expect(screen.getByText('FOLD → FNEW')).toBeInTheDocument();
  expect(screen.getByText(/Ni explication causale/)).toBeInTheDocument();
  expect(screen.getByText(/Durée, couverture, périmètre/)).toHaveTextContent('non établis');
});

test('a refused financial period pairing renders its reason and no delta table', async () => {
  fetchComparison.mockResolvedValue({ ...base, unknowns: ['Le rapprochement des libellés calendaires et fiscaux n’est pas établi.'] });
  render(<GovernedTemporalComparison analysisId="a" />);
  expect(await screen.findByText(/calendaires et fiscaux/)).toBeInTheDocument();
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
});

test('late response from previous analysis cannot overwrite selected analysis', async () => {
  let resolveOld!: (value: unknown) => void;
  fetchComparison.mockImplementation((id: string) => id === 'a' ? new Promise(resolve => { resolveOld = resolve; }) :
    Promise.resolve({ ...base, current_analysis_id: 'b', unknowns: ['Client B'] }));
  const { rerender } = render(<GovernedTemporalComparison analysisId="a" />);
  rerender(<GovernedTemporalComparison analysisId="b" />);
  expect(await screen.findByText('Client B')).toBeInTheDocument();
  resolveOld({ ...base, unknowns: ['Client A stale'] });
  await waitFor(() => expect(screen.queryByText('Client A stale')).not.toBeInTheDocument());
});
