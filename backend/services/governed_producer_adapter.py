"""Backend-owned composition between a V40 claim and a bounded producer.

This module does not register, admit or transport a producer.  It deliberately
contains no database client, Auth token, provider SDK or persistence primitive.
The backend selects the callable and its exact contract; the callable receives
only the governed source facts, task identity and correlation nonce.  Its return
is untrusted until Pepperyn rebuilds and validates the governed envelope.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from hashlib import sha256
import inspect
import json
from typing import Any, Literal

from pydantic import Field

from services.durable_producer_admission import (
    ClaimedExecution,
    DurableProducerAdmission,
    ReservedExecution,
)
from services.producer_execution_contract import Digest, ExecutionBindingsV2, VersionedName, _Closed
from services.v1_analysis_contract import (
    GovernedAnalysisEnvelope,
    GovernedFinancialAnalysis,
    UnderstandingResult,
    to_analysis_result,
)


class ProducerAdapterRefused(RuntimeError):
    """Content-free terminal refusal for local producer-composition failures."""


class GovernedProducerInvocationV2(_Closed):
    """The complete and only object visible to the selected producer."""

    schema_version: Literal["governed-producer-invocation-2"] = "governed-producer-invocation-2"
    task_id: VersionedName
    task_version: VersionedName
    invocation_nonce: str = Field(pattern=r"^[A-F0-9]{32}$")
    source_facts: UnderstandingResult


ProducerCallable = Callable[
    [GovernedProducerInvocationV2],
    Mapping[str, Any] | GovernedFinancialAnalysis | Awaitable[Mapping[str, Any] | GovernedFinancialAnalysis],
]


class GovernedProducerAdapter:
    """Validate an exact claimed composition around one injected callable.

    Expected producer/task/contract values are backend constructor inputs.  They
    are never inferred from producer output and never accepted from an HTTP body.
    The adapter returns an envelope but owns no persistence authority.
    """

    def __init__(
        self,
        *,
        producer: ProducerCallable,
        producer_id: VersionedName,
        producer_version: VersionedName,
        task_id: VersionedName,
        task_version: VersionedName,
        admission_contract_sha256: Digest,
    ) -> None:
        if not callable(producer):
            raise ProducerAdapterRefused("PRODUCER_ADAPTER_CONFIGURATION_REFUSED")
        self._producer = producer
        self._expected = {
            "producer_id": producer_id,
            "producer_version": producer_version,
            "task_id": task_id,
            "task_version": task_version,
            "admission_contract_sha256": admission_contract_sha256,
        }

    def assert_compatible(self, bindings: ExecutionBindingsV2) -> ExecutionBindingsV2:
        """Refuse before claim when the backend-selected adapter does not match."""

        try:
            checked = ExecutionBindingsV2.model_validate(bindings.model_dump(mode="json"))
            if any(getattr(checked, field) != expected for field, expected in self._expected.items()):
                raise ValueError("adapter binding")
            return checked
        except Exception:
            raise ProducerAdapterRefused("PRODUCER_ADAPTER_BINDING_REFUSED") from None

    async def invoke(self, claimed: ClaimedExecution) -> GovernedAnalysisEnvelope:
        """Invoke once with bounded data, then validate and rebuild the envelope."""

        producer_called = False
        try:
            if not isinstance(claimed, ClaimedExecution):
                raise ValueError("claim required")
            bindings = self.assert_compatible(claimed.reservation.bindings)
            if type(claimed.input_text) is not str:
                raise ValueError("input type")
            if sha256(claimed.input_text.encode("utf-8")).hexdigest().upper() != bindings.producer_input_sha256:
                raise ValueError("input digest")
            understanding = UnderstandingResult.model_validate_json(claimed.input_text)
            if (
                understanding.status != "UNDERSTOOD"
                or understanding.source_representation_sha256 != bindings.source_representation_sha256
            ):
                raise ValueError("source binding")

            # Canonical round-trip prevents the callable from sharing mutable
            # objects with the authoritative validation copy retained here.
            invocation = GovernedProducerInvocationV2(
                task_id=bindings.task_id,
                task_version=bindings.task_version,
                invocation_nonce=bindings.request_id.hex.upper(),
                source_facts=UnderstandingResult.model_validate_json(
                    understanding.model_dump_json()
                ),
            )
            input_snapshot = invocation.model_dump_json()
            producer_called = True
            result = self._producer(invocation)
            if inspect.isawaitable(result):
                result = await result
            if invocation.model_dump_json() != input_snapshot:
                raise ValueError("producer mutated input")

            payload = result.model_dump(mode="json") if isinstance(result, GovernedFinancialAnalysis) else result
            if not isinstance(payload, Mapping):
                raise ValueError("producer output type")
            # A JSON round-trip rejects non-serializable objects and separates
            # the producer-owned object from Pepperyn's validation boundary.
            isolated = json.loads(json.dumps(dict(payload), ensure_ascii=False, allow_nan=False))
            analysis = GovernedFinancialAnalysis.model_validate(isolated)
            if (
                analysis.invocation_nonce != bindings.request_id.hex.upper()
                or analysis.source_representation_sha256 != bindings.source_representation_sha256
            ):
                raise ValueError("producer output binding")
            analysis.validate_against(understanding)
            return to_analysis_result(analysis, understanding)
        except ProducerAdapterRefused:
            raise
        except Exception:
            # Never disclose producer output, source contents, scope or secrets.
            suffix = "AFTER_INVOCATION" if producer_called else "BEFORE_INVOCATION"
            raise ProducerAdapterRefused(f"PRODUCER_OUTPUT_REFUSED_{suffix}") from None


class GovernedProducerCoordinator:
    """Claim, invoke and complete once; authority stays in backend services."""

    def __init__(self, *, admission: DurableProducerAdmission, adapter: GovernedProducerAdapter) -> None:
        if not isinstance(admission, DurableProducerAdmission) or not isinstance(adapter, GovernedProducerAdapter):
            raise ProducerAdapterRefused("PRODUCER_COORDINATOR_CONFIGURATION_REFUSED")
        self._admission = admission
        self._adapter = adapter

    async def execute(self, reservation: ReservedExecution, *, authorization: str) -> Mapping[str, Any]:
        """Execute once with no retry, fallback, alternate ID or producer persistence."""

        try:
            # Fail before durable claim when the selected backend adapter is not
            # the one bound into the admitted composition.
            self._adapter.assert_compatible(reservation.bindings)
            claimed = self._admission.claim(reservation, authorization=authorization)
            envelope = await self._adapter.invoke(claimed)
            return self._admission.complete(
                claimed, authorization=authorization, envelope=envelope
            )
        except ProducerAdapterRefused:
            raise
        except Exception:
            raise ProducerAdapterRefused("PRODUCER_COORDINATION_REFUSED_NO_RETRY") from None
