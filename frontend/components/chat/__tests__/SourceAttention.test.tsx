import { fireEvent, render, screen } from '@testing-library/react';
import { SourceAttention } from '../SourceAttention';
import { listSourceAttention } from '@/lib/source-dossiers';
jest.mock('@/lib/source-dossiers', () => ({ listSourceAttention: jest.fn() }));
beforeEach(() => jest.resetAllMocks());
test('separate source status keeps provenance and client navigation without writes', async () => {
  (listSourceAttention as jest.Mock).mockResolvedValue([{ entity_id: 'client-a', entity_name: 'Synthetic A',
    dossiers: [{ dossier_id: 'dossier-a', filename: 'source.xlsx', status: 'CONTRADICTION', source_sha256: 'ABC', conflicting_metrics: ['REVENUE'] }] }]);
  render(<SourceAttention />);
  await screen.findByText('Synthetic A');
  expect(screen.getByText('source.xlsx — CONTRADICTION')).toBeInTheDocument();
  expect(screen.getByText('Dossier source : dossier-a')).toBeInTheDocument();
  expect(screen.getByRole('link')).toHaveAttribute('href', '/app/chat?entity=client-a');
  expect(screen.queryByText(/Enregistrer/)).not.toBeInTheDocument();
});
test('unavailable never becomes empty; retry replaces old state', async () => {
  (listSourceAttention as jest.Mock).mockRejectedValueOnce(new Error('private')).mockResolvedValueOnce([]);
  render(<SourceAttention />);
  await screen.findByRole('alert');
  expect(screen.queryByText(/Aucun dossier synthétique/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByText('Relire les sources'));
  await screen.findByText(/Ceci ne valide pas la fiabilité financière/);
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});
