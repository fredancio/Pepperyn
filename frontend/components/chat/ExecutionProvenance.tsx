/** Server-owned receipt projection. Never infer provenance from filename/model. */
export function ExecutionProvenance({ value }: { value: unknown }) {
  if (!value || typeof value !== 'object') return null;
  const provenance = value as Record<string, unknown>;
  if (provenance.status === 'UNATTESTED') return <p role="note">Origine d’exécution non attestée — aucun reçu durable disponible.</p>;
  const receipt = provenance.receipt as Record<string, unknown> | undefined;
  const version = provenance.receipt_version;
  const v39 = version === 'V39' && receipt?.schema_version === 'execution-provenance-1' &&
    receipt.provider_mode === 'LOCAL_MOCK' && receipt.executor === 'registered-workbook-mock-v1';
  const v40 = version === 'V40' && receipt?.schema_version === 'governed-execution-receipt-2' &&
    receipt.evidence_scope === 'LOCAL_SYNTHETIC_ONLY' && receipt.egress === 'DENY' &&
    receipt.transport === 'NONE' && typeof receipt.producer_id === 'string' &&
    typeof receipt.producer_version === 'string' && typeof receipt.task_id === 'string' &&
    typeof receipt.task_version === 'string' && typeof receipt.contract_version === 'string' &&
    typeof receipt.admission_contract_sha256 === 'string' &&
    typeof receipt.producer_input_sha256 === 'string' && typeof receipt.composition_sha256 === 'string';
  if (provenance.status !== 'VERIFIED_RECEIPT' || !receipt || (!v39 && !v40) ||
      receipt.data_origin !== 'REGISTERED_SYNTHETIC' ||
      typeof receipt.execution_id !== 'string' || typeof receipt.raw_source_sha256 !== 'string' ||
      typeof receipt.source_representation_sha256 !== 'string' ||
      typeof receipt.envelope_sha256 !== 'string') return <p role="alert">Provenance d’exécution non vérifiable.</p>;
  return <details className="rounded-lg border p-3 text-sm break-all">
    <summary>Provenance d’exécution — reçu {String(version)} durable vérifié</summary>
    <p>{v39
      ? 'Données synthétiques enregistrées ; fournisseur simulé local ; aucun transport fournisseur dans cet exécuteur.'
      : 'Exécution synthétique locale admise ; egress interdit ; le producteur générique reste non admis.'}</p>
    {v40 && <p>Producteur : {String(receipt.producer_id)} / {String(receipt.producer_version)}</p>}
    {v40 && <p>Tâche : {String(receipt.task_id)} / {String(receipt.task_version)}</p>}
    {v40 && <p>Contrat : {String(receipt.contract_version)}</p>}
    <p>Exécution : {receipt.execution_id}</p>
    <p>Source SHA-256 : {receipt.raw_source_sha256}</p>
    <p>Représentation SHA-256 : {receipt.source_representation_sha256}</p>
    {v40 && <p>Entrée producteur SHA-256 : {String(receipt.producer_input_sha256)}</p>}
    {v40 && <p>Composition SHA-256 : {String(receipt.composition_sha256)}</p>}
    <p>Enveloppe SHA-256 : {receipt.envelope_sha256}</p>
    <p>Ce reçu n’est pas une certification de l’infrastructure ni de la fiabilité financière.</p>
  </details>;
}
