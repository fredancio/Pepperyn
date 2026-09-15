import { fetchGovernedTemporalComparison } from './governed-temporal-api';
jest.mock('./api', () => ({ getAuthHeaders: async () => ({ Authorization: 'Bearer synthetic' }) }));
const valid = { status: 'UNKNOWN', current_analysis_id: 'a', previous_analysis_id: null,
  previous_period: null, current_period: '2025', changes: [], unknowns: ['Aucune période antérieure'],
  contradictions: [], causal_interpretation: null };

test('uses authenticated GET and preserves UNKNOWN', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => valid });
  expect(await fetchGovernedTemporalComparison('a')).toEqual(valid);
  expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/a/temporal-comparison'),
    { headers: { Authorization: 'Bearer synthetic' } });
});

test.each([
  { current_analysis_id: 'foreign' }, { causal_interpretation: 'invented cause' },
  { status: 'invented' }, { unknowns: null }, { changes: [{ metric: 'CASH' }] },
])('rejects mismatched or malformed response %j', async patch => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ ...valid, ...patch }) });
  await expect(fetchGovernedTemporalComparison('a')).rejects.toThrow();
});

test('503 is not converted into empty changes', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: false });
  await expect(fetchGovernedTemporalComparison('a')).rejects.toThrow('indisponible');
});
