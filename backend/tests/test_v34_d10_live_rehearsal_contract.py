"""Static and fixture safeguards for the founder-run live D10 rehearsal."""

import ast
import hashlib
import json
from pathlib import Path

from sandbox import run_v34_d10_composition_rehearsal as rehearsal


def test_fixture_is_hash_pinned_and_synthetic_only():
    payload = json.loads(rehearsal._FIXTURE.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest().upper() == rehearsal.FIXTURE_SHA256
    assert payload["evidence_role"] == "D10_COMPOSITION_REHEARSAL_ONLY"
    assert payload["synthetic"] is True
    assert payload["external_provider_allowed"] is False
    assert payload["real_data_allowed"] is False


def test_rehearsal_exposes_no_write_or_transport_operation():
    source = Path(rehearsal.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {
        node.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert called.isdisjoint({"insert", "update", "upsert", "delete", "rpc", "register", "dispatch"})
    assert 'choices=("inspect", "compose")' in source
    assert '"write_performed": False' in source


def test_output_contract_never_emits_secrets_or_exact_values():
    source = Path(rehearsal.__file__).read_text(encoding="utf-8")
    emit_section = source[source.index("def _emit"):source.index("def _fixture")]
    assert "SUPABASE_SERVICE_KEY" not in emit_section
    assert "PEPPERYN_CORRESPONDENCE_KEY" not in emit_section
    assert "previous" not in emit_section and "current" not in emit_section
    assert "exact_values_disclosed=False" in source


def test_inspect_uses_the_projection_attestation_verifier():
    source = Path(rehearsal.__file__).read_text(encoding="utf-8")
    assert "binding.registration_version" not in source
    assert "verify_projection_correspondence_binding(" in source
    assert "authorized_origin=True" in source
