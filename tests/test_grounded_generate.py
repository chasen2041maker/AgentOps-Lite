from decimal import Decimal


def test_ledger_coverage_report_extracts_matches_and_evaluates_policy():
    from groundguard import Fact, Ledger, Policy

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
    ledger.register_fact(
        Fact(
            id="fact_revenue_2025",
            source_tool="tool",
            source_call_id="call_1",
            key="revenue_2025",
            value=Decimal("383000000000"),
            unit="CNY",
        )
    )

    report = ledger.coverage_report(
        "净利润为 823.2 亿元 [fact:net_profit_2025]。",
        required_fact_keys=["net_profit_2025", "revenue_2025"],
        policy=Policy(),
    )

    assert report.verified_count == 1
    assert report.omitted_required_count == 1
    assert [fact.key for fact in report.omitted_required_facts] == ["revenue_2025"]
    assert report.passed is False
    assert "omitted_required_count=1" in report.policy_reason


def test_grounded_generate_calls_llm_and_returns_answer():
    from groundguard import Fact, Ledger, Policy, grounded_generate

    prompts: list[str] = []
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

    def fake_llm(prompt: str) -> str:
        prompts.append(prompt)
        return "净利润为 823.2 亿元 [fact:net_profit_2025]。"

    answer = grounded_generate(
        prompt="总结财务表现",
        llm_call=fake_llm,
        ledger=ledger,
        required_fact_keys=["net_profit_2025"],
        policy=Policy(),
    )

    assert answer == "净利润为 823.2 亿元 [fact:net_profit_2025]。"
    assert "总结财务表现" in prompts[0]
    assert "[fact:net_profit_2025]" in prompts[0]
    assert ledger.coverage_report(answer, required_fact_keys=["net_profit_2025"]).passed is True
