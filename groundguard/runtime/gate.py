from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from groundguard.core.config import GroundGuardConfig, load_config
from groundguard.core.extractors import extractors_for_packs
from groundguard.core.ledger import Clock, Ledger
from groundguard.core.models import CoverageReport, Fact
from groundguard.core.output_claim_extractor import ExtractorCollection
from groundguard.core.policy import Policy


class FactGate:
    """High-level runtime API for recording facts and checking final answers."""

    def __init__(
        self,
        session_id: str = "groundguard",
        config: GroundGuardConfig | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.session_id = session_id
        self.config = config or GroundGuardConfig()
        self.ledger = Ledger(session_id=session_id, clock=clock)

    @classmethod
    def from_config(
        cls,
        path: str | Path,
        session_id: str = "groundguard",
        clock: Clock | None = None,
    ) -> FactGate:
        return cls(session_id=session_id, config=load_config(path), clock=clock)

    @classmethod
    def from_jsonl(
        cls,
        path: str | Path,
        session_id: str,
        config: GroundGuardConfig | None = None,
        clock: Clock | None = None,
    ) -> FactGate:
        gate = cls(session_id=session_id, config=config, clock=clock)
        gate.ledger = Ledger.from_jsonl(path, session_id=session_id, clock=clock)
        return gate

    @property
    def report_format(self) -> str:
        return self.config.report.format

    def record_fact(
        self,
        *,
        key: str,
        value: Decimal | str | int | float,
        unit: str | None = None,
        source_tool: str = "tool",
        source_call_id: str = "manual",
        value_kind: str = "numeric",
        display_value: str | None = None,
        raw: Any = None,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> Fact:
        fact = Fact(
            id=f"fact_{key}_{uuid4().hex}",
            source_tool=source_tool,
            source_call_id=source_call_id,
            key=key,
            value=_coerce_value(value, value_kind),
            value_kind=value_kind,  # type: ignore[arg-type]
            unit=unit,
            display_value=display_value,
            raw=raw,
            confidence=confidence,
            metadata=metadata or {},
        )
        self.ledger.register_fact(fact)
        return self.ledger.query(key)[-1]

    def record_tool_result(
        self,
        key: str,
        value: Decimal | str | int | float,
        unit: str | None = None,
        *,
        source_tool: str = "tool",
        source_call_id: str = "manual",
        display_value: str | None = None,
        raw: Any = None,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> Fact:
        """Record one numeric tool result using the compact public API."""

        return self.record_fact(
            key=key,
            value=value,
            unit=unit,
            source_tool=source_tool,
            source_call_id=source_call_id,
            display_value=display_value,
            raw=raw,
            confidence=confidence,
            metadata=metadata,
        )

    def check(
        self,
        answer: str,
        required: list[str] | None = None,
        required_fact_keys: list[str] | None = None,
        policy: Policy | None = None,
        extractors: ExtractorCollection | None = None,
    ) -> CoverageReport:
        active_required = required if required is not None else required_fact_keys
        if active_required is None:
            active_required = self.config.required_facts
        active_policy = policy or self.config.policy
        active_extractors = extractors if extractors is not None else self._extractors()
        return self.ledger.coverage_report(
            answer,
            required_fact_keys=list(active_required),
            policy=active_policy,
            extractors=active_extractors,
            tolerance=self.config.units.tolerance,
        )

    def to_jsonl(self, path: str | Path) -> None:
        self.ledger.to_jsonl(path)

    def _extractors(self) -> ExtractorCollection | None:
        if not self.config.extractors.packs:
            return None
        return extractors_for_packs(self.config.extractors.packs)


def _coerce_value(value: Decimal | str | int | float, value_kind: str) -> Decimal | str:
    if value_kind == "numeric":
        return value if isinstance(value, Decimal) else Decimal(str(value))
    return str(value)
