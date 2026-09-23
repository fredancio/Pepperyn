import { render, screen } from '@testing-library/react';
import { AnalysisResult } from '../AnalysisResult';

jest.mock('@/lib/api', () => ({ downloadExcel: jest.fn(), downloadPdf: jest.fn(),
  downloadPptx: jest.fn(), downloadV1GovernedExport: jest.fn() }));

const historicalDecision = 'Décision professionnelle requise; les recommandations IA ne sont pas des décisions confirmées.';

test('governed analysis preserves historical text without presenting it as current decision state', () => {
  render(<AnalysisResult data={{ id: 'a', verification_tag: 'V1_GOVERNED_SINGLE_CALL', decision: historicalDecision }} />);
  expect(screen.getByRole('heading', { name: 'Position proposée lors de l’analyse initiale' })).toBeInTheDocument();
  expect(screen.getByText(/Texte historique de l’analyse/)).toHaveTextContent('non actualisé par les décisions ultérieures');
  expect(screen.getByText(historicalDecision)).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: '⚡ DÉCISION' })).not.toBeInTheDocument();
});

test('legacy analysis rendering is unchanged', () => {
  render(<AnalysisResult data={{ id: 'a', decision: historicalDecision }} />);
  expect(screen.getByRole('heading', { name: '⚡ DÉCISION' })).toBeInTheDocument();
  expect(screen.queryByText(/Texte historique de l’analyse/)).not.toBeInTheDocument();
});
