from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Any

from groundguard.core.models import CoverageReport


def report_to_otel_events(report: CoverageReport) -> list[dict[str, Any]]:
    """Convert a report into OpenTelemetry-style span event payloads.

    This function is dependency-free by design. Applications that already use
    OpenTelemetry can attach these dictionaries to spans themselves.
    """

    events: list[dict[str, Any]] = [
        {
            "name": "groundguard.coverage_report",
            "attributes": {
                "groundguard.session_id": report.session_id,
                "groundguard.passed": report.passed,
                "groundguard.policy_reason": report.policy_reason,
                "groundguard.verified_count": report.verified_count,
                "groundguard.candidate_match_count": report.candidate_match_count,
                "groundguard.unverified_count": report.unverified_count,
                "groundguard.contradicted_count": report.contradicted_count,
                "groundguard.ambiguous_count": report.ambiguous_count,
                "groundguard.omitted_required_count": report.omitted_required_count,
                "groundguard.extraction_coverage": report.extraction_coverage,
            },
        }
    ]
    for claim in report.output_claims:
        events.append(
            {
                "name": "groundguard.output_claim",
                "attributes": {
                    "groundguard.session_id": report.session_id,
                    "groundguard.claim.id": claim.id,
                    "groundguard.claim.status": claim.status,
                    "groundguard.claim.type": claim.claim_type,
                    "groundguard.claim.text_span": claim.text_span,
                    "groundguard.claim.unit": claim.unit or "",
                    "groundguard.claim.fact_key": claim.fact_key or "",
                    "groundguard.claim.matched_fact_id": claim.matched_fact_id or "",
                    "groundguard.claim.diff": claim.diff or "",
                    "groundguard.claim.payload": _json_safe(asdict(claim)),
                },
            }
        )
    return events


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
