"""Trusted one-shot prospective allocation, before Auth. No network/authority.

These identities are not an admission. Auth and ownership remain mandatory in
the existing composer. No caller-selected IDs and no replacement on collision.
"""
from dataclasses import dataclass
from uuid import UUID, uuid4
from sandbox.preflight_v40_rehearsal import digest
from sandbox.v40_rehearsal_orchestration import require

LABELS=('ROLLBACK','ABANDON','POSITIVE')
FIELDS=('analysis_id','request_id','execution_id')


@dataclass(frozen=True)
class IdentityPlan:
    policy_id: UUID
    triples: tuple

    @classmethod
    def create(cls):
        plan=cls(uuid4(),tuple(tuple(uuid4() for _ in FIELDS) for _ in LABELS))
        plan.validate()
        return plan

    def validate(self):
        require(type(self.policy_id) is UUID and type(self.triples) is tuple and len(self.triples)==3)
        require(all(type(t) is tuple and len(t)==3 and all(type(v) is UUID for v in t) for t in self.triples))
        values=(self.policy_id,)+tuple(v for t in self.triples for v in t)
        require(len(set(values))==10)

    def manifest(self):
        self.validate()
        return dict(policy_id=str(self.policy_id),cases={label:dict(zip(FIELDS,map(str,t))) for label,t in zip(LABELS,self.triples)})

    def commitment(self):
        return digest(self.manifest())

    def verify(self,manifest,commitment):
        require(self.commitment()==commitment)
        require(set(manifest['cases'])==set(LABELS))
        actual=dict(policy_id=manifest['policy_id'],cases={label:{k:manifest['cases'][label][k] for k in FIELDS} for label in LABELS})
        require(actual==self.manifest() and digest(actual)==commitment)


class IdentityConsumption:
    """Burn each prepared allocation once. Failures never put it back."""
    def __init__(self,plan,commitment):
        plan.verify(plan.manifest(),commitment)
        self._plan,self._commitment,self._next=plan,commitment,0

    def __call__(self):
        require(self._plan.commitment()==self._commitment and self._next<3)
        current=self._next;self._next+=1
        return self._plan.triples[current]
