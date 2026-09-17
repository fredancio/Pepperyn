import { syntheticInspectionSummary } from './synthetic-inspection-summary';
import type { V1SyntheticWorkbookInspection } from './api';

const base: V1SyntheticWorkbookInspection = {
  filename: 'synthetic.xlsx', source_sha256: 'A'.repeat(64), status: 'CONTRADICTION',
  current_period: '2031', facts: [], unknowns: [], provider_dispatch: 'CLOSED',
  conflicting_metrics: ['REVENUE'],
  source_claims: [721, 804].map((value, index) => ({
    fact_id: `F${index}`, metric: 'REVENUE', value, unit: 'EUR', period: '2031',
    source_sheet_ref: 'S1', source_field: `R${index}`,
  })),
};

test('shows both claims and exact references without choosing a canonical value', () => {
  const result = syntheticInspectionSummary({ ...base, discrepancies: [{ metric: 'REVENUE',
    claim_ids: ['F0', 'F1'], absolute_spread: '83', interpretation: 'DISCREPANCY_NOT_RESOLUTION' }] });
  expect(result).toContain('aucune valeur retenue comme vérité canonique');
  expect(result).toContain('721 EUR'); expect(result).toContain('804 EUR');
  expect(result).toContain('F0 / S1 / R0'); expect(result).toContain('F1 / S1 / R1');
  expect(result).toContain('Investigation requise');
  expect(result).toContain('83 (même unité)');
  expect(result).toContain("Mesure de l'écart, pas résolution");
  expect(result).not.toContain('faits gouvernés');
});

test('independent observations are retained but not validated automatically', () => {
  const result = syntheticInspectionSummary({ ...base, source_claims: [...base.source_claims!, {
    fact_id: 'F2', metric: 'CASH', value: 19, unit: 'EUR', period: '2031',
    source_sheet_ref: 'S1', source_field: 'R2',
  }] });
  expect(result).toContain('Observation de source indépendante du conflit (non validée) — CASH : 19 EUR');
});

test('ambiguity remains distinct and successful summary remains unchanged', () => {
  expect(syntheticInspectionSummary({ ...base, status: 'AMBIGUOUS', unknowns: ['numeric uncertainty'] }))
    .toBe('Compréhension ambiguous : numeric uncertainty');
  expect(syntheticInspectionSummary({ ...base, status: 'UNDERSTOOD', facts: [{ metric: 'CASH', value: 19, unit: 'EUR' }] }))
    .toBe('Compréhension établie pour 2031 : 1 faits gouvernés.');
});
