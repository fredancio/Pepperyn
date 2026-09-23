'use client';
import { useEffect, useState } from 'react';
import { fetchGovernedTemporalComparison, type TemporalComparison } from '@/lib/governed-temporal-api';

export function GovernedTemporalComparison({ analysisId }: { analysisId: string }) {
  const [state, setState] = useState<{ id: string; data?: TemporalComparison; error?: boolean }>({ id: analysisId });
  useEffect(() => {
    let active = true;
    setState({ id: analysisId });
    fetchGovernedTemporalComparison(analysisId).then(
      data => { if (active) setState({ id: analysisId, data }); },
      () => { if (active) setState({ id: analysisId, error: true }); },
    );
    return () => { active = false; };
  }, [analysisId]);
  const data = state.id === analysisId ? state.data : undefined;
  return <section aria-label="Continuité temporelle" className="rounded-xl border bg-white p-4 text-sm">
    <h3 className="font-semibold">Évolution depuis la période précédente</h3>
    {state.id === analysisId && state.error ? <p role="alert">Comparaison indisponible — aucune absence de changement ne peut être déduite.</p> : !data ? <p>Chargement de la comparaison…</p> : <>
      <p>{({ COMPARABLE: 'Écarts arithmétiques disponibles', PARTIALLY_COMPARABLE: 'Comparaison partielle', UNKNOWN: 'Comparaison non établie — UNKNOWN', CONTRADICTION: 'Comparaison refusée — CONTRADICTION' })[data.status]}</p>
      {data.previous_period && <p>{data.previous_period} → {data.current_period}</p>}
      {data.changes.length > 0 && <div className="overflow-x-auto"><table className="w-full text-left">
        <thead><tr><th>Métrique</th><th>Avant</th><th>Après</th><th>Écart</th></tr></thead>
        <tbody>{data.changes.map(c => <tr key={c.metric}>
          <td>{c.metric}<small className="block">{c.previous_fact_id} → {c.current_fact_id}</small></td>
          <td>{c.previous_value} {c.unit}</td><td>{c.current_value} {c.unit}</td><td>{c.absolute_change} {c.unit}</td>
        </tr>)}</tbody>
      </table></div>}
      {[...data.unknowns, ...data.contradictions].map((text, i) => <p key={i}>{text}</p>)}
      {data.status === 'CONTRADICTION' && data.contradictions.some(reason =>
        reason === 'Plusieurs analyses gouvernées existent pour la période courante.' ||
        reason === 'Plusieurs analyses gouvernées existent pour la période antérieure la plus proche.',
      ) && <div className="mt-2 rounded-lg bg-amber-50 p-3 text-amber-950">
        <p>Le couple de références temporelles n’est pas unique pour ce client et cette mission. Ce refus ne démontre pas, à lui seul, que les montants sont contradictoires.</p>
        <p>À résoudre : vérifier les versions, les sources et les périodes des analyses concernées, puis établir de façon gouvernée quelle référence fait autorité pour chaque période. Pepperyn ne choisit pas automatiquement la plus récente et ne fusionne pas les analyses.</p>
        <p>Aucun écart temporel n’est établi tant que cette ambiguïté subsiste. Ne supprimez pas une analyse pour forcer la comparaison ; la résolution des références reste à documenter.</p>
      </div>}
      <p className="mt-2 text-xs">Analyse courante : {data.current_analysis_id}{data.previous_analysis_id && ` — antérieure : ${data.previous_analysis_id}`}</p>
      <p className="text-xs">Comparaison bornée aux faits disponibles. Ni explication causale, ni résultat d’une décision, ni apprentissage établi.</p>
      <p className="text-xs">Arithmétique sur libellés annuels uniquement. Durée, couverture, périmètre et conventions comptables comparables non établis : aucune comparabilité financière professionnelle certifiée.</p>
    </>}
  </section>;
}
