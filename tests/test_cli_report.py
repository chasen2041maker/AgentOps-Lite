from decimal import Decimal
import json
from pathlib import Path
from uuid import uuid4


def test_cli_report_writes_coverage_json(capsys):
    from groundguard import Fact, Ledger
    from groundguard.cli.report import main

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)
    ledger.register_fact(
        Fact(
            id="fact_net_profit_2025",
            source_tool="tool",
            source_call_id="call_1",
            key="net_profit_2025",
            value=Decimal("82320000000"),
            unit="CNY",
        )
    )
    temp_dir = _temp_dir()
    ledger_path = temp_dir / "facts.jsonl"
    answer_path = temp_dir / "answer.txt"
    ledger.to_jsonl(ledger_path)
    answer_path.write_text("本轮未取得可核实的净利润数据。", encoding="utf-8")

    exit_code = main(
        [
            "--ledger-jsonl",
            str(ledger_path),
            "--answer-file",
            str(answer_path),
            "--required-fact",
            "net_profit_2025",
            "--session-id",
            "req_001",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["session_id"] == "req_001"
    assert payload["passed"] is False
    assert payload["omitted_required_count"] == 1
    assert payload["omitted_required_facts"][0]["key"] == "net_profit_2025"


def test_cli_report_can_fail_on_policy(capsys):
    from groundguard import Fact, Ledger
    from groundguard.cli.report import main

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)
    ledger.register_fact(
        Fact(
            id="fact_net_profit_2025",
            source_tool="tool",
            source_call_id="call_1",
            key="net_profit_2025",
            value=Decimal("82320000000"),
            unit="CNY",
        )
    )
    temp_dir = _temp_dir()
    ledger_path = temp_dir / "facts.jsonl"
    answer_path = temp_dir / "answer.txt"
    ledger.to_jsonl(ledger_path)
    answer_path.write_text("本轮未取得可核实的净利润数据。", encoding="utf-8")

    exit_code = main(
        [
            "--ledger-jsonl",
            str(ledger_path),
            "--answer-file",
            str(answer_path),
            "--required-fact",
            "net_profit_2025",
            "--session-id",
            "req_001",
            "--fail-on-policy",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["passed"] is False
    assert "omitted_required_count=1" in payload["policy_reason"]


def test_report_to_assertion_dict_exposes_promptfoo_and_deepeval_fields():
    from groundguard import CoverageReport, OutputClaim
    from groundguard.cli.report import report_to_assertion_dict

    report = CoverageReport(
        session_id="req_001",
        output_claims=[
            OutputClaim(
                id="claim_1",
                text_span="Revenue was $3.83 billion",
                claim_type="numeric",
                normalized_value=Decimal("3830000000"),
                unit="USD",
                status="contradicted",
                diff="ledger=383000000; output=3830000000",
                start=12,
                end=25,
            )
        ],
        verified_count=1,
        unverified_count=1,
        omitted_required_count=1,
        passed=False,
        policy_reason="omitted_required_count=1 > max_omitted_required=0",
    )

    payload = report_to_assertion_dict(report)

    assert payload["pass"] is False
    assert payload["passed"] is False
    assert payload["success"] is False
    assert payload["score"] == 0.5
    assert payload["reason"] == "omitted_required_count=1 > max_omitted_required=0"
    assert payload["assertion"]["type"] == "groundguard.fact_coverage"
    assert payload["namedScores"]["groundguard.verified_count"] == 1
    assert payload["metadata"]["groundguard"]["omitted_required_count"] == 1
    assert payload["claims"][0]["text_span"] == "Revenue was $3.83 billion"
    assert payload["claims"][0]["status"] == "contradicted"
    assert payload["claims"][0]["diff"] == "ledger=383000000; output=3830000000"
    assert payload["claims"][0]["start"] == 12
    assert payload["claims"][0]["end"] == 25


def test_cli_report_can_emit_assertion_schema(capsys):
    from groundguard import Fact, Ledger
    from groundguard.cli.report import main

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)
    ledger.register_fact(
        Fact(
            id="fact_net_profit_2025",
            source_tool="tool",
            source_call_id="call_1",
            key="net_profit_2025",
            value=Decimal("82320000000"),
            unit="CNY",
        )
    )
    temp_dir = _temp_dir()
    ledger_path = temp_dir / "facts.jsonl"
    answer_path = temp_dir / "answer.txt"
    ledger.to_jsonl(ledger_path)
    answer_path.write_text("No verifiable net profit data was available.", encoding="utf-8")

    exit_code = main(
        [
            "--ledger-jsonl",
            str(ledger_path),
            "--answer-file",
            str(answer_path),
            "--required-fact",
            "net_profit_2025",
            "--session-id",
            "req_001",
            "--schema",
            "assertion",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["pass"] is False
    assert payload["success"] is False
    assert payload["metadata"]["groundguard"]["session_id"] == "req_001"


def _temp_dir() -> Path:
    path = Path(".tmp") / "test_cli_report" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path
