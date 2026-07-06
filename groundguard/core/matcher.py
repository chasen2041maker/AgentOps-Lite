from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from decimal import Decimal

from groundguard.core.models import Fact, OutputClaim
from groundguard.core.units import normalize_numeric_fact


def match_claims(
    claims: list[OutputClaim],
    facts: list[Fact],
    tolerance: float = 0.005,
) -> list[OutputClaim]:
    """Match output claims against registered facts using deterministic rules."""

    fact_index = _build_fact_match_index(facts)
    matched_claims: list[OutputClaim] = []
    for claim in claims:
        if claim.fact_key is not None:
            matched_claims.append(_match_explicit_key(claim, fact_index, tolerance))
        else:
            matched_claims.append(_match_numeric_candidate(claim, fact_index, tolerance))
    return matched_claims


@dataclass(frozen=True)
class _NormalizedFact:
    fact: Fact
    value: Decimal | str
    unit: str | None


@dataclass(frozen=True)
class _FactMatchIndex:
    by_key: dict[str, Fact]
    numeric_by_unit: dict[str | None, list[_NormalizedFact]]


def _build_fact_match_index(facts: list[Fact]) -> _FactMatchIndex:
    by_key: dict[str, Fact] = {}
    numeric_by_unit: dict[str | None, list[_NormalizedFact]] = {}
    for fact in facts:
        by_key.setdefault(fact.key, fact)
        normalized_value, normalized_unit = _normalize_fact_value(fact)
        if isinstance(normalized_value, Decimal):
            numeric_by_unit.setdefault(normalized_unit, []).append(
                _NormalizedFact(
                    fact=fact,
                    value=normalized_value,
                    unit=normalized_unit,
                )
            )
    return _FactMatchIndex(by_key=by_key, numeric_by_unit=numeric_by_unit)


def _match_explicit_key(
    claim: OutputClaim,
    fact_index: _FactMatchIndex,
    tolerance: float,
) -> OutputClaim:
    fact = fact_index.by_key.get(claim.fact_key or "")
    if fact is None:
        return claim
    normalized_claim_value, normalized_claim_unit = _normalize_claim_value(claim)
    normalized_fact_value, normalized_fact_unit = _normalize_fact_value(fact)
    if normalized_fact_unit != normalized_claim_unit:
        return replace(
            claim,
            status="contradicted",
            matched_fact_id=fact.id,
            diff=f"unit ledger={normalized_fact_unit}; output={normalized_claim_unit}",
        )
    if _values_match(normalized_claim_value, normalized_fact_value, tolerance):
        return replace(claim, status="verified", matched_fact_id=fact.id, diff=None)
    return replace(
        claim,
        status="contradicted",
        matched_fact_id=fact.id,
        diff=f"ledger={normalized_fact_value}; output={normalized_claim_value}",
    )


def _match_numeric_candidate(
    claim: OutputClaim,
    fact_index: _FactMatchIndex,
    tolerance: float,
) -> OutputClaim:
    normalized_claim_value, normalized_claim_unit = _normalize_claim_value(claim)
    if not isinstance(normalized_claim_value, Decimal):
        return claim
    candidates = fact_index.numeric_by_unit.get(normalized_claim_unit, [])
    nearby = [
        normalized_fact
        for normalized_fact in candidates
        if _values_match(normalized_claim_value, normalized_fact.value, tolerance)
    ]
    if len(nearby) > 1:
        candidate_ids = ",".join(item.fact.id for item in nearby)
        return replace(
            claim,
            status="ambiguous",
            matched_fact_id=None,
            diff=f"ambiguous_candidates={candidate_ids}",
        )
    if len(nearby) == 1:
        nearest = nearby[0].fact
        return replace(
            claim,
            status="candidate_match",
            matched_fact_id=nearest.id,
            diff=None,
        )
    return claim


def _normalize_claim_value(claim: OutputClaim) -> tuple[object, str | None]:
    if isinstance(claim.normalized_value, Decimal):
        return normalize_numeric_fact(claim.normalized_value, claim.unit)
    return claim.normalized_value, claim.unit


def _normalize_fact_value(fact: Fact) -> tuple[Decimal | str, str | None]:
    if isinstance(fact.value, Decimal):
        return normalize_numeric_fact(fact.value, fact.unit)
    return fact.value, fact.unit


def _values_match(output_value: object, fact_value: Decimal | str, tolerance: float) -> bool:
    if isinstance(output_value, Decimal) and isinstance(fact_value, Decimal):
        return _decimal_values_match(output_value, fact_value, tolerance)
    return output_value == fact_value


def _decimal_values_match(output_value: Decimal, fact_value: Decimal, tolerance: float) -> bool:
    difference = abs(output_value - fact_value)
    if fact_value == 0:
        return difference <= Decimal(str(tolerance))
    relative_error = difference / abs(fact_value)
    return relative_error <= Decimal(str(tolerance))
