import { listSourceDossiers, loadSourceDossier, captureSourceDossier } from './source-dossiers';
jest.mock('./api', () => ({ getAuthHeaders: async () => ({ Authorization: 'Bearer test' }) }));
const entity = '30000000-0000-0000-0000-000000000001';
const row = { dossier_id: '50000000-0000-0000-0000-000000000001', entity_id: entity,
  company_id: '20000000-0000-0000-0000-000000000001', engagement_id: '40000000-0000-0000-0000-000000000001',
  filename: 'synthetic.xlsx', source_sha256: 'A'.repeat(64), payload_sha256: 'B'.repeat(64),
  evidence_role: 'SOURCE_INSPECTION_NOT_ANALYSIS', schema_version: 'synthetic-source-dossier-1',
  provider_dispatch: 'CLOSED', status: 'AMBIGUOUS', facts: [], unknowns: ['unclear'],
  source_claims: [], conflicting_metrics: [], discrepancies: [] };
beforeEach(() => { global.fetch = jest.fn(); });
function respond(value: unknown, ok = true) { (fetch as jest.Mock).mockResolvedValue({ ok, json: async () => value }); }
test('exact scope and ID required on reload', async () => {
  respond(row); expect(await loadSourceDossier(entity, row.dossier_id)).toEqual(row);
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining(`entity_id=${entity}`), expect.objectContaining({ cache: 'no-store' }));
  await expect(loadSourceDossier(entity, 'other')).rejects.toThrow();
  await expect(loadSourceDossier('foreign', row.dossier_id)).rejects.toThrow();
});
test('malformed list and unavailable response never become empty', async () => {
  for (const value of [null, {}, [row, row], [{ ...row, entity_id: 'foreign' }]]) {
    respond(value); await expect(listSourceDossiers(entity)).rejects.toThrow();
  }
  respond([], false); await expect(listSourceDossiers(entity)).rejects.toThrow();
});
test('capture binds selected entity without caller-controlled company or analysis', async () => {
  respond(row); await captureSourceDossier(entity, new File(['test'], 'synthetic.xlsx'));
  const options = (fetch as jest.Mock).mock.calls[0][1];
  expect(options.method).toBe('POST'); expect(options.body.get('entity_id')).toBe(entity);
  expect(options.body.has('company_id')).toBe(false); expect(options.body.has('analysis_id')).toBe(false);
});
