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
