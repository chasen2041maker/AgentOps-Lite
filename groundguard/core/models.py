from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal


FactValueKind = Literal["numeric", "entity", "text"]
ClaimType = Literal["numeric", "entity", "comparison", "assertion"]
ClaimStatus = Literal["verified", "candidate_match", "unverified", "contradicted"]
RequiredFactSeverity = Literal["required", "optional"]


@dataclass(frozen=True)
class Fact:
    """A verifiable fact explicitly registered from a tool call."""

    id: str
    source_tool: str
    source_call_id: str
    key: str
    value: Decimal | str
    value_kind: FactValueKind = "numeric"
    unit: str | None = None
    display_value: str | None = None
    raw: Any = None
    recorded_at: float = 0.0
    ttl_seconds: int | None = None
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1


@dataclass
class RequiredFact:
    """A ledger fact that the current answer is expected to cover."""

    key: str
    reason: str = ""
    severity: RequiredFactSeverity = "required"


@dataclass
class OutputClaim:
    """A claim extracted from generated output and awaiting verification."""

    id: str
    text_span: str
    claim_type: ClaimType
    normalized_value: Any
    unit: str | None = None
    fact_key: str | None = None
    matched_fact_id: str | None = None
    status: ClaimStatus = "unverified"
    diff: str | None = None


@dataclass
class CoverageReport:
    """A fact coverage report for a single generated answer."""

    session_id: str
    output_claims: list[OutputClaim] = field(default_factory=list)
    required_facts: list[RequiredFact] = field(default_factory=list)
    omitted_required_facts: list[RequiredFact] = field(default_factory=list)
    verified_count: int = 0
    candidate_match_count: int = 0
    unverified_count: int = 0
    contradicted_count: int = 0
    omitted_required_count: int = 0
    passed: bool = True
    policy_reason: str = ""
