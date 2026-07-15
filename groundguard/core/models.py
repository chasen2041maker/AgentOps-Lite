from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import math
from typing import Any, Literal


FactValueKind = Literal["numeric", "entity", "text"]
ClaimType = Literal["numeric", "entity", "comparison", "assertion"]
ClaimStatus = Literal[
    "verified",
    "candidate_match",
    "unverified",
    "contradicted",
    "ambiguous",
]
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
    subject: str | None = None
    as_of: str | None = None
    observed_at: str | None = None
    source_field: str | None = None
    fact_type: str | None = None

    def __post_init__(self) -> None:
        if self.observed_at is None:
            return
        if not isinstance(self.observed_at, str):
            raise ValueError("observed_at must be a timezone-aware ISO 8601 string")
        try:
            parsed = datetime.fromisoformat(self.observed_at)
        except ValueError as exc:
            raise ValueError("observed_at must be a timezone-aware ISO 8601 string") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("observed_at must be a timezone-aware ISO 8601 string")


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
    matched_fact_key: str | None = None
    ledger_value: Any = None
    answer_value: Any = None
    status: ClaimStatus = "unverified"
    diff: str | None = None
    start: int | None = None
    end: int | None = None
    schema_version: int = 1


@dataclass
class SuspectedNumber:
    """A numeric-looking span seen in output, whether or not an extractor covered it."""

    text_span: str
    start: int
    end: int
    covered: bool = False
    reason: str = "not_extracted"


@dataclass(frozen=True)
class Issue:
    """One deterministic checker finding attached to a coverage report."""

    code: str
    severity: Literal["hard", "soft"]
    message: str
    checker: str
    related_fact_keys: tuple[str, ...] = ()
    related_claim_ids: tuple[str, ...] = ()
    text_span: str | None = None
    start: int | None = None
    end: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code or not self.checker:
            raise ValueError("issue code and checker must be non-empty")
        if self.severity not in {"hard", "soft"}:
            raise ValueError("issue severity must be 'hard' or 'soft'")
        if not isinstance(self.details, dict) or not _is_json_safe(self.details):
            raise ValueError("issue details must be JSON-safe")
        if len(self.message) > 512:
            object.__setattr__(self, "message", self.message[:512])


@dataclass
class CoverageReport:
    """A fact coverage report for a single generated answer."""

    session_id: str
    output_claims: list[OutputClaim] = field(default_factory=list)
    suspected_numbers: list[SuspectedNumber] = field(default_factory=list)
    uncovered_numbers: list[SuspectedNumber] = field(default_factory=list)
    extraction_coverage: float = 1.0
    required_facts: list[RequiredFact] = field(default_factory=list)
    omitted_required_facts: list[RequiredFact] = field(default_factory=list)
    verified_count: int = 0
    candidate_match_count: int = 0
    unverified_count: int = 0
    contradicted_count: int = 0
    ambiguous_count: int = 0
    omitted_required_count: int = 0
    passed: bool = True
    policy_reason: str = ""
    schema_version: int = 1
    issues: tuple[Issue, ...] = ()
    hard_issue_count: int = 0
    soft_issue_count: int = 0


@dataclass(frozen=True)
class AssertionReport:
    """A promptfoo/DeepEval-friendly assertion result protocol."""

    pass_: bool
    score: float
    reason: str
    passed: bool | None = None
    success: bool | None = None
    assertion_type: str = "groundguard.fact_coverage"
    named_scores: dict[str, Any] = field(default_factory=dict)
    claims: list[dict[str, Any]] = field(default_factory=list)
    component_results: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1


@dataclass(frozen=True)
class DatasetCase:
    """A stable JSONL-compatible benchmark/eval case protocol."""

    name: str
    answer: str
    expected_passed: bool
    required_facts: list[str] = field(default_factory=list)
    facts: list[dict[str, Any]] = field(default_factory=list)
    policy: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1


def _is_json_safe(value: object) -> bool:
    if value is None or isinstance(value, (str, int, bool)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_safe(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return all(_is_json_safe(item) for item in value)
    return False
