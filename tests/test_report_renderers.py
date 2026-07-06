from decimal import Decimal


def test_versioned_report_schema_flattens_claims_for_tools():
    from groundguard import CoverageReport, OutputClaim
    from groundguard.report import report_to_versioned_dict

    report = CoverageReport(
        session_id="req_001",
        output_claims=[
            OutputClaim(
                id="claim_1",
                text_span="Revenue was $3.83 billion",
                claim_type="numeric",
                normalized_value=Decimal("3830000000"),
                unit="USD",
                status="verified",
                matched_fact_id="fact_revenue",
                start=12,
                end=25,
            )
        ],
        verified_count=1,
        passed=True,
    )

    payload = report_to_versioned_dict(report)

    assert payload["schema_version"] == "groundguard.report.v1"
    assert payload["summary"]["passed"] is True
    assert payload["claims"][0]["text_span"] == "Revenue was $3.83 billion"
    assert payload["claims"][0]["status"] == "verified"
    assert payload["claims"][0]["start"] == 12
    assert payload["claims"][0]["end"] == 25


def test_markdown_html_and_github_comment_render_report_claims():
    from groundguard import CoverageReport, OutputClaim
    from groundguard.report import (
        render_github_pr_comment,
        render_html_report,
        render_markdown_report,
    )

    report = CoverageReport(
        session_id="req_001",
        output_claims=[
            OutputClaim(
                id="claim_1",
                text_span="Revenue was <wrong> $4.00 billion",
                claim_type="numeric",
                normalized_value=Decimal("4000000000"),
                unit="USD",
                status="contradicted",
                matched_fact_id="fact_revenue",
                diff="ledger=3830000000; output=4000000000",
            )
        ],
        contradicted_count=1,
        passed=False,
        policy_reason="contradicted_count=1 > max_contradicted=0",
    )

    markdown = render_markdown_report(report)
    html = render_html_report(report)
    comment = render_github_pr_comment(report)

    assert "| Status | Claim | Unit | Matched fact | Diff |" in markdown
    assert "contradicted" in markdown
    assert "&lt;wrong&gt;" in html
    assert "GroundGuard Fact Gate" in comment
    assert "contradicted_count=1" in comment


def test_cli_report_can_write_markdown_format():
    from pathlib import Path
    from uuid import uuid4

    from groundguard import Fact, Ledger
    from groundguard.cli.report import main

    temp_dir = Path(".tmp") / "test_report_renderers" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = temp_dir / "facts.jsonl"
    answer_path = temp_dir / "answer.txt"
    output_path = temp_dir / "report.md"

    ledger = Ledger(session_id="req_cli", clock=lambda: 100.0)
    ledger.register_fact(
        Fact(
            id="fact_revenue",
            source_tool="finance_api",
            source_call_id="call_1",
            key="revenue",
            value=Decimal("3830000000"),
            unit="USD",
        )
    )
    ledger.to_jsonl(ledger_path)
    answer_path.write_text("Revenue was $3.83 billion [fact:revenue].", encoding="utf-8")

    exit_code = main(
        [
            "--ledger-jsonl",
            str(ledger_path),
            "--answer-file",
            str(answer_path),
            "--required-fact",
            "revenue",
            "--session-id",
            "req_cli",
            "--format",
            "markdown",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.read_text(encoding="utf-8").startswith("# GroundGuard Report")
