import { runV1SyntheticDemo } from './api';

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
