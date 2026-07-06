from __future__ import annotations

from groundguard.core.models import CoverageReport, Fact, OutputClaim, RequiredFact


def build_coverage_report(
    session_id: str,
    output_claims: list[OutputClaim],
    required_facts: list[RequiredFact],
    facts: list[Fact] | None = None,
    allow_candidate_matches: bool = False,
) -> CoverageReport:
    """Summarize matched output claims and required fact coverage."""

    covered_keys = _covered_required_keys(
        output_claims=output_claims,
        facts=facts or [],
        allow_candidate_matches=allow_candidate_matches,
    )
    omitted_required_facts = [
        required for required in required_facts if required.key not in covered_keys
    ]
    return CoverageReport(
        session_id=session_id,
        output_claims=output_claims,
        required_facts=required_facts,
        omitted_required_facts=omitted_required_facts,
        verified_count=_count_status(output_claims, "verified"),
        candidate_match_count=_count_status(output_claims, "candidate_match"),
        unverified_count=_count_status(output_claims, "unverified"),
        contradicted_count=_count_status(output_claims, "contradicted"),
        omitted_required_count=len(omitted_required_facts),
    )


def _covered_required_keys(
    output_claims: list[OutputClaim],
    facts: list[Fact],
    allow_candidate_matches: bool,
) -> set[str]:
    fact_key_by_id = {fact.id: fact.key for fact in facts}
    covered: set[str] = set()
    for claim in output_claims:
        if claim.status in {"verified", "contradicted"} and claim.fact_key is not None:
            covered.add(claim.fact_key)
        if (
            allow_candidate_matches
            and claim.status == "candidate_match"
            and claim.matched_fact_id in fact_key_by_id
        ):
            covered.add(fact_key_by_id[claim.matched_fact_id])
    return covered


def _count_status(output_claims: list[OutputClaim], status: str) -> int:
    return sum(1 for claim in output_claims if claim.status == status)
