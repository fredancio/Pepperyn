"""Pinned reviewed source; changing it requires explicit verifier version review."""
from hashlib import sha256
from pathlib import Path
import re

ROOT = Path(__file__).parents[1] / 'migrations'


def test_reviewed_bodies_and_raw_variants_are_pinned():
    migration = (ROOT/'v40_prospective_execution_admission.sql').read_bytes().decode()
    assert sha256(migration.encode()).hexdigest() == 'd4d278fd0bd3e9e582ae9e572d1ba36604a03977c4ba021411f3542a3b2d3f24'
    verifier = (ROOT/'v40_definition_conformance_read_only.sql').read_text()
    bodies = re.findall(r'CREATE FUNCTION public\.(\w+)[\s\S]*?AS \$\$([\s\S]*?)\$\$;', migration)
    assert len(bodies) == 6
    for name, body in bodies:
        assert name in verifier
        assert sha256(body.encode()).hexdigest() in verifier
        assert sha256(body.replace('\n','\r\n').encode()).hexdigest() in verifier
        assert '\r' not in body
        assert not re.search(r'\$\w*\$', body)
        assert all('\n' not in literal for literal in re.findall(r"'(?:''|[^'])*'",body))
    assert 'BEGIN TRANSACTION READ ONLY;' in verifier
    assert verifier.rstrip().endswith('ROLLBACK;')
    assert not re.search(r'\b(CREATE|ALTER|INSERT|UPDATE|DELETE|DROP|TRUNCATE)\b',verifier)
