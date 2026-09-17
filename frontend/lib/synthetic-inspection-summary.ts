import type { V1SyntheticWorkbookInspection } from './api';

export function syntheticInspectionSummary(result: V1SyntheticWorkbookInspection): string {
  if (result.status === 'UNDERSTOOD') {
    return `Compréhension établie pour ${result.current_period} : ${result.facts.length} faits gouvernés.`;
  }
  if (result.status !== 'CONTRADICTION') {
    return `Compréhension ${result.status.toLowerCase()} : ${result.unknowns.join(' ')}`;
  }
  const conflicts = new Set(result.conflicting_metrics || []);
  const claims = (result.source_claims || []).map(claim =>
    `${conflicts.has(claim.metric) ? 'CONTRADICTION' : 'Observation de source indépendante du conflit (non validée)'} — ` +
    `${claim.metric} : ${claim.value} ${claim.unit}, période ${claim.period}. ` +
    `Référence ${claim.fact_id} / ${claim.source_sheet_ref} / ${claim.source_field}.`);
  const discrepancies = (result.discrepancies || []).map(item =>
    `Écart entre affirmations ${item.metric} : ${item.absolute_spread} (même unité). ` +
    `Mesure de l'écart, pas résolution. Références : ${item.claim_ids.join(', ')}.`);
  return ['Contradiction de sources — aucune valeur retenue comme vérité canonique.', ...claims, ...discrepancies,
    'Investigation requise : rapprocher les sources contradictoires et confirmer leur périmètre avant toute conclusion dépendante.',
    ...result.unknowns].join('\n');
}
