from decimal import Decimal


def test_openai_chat_llm_adapts_dict_responses():
    from groundguard.adapters import openai_chat_llm

    calls: list[dict[str, object]] = []

    def fake_create(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"message": {"content": "answer text"}}]}

    llm_call = openai_chat_llm(fake_create, model="test-model", temperature=0)

    assert llm_call("hello") == "answer text"
    assert calls == [
        {
            "model": "test-model",
            "temperature": 0,
            "messages": [{"role": "user", "content": "hello"}],
        }
    ]


def test_langchain_callback_registers_mapped_tool_facts():
    from groundguard import Ledger
    from groundguard.adapters import GroundGuardCallbackHandler

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)

    def fact_mapper(output, context):
        assert context.tool_name == "get_company_financials"
        assert context.tool_input == {"ticker": "ACME"}
        return {
            "net_profit_2025": (Decimal(output["net_profit"]), "CNY"),
        }

    handler = GroundGuardCallbackHandler(ledger=ledger, fact_mapper=fact_mapper)
    handler.on_tool_start(
        {"name": "get_company_financials"},
        {"ticker": "ACME"},
        run_id="run_1",
    )
    handler.on_tool_end({"net_profit": "82320000000"}, run_id="run_1")

    [fact] = ledger.query("net_profit_2025")
    assert fact.value == Decimal("82320000000")
    assert fact.unit == "CNY"
    assert fact.source_tool == "get_company_financials"
    assert fact.source_call_id.startswith("call_")
    assert fact.raw == {"net_profit": "82320000000"}
