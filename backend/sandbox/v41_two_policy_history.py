"""Exact post-Attempt-5 history contract. No identity allocation or network."""
from copy import deepcopy
from datetime import datetime
import json

VERSION = 'v41-disabled-history-2'
FIELD = 'historical_policy_contract'
POLICY_IDS = ('5cf919e2-77e3-46ce-ab0e-c237d62cfe2d',
              'f6b1732f-e558-47a0-9106-f0b3e53c3b05')
ANALYSIS_IDS = ('07efdcad-de84-489e-890d-1709b44ef087',
                '9a2fb8cf-1e0a-4ce6-b3f6-1d865072efcd')
EVIDENCE = 'A225EF5B20CF9FF143D9C7C5EF2713458839478163571040233A69747E0F8798'
BINDING = 'CDC4BC07EA6F67275B985E76B24467CC3A1A11891EFA1953E0F6137344F73645'
SPECIFICATION = 'BA1B898959C6959F72DCE8E2A5B788EF78E2BBC7228A548911915B412B28F44E'


def enabled(manifest):
    if FIELD not in manifest:
        return False  # Historical single-policy contract, never auto-upgraded.
    if manifest[FIELD] != VERSION:
        raise ValueError('V41_HISTORY_VERSION_REFUSED')
    return True


def expected_fields(policy_id):
    from sandbox import v41_injected_rehearsal as a
    from services.generic_producer_candidate import CONTRACT_BINDING
    if policy_id not in POLICY_IDS:
        raise ValueError('V41_HISTORY_ID_REFUSED')
    binding = CONTRACT_BINDING.model_dump(mode='json')
    text = a.canonical_bytes(binding).decode()
    from hashlib import sha256
    if sha256(text.encode()).hexdigest().upper() != BINDING:
        raise ValueError('V41_HISTORY_CONTRACT_DRIFT')
    spec = a.specification_without_evidence({'scope': a.SCOPE})
    spec['policy_evidence_sha256'] = EVIDENCE
    if sha256(a.canonical_bytes(spec)).hexdigest().upper() != SPECIFICATION:
        raise ValueError('V41_HISTORY_SPECIFICATION_DRIFT')
    return dict(id=policy_id, enabled=False, specification=spec,
                contract_binding=binding, contract_binding_text=text,
                contract_binding_sha256=BINDING)


def validate(policies, *, pinned=None):
    if type(policies) is not list or len(policies) != 2:
        raise ValueError('V41_HISTORY_SET_REFUSED')
    if sorted(p.get('id', '') for p in policies) != sorted(POLICY_IDS):
        raise ValueError('V41_HISTORY_ID_REFUSED')
    for row in policies:
        expected = expected_fields(row['id'])
        from sandbox.v41_injected_rehearsal import canonical_bytes
        if (set(row) != set(expected) | {'created_at'} or
                canonical_bytes({k: row[k] for k in expected}) != canonical_bytes(expected)):
            raise ValueError('V41_HISTORY_CONTENT_REFUSED')
        stamp = datetime.fromisoformat(row['created_at'])
        if stamp.utcoffset() is None:
            raise ValueError('V41_HISTORY_TIMESTAMP_REFUSED')
    ordered = sorted(deepcopy(policies), key=lambda p: p['id'])
    if pinned is not None and ordered != sorted(pinned, key=lambda p: p['id']):
        raise ValueError('V41_HISTORY_NONREGRESSION_REFUSED')
    return ordered


def split(policies, manifest):
    if type(policies) is not list or len(policies) != 3:
        raise ValueError('V41_HISTORY_CURRENT_SET_REFUSED')
    old = [p for p in policies if p.get('id') in POLICY_IDS]
    validate(old)
    current = [p for p in policies if p.get('id') == manifest['identities']['policy_id']]
    if len(current) != 1 or current[0]['id'] in POLICY_IDS:
        raise ValueError('V41_HISTORY_CURRENT_ID_REFUSED')
    return old, current[0]


def sql_condition():
    checks = ['(SELECT count(*) FROM public.generic_producer_policies_v3) = 2']
    for identity in POLICY_IDS:
        literal = json.dumps(expected_fields(identity), ensure_ascii=False).replace("'", "''")
        checks.append("EXISTS (SELECT 1 FROM public.generic_producer_policies_v3 p WHERE "
                      f"p.id='{identity}'::uuid AND p.created_at IS NOT NULL AND "
                      f"to_jsonb(p)-'created_at'='{literal}'::jsonb)")
    for identity in ANALYSIS_IDS:
        for table, column in (('analyses','id'), ('governed_analysis_envelopes','analysis_id'),
                              ('governed_execution_receipts','analysis_id'),
                              ('execution_receipts_v2','analysis_id'),
                              ('generic_execution_receipts_v3','analysis_id')):
            checks.append(f"NOT EXISTS (SELECT 1 FROM public.{table} WHERE {column}='{identity}'::uuid)")
    return '(' + ' AND '.join(checks) + ')'


def _replace(text, before, after):
    if text.count(before) != 1:
        raise ValueError('V41_HISTORY_SQL_TEMPLATE_DRIFT')
    return text.replace(before, after)


def sql(repo, manifest, *, insert=False):
    from sandbox import v41_injected_rehearsal as a
    if not enabled(manifest):
        raise ValueError('V41_HISTORY_VERSION_REQUIRED')
    old = dict(manifest)
    old.pop(FIELD)
    if insert:
        text = a.policy_insert_sql(old)
        return _replace(text, '(SELECT count(*) FROM public.generic_producer_policies_v3) <> 1',
                        'NOT ' + sql_condition())
    text = a.precontrol_sql(repo, old)
    text = _replace(text, '(SELECT count(*) FROM public.generic_producer_policies_v3) = 1', sql_condition())
    text = _replace(text, 'policy_rows = 1 AND admission_rows = 0 AND receipt_rows = 0',
                    'policy_rows = 2 AND admission_rows = 0 AND receipt_rows = 0')
    text = _replace(text, "'check_version','v41-successor-single-result-precontrol-2',",
                    "'check_version','v41-two-policy-precontrol-1',\n 'observed_at',statement_timestamp(),")
    return _replace(text, "'historical_comparison_required',true,",
        "'historical_comparison_required',true,\n 'historical_policy_contract','" + VERSION + "',\n "
        "'historical_policies',(SELECT jsonb_agg(to_jsonb(p) ORDER BY id) FROM public.generic_producer_policies_v3 p),")


def validate_result(result, manifest, now):
    # Keep all original time/scope/catalog tests; expected count is versioned,
    # never rewritten in the preserved accepted result.
    from sandbox import run_v41_owner_ack_successor as old
    if not enabled(manifest) or result.get('historical_policy_contract') != VERSION or result.get('check_version') != 'v41-two-policy-precontrol-1':
        raise ValueError('V41_HISTORY_RESULT_VERSION_REFUSED')
    validate(result['historical_policies'])
    if result['structural']['rows'] != {'policy_rows': 2, 'admission_rows': 0, 'receipt_rows': 0}:
        raise ValueError('V41_HISTORY_COUNTS_REFUSED')
    comparison = deepcopy(result)
    comparison['structural']['rows']['policy_rows'] = 1
    comparison['check_version'] = 'v41-owner-ack-precontrol-1'
    old.validate_result(comparison, manifest, now)


def accepted_history(attempt, manifest, now):
    """No current-state fallback: require hash-bound accepted result before Auth."""
    from sandbox import run_v41_injected_rehearsal as r
    from sandbox import v41_injected_rehearsal as a
    payload = dict(manifest)
    observed = payload.pop('manifest_sha256')
    if r.digest(payload) != observed or (attempt / 'precontrol.sql').read_bytes() != sql(r.REPO, manifest).encode('utf-8'):
        raise ValueError('V41_HISTORY_ARTIFACT_REFUSED')
    result = json.loads((attempt / 'accepted-precontrol-result.json').read_text(encoding='utf-8'))
    report = json.loads((attempt / 'precontrol-ready.json').read_text(encoding='utf-8'))
    validate_result(result, manifest, now)
    expected = dict(schema_version='v41-two-policy-attestation-1',
                    manifest_sha256=manifest['manifest_sha256'],
                    sql_sha256=a.file_sha256(attempt / 'precontrol.sql'),
                    result_sha256=a.file_sha256(attempt / 'accepted-precontrol-result.json'),
                    observed_at=result['observed_at'],
                    historical_snapshot_sha256=r.digest(result['historical']),
                    historical_policies_sha256=r.digest(validate(result['historical_policies'])))
    if report != expected:
        raise ValueError('V41_HISTORY_ATTESTATION_REFUSED')
    return validate(result['historical_policies'])
