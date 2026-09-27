import copy
from types import SimpleNamespace
import pytest
from sandbox import inspect_completed_b1_r5 as inspection
from test_connected_b1_renewal import scenario


@pytest.fixture
def completed(scenario, monkeypatch):
    db, data, _, _ = scenario
    for table in inspection.TABLES:
        key = 'id' if table == 'analyses' else 'analysis_id'
        db.tables[table] = [{key: inspection.ANALYSIS, **{k: data[k] for k in ('company_id', 'entity_id', 'engagement_id')}}]
    record = SimpleNamespace(execution_id=inspection.EXECUTION, raw_source_sha256=inspection.SOURCE_HASH,
        envelope_sha256=inspection.ENVELOPE_HASH, provider_mode='LOCAL_MOCK', transport='NONE')
    monkeypatch.setattr(inspection, 'load_execution_provenance', lambda *args, **kwargs: record)
    return db, data, record


def test_positive_read_only(completed):
    db, data, _ = completed
    before = copy.deepcopy(db.tables)
    inspection.verify_remote(db, data)
    assert db.tables == before
    assert all(item[0] != 'rpc' for item in db.log)


@pytest.mark.parametrize('table', inspection.TABLES)
def test_missing_row_refused(completed, table):
    db, data, _ = completed
    db.tables[table] = []
    with pytest.raises(inspection.SafeRefusal):
        inspection.verify_remote(db, data)


@pytest.mark.parametrize('mutation', ['extra', 'baseline', 'scope', 'receipt', 'engagement'])
def test_mutations_refused(completed, mutation):
    db, data, record = completed
    if mutation == 'extra':
        db.tables['analyses'].append(dict(db.tables['analyses'][0], id='unexpected'))
    elif mutation == 'baseline':
        db.tables['entities'][0]['name'] = 'changed'
    elif mutation == 'scope':
        db.tables['analyses'][0]['entity_id'] = 'foreign'
    elif mutation == 'receipt':
        record.execution_id = 'substituted'
    else:
        db.tables['engagements'][0]['id'] = 'changed'
    with pytest.raises(inspection.SafeRefusal):
        inspection.verify_remote(db, data)
