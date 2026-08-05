/**
 * Sharing demo — Organisation Sharing Demo (prototype externe, 2026-08-05).
 *
 * Données et logique 100% locales, fictives, sans I/O. Simule la direction
 * produit retenue — Organisation → Membres → Rôles → Invitations
 * temporaires — en remplacement du modèle PIN invité permanent, rejeté.
 *
 * AUCUNE écriture Supabase, AUCUN appel réseau, AUCUN stockage persistant :
 * tout vit en mémoire React (état du composant qui l'utilise) et disparaît
 * au rafraîchissement de la page — comportement volontaire, pas un défaut
 * (voir ORGANISATION_SHARING_DEMO_REVIEW.md, section "limites").
 */

export type SharingRoleKey = 'administrateur' | 'contributeur' | 'lecteur';

export interface SharingRoleDefinition {
  key: SharingRoleKey;
  label: string;
  /** Capacités affichées telles quelles — jamais de permission technique réelle. */
  capabilities: string[];
}

/** Exactement 3 rôles — ne pas en ajouter (mandat, Mission 3). */
export const SHARING_ROLES: Record<SharingRoleKey, SharingRoleDefinition> = {
  administrateur: {
    key: 'administrateur',
    label: 'Administrateur',
    capabilities: [
      'Gère les membres',
      'Lance des analyses',
      'Modifie les décisions',
      "Consulte l'ensemble de l'organisation",
    ],
  },
  contributeur: {
    key: 'contributeur',
    label: 'Contributeur',
    capabilities: [
      'Prépare les revues',
      'Pose des questions',
      'Suit les décisions',
      'Ne gère pas les accès',
    ],
  },
  lecteur: {
    key: 'lecteur',
    label: 'Lecteur',
    capabilities: [
      'Consulte le briefing',
      'Consulte les analyses et les décisions autorisées',
      'Ne modifie rien',
    ],
  },
};

export const SHARING_ROLE_ORDER: SharingRoleKey[] = ['administrateur', 'contributeur', 'lecteur'];

/** Rôle par défaut d'une nouvelle invitation — le plus restrictif, jamais Administrateur. */
export const DEFAULT_INVITE_ROLE: SharingRoleKey = 'lecteur';

/** Membre fictif existant — jamais une vraie personne, jamais une vraie donnée. */
export interface SimulatedMember {
  id: string;
  name: string;
  role: SharingRoleKey;
}

/**
 * Liste fictive fixe, identique pour toute organisation démo — illustre le
 * concept, ne représente aucune vraie équipe.
 *
 * Le mandat donnait "Julie — Analyste" en exemple ; "Analyste" n'est pas un
 * des 3 rôles retenus (Mission 3 interdit d'en ajouter un 4e) — mappé sur
 * Contributeur, le plus proche des capacités décrites (prépare des revues,
 * ne gère pas les accès).
 */
export const SIMULATED_MEMBERS: SimulatedMember[] = [
  { id: 'sim-member-1', name: 'Frédéric', role: 'administrateur' },
  { id: 'sim-member-2', name: 'Julie', role: 'contributeur' },
  { id: 'sim-member-3', name: 'Marc', role: 'lecteur' },
];

export type SharingScope = 'this_organization' | 'selected_organizations' | 'whole_portfolio';

export interface SharingScopeOption {
  key: SharingScope;
  label: string;
  requiresExtraConfirmation: boolean;
}

/** Exactement 3 options de périmètre, dans cet ordre (mandat, Mission 4). */
export const SHARING_SCOPE_OPTIONS: SharingScopeOption[] = [
  { key: 'this_organization', label: 'Cette organisation', requiresExtraConfirmation: false },
  {
    key: 'selected_organizations',
    label: 'Plusieurs organisations sélectionnées',
    requiresExtraConfirmation: false,
  },
  { key: 'whole_portfolio', label: 'Tout le portefeuille', requiresExtraConfirmation: true },
];

/** Périmètre par défaut — le plus restreint, jamais le portefeuille entier. */
export const DEFAULT_INVITE_SCOPE: SharingScope = 'this_organization';

/** Texte de confirmation renforcée exigé pour le périmètre "Tout le portefeuille" (mandat, Mission 4). */
export const WHOLE_PORTFOLIO_CONFIRMATION_TEXT =
  'Cette personne pourra voir toutes les organisations actuelles et futures du portefeuille. Confirmer ?';

/**
 * Code temporaire purement fictif — jamais transmis, jamais stocké, jamais
 * un vrai lien d'invitation, jamais un secret réel. Format volontairement
 * proche d'un vrai code (lisible, groupé par 4) pour rendre le concept
 * crédible en test utilisateur, sans aucune valeur fonctionnelle.
 */
export function generateFakeTemporaryCode(): string {
  // Alphabet sans caractères ambigus (0/O, 1/I) — lisibilité, pas de sécurité réelle.
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const group = () =>
    Array.from({ length: 4 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join('');
  return `${group()}-${group()}`;
}

export const TEMPORARY_CODE_VALIDITY_LABEL = 'Valable 48 heures';
export const TEMPORARY_CODE_USAGE_LABEL = 'Usage unique';
