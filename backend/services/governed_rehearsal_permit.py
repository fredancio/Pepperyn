"""Local one-shot Integration permit, never an admission grant for real data.

Exclusive durable attempt file survives restart and is shared by workers on this
host. Never remove/reset/replace it to resume a failed or uncertain attempt.
Operator-controlled files are not a boundary against a compromised local admin.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from services.governed_analysis_create import GovernedCreateRefused

FILENAME = 'pepperyn_v1_heterogeneous_english.xlsx'
SOURCE_HASH = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
PROJECT = 'https://ejixkplrgobgwqnhidwt.supabase.co'
COMPANY = '89644cea-1e5c-478a-b797-b34d646064be'
ENTITY = 'dfd01f5c-a095-4fcb-8873-ccc3f427d348'
TABLES = ('analyses','governed_analysis_envelopes','governed_execution_receipts')
PROTECTED_TABLES = ('decision_feedback','decision_arcs','governed_decision_followups',
                    'governed_decision_executions','governed_decision_prerequisite_evidence','entities')


def scoped_snapshot(db, company):
    from services.governed_analysis_persistence import _digest
    result = {}
    for table in TABLES + PROTECTED_TABLES:
        rows = db.from_(table).select('*').eq('company_id',company).limit(1001).execute().data
        if not isinstance(rows,list) or len(rows) >= 1000:
            raise ValueError('SNAPSHOT_UNBOUNDED')
        key = 'analysis_id' if table in TABLES[1:] else 'id'
        if any(row.get('company_id') != company for row in rows):
            raise ValueError('SNAPSHOT_SCOPE')
        result[table] = {row[key]:_digest(row) for row in rows}
        if len(result[table]) != len(rows):
            raise ValueError('SNAPSHOT_DUPLICATE')
    return result


class RehearsalPermit:
    def __init__(self, path, company):
        self.path = Path(path)
        if not self.path.is_absolute() or not self.path.is_file():
            raise ValueError('PERMIT_REQUIRED')
        self.raw = self.path.read_bytes()
        self.data = json.loads(self.raw)
        data = self.data
        for field in ('company_id','entity_id','engagement_id','analysis_id'):
            if str(UUID(data[field])) != data[field]:
                raise ValueError('PERMIT_SCOPE')
        if (data['phase'] != 'B1_READ_ONLY_PREFLIGHT_PASS' or data['project_url'] != PROJECT
                or data['company_id'] != company or company != COMPANY or data['entity_id'] != ENTITY
                or data['source_sha256'] != SOURCE_HASH or data['filename'] != FILENAME
                or set(data['baseline']) != set(TABLES + PROTECTED_TABLES)):
            raise ValueError('PERMIT_SCOPE')
        self.deadline = datetime.fromisoformat(data['expires_at'])
        if self.deadline.tzinfo is None:
            raise ValueError('PERMIT_EXPIRY')
        self.check()

    def check(self):
        if (self.path.read_bytes() != self.raw or datetime.now(timezone.utc) >= self.deadline
                or self.path.with_suffix('.closed').exists()):
            raise ValueError('PERMIT_CLOSED')

    def reserve(self, db, *, company_id, entity_id, engagement_id, raw, filename):
        try:
            self.check()
            # Consume before payload/baseline validation: a failed attempt is not retried.
            with self.path.with_suffix('.attempt').open('x',encoding='utf-8') as handle:
                handle.write(self.data['analysis_id'] + '\n')
                handle.flush()
                import os
                os.fsync(handle.fileno())
            if ((company_id,entity_id,engagement_id) != tuple(self.data[k] for k in
                    ('company_id','entity_id','engagement_id')) or filename != FILENAME
                    or hashlib.sha256(raw).hexdigest().upper() != SOURCE_HASH
                    or scoped_snapshot(db,company_id) != self.data['baseline']):
                raise ValueError('PERMIT_BINDING')
            return self.data['analysis_id']
        except Exception:
            raise GovernedCreateRefused('REHEARSAL_REFUSED',analysis_id=self.data['analysis_id']) from None
