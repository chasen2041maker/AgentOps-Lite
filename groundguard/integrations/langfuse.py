from __future__ import annotations

from groundguard.core.models import CoverageReport
from groundguard.report import report_to_versioned_dict


def report_to_langfuse_payload(report: CoverageReport) -> dict[str, object]:
    """Return a Langfuse-friendly score payload without importing Langfuse."""

    return {
        "name": "groundguard.fact_coverage",
        "value": _score(report),
        "comment": report.policy_reason or "GroundGuard policy passed.",
        "metadata": report_to_versioned_dict(report),
    }


def _score(report: CoverageReport) -> float:
    total_claims = (
        report.verified_count
        + report.candidate_match_count
        + report.unverified_count
        + report.contradicted_count
        + report.ambiguous_count
    )
    if total_claims == 0:
        return 1.0 if report.passed else 0.0
    return report.verified_count / total_claims
