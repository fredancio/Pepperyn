import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { SourceDossiers } from '../SourceDossiers';
import * as api from '@/lib/source-dossiers';
jest.mock('@/lib/source-dossiers');
const fixture = {
  dossier_id: 'dossier-a', entity_id: 'a', filename: 'synthetic.xlsx', source_sha256: 'A'.repeat(64),
  status: 'CONTRADICTION', facts: [], unknowns: [], conflicting_metrics: ['REVENUE'], discrepancies: [],
  source_claims: [{ fact_id: 'FA', source_sheet_ref: 'SA', source_field: 'RA', metric: 'REVENUE', value: 721, unit: 'EUR', period: '2031' },
    { fact_id: 'FB', source_sheet_ref: 'SB', source_field: 'RB', metric: 'REVENUE', value: 804, unit: 'EUR', period: '2031' }],
};
beforeEach(() => {
  jest.resetAllMocks(); (api.listSourceDossiers as jest.Mock).mockResolvedValue([]);
});
test('no implicit primary entity and no write on initial read', async () => {
  render(<SourceDossiers entityId={null} />);
  expect(screen.getByText(/Sélectionnez explicitement/)).toBeInTheDocument();
  expect(api.listSourceDossiers).not.toHaveBeenCalled(); expect(api.captureSourceDossier).not.toHaveBeenCalled();
});
test('write is explicit and reread preserves conflict without another write', async () => {
  (api.captureSourceDossier as jest.Mock).mockResolvedValue(fixture);
  (api.listSourceDossiers as jest.Mock).mockResolvedValueOnce([]).mockResolvedValue([fixture]);
  (api.loadSourceDossier as jest.Mock).mockResolvedValue(fixture);
  const view = render(<SourceDossiers entityId="a" />);
  await screen.findByText(/Aucun dossier source enregistré/);
  fireEvent.change(screen.getByLabelText('Classeur source synthétique'), { target: { files: [new File(['test'], 'synthetic.xlsx')] } });
  expect(api.captureSourceDossier).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText('Enregistrer explicitement le dossier source'));
  await screen.findByText(/Dossier enregistré : dossier-a/);
  expect(api.captureSourceDossier).toHaveBeenCalledTimes(1);
  view.unmount(); render(<SourceDossiers entityId="a" />);
  fireEvent.click(await screen.findByText('synthetic.xlsx — CONTRADICTION'));
  expect(await screen.findByText(/aucune valeur retenue comme vérité canonique/)).toHaveTextContent('721 EUR');
  expect(screen.getByText(/aucune valeur retenue comme vérité canonique/)).toHaveTextContent('804 EUR');
  expect(api.loadSourceDossier).toHaveBeenCalledWith('a', 'dossier-a');
  expect(api.captureSourceDossier).toHaveBeenCalledTimes(1);
});
test('unavailable is not empty and retry is read-only', async () => {
  (api.listSourceDossiers as jest.Mock).mockRejectedValueOnce(new Error('private')).mockResolvedValueOnce([]);
  render(<SourceDossiers entityId="a" />);
  await screen.findByRole('alert'); expect(screen.queryByText(/Aucun dossier source enregistré/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByText('Relire les dossiers'));
  await screen.findByText(/Aucun dossier source enregistré/);
  expect(api.captureSourceDossier).not.toHaveBeenCalled();
});
test('switching clients suppresses a stale source result', async () => {
  let resolve!: (value: unknown) => void;
  (api.listSourceDossiers as jest.Mock).mockResolvedValue([fixture]);
  (api.loadSourceDossier as jest.Mock).mockImplementation(() => new Promise(r => { resolve = r; }));
  const view = render(<SourceDossiers entityId="a" />);
  fireEvent.click(await screen.findByText('synthetic.xlsx — CONTRADICTION'));
  (api.listSourceDossiers as jest.Mock).mockResolvedValue([]);
  view.rerender(<SourceDossiers entityId="b" />);
  await act(async () => resolve(fixture));
  await screen.findByText(/Aucun dossier source enregistré/);
  expect(screen.queryByText(/Dossier enregistré/)).not.toBeInTheDocument();
  expect(api.captureSourceDossier).not.toHaveBeenCalled();
});
