/**
 * Dataset de démonstration — External User Testing Prototype (2026-08-05).
 *
 * Couvre les cas 4 à 8 de la Mission 9 du mandat : 12 clients fictifs
 * avant filtrage, exclusion du client closed-only, exclusion du client
 * sans sujet actif, ordre des cartes, compteur multi-points.
 */
import {
  DEMO_ENTITIES,
  DEMO_PORTFOLIO_CARDS,
  getDemoPortfolio,
  getDemoReviewBriefing,
  getDemoEntityName,
} from '../demo-data';

describe('Dataset démo — 12 clients avant filtrage (cas 4)', () => {
  it('contient exactement 12 entités fictives', () => {
    expect(DEMO_ENTITIES).toHaveLength(12);
  });

  it('inclut Traiteur Second (closed-only) et Cabinet Rousseau (sans arc) parmi les 12 entités brutes', () => {
    const names = DEMO_ENTITIES.map((e) => e.name);
    expect(names).toContain('Traiteur Second');
    expect(names).toContain('Cabinet Rousseau');
  });
});

describe('Exclusion du client closed-only (cas 5)', () => {
  it("Traiteur Second (e11) n'apparaît jamais dans les cartes Portfolio", () => {
    const ids = getDemoPortfolio().map((c) => c.entity_id);
    expect(ids).not.toContain('e11');
  });

  it('reste consultable comme historique via son Review Briefing direct', () => {
    const items = getDemoReviewBriefing('e11');
    expect(items).toHaveLength(1);
    expect(items[0].priority).toBe('closed');
  });
});

describe('Exclusion du client sans sujet actif (cas 6)', () => {
  it("Cabinet Rousseau (e12) n'apparaît jamais dans les cartes Portfolio", () => {
    const ids = getDemoPortfolio().map((c) => c.entity_id);
    expect(ids).not.toContain('e12');
  });

  it('son Review Briefing direct est vide (aucun arc)', () => {
    expect(getDemoReviewBriefing('e12')).toHaveLength(0);
  });
});

describe('Ordre des cartes Portfolio (cas 7)', () => {
  it('correspond exactement à l\'ordre validé dans PORTFOLIO_HOME_PRODUCT_VALIDATION.md', () => {
    const order = getDemoPortfolio().map((c) => c.entity_name);
    expect(order).toEqual([
      'Cabinet Lefèvre & Associés',
      'Atelier Nguyen',
      'Boulangerie Girard',
      'Pharmacie Vidal',
      'Cabinet Lemoine',
      'SCI Fontaine',
      'Atelier Martin',
      'Restaurant Belhadj',
      'Cabinet Dupuis',
      'Menuiserie Roussel',
    ]);
  });

  it('contient exactement 10 cartes (12 entités moins les 2 exclues)', () => {
    expect(DEMO_PORTFOLIO_CARDS).toHaveLength(10);
  });
});

describe('Compteur multi-points (cas 8)', () => {
  it('Cabinet Lefèvre & Associés (e1) a 4 points actifs → other_active_count = 3', () => {
    const card = getDemoPortfolio().find((c) => c.entity_id === 'e1');
    expect(card?.other_active_count).toBe(3);
  });

  it('Atelier Martin (e7) a 3 points actifs → other_active_count = 2', () => {
    const card = getDemoPortfolio().find((c) => c.entity_id === 'e7');
    expect(card?.other_active_count).toBe(2);
  });

  it('Atelier Nguyen (e2), un seul point actif → other_active_count = 0', () => {
    const card = getDemoPortfolio().find((c) => c.entity_id === 'e2');
    expect(card?.other_active_count).toBe(0);
  });
});

describe('getDemoEntityName', () => {
  it('résout un nom de client connu', () => {
    expect(getDemoEntityName('e5')).toBe('Cabinet Lemoine');
  });

  it('retourne undefined pour un identifiant inconnu (aucune exception levée)', () => {
    expect(getDemoEntityName('does-not-exist')).toBeUndefined();
  });
});
