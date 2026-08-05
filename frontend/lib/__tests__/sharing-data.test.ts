/**
 * Tests — sharing-data (Organisation Sharing Demo, prototype externe,
 * 2026-08-05). Logique pure, sans I/O, sans dépendance DOM.
 */
import {
  DEFAULT_INVITE_ROLE,
  DEFAULT_INVITE_SCOPE,
  SHARING_ROLE_ORDER,
  SHARING_SCOPE_OPTIONS,
  generateFakeTemporaryCode,
} from '../sharing-data';

describe('sharing-data — valeurs par défaut sûres', () => {
  test('le rôle par défaut est le plus restrictif (lecteur)', () => {
    expect(DEFAULT_INVITE_ROLE).toBe('lecteur');
  });

  test('le périmètre par défaut est limité à cette organisation', () => {
    expect(DEFAULT_INVITE_SCOPE).toBe('this_organization');
  });

  test('exactement 3 rôles définis, ni plus ni moins (mandat, Mission 3)', () => {
    expect(SHARING_ROLE_ORDER).toHaveLength(3);
    expect(SHARING_ROLE_ORDER).toEqual(['administrateur', 'contributeur', 'lecteur']);
  });

  test('exactement 3 options de périmètre, et seule "Tout le portefeuille" exige une confirmation renforcée', () => {
    expect(SHARING_SCOPE_OPTIONS).toHaveLength(3);
    const requiringConfirmation = SHARING_SCOPE_OPTIONS.filter((o) => o.requiresExtraConfirmation);
    expect(requiringConfirmation.map((o) => o.key)).toEqual(['whole_portfolio']);
  });
});

describe('sharing-data — generateFakeTemporaryCode', () => {
  test('produit un code au format XXXX-XXXX', () => {
    const code = generateFakeTemporaryCode();
    expect(code).toMatch(/^[A-Z0-9]{4}-[A-Z0-9]{4}$/);
  });

  test('produit des codes différents à chaque appel (purement illustratif, pas un identifiant stable)', () => {
    const codes = new Set(Array.from({ length: 20 }, () => generateFakeTemporaryCode()));
    expect(codes.size).toBeGreaterThan(1);
  });
});
