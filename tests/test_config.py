from decimal import Decimal
import json
from pathlib import Path
from uuid import uuid4


def test_load_config_reads_required_facts_policy_and_report_options():
    from groundguard.core.config import load_config

    config_path = _temp_dir() / "groundguard.yml"
    config_path.write_text(
        "\n".join(
            [
                "required_facts:",
                "  - revenue_2025",
                "  - net_profit_2025",
                "policy:",
                "  allow_candidate_matches: true",
                "  on_unverified: block",
                "  max_unverified_ratio: 0.0",
                "report:",
                "  schema: assertion",
                "  fail_on_policy: true",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.required_facts == ["revenue_2025", "net_profit_2025"]
    assert config.policy.allow_candidate_matches is True
    assert config.policy.on_unverified == "block"
    assert config.policy.max_unverified_ratio == 0.0
    assert config.report.schema == "assertion"
    assert config.report.fail_on_policy is True


def test_cli_report_can_use_groundguard_config(capsys):
    from groundguard import Fact, Ledger
    from groundguard.cli.report import main

    temp_dir = _temp_dir()
    ledger_path = temp_dir / "facts.jsonl"
    answer_path = temp_dir / "answer.txt"
    config_path = temp_dir / "groundguard.yml"

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)
    ledger.register_fact(
        Fact(
            id="fact_revenue_2025",
            source_tool="tool",
            source_call_id="call_1",
            key="revenue_2025",
            value=Decimal("3830000000"),
            unit="USD",
        )
    )
    ledger.to_jsonl(ledger_path)
    answer_path.write_text(
        "Revenue was $3.83 billion [fact:revenue_2025].",
        encoding="utf-8",
    )
    config_path.write_text(
        "\n".join(
            [
                "required_facts:",
                "  - revenue_2025",
                "report:",
                "  schema: assertion",
                "  fail_on_policy: true",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--ledger-jsonl",
            str(ledger_path),
            "--answer-file",
            str(answer_path),
            "--session-id",
            "req_001",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["pass"] is True
    assert payload["metadata"]["groundguard"]["required_facts"][0]["key"] == "revenue_2025"


def _temp_dir() -> Path:
    path = Path(".tmp") / "test_config" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path

