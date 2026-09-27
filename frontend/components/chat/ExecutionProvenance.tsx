/** Server-owned receipt projection. Never infer provenance from filename/model. */
export function ExecutionProvenance({ value }: { value: unknown }) {
  if (!value || typeof value !== 'object') return null;
  const provenance = value as Record<string, unknown>;
  if (provenance.status === 'UNATTESTED') return <p role="note">Origine d’exécution non attestée — aucun reçu durable disponible.</p>;
  const receipt = provenance.receipt as Record<string, unknown> | undefined;
  if (provenance.status !== 'VERIFIED_RECEIPT' || !receipt ||
      receipt.provider_mode !== 'LOCAL_MOCK' || receipt.transport !== 'NONE' ||
      receipt.data_origin !== 'REGISTERED_SYNTHETIC' ||
      typeof receipt.execution_id !== 'string' || typeof receipt.raw_source_sha256 !== 'string' ||
      typeof receipt.envelope_sha256 !== 'string') return <p role="alert">Provenance d’exécution non vérifiable.</p>;
  return <details className="rounded-lg border p-3 text-sm break-all">
    <summary>Provenance d’exécution — reçu durable vérifié</summary>
    <p>Données synthétiques enregistrées ; fournisseur simulé local ; aucun transport fournisseur dans cet exécuteur.</p>
    <p>Exécution : {receipt.execution_id}</p>
    <p>Source SHA-256 : {receipt.raw_source_sha256}</p>
    <p>Enveloppe SHA-256 : {receipt.envelope_sha256}</p>
    <p>Ce reçu n’est pas une certification de l’infrastructure ni de la fiabilité financière.</p>
  </details>;
}
