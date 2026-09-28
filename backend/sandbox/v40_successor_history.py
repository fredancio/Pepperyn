"""Successor-only immutable history view. No mutation or authentication methods.

The snapshot is a CANDIDATE until the separate owner catalog gate verifies its
exact JSONB contents against the recorded PostgreSQL digest. Never trust counts
or a newly observed snapshot alone. Every process receives the same snapshot.
"""
import copy
import json
from uuid import UUID

from sandbox.preflight_v40_rehearsal import REGISTRIES, EXISTING, digest
from sandbox.v40_rehearsal_orchestration import require, profile_for

HISTORICAL_POLICY = 'cab54f0d-8b8c-4e77-bae6-7cc0660de0d7'
HISTORICAL_ADMISSIONS_SHA = '193a878f3b896212db174c1e3ed1adb52f01ae70786fab907b3eaef30dfb09b6'
KEYS = dict(zip(REGISTRIES, ('id', 'execution_id', 'execution_id')))


def snapshot(reader, manifest):
    policies = reader.rows(REGISTRIES[0])
    admissions = reader.rows(REGISTRIES[1])
    require(len(policies) == 1 and len(admissions) == 3 and reader.rows(REGISTRIES[2]) == [])
    p = policies[0]
    require(p == dict(id=manifest['policy_id'], enabled=False,
            specification=manifest['profile'], contract_sha256=manifest['contract_sha256'],
            contract_version='local-synthetic-durable-admission-2', origin='SYNTHETIC',egress='DENY'))
    expected = {b['execution_id']: (b, {'ROLLBACK':'REFUSED', 'ABANDON':'CLOSED', 'POSITIVE':'REFUSED'}[label])
                for label, b in manifest['cases'].items()}
    require(set(expected) == {a['execution_id'] for a in admissions})
    for a in admissions:
        b, state = expected[a['execution_id']]
        require(a['bindings'] == b and a['state'] == state and a['policy_id'] == p['id'])
    ids = {b['analysis_id'] for b in manifest['cases'].values()}
    for table, key in [('analyses','id'), ('governed_analysis_envelopes','analysis_id'),
                       ('governed_execution_receipts','analysis_id')]:
        require(not any(r.get(key) in ids for r in reader.rows(table)))
    return {REGISTRIES[0]: copy.deepcopy(policies), REGISTRIES[1]: copy.deepcopy(admissions), REGISTRIES[2]: []}


class HistoryReader:
    def __init__(self, reader, historical):
        self.reader = reader
        # Private frozen serialized snapshot, not a mutable caller-owned alias.
        self._history = json.dumps(historical, sort_keys=True)

    def rows(self, table, **filters):
        history = json.loads(self._history)
        current = {t: self.reader.rows(t) for t in REGISTRIES}
        for t in REGISTRIES:
            key = KEYS[t]
            ids = {r[key] for r in history[t]}
            old = [r for r in current[t] if r.get(key) in ids]
            require(digest(sorted(old, key=digest)) == digest(sorted(history[t], key=digest)))
        if table in REGISTRIES:
            key = KEYS[table]; ids = {r[key] for r in history[table]}
            rows = [r for r in current[table] if r.get(key) not in ids]
            return [r for r in rows if all(r.get(k) == v for k,v in filters.items())]
        return self.reader.rows(table, **filters)

    def close(self):
        self.reader.close()


def assert_fresh_identities(reader, manifest, historical):
    """All ten prospective identities are distinct and absent, before INSERT."""
    proposed = [manifest['policy_id']] + [b[k] for b in manifest['cases'].values()
                                        for k in ('execution_id','request_id','analysis_id')]
    require(len(proposed) == len(set(proposed)) == 10)
    require(all(str(UUID(v)) == v for v in proposed))
    occupied = set()
    for t in REGISTRIES + EXISTING:
        for r in reader.rows(t):
            for key in ('id','execution_id','request_id','analysis_id','policy_id'):
                if isinstance(r.get(key), str): occupied.add(r[key])
    for rows in historical.values():
        for r in rows:
            for key in ('id','execution_id','request_id','analysis_id','policy_id'):
                if isinstance(r.get(key), str): occupied.add(r[key])
    require(not occupied.intersection(proposed))


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def history_guard(historical, admissions_sha):
    """SQL guard checked under locks by both owner actions, before AND after.

    PostgreSQL verifies its own recorded canonical representation. Python does
    not emulate JSONB serialization or normalize timestamps/numbers.
    """
    require(len(admissions_sha) == 64 and all(c in '0123456789abcdef' for c in admissions_sha))
    clauses=[]
    for table in REGISTRIES[:2]:
        key=KEYS[table]; rows=sorted(historical[table], key=lambda r:r[key])
        require(len(rows) == (1 if table == REGISTRIES[0] else 3))
        ids=','.join(literal(str(UUID(r[key])))+'::uuid' for r in rows)
        aggregate=f"(SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY {key}), '[]'::jsonb) FROM public.{table} t WHERE {key} IN ({ids}))"
        clauses.append(f"{aggregate} IS DISTINCT FROM {literal(json.dumps(rows,ensure_ascii=False))}::jsonb")
        if table == REGISTRIES[1]:
            clauses.append(f"encode(sha256(convert_to({aggregate}::text,'UTF8')),'hex') <> {literal(admissions_sha)}")
    require(historical[REGISTRIES[0]][0]['enabled'] is False)
    return "IF " + '\n OR '.join(clauses) + " THEN RAISE EXCEPTION 'V40 successor historical evidence changed'; END IF;"


def catalog_history_sql(historical, admissions_sha):
    return "BEGIN READ ONLY; DO $history$ BEGIN\n" + history_guard(historical,admissions_sha) + "\nEND $history$; SELECT 'V40_SUCCESSOR_HISTORICAL_ANCHOR_PASS'; ROLLBACK;"


def owner_sql(action, manifest, historical, admissions_sha):
    # Reuse validation, NOT the old empty-registry SQL or its launcher.
    from sandbox.v40_rehearsal_owner import owner_sql as validate_manifest
    validate_manifest(action, manifest)
    policy=literal(manifest['policy_id'])+'::uuid'
    spec=literal(json.dumps(manifest['profile']))+'::jsonb'
    contract=literal(manifest['contract_sha256'])
    guard=history_guard(historical,admissions_sha)
    old_policy=literal(historical[REGISTRIES[0]][0]['id'])+'::uuid'
    if action == 'POLICY_INSERT':
        ids=[manifest['policy_id']]+[b[k] for b in manifest['cases'].values() for k in ('execution_id','request_id','analysis_id')]
        require(len(set(ids))==10)
        idlist=','.join(literal(str(UUID(v)))+'::uuid' for v in ids)
        guard += f"\nIF (SELECT count(*) FROM public.producer_policies_v2)<>1 OR (SELECT count(*) FROM public.execution_admissions_v2)<>3 OR EXISTS(SELECT FROM public.execution_receipts_v2) OR EXISTS(SELECT FROM public.analyses WHERE id IN ({idlist})) OR EXISTS(SELECT FROM public.governed_analysis_envelopes WHERE analysis_id IN ({idlist})) OR EXISTS(SELECT FROM public.governed_execution_receipts WHERE analysis_id IN ({idlist})) OR EXISTS(SELECT FROM public.execution_admissions_v2 WHERE execution_id IN ({idlist}) OR analysis_id IN ({idlist}) OR request_id IN ({idlist})) OR EXISTS(SELECT FROM public.producer_policies_v2 WHERE id IN ({idlist})) THEN RAISE EXCEPTION 'V40 successor fresh identities refused'; END IF;"
        write=f"INSERT INTO public.producer_policies_v2(id,specification,contract_sha256,enabled) VALUES ({policy},{spec},{contract},true);"
    else:
        expected=','.join('('+literal(b['execution_id'])+'::uuid,'+literal({'ROLLBACK':'REFUSED','ABANDON':'CLOSED','POSITIVE':'COMPLETE'}[label])+')' for label,b in manifest['cases'].items())
        guard += f"\nIF (SELECT count(*) FROM public.producer_policies_v2)<>2 OR (SELECT count(*) FROM public.execution_admissions_v2)<>6 OR (SELECT count(*) FROM public.execution_receipts_v2)<>1 OR NOT EXISTS(SELECT FROM public.producer_policies_v2 WHERE id={policy} AND id<>{old_policy} AND specification={spec} AND contract_sha256={contract} AND enabled AND origin='SYNTHETIC' AND egress='DENY') OR EXISTS(SELECT FROM (VALUES {expected}) e(id,state) LEFT JOIN public.execution_admissions_v2 a ON a.execution_id=e.id WHERE a.execution_id IS NULL OR a.state<>e.state OR a.policy_id<>{policy}) THEN RAISE EXCEPTION 'V40 successor disable refused'; END IF;"
        write=f"UPDATE public.producer_policies_v2 SET enabled=false WHERE id={policy} AND enabled;"
    return f"""-- Distinct successor owner ticket. Requires distinct Founder GO; never replay.
BEGIN;
LOCK TABLE public.producer_policies_v2, public.execution_admissions_v2, public.execution_receipts_v2 IN SHARE ROW EXCLUSIVE MODE;
DO $successor$ BEGIN
{guard}
{write}
{history_guard(historical,admissions_sha)}
END $successor$;
SELECT '{action}_ACK';
COMMIT;
"""
