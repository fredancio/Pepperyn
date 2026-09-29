"""Pinned V41 definition variants; only CRLF-to-LF equivalence is allowed."""

from hashlib import sha256
from pathlib import Path
import re


ROOT = Path(__file__).parents[1] / "migrations"


def _bodies():
    migration = (ROOT / "v41_generic_producer_receipts_v3.sql").read_text(
        encoding="utf-8"
    )
    return re.findall(
        r"CREATE FUNCTION public\.(\w+)[\s\S]*?AS \$\$([\s\S]*?)\$\$;",
        migration,
    )


def test_reviewed_lf_and_crlf_bodies_are_pinned_separately():
    verifier = (ROOT / "v41_definition_conformance_read_only.sql").read_text(
        encoding="utf-8"
    )
    bodies = _bodies()
    assert len(bodies) == 5
    for name, body in bodies:
        assert "\r" not in body
        lf_hash = sha256(body.encode()).hexdigest()
        crlf_hash = sha256(body.replace("\n", "\r\n").encode()).hexdigest()
        assert lf_hash != crlf_hash
        assert name in verifier
        assert lf_hash in verifier
        assert crlf_hash in verifier


def test_verifier_normalizes_only_crlf_to_lf_and_preserves_raw_evidence():
    verifier = (ROOT / "v41_definition_conformance_read_only.sql").read_text(
        encoding="utf-8"
    )
    assert "replace(p.prosrc,chr(13)||chr(10),chr(10))" in verifier
    assert "position(chr(13) IN replace(p.prosrc,chr(13)||chr(10),''))=0" in verifier
    assert "raw_sha256 IN (lf_hash,crlf_hash)" in verifier
    assert "lower(" not in verifier
    assert "trim(" not in verifier
    assert "regexp_replace(" not in verifier
    assert "BEGIN TRANSACTION READ ONLY;" in verifier
    assert verifier.rstrip().endswith("ROLLBACK;")
    assert not re.search(
        r"\b(CREATE|ALTER|INSERT|UPDATE|DELETE|DROP|TRUNCATE)\b", verifier
    )


def test_semantic_or_whitespace_mutation_is_not_an_allowed_raw_variant():
    verifier = (ROOT / "v41_definition_conformance_read_only.sql").read_text(
        encoding="utf-8"
    )
    for _, body in _bodies():
        semantic = body.replace("RETURN NEW;", "RETURN NULL;", 1)
        whitespace = body.replace("BEGIN", "BEGIN ", 1)
        if semantic != body:
            assert sha256(semantic.encode()).hexdigest() not in verifier
            assert sha256(semantic.replace("\n", "\r\n").encode()).hexdigest() not in verifier
        assert sha256(whitespace.encode()).hexdigest() not in verifier
        assert sha256(whitespace.replace("\n", "\r\n").encode()).hexdigest() not in verifier
