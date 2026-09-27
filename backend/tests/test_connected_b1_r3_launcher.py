"""Local-only R3 launch guard tests; no live activation."""
import hashlib
import os
from pathlib import Path
import pytest
from sandbox import run_connected_b1_r3 as launcher
from sandbox import inspect_closed_b1_r2 as inspection
from test_governed_pipeline import environment
from test_governed_analysis_persistence import COMPANY_A


@pytest.mark.parametrize('marker', ['.attempt', '.activated', '.closed'])
def test_r3_cannot_reactivate_or_replay(environment, monkeypatch, marker):
    original = Path(os.environ['PEPPERYN_GOVERNED_REHEARSAL_MANIFEST'])
    path = original.with_name('b1-connected-rehearsal-r3.json')
    path.write_bytes(original.read_bytes())
    monkeypatch.setattr(inspection, 'local_check', lambda root: None)
    monkeypatch.setattr(launcher, 'COMPANY', COMPANY_A)
    monkeypatch.setattr(launcher, 'MANIFEST_HASH', hashlib.sha256(path.read_bytes()).hexdigest().upper())
    launcher.check_local(path)
    path.with_suffix(marker).write_text('existing')
    with pytest.raises(ValueError):
        launcher.check_local(path)


def test_predecessor_refusal_propagates(tmp_path, monkeypatch):
    def refused(root):
        raise inspection.SafeRefusal('LOCAL_EVIDENCE_CHANGED')
    monkeypatch.setattr(inspection, 'local_check', refused)
    with pytest.raises(inspection.SafeRefusal, match='LOCAL_EVIDENCE_CHANGED'):
        launcher.check_local(tmp_path / 'b1-connected-rehearsal-r3.json')
