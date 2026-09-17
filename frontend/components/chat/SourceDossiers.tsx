'use client';
import { useEffect, useRef, useState } from 'react';
import { captureSourceDossier, listSourceDossiers, loadSourceDossier, type SourceDossier } from '@/lib/source-dossiers';
import { syntheticInspectionSummary } from '@/lib/synthetic-inspection-summary';

export function SourceDossiers({ entityId }: { entityId: string | null }) {
  return entityId ? <ScopedDossiers key={entityId} entityId={entityId} />
    : <p>Sélectionnez explicitement un client pour consulter ses dossiers sources synthétiques.</p>;
}

function ScopedDossiers({ entityId }: { entityId: string }) {
  const [rows, setRows] = useState<SourceDossier[] | null>(null);
  const [selected, setSelected] = useState<SourceDossier | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const active = useRef(true), epoch = useRef(0), writing = useRef(false);
  const input = useRef<HTMLInputElement>(null);
  async function refresh() {
    const version = ++epoch.current;
    setError(''); setRows(null);
    try {
      const result = await listSourceDossiers(entityId);
      if (active.current && version === epoch.current) setRows(result);
    } catch {
      if (active.current && version === epoch.current) setError('Lecture indisponible — absence de dossiers non établie.');
    }
  }
  useEffect(() => {
    active.current = true; void refresh();
    return () => { active.current = false; epoch.current++; };
    // Keyed scope: remount, do not retain another client's state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  async function open(id: string) {
    const version = ++epoch.current; setSelected(null); setError('');
    try {
      const result = await loadSourceDossier(entityId, id);
      if (active.current && epoch.current === version) setSelected(result);
    } catch {
      if (active.current && epoch.current === version) setError('Dossier indisponible — aucun contenu de remplacement.');
    }
  }
  async function save() {
    if (!file || writing.current) return;
    writing.current = true; ++epoch.current; setBusy(true); setError('');
    try {
      const result = await captureSourceDossier(entityId, file);
      if (!active.current) return;
      setSelected(result); setFile(null); if (input.current) input.current.value = ''; await refresh();
    } catch {
      if (active.current) setError('Enregistrement non confirmé. Relisez les dossiers avant toute nouvelle tentative.');
    } finally {
      writing.current = false; if (active.current) setBusy(false);
    }
  }
  return <section className="w-full rounded-xl border border-amber-400 p-4 space-y-3" aria-label="Dossiers sources synthétiques">
    <h3 className="font-semibold">Dossiers sources synthétiques</h3>
    <p className="text-sm">Capture de sources uniquement : aucune analyse fournisseur, décision ou résolution automatique.</p>
    <input ref={input} aria-label="Classeur source synthétique" type="file" accept=".xlsx" disabled={busy}
      onChange={event => setFile(event.target.files?.[0] || null)} />
    <button type="button" disabled={!file || busy} onClick={() => void save()} className="border rounded p-2 disabled:opacity-50">
      Enregistrer explicitement le dossier source
    </button>
    <button type="button" disabled={busy} onClick={() => void refresh()} className="border rounded p-2">Relire les dossiers</button>
    {error && <p role="alert">{error}</p>}
    {!error && rows === null && <p>Lecture des dossiers…</p>}
    {rows?.length === 0 && <p>Aucun dossier source enregistré pour ce client.</p>}
    {rows?.map(row => <button type="button" key={row.dossier_id} disabled={busy} onClick={() => void open(row.dossier_id)}
      className="block underline">{row.filename} — {row.status}</button>)}
    {selected && <article>
      <p>Dossier enregistré : {selected.dossier_id}</p>
      <p>Empreinte source : {selected.source_sha256}</p>
      <p className="whitespace-pre-wrap">{syntheticInspectionSummary(selected)}</p>
      <p>Aucun appel fournisseur effectué. Ce dossier ne constitue pas une analyse gouvernée.</p>
    </article>}
  </section>;
}
