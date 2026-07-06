from decimal import Decimal


def test_tool_call_records_explicit_facts_into_ledger():
    from groundguard import Ledger, tool_call

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)
    raw = {"net_profit": "82320000000", "revenue": "383000000000"}

    with tool_call(
        "get_company_financials",
        args={"ticker": "AAPL"},
        ledger=ledger,
        clock=lambda: 10.0,
    ) as call:
        call.record_facts(
            {
                "net_profit_2025": (Decimal("82320000000"), "CNY"),
                "revenue_2025": (Decimal("383000000000"), "CNY"),
            },
            raw=raw,
        )

    facts = ledger.all_facts()
    assert [fact.key for fact in facts] == ["net_profit_2025", "revenue_2025"]
    assert all(fact.source_tool == "get_company_financials" for fact in facts)
    assert all(fact.source_call_id == call.id for fact in facts)
    assert all(fact.raw == raw for fact in facts)
    assert all(fact.recorded_at == 100.0 for fact in facts)
    assert facts[0].unit == "CNY"
    assert facts[0].id.startswith("fact_")


def test_tool_call_captures_args_and_elapsed_seconds():
    from groundguard import Ledger, tool_call

    ticks = iter([10.0, 13.5])
    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)

    with tool_call(
        "lookup",
        args={"query": "answer"},
        ledger=ledger,
        clock=lambda: next(ticks),
    ) as call:
        assert call.id.startswith("call_")
        assert call.name == "lookup"
        assert call.args == {"query": "answer"}
        assert call.started_at == 10.0
        assert call.ended_at is None
        assert call.elapsed_seconds is None

    assert call.ended_at == 13.5
    assert call.elapsed_seconds == 3.5


def test_record_facts_accepts_value_without_unit():
    from groundguard import Ledger, tool_call

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)

    with tool_call("lookup", args={}, ledger=ledger, clock=lambda: 1.0) as call:
        call.record_facts({"company_name": "Example Corp"})

    [fact] = ledger.query("company_name")
    assert fact.value == "Example Corp"
    assert fact.value_kind == "text"
    assert fact.unit is None
    assert fact.source_call_id == call.id
