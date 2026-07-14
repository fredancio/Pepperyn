/**
 * featureGate.ts — Pepperyn V11
 * Hiérarchie des plans et contrôle d'accès aux fonctionnalités.
 * Stratégie "show everything, gate execution" : toutes les features
 * sont visibles pour créer l'envie, mais déclenchent une modale
 * d'upgrade si le plan est insuffisant.
 */

export type Plan = 'free' | 'pro' | 'power' | 'scale' | 'enterprise'
  // legacy names kept for backward compat
  | 'premium' | 'standard' | 'standard_beta';

export type Feature =
  | 'entities'           // Gestion multi-entités (PRO+) — absorbé depuis POWER
  | 'export_excel'       // Export Excel (.xlsx) (PRO+)
  | 'export_pptx'        // Export PowerPoint (.pptx) (PRO+)
  | 'export_pdf'         // Export PDF (FREE)
  | 'conversational'     // Usage conversationnel étendu (PRO+) — FREE a 3 interactions/analyse
  | 'memory'             // Mémoire légère (FREE) — incluse gratuitement
  | 'memory_full'        // Mémoire persistante complète + suivi tendances (PRO+)
  | 'multi_period'       // Analyse multi-périodes (PRO+)
  | 'projections'        // Projections financières avancées (PRO+)
  | 'simulator'          // Simulateur de décisions (PRO+) — absorbé depuis POWER
  | 'multi_user'         // Workspace collaboratif multi-users (SCALE+)
  | 'priority_support'   // Support prioritaire (SCALE+)
  | 'erp_integration';   // Connexion ERP/CRM/comptabilité sur devis (SCALE+)

// ── Hiérarchie plan (index = niveau) ────────────────────────────────────────
const PLAN_LEVEL: Record<Plan, number> = {
  free:          0,
  pro:           1,
  power:         2,
  scale:         3,
  enterprise:    4,
  // Legacy aliases
  standard_beta: 1,
  standard:      1,
  premium:       2,
};

/** Normalise un plan legacy vers son équivalent V11 */
export function normalizePlan(plan: string): Plan {
  const map: Record<string, Plan> = {
    standard_beta: 'pro',
    standard:      'pro',
    premium:       'power',
  };
  return (map[plan] ?? plan) as Plan;
}

/** Retourne le niveau numérique d'un plan (0 = free, 4 = enterprise) */
export function planLevel(plan: string): number {
  return PLAN_LEVEL[plan as Plan] ?? 0;
}

// ── Seuil minimum par feature ────────────────────────────────────────────────
// V12 : 3 plans (FREE / PRO / SCALE) — POWER supprimé, ses features absorbées par PRO
const FEATURE_MIN_LEVEL: Record<Feature, number> = {
  export_pdf:       0, // free
  memory:           0, // free (mémoire légère incluse)
  export_excel:     1, // pro+
  export_pptx:      1, // pro+
  conversational:   1, // pro+ (free = 3 interactions/analyse seulement)
  memory_full:      1, // pro+ (mémoire persistante complète)
  multi_period:     1, // pro+
  projections:      1, // pro+
  entities:         1, // pro+ (absorbé depuis POWER)
  simulator:        1, // pro+ (absorbé depuis POWER)
  multi_user:       3, // scale+
  priority_support: 3, // scale+
  erp_integration:  3, // scale+ (connexion ERP/CRM sur devis)
};

/** Vérifie si un plan a accès à une feature */
export function canAccess(plan: string, feature: Feature): boolean {
  return planLevel(plan) >= FEATURE_MIN_LEVEL[feature];
}

// ── Métadonnées upsell par feature ──────────────────────────────────────────
export interface FeatureMeta {
  label: string;
  description: string;
  requiredPlan: 'PRO' | 'POWER' | 'SCALE';
  requiredPlanPrice: string;
  benefits: string[];
  emoji: string;
}

export const FEATURE_META: Record<Feature, FeatureMeta | null> = {
  // ── Toujours gratuit — pas de modale ────────────────────────────────────────
  export_pdf: null,
  memory:     null, // mémoire légère incluse en FREE, pas de modale

  // ── PRO ─────────────────────────────────────────────────────────────────────
  export_excel: {
    label: 'Executive Financial Model',
    description: 'Exportez votre analyse complète dans un modèle financier Excel structuré, à formules vivantes.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '149€/mois',
    benefits: [
      '30 analyses / mois',
      'Exports Excel, PDF et PowerPoint',
      'Mémoire persistante complète',
      'Suivi des tendances financières',
      'Alertes et dérives détectées automatiquement',
    ],
    emoji: '📊',
  },
  export_pptx: {
    label: 'Executive Board Deck',
    description: 'Générez une présentation prête à l\'emploi pour votre comité de direction ou vos investisseurs.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '149€/mois',
    benefits: [
      '30 analyses / mois',
      'Exports Excel, PDF et PowerPoint',
      'Mémoire persistante complète',
      'Suivi des tendances financières',
      'Alertes et dérives détectées automatiquement',
    ],
    emoji: '📑',
  },
  conversational: {
    label: 'Usage conversationnel étendu',
    description: 'Posez autant de questions de suivi que nécessaire sur chaque analyse, sans limite de session.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '149€/mois',
    benefits: [
      'Usage conversationnel inclus (illimité)',
      '30 analyses / mois',
      'Mémoire persistante complète',
      'Priorisation intelligente',
    ],
    emoji: '💬',
  },
  memory_full: {
    label: 'Mémoire persistante complète',
    description: 'Pepperyn mémorise l\'historique complet de vos analyses et détecte automatiquement les tendances dans le temps.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '149€/mois',
    benefits: [
      'Mémoire persistante complète',
      'Suivi des tendances financières',
      'Alertes et dérives détectées automatiquement',
      '30 analyses / mois',
    ],
    emoji: '🧠',
  },
  multi_period: {
    label: 'Analyse multi-périodes',
    description: 'Comparez N-1, YTD et projections sur plusieurs exercices fiscaux.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '149€/mois',
    benefits: [
      'Analyse multi-périodes',
      'Comparaison de périodes',
      'Suivi des tendances financières',
      '30 analyses / mois',
    ],
    emoji: '📅',
  },
  projections: {
    label: 'Projections financières',
    description: 'Modélisez vos scénarios financiers à 3, 6 et 12 mois avec des hypothèses personnalisées.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '149€/mois',
    benefits: [
      'Projections simples',
      'Priorisation intelligente',
      '30 analyses / mois',
      'Mémoire persistante complète',
    ],
    emoji: '🔮',
  },

  // ── PRO (absorbé depuis POWER) ───────────────────────────────────────────────
  entities: {
    label: 'Clients ou entreprises multiples',
    description: 'Gérez plusieurs sociétés, filiales ou portefeuilles clients avec une mémoire et un historique distincts par client ou entreprise.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '149€/mois',
    benefits: [
      '30 analyses / mois',
      'Clients ou entreprises multiples avec mémoire persistante',
      'Simulateur de décisions',
      'Projections avancées',
      'Comparaison de périodes',
      'Exports Excel, PDF et PowerPoint',
    ],
    emoji: '🏢',
  },
  simulator: {
    label: 'Simulateur de décisions',
    description: 'Simulez l\'impact financier de chaque décision avant de l\'exécuter — recrutement, investissement, restructuration.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '149€/mois',
    benefits: [
      'Simulateur de décisions',
      '30 analyses / mois',
      'Clients ou entreprises multiples',
      'Projections avancées',
      'Exports Excel, PDF et PowerPoint',
    ],
    emoji: '⚡',
  },

  // ── SCALE ────────────────────────────────────────────────────────────────────
  multi_user: {
    label: 'Workspace multi-utilisateurs',
    description: 'Invitez toute votre équipe finance avec des permissions granulaires et un espace collaboratif partagé.',
    requiredPlan: 'SCALE',
    requiredPlanPrice: '349€/mois',
    benefits: [
      '100 analyses / mois',
      'Multi-users avec permissions utilisateurs',
      'Workspace collaboratif',
      'Gouvernance des analyses',
      'Connexion ERP/CRM sur devis',
    ],
    emoji: '👥',
  },
  priority_support: {
    label: 'Support prioritaire',
    description: 'Accès direct à l\'équipe Pepperyn avec temps de réponse garanti.',
    requiredPlan: 'SCALE',
    requiredPlanPrice: '349€/mois',
    benefits: [
      'Support prioritaire',
      'Workspace collaboratif',
      '100 analyses / mois',
      'Connexion ERP/CRM sur devis',
    ],
    emoji: '🎯',
  },
  erp_integration: {
    label: 'Connexion ERP / CRM',
    description: 'Connectez Pepperyn directement à vos systèmes existants — ERP, CRM, logiciels comptables — pour un pilotage financier en temps réel.',
    requiredPlan: 'SCALE',
    requiredPlanPrice: '349€/mois',
    benefits: [
      'Connexion ERP, CRM, comptabilité sur devis',
      'Onboarding et implémentation inclus dans le devis',
      'Workflows personnalisés selon vos processus',
      '100 analyses / mois',
      'Support prioritaire dédié',
    ],
    emoji: '🔗',
  },
};

// ── Quota analyses par plan ──────────────────────────────────────────────────
// Valeurs alignées sur config/product_catalog.py (WP1A).
// Utilisées UNIQUEMENT comme fallback si l'API /billing/usage est indisponible.
// La source de vérité reste toujours le backend (BillingUsage.analyses_limit).
export const PLAN_QUOTA: Record<string, number> = {
  free:          1,
  pro:           30,
  power:         100,   // alias SCALE — plan supprimé du catalogue public
  scale:         100,
  enterprise:    9999,
  // Legacy aliases
  standard_beta: 30,
  standard:      30,
  premium:       100,   // alias POWER → SCALE
};

export function getQuota(plan: string): number {
  return PLAN_QUOTA[plan] ?? 1;
}

// ── Label d'affichage du plan ────────────────────────────────────────────────
export function planDisplayLabel(plan: string): string {
  const labels: Record<string, string> = {
    free: 'Gratuit',
    pro: 'PRO',
    power: 'POWER',
    scale: 'SCALE',
    enterprise: 'Enterprise',
    standard_beta: 'PRO',
    standard: 'PRO',
    premium: 'POWER',
  };
  return labels[plan] ?? plan.toUpperCase();
}

export function planEmoji(plan: string): string {
  const emojis: Record<string, string> = {
    free: '🆓',
    pro: '🚀',
    power: '⭐',
    scale: '🏆',
    enterprise: '🏢',
    standard_beta: '🚀',
    standard: '🚀',
    premium: '⭐',
  };
  return emojis[plan] ?? '🆓';
}

export function planBadgeColors(plan: string): string {
  const normalized = normalizePlan(plan);
  const colors: Record<Plan, string> = {
    free:       'bg-gray-100 text-[#5F6368]',
    pro:        'bg-blue-100 text-blue-700',
    power:      'bg-amber-100 text-amber-700',
    scale:      'bg-purple-100 text-purple-700',
    enterprise: 'bg-[#0A2540] text-white',
    // These shouldn't be reached after normalization but keeping for TS
    standard_beta: 'bg-blue-100 text-blue-700',
    standard:      'bg-blue-100 text-blue-700',
    premium:       'bg-amber-100 text-amber-700',
  };
  return colors[normalized] ?? 'bg-gray-100 text-[#5F6368]';
}
