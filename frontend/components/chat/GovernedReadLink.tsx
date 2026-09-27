'use client';
import { useRef, useState } from 'react';

// A navigation target, never an ownership/admission grant or a history record.
export function GovernedReadLink({ target, read }: { target: string | null; read: (id: string) => Promise<void> }) {
  const used = useRef(false);
  const [attempted, setAttempted] = useState(false);
  if (!target || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(target)) return null;
  return <section aria-label="Relecture ciblée" className="border-b bg-amber-50 p-3 text-sm">
    <p>Résultat ciblé : {target}. L’accès reste soumis à l’authentification et au contrôle d’appartenance du serveur.</p>
    <button disabled={attempted} onClick={async () => {
      if (used.current) return;
      used.current = true; setAttempted(true);
      await read(target);
    }}>Relire une seule fois le résultat ciblé</button>
  </section>;
}
