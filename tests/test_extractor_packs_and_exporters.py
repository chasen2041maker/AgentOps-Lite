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


def test_domain_extractor_packs_assign_fact_keys_from_metric_labels():
    from groundguard import FactGate
    from groundguard.core.config import ExtractorConfig, GroundGuardConfig

    gate = FactGate(
        session_id="req_packs",
        config=GroundGuardConfig(
            required_facts=["arr", "gross_margin", "p95_latency"],
            extractors=ExtractorConfig(packs=["finance", "saas", "ops"]),
        ),
        clock=lambda: 100.0,
    )
    gate.record_tool_result("arr", Decimal("1200000"), "USD")
    gate.record_tool_result("gross_margin", Decimal("21.5"), "%")
    gate.record_tool_result("p95_latency", Decimal("230"), "ms")

    report = gate.check(
        "ARR was $1.2M. Gross margin was 21.5%. P95 latency was 230ms.",
    )

    assert report.passed is True
    assert [claim.fact_key for claim in report.output_claims] == [
        "arr",
        "gross_margin",
        "p95_latency",
    ]
    assert [claim.status for claim in report.output_claims] == [
        "verified",
        "verified",
        "verified",
    ]


def test_domain_extractor_packs_assign_chinese_fact_keys_without_source_encoding_risk():
    from groundguard import FactGate
    from groundguard.core.config import ExtractorConfig, GroundGuardConfig

    answer = (
        "\u8425\u6536\u4e3a\u4eba\u6c11\u5e0138.3\u4ebf\u5143\u3002"
        "\u6bdb\u5229\u7387\u4e3a21.5%\u3002"
        "P95\u5ef6\u8fdf\u4e3a230\u6beb\u79d2\u3002"
    )
    gate = FactGate(
        config=GroundGuardConfig(
            required_facts=["revenue", "gross_margin", "p95_latency"],
            extractors=ExtractorConfig(packs=["finance", "ops"]),
        ),
        clock=lambda: 100.0,
    )
    gate.record_tool_result("revenue", Decimal("3830000000"), "CNY")
    gate.record_tool_result("gross_margin", Decimal("21.5"), "%")
    gate.record_tool_result("p95_latency", Decimal("230"), "ms")

    report = gate.check(answer)

    assert report.passed is True
    assert [claim.fact_key for claim in report.output_claims] == [
        "revenue",
        "gross_margin",
        "p95_latency",
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


def test_langfuse_and_phoenix_exporters_return_dependency_free_payloads():
    from groundguard import CoverageReport, OutputClaim
    from groundguard.integrations.langfuse import report_to_langfuse_payload
    from groundguard.integrations.phoenix import report_to_phoenix_eval

    report = CoverageReport(
        session_id="req_export",
        output_claims=[
            OutputClaim(
                id="claim_1",
                text_span="ARR was $1.2M",
                claim_type="numeric",
                normalized_value=Decimal("1200000"),
                unit="USD",
                status="verified",
                matched_fact_key="arr",
            )
        ],
        verified_count=1,
        passed=True,
    )

    langfuse_payload = report_to_langfuse_payload(report)
    phoenix_payload = report_to_phoenix_eval(report)

    assert langfuse_payload["name"] == "groundguard.fact_coverage"
    assert langfuse_payload["value"] == 1.0
    assert langfuse_payload["metadata"]["session_id"] == "req_export"
    assert phoenix_payload["eval_name"] == "groundguard.fact_coverage"
    assert phoenix_payload["score"] == 1.0
    assert phoenix_payload["label"] == "pass"


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


def test_server_payload_evaluator_can_use_configured_extractor_packs_and_tolerance():
    from pathlib import Path
    from uuid import uuid4

    from groundguard.core.config import load_config
    from groundguard.server import evaluate_payload

    temp_dir = Path(".tmp") / "test_server_config" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    config_path = temp_dir / "groundguard.yml"
    config_path.write_text(
        "\n".join(
            [
                "required_facts:",
                "  - arr",
                "extractors:",
                "  packs:",
                "    - saas",
                "units:",
                "  tolerance: 0.02",
            ]
        ),
        encoding="utf-8",
    )

    result = evaluate_payload(
        {
            "session_id": "req_server_config",
            "facts": [
                {
                    "key": "arr",
                    "value": "1200000",
                    "unit": "USD",
                }
            ],
            "answer": "ARR was $1.21M.",
        },
        config=load_config(config_path),
    )

    assert result["summary"]["passed"] is True
    assert result["claims"][0]["fact_key"] == "arr"
