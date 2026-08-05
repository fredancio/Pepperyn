/**
 * Tests — GuestPreview (Organisation Sharing Demo, prototype externe,
 * 2026-08-05).
 *
 * Couvre Mission 6 du mandat : l'aperçu "Voir ce que cette personne verra"
 * ne montre jamais le reste du portefeuille, les réglages de compte, les
 * quotas, les autres organisations ni les fonctions d'administration — et
 * reflète les capacités réelles du rôle choisi (purement illustratives).
 */
import { render, screen } from '@testing-library/react';
import { GuestPreview } from '../GuestPreview';

const noop = () => {};

describe('GuestPreview — rôle Lecteur', () => {
  test('affiche uniquement le nom de cette organisation, le briefing et l\'exemple d\'analyse', () => {
    render(<GuestPreview entityId="e2" entityName="Atelier Nguyen" role="lecteur" onClose={noop} />);

    expect(screen.getByTestId('guest-preview-org-name')).toHaveTextContent('Atelier Nguyen');
    expect(screen.getByTestId('guest-preview-role-title')).toHaveTextContent('Ce que verra : Lecteur');
    expect(screen.getByTestId('guest-preview-briefing')).toBeInTheDocument();
    expect(screen.getByTestId('guest-preview-analysis')).toBeInTheDocument();
  });

  test('les capacités affichées correspondent au rôle Lecteur ("Ne modifie rien")', () => {
    render(<GuestPreview entityId="e2" entityName="Atelier Nguyen" role="lecteur" onClose={noop} />);

    expect(screen.getByTestId('guest-preview-capabilities')).toHaveTextContent('Ne modifie rien');
  });

  test('aucune autre organisation du portefeuille n\'apparaît dans l\'aperçu', () => {
    render(<GuestPreview entityId="e2" entityName="Atelier Nguyen" role="lecteur" onClose={noop} />);

    // Autre organisation du dataset fictif — ne doit jamais apparaître ici.
    expect(screen.queryByText('Cabinet Lefèvre & Associés')).not.toBeInTheDocument();
  });

  test('aucun réglage de compte, quota ni fonction d\'administration n\'apparaît dans l\'aperçu', () => {
    render(<GuestPreview entityId="e2" entityName="Atelier Nguyen" role="lecteur" onClose={noop} />);

    const bodyText = document.body.textContent?.toLowerCase() || '';
    for (const forbidden of ['quota', 'facturation', 'abonnement pro', 'gérer les membres']) {
      expect(bodyText).not.toContain(forbidden);
    }
  });
});

describe('GuestPreview — rôle Contributeur', () => {
  test('les capacités affichées précisent que ce rôle ne gère pas les accès', () => {
    render(<GuestPreview entityId="e7" entityName="Atelier Martin" role="contributeur" onClose={noop} />);

    expect(screen.getByTestId('guest-preview-capabilities')).toHaveTextContent('Ne gère pas les accès');
  });
});

describe('GuestPreview — rôle Administrateur', () => {
  test('les capacités affichées incluent la gestion des membres (illustratif, non fonctionnel)', () => {
    render(<GuestPreview entityId="e1" entityName="Cabinet Lefèvre & Associés" role="administrateur" onClose={noop} />);

    expect(screen.getByTestId('guest-preview-capabilities')).toHaveTextContent('Gère les membres');
  });
});
