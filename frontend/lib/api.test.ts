import { analyzeV1SyntheticWorkbook, inspectV1SyntheticWorkbook, runV1SyntheticDemo, fetchEntities, createEntity, fetchV1GovernedAnalysis } from './api';

jest.mock('./supabase', () => ({
  supabase: {
    auth: { getSession: jest.fn().mockResolvedValue({ data: { session: null } }) },
  },
}));

describe('client-list availability', () => {
  beforeEach(() => sessionStorage.clear());
  test.each([{ success: false, data: [] }, { success: true, data: {} }, { success: true, data: [{ name: 'Synthetic' }] }])('rejects unverified list %j', async body => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => body });
    await expect(fetchEntities()).rejects.toThrow();
  });
  test('503 refuses while successful empty remains empty', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({ ok: false }).mockResolvedValueOnce({ ok: true, json: async () => ({ success: true, data: [] }) });
    await expect(fetchEntities()).rejects.toThrow('indisponible');
    await expect(fetchEntities()).resolves.toEqual([]);
  });
  test('creation returns the confirmed entity rather than its response wrapper', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ success: true, data: { id: 'synthetic', name: 'Synthetic' } }) });
    await expect(createEntity('Synthetic', 'client')).resolves.toEqual({ id: 'synthetic', name: 'Synthetic' });
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });
});

test.each([{ analyse_id: 'foreign', result: {} }, { analyse_id: 'expected', result: null }, { analyse_id: 'expected', result: [] }])('governed read rejects mismatched or absent result %j', async body => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => body });
  await expect(fetchV1GovernedAnalysis('expected')).rejects.toThrow('non vérifiable');
});

test('governed read preserves matching result and makes only one GET', async () => {
  const body = { analyse_id: 'expected', result: { verification_tag: 'V1_GOVERNED_SINGLE_CALL' } };
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => body });
  await expect(fetchV1GovernedAnalysis('expected')).resolves.toEqual(body);
  expect(global.fetch).toHaveBeenCalledTimes(1);
});

describe('synthetic client selection', () => {
  it('sends the selected client with the synthetic workbook', async () => {
    sessionStorage.clear();
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    await analyzeV1SyntheticWorkbook(new File(['synthetic'], 'fixture.xlsx'), 'client-b');
    const [, request] = (global.fetch as jest.Mock).mock.calls[0];
    expect(request.body.get('entity_id')).toBe('client-b');
    expect(request.body.get('file').name).toBe('fixture.xlsx');
  });
});

describe('runV1SyntheticDemo', () => {
  beforeEach(() => {
    sessionStorage.clear();
    global.fetch = jest.fn();
  });

  it('turns a browser network rejection into a safe actionable message', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(runV1SyntheticDemo()).rejects.toThrow(
      'Impossible de joindre le serveur Pepperyn. Vérifiez que le service est démarré puis réessayez.',
    );
  });

  it('preserves an intentional bounded backend refusal', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: jest.fn().mockResolvedValue({
        detail: 'Démonstration synthétique indisponible pour cette entreprise.',
      }),
    });

    await expect(runV1SyntheticDemo()).rejects.toThrow(
      'Démonstration synthétique indisponible pour cette entreprise.',
    );
  });
});

describe('inspectV1SyntheticWorkbook', () => {
  beforeEach(() => {
    sessionStorage.clear();
    global.fetch = jest.fn();
  });

  it('uploads through the dedicated closed synthetic endpoint', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({
        filename: 'pepperyn_v1_heterogeneous_english.xlsx',
        status: 'UNDERSTOOD', current_period: '2025', facts: [], unknowns: [],
        source_sha256: 'A'.repeat(64), provider_dispatch: 'CLOSED',
      }),
    });
    const file = new File(['synthetic'], 'pepperyn_v1_heterogeneous_english.xlsx');

    await expect(inspectV1SyntheticWorkbook(file)).resolves.toMatchObject({
      status: 'UNDERSTOOD', provider_dispatch: 'CLOSED',
    });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/synthetic-workbook-inspection'),
      expect.objectContaining({ method: 'POST', body: expect.any(FormData) }),
    );
  });

  it('surfaces the bounded refusal for an unregistered file', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: jest.fn().mockResolvedValue({
        detail: 'Fichier refusé : sélectionnez uniquement un classeur synthétique V1 enregistré.',
      }),
    });
    await expect(inspectV1SyntheticWorkbook(new File(['real'], 'client.xlsx'))).rejects.toThrow(
      'Fichier refusé',
    );
  });
});

describe('analyzeV1SyntheticWorkbook', () => {
  beforeEach(() => {
    sessionStorage.clear();
    global.fetch = jest.fn();
  });

  it('uses only the dedicated simulated-provider endpoint', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ analyse_id: 'synthetic-id', result: {} }),
    });
    const file = new File(['synthetic'], 'pepperyn_v1_heterogeneous_english.xlsx');
    await expect(analyzeV1SyntheticWorkbook(file)).resolves.toMatchObject({ analyse_id: 'synthetic-id' });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/synthetic-workbook-analysis'),
      expect.objectContaining({ method: 'POST', body: expect.any(FormData) }),
    );
  });

  it('preserves the bounded refusal from the closed backend', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: jest.fn().mockResolvedValue({ detail: 'Analyse simulée refusée' }),
    });
    await expect(analyzeV1SyntheticWorkbook(new File(['unsafe'], 'unknown.xlsx'))).rejects.toThrow(
      'Analyse simulée refusée',
    );
  });
});
