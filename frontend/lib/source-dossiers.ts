import { getAuthHeaders, type V1SyntheticWorkbookInspection } from './api';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export type SourceDossier = V1SyntheticWorkbookInspection & {
  dossier_id: string; company_id: string; entity_id: string; engagement_id: string;
  payload_sha256: string; schema_version: 'synthetic-source-dossier-1';
  evidence_role: 'SOURCE_INSPECTION_NOT_ANALYSIS';
};
const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
function checked(value: unknown, entity: string, id?: string): SourceDossier {
  const row = value as SourceDossier;
  if (!row || !uuid.test(row.dossier_id) || (id && row.dossier_id !== id) || row.entity_id !== entity ||
      !uuid.test(row.company_id) || !uuid.test(row.engagement_id) || typeof row.filename !== 'string' ||
      !/^[A-F0-9]{64}$/.test(row.source_sha256) || !/^[A-F0-9]{64}$/.test(row.payload_sha256) ||
      row.evidence_role !== 'SOURCE_INSPECTION_NOT_ANALYSIS' || row.schema_version !== 'synthetic-source-dossier-1' ||
      row.provider_dispatch !== 'CLOSED' || !['UNDERSTOOD', 'AMBIGUOUS', 'INSUFFICIENT', 'CONTRADICTION'].includes(row.status) ||
      !Array.isArray(row.facts) || !Array.isArray(row.unknowns) || !row.unknowns.every(v => typeof v === 'string') ||
      !Array.isArray(row.source_claims) || !Array.isArray(row.conflicting_metrics) ||
      !row.conflicting_metrics.every(v => typeof v === 'string') ||
      (row.status !== 'UNDERSTOOD' && row.facts.length !== 0) ||
      (row.status === 'CONTRADICTION' && (!row.source_claims.length || !row.conflicting_metrics.length))) {
    throw new Error('Dossier source non vérifiable.');
  }
  for (const claim of row.source_claims) {
    if (!claim || typeof claim.metric !== 'string' || !Number.isFinite(claim.value) ||
        !/^F[A-F0-9]{12}$/.test(claim.fact_id) || !/^S[A-F0-9]{12}$/.test(claim.source_sheet_ref) ||
        !/^R[A-F0-9]{12}$/.test(claim.source_field) || typeof claim.period !== 'string' || typeof claim.unit !== 'string') {
      throw new Error('Référence de source non vérifiable.');
    }
  }
  if (!Array.isArray(row.discrepancies) || !row.discrepancies.every(item => item &&
      typeof item.metric === 'string' && item.interpretation === 'DISCREPANCY_NOT_RESOLUTION' &&
      typeof item.absolute_spread === 'string' && /^\d+(?:\.\d+)?(?:E[+-]?\d+)?$/i.test(item.absolute_spread) &&
      Array.isArray(item.claim_ids) && item.claim_ids.every(id => row.source_claims!.some(claim => claim.fact_id === id)))) {
    throw new Error('Écart de source non vérifiable.');
  }
  return row;
}
async function request(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API}/api/v1/synthetic-source-dossiers${path}`, {
    ...options, headers: await getAuthHeaders(), cache: 'no-store',
  });
  if (!response.ok) throw new Error('Dossiers sources indisponibles.');
  return response.json();
}
export async function listSourceDossiers(entity: string): Promise<SourceDossier[]> {
  const rows = await request(`?entity_id=${encodeURIComponent(entity)}`);
  if (!Array.isArray(rows) || rows.length > 100) throw new Error('Liste des dossiers non vérifiable.');
  const checkedRows = rows.map(row => checked(row, entity));
  if (new Set(checkedRows.map(row => row.dossier_id)).size !== checkedRows.length) throw new Error('Dossiers dupliqués.');
  return checkedRows;
}
export async function loadSourceDossier(entity: string, id: string): Promise<SourceDossier> {
  return checked(await request(`/${encodeURIComponent(id)}?entity_id=${encodeURIComponent(entity)}`), entity, id);
}
export async function captureSourceDossier(entity: string, file: File): Promise<SourceDossier> {
  const data = new FormData(); data.append('entity_id', entity); data.append('file', file);
  return checked(await request('', { method: 'POST', body: data }), entity);
}

export type SourceAttentionGroup = { entity_id: string; entity_name: string; dossiers: SourceDossier[] };
export async function listSourceAttention(): Promise<SourceAttentionGroup[]> {
  const response = await fetch(`${API}/api/v1/synthetic-source-attention`, {
    headers: await getAuthHeaders(), cache: 'no-store',
  });
  if (!response.ok) throw new Error('Lecture des sources indisponible.');
  const groups = await response.json();
  if (!Array.isArray(groups) || groups.length > 100) throw new Error('Sources non vérifiables.');
  const entities = new Set<string>(), dossiers = new Set<string>(), companies = new Set<string>();
  return groups.map(group => {
    if (!group || !uuid.test(group.entity_id) || entities.has(group.entity_id) ||
        typeof group.entity_name !== 'string' || !group.entity_name.trim() ||
        !Array.isArray(group.dossiers) || !group.dossiers.length) throw new Error('Client source non vérifiable.');
    entities.add(group.entity_id);
    const verified = group.dossiers.map((value: unknown) => {
      const row = checked(value, group.entity_id);
      if (row.status === 'UNDERSTOOD' || dossiers.has(row.dossier_id)) throw new Error('Source incohérente.');
      dossiers.add(row.dossier_id); companies.add(row.company_id);
      if (dossiers.size > 100 || companies.size > 1) throw new Error('Périmètre source incohérent.');
      return row;
    });
    return { entity_id: group.entity_id, entity_name: group.entity_name, dossiers: verified };
  });
}
