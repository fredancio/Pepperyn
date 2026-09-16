'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchAnalysesHistory } from '@/lib/api';
import type { Session } from '@/lib/types';

export function useClientHistory(entityId: string | null) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [loadedScope, setLoadedScope] = useState(entityId);
  const current = useRef(entityId);
  const sequence = useRef(0);
  if (current.current !== entityId) {
    sequence.current += 1;
    current.current = entityId;
  }
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; sequence.current += 1; };
  }, []);
  const refresh = useCallback(async () => {
    const scope = current.current;
    const request = ++sequence.current;
    const active = () => alive.current && current.current === scope && sequence.current === request;
    setLoading(true);
    setError(false);
    try {
      const analyses = await fetchAnalysesHistory(scope || undefined);
      if (!active()) return;
      setLoadedScope(scope);
      setSessions(analyses.map(a => ({ id: a.id, company_id: '', is_admin_session: false,
        titre: a.fichier_nom || `Analyse ${a.type_document || ''}`.trim(), is_archived: false,
        created_at: a.created_at, updated_at: a.created_at })));
    } catch {
      if (active()) { setLoadedScope(scope); setSessions([]); setError(true); }
    } finally {
      if (active()) setLoading(false);
    }
  }, []);
  return { sessions: loadedScope === entityId ? sessions : [], setSessions, loading,
    error: loadedScope === entityId && error, refresh };
}
