import fs from 'node:fs';
import { render, screen } from '@testing-library/react';
import { ExecutionProvenance } from '../ExecutionProvenance';

const fixture = process.env.PEPPERYN_V41_LIVE_UI_FIXTURE;

(fixture ? test : test.skip)('renders persisted V41 injected provenance without global or provider claims', () => {
  const value = JSON.parse(fs.readFileSync(fixture!, 'utf8'));
  render(<ExecutionProvenance value={value} />);
  expect(screen.getByText(/reçu V41 durable vérifié/)).toBeInTheDocument();
  expect(screen.getByText(/aucune exécution OpenAI attestée/)).toBeInTheDocument();
  expect(screen.getByText(/non admis globalement/)).toBeInTheDocument();
  expect(screen.getByText(/Requête SHA-256/)).toHaveTextContent(String(value.receipt.request_sha256));
  expect(screen.getByText(/Réponse SHA-256/)).toHaveTextContent(String(value.receipt.response_sha256));
});
