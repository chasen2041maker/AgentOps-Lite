from decimal import Decimal
from importlib import resources
import json
from pathlib import Path


def test_public_protocol_models_expose_schema_version():
    from groundguard import (
        AssertionReport,
        CoverageReport,
        DatasetCase,
        Fact,
        OutputClaim,
        Policy,
    )

    fact = Fact(
        id="fact_revenue",
        source_tool="finance_api",
        source_call_id="call_1",
        key="revenue",
        value=Decimal("3830000000"),
        unit="USD",
    )
    claim = OutputClaim(
        id="claim_revenue",
        text_span="Revenue was $3.83 billion",
        claim_type="numeric",
        normalized_value=Decimal("3830000000"),
        unit="USD",
    )
    report = CoverageReport(session_id="req_001")
    policy = Policy()
    assertion = AssertionReport(pass_=True, score=1.0, reason="ok")
    dataset_case = DatasetCase(
        name="verified_revenue",
        answer="Revenue was $3.83 billion [fact:revenue].",
        expected_passed=True,
        required_facts=["revenue"],
    )

    assert fact.schema_version == 1
    assert claim.schema_version == 1
    assert report.schema_version == 1
    assert policy.schema_version == 1
    assert assertion.schema_version == 1
    assert dataset_case.schema_version == 1


def test_schema_compatibility_is_documented():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Schema Compatibility" in readme
    assert "schema_version" in readme
    assert "GroundGuard will not remove or rename fields within a major version" in readme


def test_readme_has_text_brand_before_remote_logo_dependency():
    readme = Path("README.md").read_text(encoding="utf-8")
    heading_index = readme.index("<h1>GroundGuard</h1>")
    image_index = readme.index("groundguard-logo-wordmark.png")

    assert heading_index < image_index


def test_public_json_schema_files_exist_and_expose_core_contracts():
    report_schema = json.loads(
        Path("schemas/groundguard.report.v1.schema.json").read_text(encoding="utf-8")
    )
    config_schema = json.loads(
        Path("schemas/groundguard.config.v1.schema.json").read_text(encoding="utf-8")
    )

    assert report_schema["$id"].endswith("groundguard.report.v1.schema.json")
    assert report_schema["properties"]["schema_version"]["const"] == (
        "groundguard.report.v1"
    )
    assert {"schema_version", "session_id", "summary", "claims"} <= set(
        report_schema["required"]
    )
    claim_properties = report_schema["$defs"]["output_claim"]["properties"]
    assert {"status", "text_span", "matched_fact_key", "ledger_value"} <= set(
        claim_properties
    )
    assert "issues" in report_schema["properties"]
    assert report_schema["properties"]["issues"]["items"]["$ref"] == "#/$defs/issue"
    assert {"hard_issue_count", "soft_issue_count"} <= set(
        report_schema["$defs"]["summary"]["properties"]
    )
    issue_properties = report_schema["$defs"]["issue"]["properties"]
    assert {
        "code",
        "severity",
        "message",
        "checker",
        "related_fact_keys",
        "related_claim_ids",
        "text_span",
        "start",
        "end",
        "details",
    } <= set(issue_properties)

    assert config_schema["$id"].endswith("groundguard.config.v1.schema.json")
    assert {"required_facts", "policy", "extractors", "units", "report"} <= set(
        config_schema["properties"]
    )
    assert "on_contradicted" in config_schema["$defs"]["policy"]["properties"]


def test_packaged_json_schema_files_match_public_files():
    for filename in (
        "groundguard.report.v1.schema.json",
        "groundguard.config.v1.schema.json",
    ):
        public_schema = Path("schemas", filename).read_text(encoding="utf-8")
        packaged_schema = (
            resources.files("groundguard.schemas")
            .joinpath(filename)
            .read_text(encoding="utf-8")
        )

        assert json.loads(packaged_schema) == json.loads(public_schema)
