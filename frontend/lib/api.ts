const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getAuthHeaders(): Promise<Record<string, string>> {
  if (typeof window === 'undefined') return {};

  // Try guest token first
  const guestToken = sessionStorage.getItem('pepperyn_guest_token');
  if (guestToken) {
    return {
      'Authorization': `Bearer ${guestToken}`,
      'X-Auth-Type': 'guest',
    };
  }

  // Try admin Supabase token
  const { supabase } = await import('./supabase');
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'X-Auth-Type': 'admin',
    };
  }

  return {};
}

export async function loginWithPin(pin: string) {
  const res = await fetch(`${API_URL}/api/auth/pin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pin }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Code PIN incorrect');
  }
  return res.json();
}

export async function loginWithPinAndEmail(email: string, pin: string) {
  const res = await fetch(`${API_URL}/api/auth/pin-guest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, pin }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Email ou code PIN incorrect');
  }
  return res.json();
}

export async function analyzeFile(
  file: File,
  context: string,
  mode: 'quick' | 'complete' = 'complete',
  sessionId?: string,
  entityId?: string,
  analysisPeriodMonths?: number,
  targetDate?: string
) {
  const headers = await getAuthHeaders();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('context', context);
  formData.append('mode', mode);
  if (sessionId) formData.append('session_id', sessionId);
  if (entityId) formData.append('entity_id', entityId);
  if (analysisPeriodMonths !== undefined) formData.append('analysis_period_months', String(analysisPeriodMonths));
  if (targetDate) formData.append('target_date', targetDate);

  const res = await fetch(`${API_URL}/api/analyze`, {
    method: 'POST',
    headers,
    body: formData,
  });

  // La réponse peut être précédée d'octets "heartbeat" (espaces) envoyés
  // pendant le traitement des analyses longues, pour éviter qu'un proxy
  // ne coupe la connexion par inactivité. JSON.parse ignore les espaces
  // de tête, donc on parse le texte brut nous-mêmes.
  const text = await res.text();
  const trimmed = text.trim();

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let data: any = null;
  if (trimmed) {
    try {
      data = JSON.parse(trimmed);
    } catch {
      // Réponse reçue mais JSON invalide — lever une erreur explicite
      throw new Error("La réponse du serveur n'a pas pu être décodée. Réessayez dans quelques instants.");
    }
  } else {
    // Corps vide : la connexion streaming a été coupée avant le JSON final
    throw new Error("La réponse de l'analyse n'a pas été reçue (connexion interrompue). Réessayez.");
  }

  if (!res.ok) {
    throw new Error((data as { detail?: string }).detail || "Erreur lors de l'analyse");
  }
  if ((data as { success?: boolean }).success === false) {
    throw new Error((data as { message?: string }).message || "Erreur lors de l'analyse");
  }
  return data;
}

export async function analyzeText(
  query: string,
  sessionId?: string
) {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/analyze/text`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Erreur lors de l'analyse");
  }
  return res.json();
}

export async function updatePin(newPin: string) {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/admin/update-pin`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_pin: newPin }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors de la mise à jour du PIN');
  }
  return res.json();
}

export async function downloadExcel(analyseId: string): Promise<Blob> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/export/${analyseId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors du téléchargement Excel');
  }
  return res.blob();
}

export async function downloadPdf(analyseId: string): Promise<Blob> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/export-pdf/${analyseId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors du téléchargement PDF');
  }
  return res.blob();
}

export async function downloadPptx(analyseId: string): Promise<Blob> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/export-pptx/${analyseId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors du téléchargement PowerPoint');
  }
  return res.blob();
}

export async function fetchAnalysesHistory(entityId?: string): Promise<Array<{
  id: string;
  fichier_nom: string;
  type_document: string;
  created_at: string;
  score_confiance: number;
  entity_id?: string;
}>> {
  const headers = await getAuthHeaders();
  const url = entityId
    ? `${API_URL}/api/analyses/history?entity_id=${entityId}`
    : `${API_URL}/api/analyses/history`;
  const res = await fetch(url, { headers });
  if (!res.ok) return [];
  const data = await res.json();
  return data.analyses || [];
}

export async function deleteAnalysesHistory(): Promise<{ success: boolean; deleted: number }> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/analyses/history`, {
    method: 'DELETE',
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Erreur lors de la suppression de l'historique");
  }
  return res.json();
}

// Relation de l'entité secondaire avec l'entité principale :
// - "filiale" : filiale du groupe (l'analyse situe son poids/risque au niveau du groupe)
// - "client"  : client suivi par l'utilisateur (l'analyse aide à évaluer la relation)
// - undefined/null : non renseigné (entité principale, ou non précisé)
export type EntityRelationType = 'filiale' | 'client';

export interface Entity {
  id: string;
  name: string;
  industry?: string;
  business_model?: string;
  is_primary: boolean;
  relation_type?: EntityRelationType | null;
  workspace_id: string;
  created_at: string;
}

export async function createEntity(name: string, relationType?: EntityRelationType): Promise<Entity> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/entities`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, relation_type: relationType ?? null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Erreur création client ou entreprise');
  }
  return res.json();
}

export async function fetchEntities(): Promise<Entity[]> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_URL}/api/entities`, { headers });
    if (!res.ok) return [];
    const data = await res.json();
    return data.data || [];
  } catch {
    return [];
  }
}

export interface BillingUsage {
  plan: string;
  year_month: string;

  // ── Quota mensuel ────────────────────────────────────────────────────────
  analyses_used: number;               // analyses consommées ce mois
  analyses_limit: number;              // quota mensuel du plan
  analyses_monthly_used: number;       // = analyses_used en Option B
  analyses_monthly_remaining: number | null;  // calculé par le backend

  // ── Executive Capacity Pack (Option B — companies.bonus_analyses_remaining)
  analyses_bonus_remaining: number;    // stock permanent — jamais remis à zéro
  analyses_bonus_suspended: boolean;   // true si plan FREE avec stock > 0
  analyses_total_allowed: number | null;
  analyses_remaining: number | null;   // total immédiatement utilisable

  // ── Interactions ─────────────────────────────────────────────────────────
  interactions_used: number;
  interactions_limit: number | null;
  interactions_remaining: number | null;

  // ── Entités & Renouvellement ─────────────────────────────────────────────
  max_entities: number | null;
  renewal_date: string;                // ISO8601 — 1er du mois suivant UTC

  // ── Aliases compat — à supprimer en WP5 ─────────────────────────────────
  bonus_analyses?: number;
  total_allowed?: number | null;
}

export async function fetchBillingUsage(): Promise<BillingUsage | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_URL}/api/billing/usage`, { headers });
    if (!res.ok) return null;
    const data = await res.json();
    return data.data || null;
  } catch {
    return null;
  }
}

// ─── Decision Memory (mémoire décisionnelle) ──────────────────────────────

import type { PreviousRecommendations, DecisionFeedbackStatus } from './types';

/**
 * Récupère les recommandations du dernier rapport complété, avec le statut/
 * commentaire déjà enregistré pour chacune (ou null si pas encore de feedback).
 * Utilisé pour l'écran de pré-analyse et les cartes de feedback post-rapport.
 * Aucun appel à Claude — lecture Supabase uniquement.
 */
export async function fetchPreviousRecommendations(): Promise<PreviousRecommendations> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_URL}/api/decision-feedback/previous`, { headers });
    if (!res.ok) return { has_previous: false, report_id: null, recommendations: [] };
    return res.json();
  } catch {
    return { has_previous: false, report_id: null, recommendations: [] };
  }
}

/**
 * Récupère le contexte conversationnel V2 pour un analyse_id donné.
 * Retourne auto_opening_message, suggested_quick_prompts et sacred_sentence.
 * Retourne null silencieusement en cas d'erreur (analyse non encore disponible, etc.).
 */
export async function fetchConversationContext(analyseId: string): Promise<{
  auto_opening_message: string;
  suggested_quick_prompts: string[];
  sacred_sentence: string;
} | null> {
  try {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_URL}/api/conversation-context/${analyseId}`, { headers });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/**
 * Enregistre (ou met à jour) le feedback de l'utilisateur sur une
 * recommandation : intention (post-rapport) ou bilan (pré-analyse).
 * Aucun appel à Claude — écriture Supabase uniquement.
 */
export async function submitDecisionFeedback(params: {
  report_id: string;
  recommendation_id: string;
  recommendation_text: string;
  recommendation_source?: string;
  status: DecisionFeedbackStatus;
  comment?: string;
}): Promise<{
  success: boolean;
  // Arc Décisionnel MVP v16 — présent si status='planned' et arc créé côté backend
  arc_created?: boolean;
  arc_id?: string | null;
  arc_status?: string | null;
}> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/decision-feedback`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Erreur lors de l'enregistrement du feedback");
  }
  return res.json();
}
