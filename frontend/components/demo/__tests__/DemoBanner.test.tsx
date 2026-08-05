/**
 * Bandeau d'identification du prototype — External User Testing Prototype
 * (2026-08-05), Mission 9, cas 13.
 */
import { render, screen } from '@testing-library/react';
import { DemoBanner } from '../DemoBanner';

describe('DemoBanner (cas 13)', () => {
  it('affiche le texte d\'identification "Prototype de test — données fictives"', () => {
    render(<DemoBanner />);
    const banner = screen.getByTestId('demo-banner');
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent('Prototype de test — données fictives');
  });

  it('propose un lien de feedback discret (Mission 6)', () => {
    render(<DemoBanner />);
    const link = screen.getByTestId('demo-feedback-link');
    expect(link).toBeInTheDocument();
    expect(link.getAttribute('href')).toMatch(/^mailto:/);
  });
});
