"""Successor launcher falsification, synthetic local files only."""
import hashlib
import os
from pathlib import Path

import pytest
from sandbox import run_connected_b1_r2 as launcher
from sandbox import renew_connected_b1 as renewal
from test_governed_pipeline import environment
from test_governed_analysis_persistence import COMPANY_A


def test_successor_requires_unchanged_closed_predecessor(environment, monkeypatch):
    original = Path(os.environ['PEPPERYN_GOVERNED_REHEARSAL_MANIFEST'])
    successor = original.with_name('b1-connected-rehearsal-r2.json')
    predecessor = original.with_name('b1-connected-rehearsal.json')
    successor.write_bytes(original.read_bytes())
    predecessor.write_bytes(b'local predecessor evidence')
    predecessor.with_suffix('.closed').write_bytes(b'closed')
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
    monkeypatch.setattr(renewal, 'OLD_HASH', digest(predecessor))
    monkeypatch.setattr(renewal, 'CLOSED_HASH', digest(predecessor.with_suffix('.closed')))
    monkeypatch.setattr(launcher, 'MANIFEST_HASH', digest(successor))
    monkeypatch.setattr(launcher, 'COMPANY', COMPANY_A)
    launcher.check_local(successor)
    assert not successor.with_suffix('.activated').exists()
    assert not successor.with_suffix('.attempt').exists()
    predecessor.with_suffix('.closed').write_bytes(b'changed')
    with pytest.raises(ValueError, match='PREDECESSOR_INTEGRITY'):
        launcher.check_local(successor)
