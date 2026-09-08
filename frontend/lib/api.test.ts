import { inspectV1SyntheticWorkbook, runV1SyntheticDemo } from './api';

jest.mock('./supabase', () => ({
  supabase: {
    auth: { getSession: jest.fn().mockResolvedValue({ data: { session: null } }) },
  },
}));

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
