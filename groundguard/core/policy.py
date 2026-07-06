from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from groundguard.core.models import CoverageReport


@dataclass(frozen=True)
class Policy:
    max_unverified_ratio: float = 0.1
    max_contradicted: int = 0
    max_ambiguous: int = 0
    max_omitted_required: int = 0
    allow_candidate_matches: bool = False
    on_unverified: Literal["flag", "strip", "block"] = "flag"
    on_contradicted: Literal["flag", "block", "fix", "reask"] = "block"
    on_omitted_required: Literal["flag", "block"] = "block"


def evaluate_policy(report: CoverageReport, policy: Policy) -> CoverageReport:
    reasons: list[str] = []
    if (
        policy.on_contradicted in {"block", "fix", "reask"}
        and report.contradicted_count > policy.max_contradicted
    ):
        reasons.append(
            f"contradicted_count={report.contradicted_count} "
            f"> max_contradicted={policy.max_contradicted}"
        )
    if report.ambiguous_count > policy.max_ambiguous:
        reasons.append(
            f"ambiguous_count={report.ambiguous_count} "
            f"> max_ambiguous={policy.max_ambiguous}"
        )
    if (
        policy.on_omitted_required == "block"
        and report.omitted_required_count > policy.max_omitted_required
    ):
        reasons.append(
            f"omitted_required_count={report.omitted_required_count} "
            f"> max_omitted_required={policy.max_omitted_required}"
        )
    unverified_ratio = _unverified_ratio(report)
    if policy.on_unverified == "block" and unverified_ratio > policy.max_unverified_ratio:
        reasons.append(
            f"unverified_ratio={unverified_ratio:.3f} "
            f"> max_unverified_ratio={policy.max_unverified_ratio:.3f}"
        )
    if policy.on_unverified == "strip" and unverified_ratio > policy.max_unverified_ratio:
        reasons.append(
            f"unverified_ratio={unverified_ratio:.3f} "
            f"> max_unverified_ratio={policy.max_unverified_ratio:.3f}"
        )
    if policy.on_unverified == "flag" and unverified_ratio > policy.max_unverified_ratio:
        reasons.append(
            f"unverified_ratio={unverified_ratio:.3f} "
            f"> max_unverified_ratio={policy.max_unverified_ratio:.3f}"
        )
    return replace(
        report,
        passed=not reasons,
        policy_reason="; ".join(reasons),
    )


def _unverified_ratio(report: CoverageReport) -> float:
    total_claims = len(report.output_claims)
    if total_claims == 0:
        return 0.0
    return report.unverified_count / total_claims
