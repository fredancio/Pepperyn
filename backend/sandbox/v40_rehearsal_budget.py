"""Fail-closed local attempt journal. No credentials/payloads stored here.

The journal is not remote authority. A slot is burned BEFORE its external action,
including Auth, expected refusals and owner-only SQL executed separately.
"""
import sqlite3
from pathlib import Path

SLOTS = (
    'AUTH_ONCE', 'POLICY_INSERT', 'INVALID_SCOPE', 'INVALID_SOURCE',
    'ROLLBACK_RESERVE', 'ROLLBACK_CLAIM', 'ROLLBACK_COMPLETE', 'ROLLBACK_RECLAIM',
    'ABANDON_RESERVE', 'ABANDON_CLAIM', 'ABANDON_RECLAIM', 'ABANDON_CLOSE',
    'POSITIVE_RESERVE', 'POSITIVE_CLAIM_A', 'POSITIVE_CLAIM_B',
    'POSITIVE_COMPLETE', 'POSITIVE_RECLAIM', 'POSITIVE_RECOMPLETE', 'POLICY_DISABLE',
)


class BudgetRefused(ValueError):
    pass


class Budget:
    def __init__(self, path):
        self.path = Path(path)

    @classmethod
    def create(cls, path):
        path = Path(path)
        # Never truncate/reset an attempt, even if initialization previously failed.
        with path.open('xb'):
            pass
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE state (id INTEGER PRIMARY KEY CHECK(id=1), closed INTEGER NOT NULL)')
            db.execute('INSERT INTO state VALUES (1,0)')
            db.execute('CREATE TABLE attempts (slot TEXT PRIMARY KEY, ordinal INTEGER UNIQUE NOT NULL)')
        return cls(path)

    def _connect(self):
        # mode=rw refuses missing file rather than inventing an empty journal.
        return sqlite3.connect(self.path.resolve().as_uri()+'?mode=rw', uri=True, timeout=5)

    def take(self, slot):
        if type(slot) is not str or slot not in SLOTS:
            raise BudgetRefused('UNRECOGNIZED_EFFECT_REFUSED')
        try:
            with self._connect() as db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT closed FROM state WHERE id=1').fetchone() != (0,):
                    raise BudgetRefused('CLOSED_ATTEMPT')
                used = {r[0] for r in db.execute('SELECT slot FROM attempts')}
                if slot in used or len(used) >= 19:
                    raise BudgetRefused('SLOT_REPLAY_OR_BUDGET_EXCEEDED')
                if slot != 'AUTH_ONCE' and 'AUTH_ONCE' not in used:
                    raise BudgetRefused('AUTH_SLOT_REQUIRED')
                db.execute('INSERT INTO attempts VALUES (?,?)', (slot,len(used)+1))
                return len(used)+1
        except BudgetRefused:
            raise
        except Exception:
            raise BudgetRefused('JOURNAL_UNAVAILABLE_NO_ACTION') from None

    def close(self):
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('UPDATE state SET closed=1 WHERE id=1')

    def report(self):
        with self._connect() as db:
            rows = list(db.execute('SELECT slot,ordinal FROM attempts ORDER BY ordinal'))
        return {'effect_attempts':len(rows), 'auth_attempts':sum(s=='AUTH_ONCE' for s,_ in rows),
                'slots':[s for s,_ in rows], 'maximum_effect_attempts':19}
