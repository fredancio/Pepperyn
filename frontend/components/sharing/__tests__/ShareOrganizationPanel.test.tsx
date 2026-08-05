/**
 * Tests — ShareOrganizationPanel (Organisation Sharing Demo, prototype
 * externe, 2026-08-05).
 *
 * Couvre le périmètre du mandat "EXTERNAL TESTING PROTOTYPE — ORGANISATION
 * SHARING — DEMO ONLY" : membres fictifs, rôle/périmètre par défaut sûrs,
 * confirmation obligatoire pour "Tout le portefeuille", invitation simulée
 * sans aucun appel réseau, code temporaire fictif, absence du terme
 * "PIN invité", réinitialisation du formulaire.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { ShareOrganizationPanel } from '../ShareOrganizationPanel';

const noop = () => {};

describe('ShareOrganizationPanel — vue membres', () => {
  test('affiche les 3 membres fictifs avec leur rôle', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);

    expect(screen.getByText('Frédéric')).toBeInTheDocument();
    expect(screen.getByText('Julie')).toBeInTheDocument();
    expect(screen.getByText('Marc')).toBeInTheDocument();
    expect(screen.getByText('Administrateur')).toBeInTheDocument();
    expect(screen.getByText('Contributeur')).toBeInTheDocument();
    expect(screen.getByText('Lecteur')).toBeInTheDocument();
  });

  test('le texte explicatif précise un périmètre limité à cette organisation', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);

    expect(screen.getByTestId('share-panel-explainer')).toHaveTextContent(
      'Cette invitation donne accès uniquement à Cabinet Lefèvre & Associés. Les autres organisations de votre portefeuille restent invisibles.'
    );
  });

  test('le terme "PIN invité" n\'apparaît jamais dans le panneau', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);

    const bodyText = document.body.textContent || '';
    expect(bodyText.toLowerCase()).not.toContain('pin invité');
  });
});

describe('ShareOrganizationPanel — formulaire d\'invitation, valeurs par défaut sûres', () => {
  test('rôle par défaut = Lecteur (le plus restrictif)', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);
    fireEvent.click(screen.getByTestId('share-panel-open-invite'));

    expect(screen.getByTestId('share-invite-role-lecteur')).toHaveClass('bg-[#1B73E8]');
    expect(screen.getByTestId('share-invite-role-administrateur')).not.toHaveClass('bg-[#1B73E8]');
  });

  test('périmètre par défaut = "Cette organisation"', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);
    fireEvent.click(screen.getByTestId('share-panel-open-invite'));

    expect(screen.getByTestId('share-scope-this_organization')).toBeChecked();
    expect(screen.getByTestId('share-scope-whole_portfolio')).not.toBeChecked();
  });

  test('périmètre "Plusieurs organisations sélectionnées" affiche le sélecteur, soumission bloquée tant qu\'aucune n\'est cochée', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);
    fireEvent.click(screen.getByTestId('share-panel-open-invite'));
    fireEvent.change(screen.getByTestId('share-invite-email'), { target: { value: 'test@exemple.fr' } });
    fireEvent.click(screen.getByTestId('share-scope-selected_organizations'));

    expect(screen.getByTestId('share-scope-org-picker')).toBeInTheDocument();
    expect(screen.getByTestId('share-invite-submit')).toBeDisabled();
  });

  test('périmètre "Tout le portefeuille" affiche l\'avertissement et exige la confirmation explicite avant soumission', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);
    fireEvent.click(screen.getByTestId('share-panel-open-invite'));
    fireEvent.change(screen.getByTestId('share-invite-email'), { target: { value: 'test@exemple.fr' } });
    fireEvent.click(screen.getByTestId('share-scope-whole_portfolio'));

    expect(screen.getByTestId('share-scope-whole-portfolio-warning')).toHaveTextContent(
      'Cette personne pourra voir toutes les organisations actuelles et futures du portefeuille. Confirmer ?'
    );
    expect(screen.getByTestId('share-invite-submit')).toBeDisabled();

    fireEvent.click(screen.getByTestId('share-scope-whole-portfolio-confirm'));
    expect(screen.getByTestId('share-invite-submit')).not.toBeDisabled();
  });
});

describe('ShareOrganizationPanel — invitation simulée', () => {
  test('créer une invitation ne déclenche aucun appel réseau réel', () => {
    const originalFetch = (global as unknown as { fetch?: unknown }).fetch;
    const fetchMock = jest.fn();
    (global as unknown as { fetch: unknown }).fetch = fetchMock;

    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);
    fireEvent.click(screen.getByTestId('share-panel-open-invite'));
    fireEvent.change(screen.getByTestId('share-invite-email'), { target: { value: 'test@exemple.fr' } });
    fireEvent.click(screen.getByTestId('share-invite-submit'));

    expect(fetchMock).not.toHaveBeenCalled();

    (global as unknown as { fetch: unknown }).fetch = originalFetch;
  });

  test('affiche un code temporaire fictif, sa validité et son usage unique après création', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);
    fireEvent.click(screen.getByTestId('share-panel-open-invite'));
    fireEvent.change(screen.getByTestId('share-invite-email'), { target: { value: 'test@exemple.fr' } });
    fireEvent.click(screen.getByTestId('share-invite-submit'));

    expect(screen.getByTestId('share-invite-success')).toBeInTheDocument();
    expect(screen.getByTestId('share-invite-code').textContent).toMatch(/^[A-Z0-9]{4}-[A-Z0-9]{4}$/);
    expect(screen.getByText(/Valable 48 heures/)).toBeInTheDocument();
    expect(screen.getByText(/Usage unique/)).toBeInTheDocument();
  });

  test('"Nouvelle invitation" réinitialise le formulaire à ses valeurs par défaut', () => {
    render(<ShareOrganizationPanel entityId="e1" entityName="Cabinet Lefèvre & Associés" onClose={noop} />);
    fireEvent.click(screen.getByTestId('share-panel-open-invite'));
    fireEvent.change(screen.getByTestId('share-invite-email'), { target: { value: 'test@exemple.fr' } });
    fireEvent.click(screen.getByTestId('share-invite-submit'));
    fireEvent.click(screen.getByText('Nouvelle invitation'));

    expect(screen.getByTestId('share-panel-members')).toBeInTheDocument();
  });
});
