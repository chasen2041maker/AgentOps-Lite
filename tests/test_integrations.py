from decimal import Decimal

from groundguard import Issue


def _sample_report():
    from groundguard import CoverageReport, OutputClaim

    return CoverageReport(
        session_id="req_001",
        output_claims=[
            OutputClaim(
                id="claim_1",
                text_span="Revenue was $3.80 billion",
                claim_type="numeric",
                normalized_value=Decimal("3800000000"),
                unit="USD",
                status="contradicted",
                diff="ledger=3830000000; output=3800000000",
                start=12,
                end=25,
            )
        ],
        contradicted_count=1,
        passed=False,
        policy_reason="contradicted_count=1 > max_contradicted=0",
        issues=(
            Issue(
                code="orphan_numeric_claim",
                severity="hard",
                message="Numeric claim is not covered by a recorded fact.",
                checker="orphan_numeric",
            ),
        ),
        hard_issue_count=1,
    )


def test_promptfoo_adapter_returns_assertion_payload_with_components():
    from groundguard.integrations.promptfoo import to_promptfoo_assertion

    payload = to_promptfoo_assertion(_sample_report())

    assert payload["pass"] is False
    assert payload["assertion"]["type"] == "groundguard.fact_coverage"
    assert payload["componentResults"][0]["pass"] is False
    assert payload["componentResults"][0]["metadata"]["status"] == "contradicted"
    assert payload["namedScores"]["groundguard.contradicted_count"] == 1
    assert payload["metadata"]["groundguard"]["issues"][0]["code"] == "orphan_numeric_claim"


def test_deepeval_adapter_returns_metric_result_without_optional_dependency():
    from groundguard.integrations.deepeval import to_deepeval_result

    payload = to_deepeval_result(_sample_report())

    assert payload["success"] is False
    assert payload["score"] == 0.0
    assert payload["reason"] == "contradicted_count=1 > max_contradicted=0"
    assert payload["metadata"]["groundguard"]["session_id"] == "req_001"
    assert payload["metadata"]["groundguard"]["issues"][0]["severity"] == "hard"

