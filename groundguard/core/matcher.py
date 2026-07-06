from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from groundguard.core.models import Fact, OutputClaim


def match_claims(
    claims: list[OutputClaim],
    facts: list[Fact],
    tolerance: float = 0.005,
) -> list[OutputClaim]:
    """Match output claims against registered facts using deterministic rules."""

    matched_claims: list[OutputClaim] = []
    for claim in claims:
        if claim.fact_key is not None:
            matched_claims.append(_match_explicit_key(claim, facts, tolerance))
        else:
            matched_claims.append(_match_numeric_candidate(claim, facts, tolerance))
    return matched_claims


def _match_explicit_key(
    claim: OutputClaim,
    facts: list[Fact],
    tolerance: float,
) -> OutputClaim:
    fact = next((candidate for candidate in facts if candidate.key == claim.fact_key), None)
    if fact is None:
        return claim
    if fact.unit != claim.unit:
        return replace(
            claim,
            status="contradicted",
            matched_fact_id=fact.id,
            diff=f"unit ledger={fact.unit}; output={claim.unit}",
        )
    if _values_match(claim.normalized_value, fact.value, tolerance):
        return replace(claim, status="verified", matched_fact_id=fact.id, diff=None)
    return replace(
        claim,
        status="contradicted",
        matched_fact_id=fact.id,
        diff=f"ledger={fact.value}; output={claim.normalized_value}",
    )


def _match_numeric_candidate(
    claim: OutputClaim,
    facts: list[Fact],
    tolerance: float,
) -> OutputClaim:
    candidates = [
        fact
        for fact in facts
        if fact.unit == claim.unit and isinstance(fact.value, Decimal)
    ]
    nearest = _nearest_fact(claim.normalized_value, candidates)
    if nearest is None:
        return claim
    if _values_match(claim.normalized_value, nearest.value, tolerance):
        return replace(
            claim,
            status="candidate_match",
            matched_fact_id=nearest.id,
            diff=None,
        )
    return claim


def _nearest_fact(value: object, facts: list[Fact]) -> Fact | None:
    if not isinstance(value, Decimal) or not facts:
        return None
    return min(facts, key=lambda fact: abs(fact.value - value))  # type: ignore[operator]


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
