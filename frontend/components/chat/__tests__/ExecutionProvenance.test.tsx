import { render, screen } from '@testing-library/react';
import { ExecutionProvenance } from '../ExecutionProvenance';

test('legacy absence never acquires a synthetic label',()=>{
  render(<ExecutionProvenance value={{status:'UNATTESTED',receipt:null}} />);
  expect(screen.getByText(/non attestée/)).toBeInTheDocument();
  expect(screen.queryByText(/fournisseur simulé/)).not.toBeInTheDocument();
});
test('verified local receipt displays its evidence and limits',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt:{provider_mode:'LOCAL_MOCK',transport:'NONE',
    data_origin:'REGISTERED_SYNTHETIC',execution_id:'synthetic-id',raw_source_sha256:'source-hash',envelope_sha256:'envelope-hash'}}} />);
  expect(screen.getByText(/synthetic-id/)).toBeInTheDocument();
  expect(screen.getByText(/source-hash/)).toBeInTheDocument();
  expect(screen.getByText(/pas une certification/)).toBeInTheDocument();
});
test('unknown provenance refuses rather than showing mock claims',()=>{
  render(<ExecutionProvenance value={{status:'VERIFIED_RECEIPT',receipt:{provider_mode:'unknown'}}} />);
  expect(screen.getByRole('alert')).toHaveTextContent('non vérifiable');
});
