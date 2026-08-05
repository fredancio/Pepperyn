/**
 * Absence de téléchargement réel en mode démo — External User Testing
 * Prototype (2026-08-05), Mission 9, cas 14.
 *
 * downloadExcel / downloadPdf / downloadPptx doivent résoudre en mode démo
 * sans jamais construire de fetch() — preuve directe qu'aucun fichier réel
 * n'est demandé au backend, seul un Blob local et honnêtement labellisé
 * est retourné.
 */
jest.mock('@/lib/demo-mode', () => ({
  ...jest.requireActual('@/lib/demo-mode'),
  isDemoModeEnabled: jest.fn(),
}));

import { downloadExcel, downloadPdf, downloadPptx } from '../api';
import { isDemoModeEnabled } from '../demo-mode';

const mockedIsDemoModeEnabled = isDemoModeEnabled as jest.Mock;

describe('Téléchargements en mode démo (cas 14)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedIsDemoModeEnabled.mockReturnValue(true);
    global.fetch = jest.fn();
  });

  it('downloadExcel() ne construit jamais de fetch() et retourne un Blob local', async () => {
    const blob = await downloadExcel('demo-analysis-example');
    expect(global.fetch).not.toHaveBeenCalled();
    expect(blob).toBeInstanceOf(Blob);
  });

  it('downloadPdf() ne construit jamais de fetch() et retourne un Blob local', async () => {
    const blob = await downloadPdf('demo-analysis-example');
    expect(global.fetch).not.toHaveBeenCalled();
    expect(blob).toBeInstanceOf(Blob);
  });

  it('downloadPptx() ne construit jamais de fetch() et retourne un Blob local', async () => {
    const blob = await downloadPptx('demo-analysis-example');
    expect(global.fetch).not.toHaveBeenCalled();
    expect(blob).toBeInstanceOf(Blob);
  });

  it('le contenu du Blob s\'annonce lui-même comme un aperçu de démonstration', async () => {
    const blob = await downloadPdf('demo-analysis-example');
    // jsdom ne fournit pas Blob.text() — lecture via FileReader, seule API
    // fiable dans cet environnement de test pour inspecter le contenu.
    const text = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = reject;
      reader.readAsText(blob);
    });
    expect(text).toMatch(/APERÇU DE DÉMONSTRATION/);
    expect(text).toMatch(/Aucune analyse n'a été exécutée/);
  });
});
