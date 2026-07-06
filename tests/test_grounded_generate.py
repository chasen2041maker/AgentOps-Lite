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


def test_grounded_generate_can_return_answer_with_report():
    from groundguard import Fact, GroundedResult, Ledger, Policy, grounded_generate

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

    result = grounded_generate(
        prompt="总结财务表现",
        llm_call=lambda prompt: "净利润为 823.2 亿元 [fact:net_profit_2025]。",
        ledger=ledger,
        required_fact_keys=["net_profit_2025"],
        policy=Policy(),
        return_report=True,
    )

    assert isinstance(result, GroundedResult)
    assert result.answer == "净利润为 823.2 亿元 [fact:net_profit_2025]。"
    assert result.report.passed is True
    assert result.report.verified_count == 1


def test_grounded_generate_blocks_required_fact_omissions_by_default():
    from groundguard import Fact, GroundingPolicyError, Ledger, Policy, grounded_generate

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

    try:
        grounded_generate(
            prompt="总结财务表现",
            llm_call=lambda prompt: "本轮未取得可核实的净利润数据。",
            ledger=ledger,
            required_fact_keys=["net_profit_2025"],
            policy=Policy(),
        )
    except GroundingPolicyError as exc:
        assert exc.answer == "本轮未取得可核实的净利润数据。"
        assert exc.report.omitted_required_count == 1
        assert "omitted_required_count=1" in str(exc)
    else:
        raise AssertionError("expected GroundingPolicyError")


def test_grounded_generate_blocks_any_failed_policy_report():
    from groundguard import GroundingPolicyError, Ledger, Policy, grounded_generate

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)

    try:
        grounded_generate(
            prompt="总结财务表现",
            llm_call=lambda prompt: "现金储备为 120 亿元。",
            ledger=ledger,
            policy=Policy(max_unverified_ratio=0.1, on_unverified="flag"),
        )
    except GroundingPolicyError as exc:
        assert exc.report.passed is False
        assert "unverified_ratio=1.000" in str(exc)
    else:
        raise AssertionError("expected GroundingPolicyError")


def test_grounded_generate_strips_unverified_claims_when_policy_requests_strip():
    from groundguard import Fact, GroundedResult, Ledger, Policy, grounded_generate

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

    result = grounded_generate(
        prompt="总结财务表现",
        llm_call=lambda prompt: (
            "净利润为 823.2 亿元 [fact:net_profit_2025]，现金储备为 120 亿元。"
        ),
        ledger=ledger,
        required_fact_keys=["net_profit_2025"],
        policy=Policy(on_unverified="strip"),
        return_report=True,
    )

    assert isinstance(result, GroundedResult)
    assert "120 亿元" not in result.answer
    assert "823.2 亿元 [fact:net_profit_2025]" in result.answer
    assert result.report.unverified_count == 0
    assert result.report.passed is True


def test_grounded_generate_strips_english_unverified_sentence_cleanly():
    from groundguard import Fact, GroundedResult, Ledger, Policy, grounded_generate

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)
    ledger.register_fact(
        Fact(
            id="fact_net_profit_2025",
            source_tool="tool",
            source_call_id="call_1",
            key="net_profit_2025",
            value=Decimal("823200000"),
            unit="USD",
        )
    )

    result = grounded_generate(
        prompt="Summarize performance",
        llm_call=lambda prompt: (
            "Cash reserves were $120 million. "
            "Net profit was $823.2 million [fact:net_profit_2025]."
        ),
        ledger=ledger,
        required_fact_keys=["net_profit_2025"],
        policy=Policy(on_unverified="strip"),
        return_report=True,
    )

    assert isinstance(result, GroundedResult)
    assert "$120 million" not in result.answer
    assert result.answer == "Net profit was $823.2 million [fact:net_profit_2025]."
    assert result.report.unverified_count == 0
    assert result.report.passed is True


def test_strip_unverified_claims_uses_span_offsets_for_repeated_text():
    from groundguard import CoverageReport, OutputClaim
    from groundguard.generate.grounded_generate import _strip_unverified_claims

    answer = "Cash was $120 million. Cash was $120 million."
    second_start = answer.rfind("$120 million")
    second_end = second_start + len("$120 million")
    report = CoverageReport(
        session_id="req_001",
        output_claims=[
            OutputClaim(
                id="claim_1",
                text_span="Cash was $120 million",
                claim_type="numeric",
                normalized_value=Decimal("120000000"),
                unit="USD",
                status="unverified",
                start=second_start,
                end=second_end,
            )
        ],
    )

    assert _strip_unverified_claims(answer, report) == "Cash was $120 million."


def test_grounded_decorator_returns_report_for_framework_free_functions():
    from groundguard import Fact, GroundedResult, Ledger, Policy, grounded

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)
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

    @grounded(
        ledger=ledger,
        required_fact_keys=["revenue_2025"],
        policy=Policy(),
        return_report=True,
    )
    def summarize() -> str:
        return "收入为 3830 亿元 [fact:revenue_2025]。"

    result = summarize()

    assert isinstance(result, GroundedResult)
    assert result.answer == "收入为 3830 亿元 [fact:revenue_2025]。"
    assert result.report.passed is True
    assert result.report.verified_count == 1


def test_grounded_decorator_blocks_failed_reports():
    from groundguard import Fact, GroundingPolicyError, Ledger, Policy, grounded

    ledger = Ledger(session_id="req_001", clock=lambda: 100.0)
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

    @grounded(
        ledger=ledger,
        required_fact_keys=["revenue_2025"],
        policy=Policy(),
    )
    def summarize() -> str:
        return "No revenue data was available."

    try:
        summarize()
    except GroundingPolicyError as exc:
        assert exc.report.passed is False
        assert exc.report.omitted_required_count == 1
    else:
        raise AssertionError("expected GroundingPolicyError")
