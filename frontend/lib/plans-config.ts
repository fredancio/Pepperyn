/**
 * plans-config.ts — Pepperyn Release 1.0
 * Adaptateur frontend canonique pour les données commerciales.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * SOURCE DE VÉRITÉ
 * ═══════════════════════════════════════════════════════════════════════════
 * Backend : backend/config/product_catalog.py
 * API     : GET /api/billing/plans
 *
 * RÈGLE : Aucune constante commerciale ne doit être dupliquée
 * dans plusieurs composants frontend. Tout composant affichant
 * des informations commerciales importe depuis ce fichier.
 *
 * Toute évolution tarifaire ou de quota nécessite de modifier :
 *   1. backend/config/product_catalog.py  (source de vérité)
 *   2. ce fichier                          (adaptateur frontend)
 *
 * Valeurs alignées sur product_catalog.py (WP0.75 — NON NÉGOCIABLES).
 * Alignement réalisé en WP4A (Release 1.0 — 14 juillet 2026).
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ─── Plans commerciaux ────────────────────────────────────────────────────────

export interface PlanConfig {
  /** Identifiant interne du plan (correspond à companies.plan en DB) */
  id: 'free' | 'pro' | 'scale';
  /** Nom court public */
  name: string;
  /** Prix en centimes d'euro */
  priceCents: number;
  /** Libellé prix formaté pour l'affichage */
  priceLabel: string;
  /** Période d'abonnement : '' pour FREE, '/mois' pour les payants */
  period: string;
  /** Quota mensuel d'Analyses */
  analysesPerMonth: number;
  /**
   * Quota mensuel d'Interactions (échanges de suivi).
   * Ce quota est GLOBAL et mensuel — aucune limite par Analyse.
   */
  interactionsPerMonth: number | null;
  /** Nombre maximum d'Entités. null = illimité (SCALE). */
  maxEntities: number | null;
}

/**
 * Plans commerciaux actifs.
 * Seuls FREE, PRO et SCALE sont exposés dans l'interface Pepperyn.
 * Ne jamais afficher : POWER, PREMIUM, STANDARD, STANDARD_BETA, ENTERPRISE.
 */
export const COMMERCIAL_PLANS: PlanConfig[] = [
  {
    id:                   'free',
    name:                 'FREE',
    priceCents:           0,
    priceLabel:           '0€',
    period:               '',
    analysesPerMonth:     1,
    interactionsPerMonth: 3,
    maxEntities:          1,
  },
  {
    id:                   'pro',
    name:                 'PRO',
    priceCents:           14_900,  // 149,00 €
    priceLabel:           '149€',
    period:               '/mois',
    analysesPerMonth:     30,
    interactionsPerMonth: 75,
    maxEntities:          10,
  },
  {
    id:                   'scale',
    name:                 'SCALE',
    priceCents:           34_900,  // 349,00 €
    priceLabel:           '349€',
    period:               '/mois',
    analysesPerMonth:     100,
    interactionsPerMonth: 500,
    maxEntities:          null,    // illimité
  },
];

/** Accès rapide par identifiant de plan */
export function getCommercialPlan(id: 'free' | 'pro' | 'scale'): PlanConfig {
  const plan = COMMERCIAL_PLANS.find(p => p.id === id);
  if (!plan) throw new Error(`Plan inconnu : ${id}`);
  return plan;
}

// ─── Accès rapide par plan (shorthands) ──────────────────────────────────────

/** Quota mensuel d'Analyses par plan */
export const PLAN_ANALYSES_PER_MONTH: Record<'free' | 'pro' | 'scale', number> = {
  free:  1,
  pro:   30,
  scale: 100,
};

/** Prix d'abonnement en euros par plan */
export const PLAN_PRICE_EUR: Record<'free' | 'pro' | 'scale', number> = {
  free:  0,
  pro:   149,
  scale: 349,
};


// ─── Executive Capacity Packs ─────────────────────────────────────────────────

export interface PackConfig {
  /** Identifiant interne du pack (correspond à Stripe metadata.plan_or_addon) */
  id: 'addon_starter' | 'addon_growth' | 'addon_scale';
  /** Nom officiel selon TERMINOLOGY.md */
  name: string;
  /** Nombre d'Analyses créditées (bonus_analyses en DB) */
  analysesAdded: number;
  /** Prix en centimes d'euro */
  priceCents: number;
  /** Libellé prix formaté pour l'affichage */
  priceLabel: string;
}

/**
 * Executive Capacity Packs actifs.
 *
 * Règles NON NÉGOCIABLES :
 * - Ajoutent uniquement des Analyses supplémentaires.
 * - N'ajoutent JAMAIS d'Interactions, d'Entités, ni de changement de Plan.
 * - Les Analyses bonus sont consommées EN PREMIER (avant le quota mensuel).
 * - Les Analyses bonus non consommées persistent au renouvellement mensuel.
 */
export const EXECUTIVE_CAPACITY_PACKS: PackConfig[] = [
  {
    id:            'addon_starter',
    name:          'Starter Capacity Pack',
    analysesAdded: 10,
    priceCents:    3_900,   // 39,00 €
    priceLabel:    '39€',
  },
  {
    id:            'addon_growth',
    name:          'Growth Capacity Pack',
    analysesAdded: 20,
    priceCents:    7_900,   // 79,00 €
    priceLabel:    '79€',
  },
  {
    id:            'addon_scale',
    name:          'Scale Capacity Pack',
    analysesAdded: 80,
    priceCents:    23_900,  // 239,00 €
    priceLabel:    '239€',
  },
];

/** Accès rapide par identifiant de pack */
export function getExecutiveCapacityPack(
  id: 'addon_starter' | 'addon_growth' | 'addon_scale',
): PackConfig {
  const pack = EXECUTIVE_CAPACITY_PACKS.find(p => p.id === id);
  if (!pack) throw new Error(`Executive Capacity Pack inconnu : ${id}`);
  return pack;
}

/** Label d'affichage complet d'un pack pour billing/success et notifications */
export function packLabel(id: string): string {
  const pack = EXECUTIVE_CAPACITY_PACKS.find(p => p.id === id);
  if (!pack) return id.toUpperCase();
  return `${pack.name} (+${pack.analysesAdded} analyses)`;
}
