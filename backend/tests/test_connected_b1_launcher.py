"""Launcher checks only, no Uvicorn, network or actual manifest changes."""
import hashlib
import json
from pathlib import Path
import pytest
from sandbox import run_connected_b1 as launcher
from test_governed_pipeline import environment, LocalDatabase
from test_governed_analysis_persistence import _db, COMPANY_A, ENGAGEMENT_A
import os


def test_launcher_uses_existing_id_and_rechecks_baseline(environment,monkeypatch):
    path=Path(os.environ['PEPPERYN_GOVERNED_REHEARSAL_MANIFEST'])
    monkeypatch.setattr(launcher,'COMPANY',COMPANY_A)
    monkeypatch.setattr(launcher,'MANIFEST_HASH',hashlib.sha256(path.read_bytes()).hexdigest().upper())
    permit=launcher.check_local(path)
    db=LocalDatabase(_db().tables)
    before=path.read_bytes()
    launcher.check_remote(permit,db)
    assert path.read_bytes()==before
    assert not any(entry[0]=='rpc' for entry in db.log)
    db.tables['engagements'][0]['id']='40000000-0000-0000-0000-000000000099'
    with pytest.raises(ValueError,match='ENGAGEMENT_CHANGED'):
        launcher.check_remote(permit,db)


def test_reactivation_denied_and_closure_durable(environment,monkeypatch):
    path=Path(os.environ['PEPPERYN_GOVERNED_REHEARSAL_MANIFEST'])
    monkeypatch.setattr(launcher,'COMPANY',COMPANY_A)
    monkeypatch.setattr(launcher,'MANIFEST_HASH',hashlib.sha256(path.read_bytes()).hexdigest().upper())
    permit=launcher.check_local(path)
    path.with_suffix('.activated').write_text('activated')
    with pytest.raises(ValueError,match='EXISTING_ATTEMPT'):
        launcher.check_local(path)
    launcher.close(path)
    with pytest.raises(ValueError,match='PERMIT_CLOSED'): permit.check()
    launcher.close(path)  # Does not replace an existing close marker.
    assert path.with_suffix('.closed').read_text()=='CLOSED_NO_AUTOMATIC_RESUME\n'
