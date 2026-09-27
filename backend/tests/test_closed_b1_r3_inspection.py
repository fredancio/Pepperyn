import copy
import pytest
from sandbox import inspect_closed_b1_r3 as inspection
from test_connected_b1_renewal import scenario


def test_read_only_unchanged_state(scenario):
    db, data, _, _ = scenario
    before = copy.deepcopy(db.tables)
    inspection.verify_remote(db, data)
    assert db.tables == before
    assert all(entry[0] != 'rpc' for entry in db.log)


@pytest.mark.parametrize('table', inspection.TABLES)
def test_any_prospective_row_refused_even_foreign(scenario, table):
    db, data, _, _ = scenario
    key = 'id' if table == 'analyses' else 'analysis_id'
    db.tables[table] = [{key: inspection.ANALYSIS, 'company_id': 'foreign'}]
    with pytest.raises(inspection.SafeRefusal, match='PROSPECTIVE_UUID_PRESENT'):
        inspection.verify_remote(db, data)


def test_baseline_drift_refused(scenario):
    db, data, _, _ = scenario
    db.tables['entities'][0]['name'] = 'changed'
    with pytest.raises(inspection.SafeRefusal, match='BASELINE_CHANGED'):
        inspection.verify_remote(db, data)


def test_engagement_drift_refused(scenario):
    db, data, _, _ = scenario
    db.tables['engagements'][0]['id'] = 'changed'
    with pytest.raises(inspection.SafeRefusal, match='ENGAGEMENT_CHANGED'):
        inspection.verify_remote(db, data)
