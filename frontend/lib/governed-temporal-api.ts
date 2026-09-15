import { getAuthHeaders } from './api';

export type TemporalComparison = {
  status: 'COMPARABLE' | 'PARTIALLY_COMPARABLE' | 'UNKNOWN' | 'CONTRADICTION';
  current_analysis_id: string;
  previous_analysis_id: string | null;
  current_period: string | null;
  previous_period: string | null;
  changes: Array<{ metric: string; unit: string; previous_value: number; current_value: number;
    absolute_change: number; previous_fact_id: string; current_fact_id: string }>;
  unknowns: string[];
  contradictions: string[];
  causal_interpretation: null;
};

export async function fetchGovernedTemporalComparison(analysisId: string): Promise<TemporalComparison> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/governed-analyses/${encodeURIComponent(analysisId)}/temporal-comparison`, { headers });
  if (!res.ok) throw new Error('Comparaison indisponible');
  const data = await res.json();
  const strings = (v: unknown): v is string[] => Array.isArray(v) && v.every(x => typeof x === 'string');
  const nullableString = (v: unknown) => v === null || typeof v === 'string';
  if (!data || data.current_analysis_id !== analysisId || data.causal_interpretation !== null ||
      !['COMPARABLE', 'PARTIALLY_COMPARABLE', 'UNKNOWN', 'CONTRADICTION'].includes(data.status) ||
      !nullableString(data.previous_analysis_id) || !nullableString(data.previous_period) ||
      !nullableString(data.current_period) || !strings(data.unknowns) || !strings(data.contradictions) ||
      !Array.isArray(data.changes) || !data.changes.every((c: Record<string, unknown>) => c &&
        ['metric', 'unit', 'previous_fact_id', 'current_fact_id'].every(k => typeof c[k] === 'string' && c[k]) &&
        ['previous_value', 'current_value', 'absolute_change'].every(k => typeof c[k] === 'number' && Number.isFinite(c[k])))) {
    throw new Error('Comparaison non vérifiable');
  }
  if ((['UNKNOWN', 'CONTRADICTION'].includes(data.status) && data.changes.length !== 0) ||
      (data.changes.length > 0 && (!data.previous_analysis_id || !data.previous_period || !data.current_period))) {
    throw new Error('Comparaison incohérente');
  }
  return data;
}
