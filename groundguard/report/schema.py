from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Any

from groundguard.core.models import CoverageReport


REPORT_SCHEMA_VERSION = "groundguard.report.v1"


def report_to_versioned_dict(report: CoverageReport) -> dict[str, Any]:
    """Return GroundGuard's stable report schema for tools and UIs."""

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "session_id": report.session_id,
        "summary": {
            "passed": report.passed,
            "policy_reason": report.policy_reason,
            "verified_count": report.verified_count,
            "candidate_match_count": report.candidate_match_count,
            "unverified_count": report.unverified_count,
            "contradicted_count": report.contradicted_count,
            "ambiguous_count": report.ambiguous_count,
            "omitted_required_count": report.omitted_required_count,
            "extraction_coverage": report.extraction_coverage,
        },
        "claims": _json_safe([asdict(claim) for claim in report.output_claims]),
        "required_facts": _json_safe([asdict(item) for item in report.required_facts]),
        "omitted_required_facts": _json_safe(
            [asdict(item) for item in report.omitted_required_facts]
        ),
        "suspected_numbers": _json_safe(
            [asdict(item) for item in report.suspected_numbers]
        ),
        "uncovered_numbers": _json_safe(
            [asdict(item) for item in report.uncovered_numbers]
        ),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
