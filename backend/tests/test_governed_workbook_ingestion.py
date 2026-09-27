"""Synthetic local parsing generality, not admission/financial certification."""
from io import BytesIO
from pathlib import Path
from hashlib import sha256
from openpyxl import load_workbook
import pytest
from services.governed_workbook_ingestion import ingest_governed_workbook
from sandbox.heterogeneous_workbooks import run_recorded_registered_mock_analysis
from sandbox.synthetic_product import SandboxRefused

@pytest.mark.parametrize('suffix,status',[('english','UNDERSTOOD'),('ambiguous_period','AMBIGUOUS'),
    ('ambiguous_number','AMBIGUOUS'),('conflict','CONTRADICTION')])
def test_existing_epistemic_states_preserved(suffix,status):
    name=f'pepperyn_v1_heterogeneous_{suffix}.xlsx'
    result=ingest_governed_workbook(Path('tests/golden/fixtures',name).read_bytes(),name)
    assert result.understanding.status == status

def test_parser_not_filename_or_registry_hash_bound_but_execution_remains_closed():
    raw=Path('tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx').read_bytes()
    workbook=load_workbook(BytesIO(raw))
    changed=0
    for sheet in workbook:
        for row in sheet:
            for cell in row:
                if isinstance(cell.value,(float,int)) and cell.value > 10000:
                    cell.value += 100
                    changed+=1
    assert changed
    output=BytesIO(); workbook.save(output); synthetic=output.getvalue()
    parsed=ingest_governed_workbook(synthetic,'locally_generated_synthetic.xlsx')
    assert parsed.source_sha256 == sha256(synthetic).hexdigest().upper()
    assert parsed.understanding.status == 'UNDERSTOOD'
    original=ingest_governed_workbook(raw,'original.xlsx')
    assert parsed.understanding.facts != original.understanding.facts
    with pytest.raises(SandboxRefused):
        run_recorded_registered_mock_analysis(synthetic,'locally_generated_synthetic.xlsx')
