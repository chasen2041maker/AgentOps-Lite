from decimal import Decimal
from pathlib import Path
from uuid import uuid4


def test_fact_gate_records_facts_and_checks_answer_with_required_coverage():
    from groundguard import FactGate

    gate = FactGate(session_id="req_001", clock=lambda: 100.0)
    fact = gate.record_fact(
        key="revenue_2025",
        value=Decimal("3830000000"),
        unit="USD",
        source_tool="finance_api",
        source_call_id="call_1",
    )

    report = gate.check(
        "Revenue was $3.83 billion [fact:revenue_2025].",
        required_fact_keys=["revenue_2025"],
    )

    assert fact.id.startswith("fact_revenue_2025_")
    assert report.passed is True
    assert report.verified_count == 1
    assert report.omitted_required_count == 0


def test_fact_gate_from_config_uses_required_facts_policy_and_extractor_packs():
    from groundguard import FactGate

    config_path = _temp_dir() / "groundguard.yml"
    config_path.write_text(
        "\n".join(
            [
                "required_facts:",
                "  - arr",
                "policy:",
                "  on_omitted_required: block",
                "extractors:",
                "  packs:",
                "    - saas",
                "report:",
                "  schema: groundguard",
                "  format: markdown",
            ]
        ),
        encoding="utf-8",
    )

    gate = FactGate.from_config(config_path, session_id="req_saas", clock=lambda: 100.0)
    gate.record_fact(
        key="arr",
        value=Decimal("1200000"),
        unit="USD",
        source_tool="billing",
        source_call_id="call_1",
    )

    report = gate.check("ARR was $1.2M [fact:arr].")

    assert report.passed is True
    assert report.required_facts[0].key == "arr"
    assert gate.report_format == "markdown"


def test_fact_gate_from_config_can_use_default_session_and_record_tool_result_alias():
    from groundguard import FactGate

    config_path = _temp_dir() / "groundguard.yml"
    config_path.write_text(
        "\n".join(
            [
                "required_facts:",
                "  - revenue",
                "extractors:",
                "  packs:",
                "    - finance",
            ]
        ),
        encoding="utf-8",
    )

    gate = FactGate.from_config(config_path, clock=lambda: 100.0)
    fact = gate.record_tool_result("revenue", Decimal("3.83"), "usd_b")
    report = gate.check("Revenue was $3.83 billion.", required=["revenue"])

    assert gate.session_id == "groundguard"
    assert fact.key == "revenue"
    assert report.passed is True
    assert report.output_claims[0].fact_key == "revenue"


def test_fact_gate_config_units_tolerance_controls_matching():
    from groundguard import FactGate

    config_path = _temp_dir() / "groundguard.yml"
    config_path.write_text(
        "\n".join(
            [
                "required_facts:",
                "  - price",
                "units:",
                "  tolerance: 0.02",
            ]
        ),
        encoding="utf-8",
    )

    gate = FactGate.from_config(config_path, session_id="req_tolerance", clock=lambda: 100.0)
    gate.record_tool_result("price", Decimal("100"), "USD")
    report = gate.check("Price was $101 [fact:price].")

    assert report.passed is True
    assert report.output_claims[0].status == "verified"


def test_fact_gate_can_write_and_restore_ledger_jsonl():
    from groundguard import FactGate

    temp_dir = _temp_dir()
    ledger_path = temp_dir / "facts.jsonl"

    gate = FactGate(session_id="req_jsonl", clock=lambda: 100.0)
    gate.record_fact(
        key="net_profit",
        value=Decimal("82320000000"),
        unit="CNY",
        source_tool="financials",
        source_call_id="call_1",
    )
    gate.to_jsonl(ledger_path)

    restored = FactGate.from_jsonl(ledger_path, session_id="req_jsonl")
    report = restored.check(
        "Net profit was RMB 82.32 billion [fact:net_profit].",
        required_fact_keys=["net_profit"],
    )

    assert report.passed is True
    assert report.verified_count == 1


def _temp_dir() -> Path:
    path = Path(".tmp") / "test_fact_gate_runtime" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path
