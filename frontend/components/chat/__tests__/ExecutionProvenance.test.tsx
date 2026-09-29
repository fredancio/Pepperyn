import { render, screen } from '@testing-library/react';
import { ExecutionProvenance } from '../ExecutionProvenance';

test('legacy absence never acquires a synthetic label',()=>{
  render(<ExecutionProvenance value={{status:'UNATTESTED',receipt:null}} />);
  expect(screen.getByText(/non attestée/)).toBeInTheDocument();
  expect(screen.queryByText(/fournisseur simulé/)).not.toBeInTheDocument();
});
test('verified local receipt displays its evidence and limits',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt_version:'V39',receipt:{schema_version:'execution-provenance-1',
    provider_mode:'LOCAL_MOCK',executor:'registered-workbook-mock-v1',transport:'NONE',data_origin:'REGISTERED_SYNTHETIC',
    execution_id:'synthetic-id',raw_source_sha256:'source-hash',source_representation_sha256:'representation-hash',envelope_sha256:'envelope-hash'}}} />);
  expect(screen.getByText(/synthetic-id/)).toBeInTheDocument();
  expect(screen.getByText(/source-hash/)).toBeInTheDocument();
  expect(screen.getByText(/pas une certification/)).toBeInTheDocument();
});
test('verified V40 receipt displays versioned producer, task and limits',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt_version:'V40',receipt:{schema_version:'governed-execution-receipt-2',
    evidence_scope:'LOCAL_SYNTHETIC_ONLY',egress:'DENY',transport:'NONE',data_origin:'REGISTERED_SYNTHETIC',
    producer_id:'local-synthetic-analysis-v2',producer_version:'producer-v2',task_id:'financial-analysis',task_version:'task-v1',
    contract_version:'local-synthetic-durable-admission-2',admission_contract_sha256:'contract-hash',
    producer_input_sha256:'input-hash',composition_sha256:'composition-hash',execution_id:'execution-id',raw_source_sha256:'source-hash',
    source_representation_sha256:'representation-hash',envelope_sha256:'envelope-hash'}}} />);
  expect(screen.getByText(/reçu V40 durable vérifié/)).toBeInTheDocument();
  expect(screen.getByText(/local-synthetic-analysis-v2/)).toBeInTheDocument();
  expect(screen.getByText(/financial-analysis/)).toBeInTheDocument();
  expect(screen.getByText(/local-synthetic-durable-admission-2/)).toBeInTheDocument();
  expect(screen.getByText(/input-hash/)).toBeInTheDocument();
  expect(screen.getByText(/composition-hash/)).toBeInTheDocument();
  expect(screen.getByText(/producteur générique reste non admis/)).toBeInTheDocument();
});
test('verified V41 injected receipt never claims an attested OpenAI execution',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt_version:'V41',receipt:{
    schema_version:'governed-generic-producer-receipt-3',data_origin:'SYNTHETIC_ONLY',
    transport:'INJECTED_LOCAL_ONLY',provider_execution_attested:false,
    admission_scope:'LOCAL_TEST_ADMISSION',producer_admission_status:'UNADMITTED',
    producer_id:'openai-responses-financial-analysis',producer_version:'gpt-5-contract-v1',
    task_id:'governed-financial-analysis',task_version:'v1-governed-single-call',
    contract_binding_sha256:'contract-hash',fact_schema_version:'facts-v1',
    positive_projection_policy_version:'projection-v1',output_contract_version:'output-v1',
    request_sha256:'request-hash',response_sha256:'response-hash',
    provider_policy_evidence_sha256:'policy-hash',execution_id:'execution-id',
    raw_source_sha256:'source-hash',source_representation_sha256:'representation-hash',
    envelope_sha256:'envelope-hash'}}} />);
  expect(screen.getByText(/reçu V41 durable vérifié/)).toBeInTheDocument();
  expect(screen.getByText(/aucune exécution OpenAI attestée/)).toBeInTheDocument();
  expect(screen.getByText(/non admis globalement/)).toBeInTheDocument();
  expect(screen.getByText(/request-hash/)).toBeInTheDocument();
  expect(screen.getByText(/response-hash/)).toBeInTheDocument();
});
test('V41 injected receipt claiming provider attestation refuses',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt_version:'V41',receipt:{
    schema_version:'governed-generic-producer-receipt-3',data_origin:'SYNTHETIC_ONLY',
    transport:'INJECTED_LOCAL_ONLY',provider_execution_attested:true,
    producer_id:'p',producer_version:'v',task_id:'t',task_version:'v',
    contract_binding_sha256:'c',fact_schema_version:'f',positive_projection_policy_version:'p',
    output_contract_version:'o',request_sha256:'r',response_sha256:'s',
    provider_policy_evidence_sha256:'e',execution_id:'x',raw_source_sha256:'x',
    source_representation_sha256:'x',envelope_sha256:'x'}}} />);
  expect(screen.getByRole('alert')).toHaveTextContent('non vérifiable');
});
test('V41 OpenAI transport is outside the bounded local-test contract',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt_version:'V41',receipt:{
    schema_version:'governed-generic-producer-receipt-3',data_origin:'SYNTHETIC_ONLY',
    transport:'OPENAI_RESPONSES',provider_execution_attested:false,
    producer_id:'p',producer_version:'v',task_id:'t',task_version:'v',
    contract_binding_sha256:'c',fact_schema_version:'f',positive_projection_policy_version:'p',
    output_contract_version:'o',request_sha256:'r',response_sha256:'s',
    provider_policy_evidence_sha256:'e',execution_id:'x',raw_source_sha256:'x',
    source_representation_sha256:'x',envelope_sha256:'x'}}} />);
  expect(screen.getByRole('alert')).toHaveTextContent('non vérifiable');
});
test('unknown provenance refuses rather than showing mock claims',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt:{provider_mode:'unknown'}}} />);
  expect(screen.getByRole('alert')).toHaveTextContent('non vérifiable');
});
