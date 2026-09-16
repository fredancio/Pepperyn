import { fetchGovernedTemporalComparison } from './governed-temporal-api';
jest.mock('./api', () => ({ getAuthHeaders: async () => ({ Authorization: 'Bearer synthetic' }) }));
const valid = { status: 'UNKNOWN', current_analysis_id: 'a', previous_analysis_id: null,
  previous_period: null, current_period: '2025', changes: [], unknowns: ['Aucune période antérieure'],
  contradictions: [], causal_interpretation: null,
  comparison_scope: 'ANNUAL_LABEL_ARITHMETIC_ONLY', financial_comparability: 'NOT_ESTABLISHED' };

test('uses authenticated GET and preserves UNKNOWN', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => valid });
  expect(await fetchGovernedTemporalComparison('a')).toEqual(valid);
  expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/a/temporal-comparison'),
    { headers: { Authorization: 'Bearer synthetic' } });
});

test.each([
  { current_analysis_id: 'foreign' }, { causal_interpretation: 'invented cause' },
  { status: 'invented' }, { unknowns: null }, { changes: [{ metric: 'CASH' }] },
  { comparison_scope: undefined }, { financial_comparability: 'CERTIFIED' },
  { status: 'COMPARABLE' },
])('rejects mismatched or malformed response %j', async patch => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ ...valid, ...patch }) });
  await expect(fetchGovernedTemporalComparison('a')).rejects.toThrow();
});

test('unsafe browser numeric range is refused rather than silently rounded', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ ...valid,
    status: 'COMPARABLE', unknowns: [], previous_analysis_id: 'old', previous_period: '2024',
    changes: [{ metric: 'CASH', unit: 'EUR', previous_fact_id: 'FOLD', current_fact_id: 'FNEW',
      previous_value: 10 ** 30, current_value: 0, absolute_change: -(10 ** 30) }],
  }) });
  await expect(fetchGovernedTemporalComparison('a')).rejects.toThrow('non vérifiable');
});

test('503 is not converted into empty changes', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: false });
  await expect(fetchGovernedTemporalComparison('a')).rejects.toThrow('indisponible');
});
