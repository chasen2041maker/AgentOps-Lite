from decimal import Decimal
from pathlib import Path
from uuid import uuid4


def test_ledger_registers_and_queries_facts_by_key():
    from groundguard import Fact, Ledger

    ledger = Ledger(session_id="req_001", clock=lambda: 123.0)
    fact = Fact(
        id="fact_1",
        source_tool="get_company_financials",
        source_call_id="call_1",
        key="net_profit_2025",
        value=Decimal("82320000000"),
        unit="CNY",
    )

    ledger.register_fact(fact)

    [registered] = ledger.query("net_profit_2025")
    assert registered.recorded_at == 123.0
    assert registered.key == "net_profit_2025"
    assert registered.value == Decimal("82320000000")
    assert ledger.query("revenue_2025") == []


def test_ledger_preserves_existing_recorded_at():
    from groundguard import Fact, Ledger

    ledger = Ledger(session_id="req_001", clock=lambda: 999.0)
    fact = Fact(
        id="fact_1",
        source_tool="tool",
        source_call_id="call_1",
        key="stable_fact",
        value="known",
        value_kind="text",
        recorded_at=10.0,
    )

    ledger.register_fact(fact)

    assert ledger.query("stable_fact")[0].recorded_at == 10.0


def test_ledger_filters_expired_facts_by_default():
    from groundguard import Fact, Ledger

    ledger = Ledger(session_id="req_001", clock=lambda: 200.0)
    ledger.register_fact(
        Fact(
            id="fact_old",
            source_tool="market_quote",
            source_call_id="call_1",
            key="price",
            value=Decimal("10"),
            unit="USD",
            recorded_at=100.0,
            ttl_seconds=50,
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_current",
            source_tool="market_quote",
            source_call_id="call_2",
            key="price",
            value=Decimal("12"),
            unit="USD",
            recorded_at=180.0,
            ttl_seconds=50,
        )
    )

    assert [fact.id for fact in ledger.all_facts()] == ["fact_current"]
    assert [fact.id for fact in ledger.all_facts(exclude_expired=False)] == [
        "fact_old",
        "fact_current",
    ]


def test_ledger_context_manager_returns_self_and_does_not_drop_facts():
    from groundguard import Fact, Ledger

    with Ledger(session_id="req_001", clock=lambda: 1.0) as ledger:
        ledger.register_fact(
            Fact(
                id="fact_1",
                source_tool="tool",
                source_call_id="call_1",
                key="answer",
                value=Decimal("42"),
            )
        )

    assert ledger.query("answer")[0].value == Decimal("42")


def test_ledger_jsonl_round_trip_preserves_decimal_and_metadata():
    from groundguard import Fact, Ledger

    tmp_dir = Path(".tmp")
    tmp_dir.mkdir(exist_ok=True)
    path = tmp_dir / f"facts-round-trip-{uuid4().hex}.jsonl"

    ledger = Ledger(session_id="req_001", clock=lambda: 10.0)
    ledger.register_fact(
        Fact(
            id="fact_1",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="net_profit_2025",
            value=Decimal("82320000000"),
            unit="CNY",
            display_value="823.2 亿元",
            raw={"net_profit": "82320000000"},
            metadata={"ticker": "AAPL"},
        )
    )

    ledger.to_jsonl(path)
    loaded = Ledger.from_jsonl(path, session_id="req_001", clock=lambda: 20.0)

    [fact] = loaded.query("net_profit_2025")
    assert fact.value == Decimal("82320000000")
    assert fact.display_value == "823.2 亿元"
    assert fact.raw == {"net_profit": "82320000000"}
    assert fact.metadata == {"ticker": "AAPL"}
    assert fact.recorded_at == 10.0


def test_coverage_report_accepts_scoped_extractors_without_global_registration():
    from groundguard import Ledger, OutputClaim

    def extract_entity(text: str) -> list[OutputClaim]:
        start = text.index("ACME Corp")
        return [
            OutputClaim(
                id="claim_entity_acme",
                text_span="ACME Corp",
                claim_type="entity",
                normalized_value="ACME Corp",
                start=start,
                end=start + len("ACME Corp"),
            )
        ]

    ledger = Ledger(session_id="req_001")

    report = ledger.coverage_report(
        "ACME Corp reported revenue.",
        extractors={"entity": extract_entity},
    )

    assert [claim.claim_type for claim in report.output_claims] == ["entity"]
