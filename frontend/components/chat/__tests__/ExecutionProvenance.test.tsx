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
test('unknown provenance refuses rather than showing mock claims',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt:{provider_mode:'unknown'}}} />);
  expect(screen.getByRole('alert')).toHaveTextContent('non vérifiable');
});
