from decimal import Decimal


def test_grounded_generate_can_fix_tagged_contradictions_from_display_value():
    from groundguard import Fact, GroundedResult, Ledger, Policy, grounded_generate

    ledger = Ledger(session_id="req_001")
    ledger.register_fact(
        Fact(
            id="fact_revenue_2025",
            source_tool="tool",
            source_call_id="call_1",
            key="revenue_2025",
            value=Decimal("3830000000"),
            unit="USD",
            display_value="$3.83 billion [fact:revenue_2025]",
        )
    )

    result = grounded_generate(
        prompt="Summarize revenue",
        llm_call=lambda prompt: "Revenue was $3.80 billion [fact:revenue_2025].",
        ledger=ledger,
        required_fact_keys=["revenue_2025"],
        policy=Policy(on_contradicted="fix"),
        return_report=True,
    )

    assert isinstance(result, GroundedResult)
    assert result.answer == "Revenue was $3.83 billion [fact:revenue_2025]."
    assert result.report.passed is True
    assert result.report.verified_count == 1


def test_grounded_generate_reasks_once_with_policy_feedback():
    from groundguard import Fact, GroundedResult, Ledger, Policy, grounded_generate

    ledger = Ledger(session_id="req_001")
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
    prompts: list[str] = []
    answers = iter(
        [
            "Revenue was $3.80 billion [fact:revenue_2025].",
            "Revenue was $3.83 billion [fact:revenue_2025].",
        ]
    )

    def fake_llm(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    result = grounded_generate(
        prompt="Summarize revenue",
        llm_call=fake_llm,
        ledger=ledger,
        required_fact_keys=["revenue_2025"],
        policy=Policy(on_contradicted="reask"),
        return_report=True,
    )

    assert isinstance(result, GroundedResult)
    assert len(prompts) == 2
    assert "GroundGuard blocked the previous answer" in prompts[1]
    assert "contradicted_count=1" in prompts[1]
    assert result.answer == "Revenue was $3.83 billion [fact:revenue_2025]."
    assert result.report.passed is True

