/**
 * Arc Décisionnel API — MVP v16.
 *
 * Deux endpoints publics uniquement :
 *   - confirmConsequenceLink : confirmer/rejeter un lien conséquence candidate
 *   - validateLearning       : valider le learning et fermer l'arc
 *
 * NOTE : la création d'arc n'est PAS exposée ici.
 * Le backend est la source de vérité unique — l'arc est créé dans decision_memory.py
 * et retourné dans la réponse du feedback. Le frontend lit arc_id depuis cette réponse.
 */

import { getAuthHeaders } from '@/lib/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

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
