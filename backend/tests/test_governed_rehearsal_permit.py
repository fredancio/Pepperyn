"""No network, no real credentials, local one-shot permit falsification."""
import json
from pathlib import Path
import os
from test_governed_pipeline import environment, LocalDatabase, client_for, upload
from test_governed_analysis_persistence import _db, COMPANY_A, ENTITY_A
from services.governed_rehearsal_permit import RehearsalPermit


def test_consumption_survives_second_application(environment):
    db=LocalDatabase(_db().tables)
    client,_=client_for(db)
    assert upload(client).status_code==201
    second,_=client_for(db)
    assert upload(second).status_code==503
    assert len(db.tables['analyses'])==1
    assert len([entry for entry in db.log if entry[0]=='rpc'])==1


def test_failed_payload_consumes_attempt_without_write(environment):
    db=LocalDatabase(_db().tables)
    client,_=client_for(db)
    assert upload(client,raw=b'wrong').status_code==503
    assert upload(client).status_code==503
    assert not db.tables.get('analyses')


def test_changed_baseline_refuses(environment):
    db=LocalDatabase(_db().tables)
    db.tables['analyses']=[dict(id='existing',company_id=COMPANY_A)]
    client,_=client_for(db)
    assert upload(client).status_code==503
    assert len(db.tables['analyses'])==1


def test_explicit_closure_and_outside_record_deny(environment):
    db=LocalDatabase(_db().tables)
    client,_=client_for(db)
    assert client.get('/api/governed/analyses/outside',headers={'Authorization':'Bearer owner'}).status_code==503
    Path(os.environ['PEPPERYN_GOVERNED_REHEARSAL_MANIFEST']).with_suffix('.closed').write_text('CLOSED')
    assert upload(client).status_code==503
    assert not db.log


def test_mutated_manifest_refuses_existing_worker(environment):
    db=LocalDatabase(_db().tables)
    client,_=client_for(db)
    manifest=Path(os.environ['PEPPERYN_GOVERNED_REHEARSAL_MANIFEST'])
    manifest.write_bytes(manifest.read_bytes()+b' ')
    assert upload(client).status_code==503


def test_expired_permit_refuses_startup(environment):
    import pytest
    path=Path(os.environ['PEPPERYN_GOVERNED_REHEARSAL_MANIFEST'])
    data=json.loads(path.read_text()); data['expires_at']='2000-01-01T00:00:00+00:00'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError): RehearsalPermit(path,COMPANY_A)


def test_preflight_reads_only_and_stores_hashes_not_business_content():
    from sandbox.preflight_connected_b1 import preflight
    from services.governed_rehearsal_permit import COMPANY, ENTITY
    db=LocalDatabase(dict(entities=[dict(id=ENTITY,company_id=COMPANY,name='Optilux Synthetic Internal Pilot')],
        companies=[dict(id=COMPANY)],engagements=[dict(id='40000000-0000-0000-0000-000000000001',entity_id=ENTITY)],
        analyses=[dict(id='10000000-0000-0000-0000-000000000001',company_id=COMPANY,analyse_json={'test':'synthetic'})]))
    data=preflight(db)
    assert data['phase']=='B1_READ_ONLY_PREFLIGHT_PASS'
    assert all(entry[0]!='rpc' for entry in db.log)
    assert 'synthetic' not in json.dumps(data['baseline'])
