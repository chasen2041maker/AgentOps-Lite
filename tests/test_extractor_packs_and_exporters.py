from decimal import Decimal


def test_builtin_extractor_packs_are_discoverable_and_scoped():
    from groundguard.core.extractors import available_extractor_packs, extractors_for_packs
    from groundguard.core.output_claim_extractor import extract_output_claims

    assert {"finance", "saas", "ops"}.issubset(set(available_extractor_packs()))

    claims = extract_output_claims(
        "ARR was $1.2M [fact:arr] and P95 latency was 230ms [fact:p95].",
        extractors=extractors_for_packs(["saas", "ops"]),
    )

    assert [claim.fact_key for claim in claims] == ["arr", "p95"]
    assert [claim.normalized_value for claim in claims] == [
        Decimal("1200000"),
        Decimal("230"),
    ]


def test_otel_exporter_returns_dependency_free_span_events():
    from groundguard import CoverageReport, OutputClaim
    from groundguard.integrations.otel import report_to_otel_events

    report = CoverageReport(
        session_id="req_otel",
        output_claims=[
            OutputClaim(
                id="claim_1",
                text_span="ARR was $1.2M",
                claim_type="numeric",
                normalized_value=Decimal("1200000"),
                unit="USD",
                status="verified",
                matched_fact_id="fact_arr",
            )
        ],
        verified_count=1,
        passed=True,
    )

    events = report_to_otel_events(report)

    assert events[0]["name"] == "groundguard.coverage_report"
    assert events[0]["attributes"]["groundguard.session_id"] == "req_otel"
    assert events[0]["attributes"]["groundguard.passed"] is True
    assert events[1]["name"] == "groundguard.output_claim"
    assert events[1]["attributes"]["groundguard.claim.status"] == "verified"


def test_server_payload_evaluator_checks_facts_without_runtime_dependencies():
    from groundguard.server import evaluate_payload

    payload = {
        "session_id": "req_server",
        "facts": [
            {
                "id": "fact_arr",
                "source_tool": "billing",
                "source_call_id": "call_1",
                "key": "arr",
                "value": "1200000",
                "unit": "USD",
            }
        ],
        "answer": "ARR was $1.2M [fact:arr].",
        "required_facts": ["arr"],
    }

    result = evaluate_payload(payload)

    assert result["summary"]["passed"] is True
    assert result["summary"]["verified_count"] == 1
