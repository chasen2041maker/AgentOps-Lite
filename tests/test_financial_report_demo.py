def test_financial_report_demo_shows_before_after_reports():
    from examples.financial_report_demo.run import run_demo

    result = run_demo()

    assert result.before.passed is False
    assert result.before.omitted_required_count == 2
    assert [fact.key for fact in result.before.omitted_required_facts] == [
        "net_profit_2025",
        "revenue_2025",
    ]
    assert result.after.passed is True
    assert result.after.verified_count == 2
    assert result.after.omitted_required_count == 0


def test_financial_report_demo_prints_colored_gate_status(capsys, monkeypatch):
    from examples.financial_report_demo.run import _print_report, run_demo

    monkeypatch.delenv("NO_COLOR", raising=False)
    result = run_demo()

    _print_report("Before GroundGuard correction", result.before)
    _print_report("After fact-key correction", result.after)

    output = capsys.readouterr().out
    assert "passed: \033[91m\033[1mFalse\033[0m" in output
    assert "passed: \033[92m\033[1mTrue\033[0m" in output
