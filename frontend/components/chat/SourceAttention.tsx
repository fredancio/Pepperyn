'use client';
import { useEffect, useState } from 'react';
import { listSourceAttention, type SourceAttentionGroup } from '@/lib/source-dossiers';

export function SourceAttention() {
  const [groups, setGroups] = useState<SourceAttentionGroup[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setGroups(null); setFailed(false);
    listSourceAttention().then(result => { if (active) setGroups(result); })
      .catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [attempt]);
  return <section aria-label="Sources synthétiques à clarifier" className="mt-6 space-y-3">
    <h2 className="font-semibold">Sources synthétiques à clarifier</h2>
    <p className="text-sm">Registre distinct des décisions. Aucun fait canonique, urgence financière ou résolution n’est déduit de cette liste.</p>
    {failed ? <p role="alert">Sources indisponibles — absence de points à clarifier non établie.</p>
      : groups === null ? <p>Lecture des sources…</p>
      : groups.length === 0 ? <p>Aucun dossier synthétique à clarifier dans le périmètre lu. Ceci ne valide pas la fiabilité financière des clients.</p>
      : groups.map(group => <article key={group.entity_id} className="rounded border bg-white p-3">
        <h3 className="font-semibold">{group.entity_name}</h3>
        {group.dossiers.map(dossier => <div key={dossier.dossier_id} className="my-2 text-sm break-words">
          <p>{dossier.filename} — {dossier.status}</p>
          <p>Dossier source : {dossier.dossier_id}</p>
          <p>Empreinte source : {dossier.source_sha256}</p>
          {dossier.conflicting_metrics?.length ? <p>Postes contradictoires : {dossier.conflicting_metrics.join(', ')}</p> : null}
          <p>Clarifier les sources avant toute conclusion dépendante. Aucune résolution enregistrée par cette vue.</p>
        </div>)}
        <a className="underline" href={`/app/chat?entity=${encodeURIComponent(group.entity_id)}`}>Consulter les dossiers de ce client</a>
      </article>)}
    <button type="button" className="border rounded p-2" onClick={() => { setGroups(null); setFailed(false); setAttempt(n => n + 1); }}>Relire les sources</button>
  </section>;
}
