/**
 * Arc Décisionnel API — MVP v16 + Review Briefing (Capability 3).
 *
 * Endpoints publics :
 *   - confirmConsequenceLink : confirmer/rejeter un lien conséquence candidate
 *   - validateLearning       : valider le learning et fermer l'arc
 *   - fetchReviewBriefing    : lire le briefing de revue actif
 *   - abandonArc             : "Ne plus suivre" — retire un arc du briefing actif
 *
 * NOTE : la création d'arc n'est PAS exposée ici.
 * Le backend est la source de vérité unique — l'arc est créé dans decision_memory.py
 * et retourné dans la réponse du feedback. Le frontend lit arc_id depuis cette réponse.
 */

import { getAuthHeaders } from '@/lib/api';
import type { BriefingItem, PortfolioCard } from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Motifs proposés pour "Ne plus suivre" — mêmes clés que
 * ABANDON_REASON_CHOICES côté backend (models/decision_arc.py).
 */
export const ABANDON_REASON_CHOICES: Record<string, string> = {
  handled_elsewhere: 'Traité en dehors de Pepperyn',
  no_longer_relevant: 'Devenu non pertinent',
  decision_abandoned: 'Décision abandonnée',
  other: 'Autre',
};

export interface ArcConsequenceResult {
  confirmed: boolean;
  arc_id: string;
  arc_status: string;
  learning_text?: string;  // présent si confirmed=true
}

export interface ArcLearningResult {
  arc_id: string;
  status: 'closed';
  closed_at: string;
  decision_confirmation_source: 'explicit' | 'inferred_from_execution';
}

/**
 * Confirme ou rejette un lien conséquence candidate.
 *
 * Si confirmed=true → arc avance à CONSEQUENCES_LINKED puis LEARNING_PROPOSED.
 *   La réponse inclut learning_text pour afficher ArcLearningCard.
 * Si confirmed=false → lien rejeté, arc reste en EXECUTION.
 *   RÈGLE : refuser ≠ abandonner. L'arc reste ouvert pour de futurs candidats.
 */
export async function confirmConsequenceLink(
  arcId: string,
  analysisId: string,
  confirmed: boolean,
  rejectionReason?: string,
): Promise<ArcConsequenceResult> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/arcs/${arcId}/consequence`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      analysis_id: analysisId,
      confirmed,
      rejection_reason: rejectionReason,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur confirmation conséquence');
  }
  return res.json();
}

/**
 * Valide le learning et ferme l'arc (CLOSED).
 *
 * GUARD : decision_text IS NOT NULL requis pour CLOSED.
 * Si l'arc a decision_text=NULL (décision inférée, jamais documentée),
 * passer decision_text ici constitue une confirmation rétrospective explicite.
 *
 * Retourne HTTP 422 si decision_text est manquant et non fourni.
 */
export async function validateLearning(
  arcId: string,
  options: {
    action: 'validate' | 'modify';
    learning_text?: string;
    decision_text?: string;  // requis si arc.decision_text === null
  },
): Promise<ArcLearningResult> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/arcs/${arcId}/learning`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify(options),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur validation learning');
  }
  return res.json();
}

/**
 * Lit le Review Briefing actif — synthèse opérationnelle des décisions
 * suivies avec un client, priorisées, avec questions prêtes à poser.
 *
 * entityId optionnel : scope sur le client actuellement sélectionné
 * (même convention que fetchAnalysesHistory). Sans lui, renvoie les arcs
 * actifs de toute la company.
 *
 * Périmètre : uniquement les décisions/recommandations DecisionArc —
 * jamais d'échéances comptables, fiscales ou administratives.
 */
export async function fetchReviewBriefing(
  entityId?: string,
  limit = 5,
): Promise<BriefingItem[]> {
  const headers = await getAuthHeaders();
  const params = new URLSearchParams();
  if (entityId) params.set('entity_id', entityId);
  if (limit) params.set('limit', String(limit));
  const qs = params.toString();
  const res = await fetch(`${API_URL}/api/review-briefing${qs ? `?${qs}` : ''}`, {
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lecture du briefing de revue');
  }
  const data = await res.json();
  return data.items as BriefingItem[];
}

/**
 * Lit le Portfolio Intelligence (Incrément 1) — une carte par client,
 * triée par priorité, portant son point le plus prioritaire du Briefing
 * de revue. Regroupement pur côté backend, aucune nouvelle donnée.
 */
export async function fetchPortfolio(): Promise<PortfolioCard[]> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/portfolio`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lecture du portefeuille');
  }
  const data = await res.json();
  return data.cards as PortfolioCard[];
}

/**
 * "Ne plus suivre" — retire un arc du Review Briefing actif.
 *
 * RÈGLE SÉMANTIQUE : ne signifie jamais que le sujet est réglé, résolu ou
 * exécuté — uniquement que le suivi s'arrête. L'arc n'est jamais supprimé ;
 * historique et liens restent intacts (transition vers status='abandoned').
 */
export async function abandonArc(
  arcId: string,
  reason?: string,
): Promise<{ abandoned: boolean; arc_id: string; already_abandoned?: boolean }> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/arcs/${arcId}/abandon`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: reason ?? null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors du retrait du briefing actif');
  }
  return res.json();
}
