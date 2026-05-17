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
  | 'entities'           // Gestion multi-entités dans la sidebar (POWER+)
  | 'export_excel'       // Export Excel (.xlsx) (PRO+)
  | 'export_pptx'        // Export PowerPoint (.pptx) (PRO+)
  | 'export_pdf'         // Export PDF (FREE)
  | 'conversational'     // Usage conversationnel étendu (PRO+) — FREE a 3 interactions/analyse
  | 'memory'             // Mémoire légère (FREE) — incluse gratuitement
  | 'memory_full'        // Mémoire persistante complète + suivi tendances (PRO+)
  | 'multi_period'       // Analyse multi-périodes (PRO+)
  | 'projections'        // Projections financières avancées (PRO+)
  | 'simulator'          // Simulateur de décisions (POWER+)
  | 'multi_user'         // Workspace collaboratif multi-users (SCALE+)
  | 'priority_support';  // Support prioritaire (SCALE+)

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
const FEATURE_MIN_LEVEL: Record<Feature, number> = {
  export_pdf:       0, // free
  memory:           0, // free (mémoire légère incluse)
  export_excel:     1, // pro+
  export_pptx:      1, // pro+
  conversational:   1, // pro+ (free = 3 interactions/analyse seulement)
  memory_full:      1, // pro+ (mémoire persistante complète)
  multi_period:         1, // pro+
  projections:          1, // pro+
  entities:             2, // power+
  simulator:            2, // power+
  multi_user:           3, // scale+
  priority_support:     3, // scale+
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
    label: 'Export Excel',
    description: 'Exportez votre analyse complète dans un fichier Excel structuré et réutilisable.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '59€/mois',
    benefits: [
      '15 analyses / mois',
      'Exports Excel, PDF et PowerPoint',
      'Mémoire persistante complète',
      'Suivi des tendances financières',
      'Alertes et dérives détectées automatiquement',
    ],
    emoji: '📊',
  },
  export_pptx: {
    label: 'Export PowerPoint',
    description: 'Générez un deck de présentation prêt à l\'emploi pour vos réunions de direction.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '59€/mois',
    benefits: [
      '15 analyses / mois',
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
    requiredPlanPrice: '59€/mois',
    benefits: [
      'Usage conversationnel inclus (illimité)',
      '15 analyses / mois',
      'Mémoire persistante complète',
      'Priorisation intelligente',
    ],
    emoji: '💬',
  },
  memory_full: {
    label: 'Mémoire persistante complète',
    description: 'Pepperyn mémorise l\'historique complet de vos analyses et détecte automatiquement les tendances dans le temps.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '59€/mois',
    benefits: [
      'Mémoire persistante complète',
      'Suivi des tendances financières',
      'Alertes et dérives détectées automatiquement',
      '15 analyses / mois',
    ],
    emoji: '🧠',
  },
  multi_period: {
    label: 'Analyse multi-périodes',
    description: 'Comparez N-1, YTD et projections sur plusieurs exercices fiscaux.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '59€/mois',
    benefits: [
      'Analyse multi-périodes',
      'Comparaison de périodes',
      'Suivi des tendances financières',
      '15 analyses / mois',
    ],
    emoji: '📅',
  },
  projections: {
    label: 'Projections financières',
    description: 'Modélisez vos scénarios financiers à 3, 6 et 12 mois avec des hypothèses personnalisées.',
    requiredPlan: 'PRO',
    requiredPlanPrice: '59€/mois',
    benefits: [
      'Projections simples',
      'Priorisation intelligente',
      '15 analyses / mois',
      'Mémoire persistante complète',
    ],
    emoji: '🔮',
  },

  // ── POWER ────────────────────────────────────────────────────────────────────
  entities: {
    label: 'Multi-entités',
    description: 'Gérez plusieurs sociétés, filiales ou portefeuilles clients avec une mémoire et un historique distincts par entité.',
    requiredPlan: 'POWER',
    requiredPlanPrice: '129€/mois',
    benefits: [
      '75 analyses / mois',
      'Multi-entités avec mémoire persistante par entité',
      'Simulateur de décisions',
      'Projections avancées',
      'Comparaison de périodes',
      'Analyse comparative',
    ],
    emoji: '🏢',
  },
  simulator: {
    label: 'Simulateur de décisions',
    description: 'Simulez l\'impact financier de chaque décision avant de l\'exécuter — recrutement, investissement, restructuration.',
    requiredPlan: 'POWER',
    requiredPlanPrice: '129€/mois',
    benefits: [
      'Simulateur de décisions',
      '75 analyses / mois',
      'Multi-entités',
      'Projections avancées',
      'Analyse comparative',
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
      '250 analyses / mois',
      'Multi-users avec permissions utilisateurs',
      'Workspace collaboratif',
      'Gouvernance des analyses',
      'Collaboration équipe finance',
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
      '250 analyses / mois',
      'Gouvernance des analyses',
    ],
    emoji: '🎯',
  },
};

// ── Quota analyses par plan ──────────────────────────────────────────────────
export const PLAN_QUOTA: Record<string, number> = {
  free:          1,
  pro:           15,
  power:         75,
  scale:         250,
  enterprise:    9999,
  // Legacy
  standard_beta: 15,
  standard:      15,
  premium:       75,
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
