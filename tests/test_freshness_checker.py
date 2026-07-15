from __future__ import annotations

from decimal import Decimal

from groundguard import FactGate


def _quote_gate() -> FactGate:
    gate = FactGate(session_id="freshness", clock=lambda: 100.0)
    gate.record_fact(
        key="previous_quote",
        value=Decimal("10.00"),
        unit="CNY",
        source_tool="market_data",
        source_call_id="call_old",
        subject="SSE.600000",
        as_of="2026-07-14",
        fact_type="quote",
    )
    gate.record_fact(
        key="latest_quote",
        value=Decimal("10.50"),
        unit="CNY",
        source_tool="market_data",
        source_call_id="call_new",
        subject="SSE.600000",
        as_of="2026-07-15",
        fact_type="quote",
    )
    return gate


def _checker():
    from groundguard.checkers import RelativeFreshnessChecker

    return RelativeFreshnessChecker(
        fact_groups={"previous_quote": "quote", "latest_quote": "quote"}
    )


def test_relative_freshness_flags_referenced_older_fact_in_same_subject_and_group() -> None:
    report = _quote_gate().check(
        "The price was CNY 10.00 [fact:previous_quote].",
        checkers=(_checker(),),
    )

    assert report.passed is True
    assert report.soft_issue_count == 1
    issue = report.issues[0]
    assert issue.code == "relative_stale_fact"
    assert issue.related_fact_keys == ("previous_quote", "latest_quote")
    assert issue.details == {
        "subject": "SSE.600000",
        "fact_group": "quote",
        "referenced_as_of": "2026-07-14",
        "latest_as_of": "2026-07-15",
    }


def test_relative_freshness_does_not_flag_latest_referenced_fact() -> None:
    report = _quote_gate().check(
        "The price is CNY 10.50 [fact:latest_quote].",
        checkers=(_checker(),),
    )

    assert report.issues == ()


def test_relative_freshness_does_not_compare_other_subject_or_group() -> None:
    from groundguard.checkers import RelativeFreshnessChecker

    gate = _quote_gate()
    gate.record_fact(
        key="other_subject_quote",
        value=Decimal("20.00"),
        unit="CNY",
        source_tool="market_data",
        source_call_id="call_other_subject",
        subject="SZSE.000001",
        as_of="2026-07-20",
        fact_type="quote",
    )
    gate.record_fact(
        key="later_financial_period",
        value=Decimal("100"),
        unit="CNY",
        source_tool="financials",
        source_call_id="call_financial",
        subject="SSE.600000",
        as_of="2026-07-20",
        fact_type="financial",
    )
    checker = RelativeFreshnessChecker(
        fact_groups={
            "previous_quote": "quote",
            "latest_quote": "quote",
            "other_subject_quote": "quote",
            "later_financial_period": "financial_period",
        }
    )

    report = gate.check(
        "The price was CNY 10.00 [fact:previous_quote].",
        checkers=(checker,),
    )

    assert len(report.issues) == 1
    assert report.issues[0].related_fact_keys == ("previous_quote", "latest_quote")


def test_relative_freshness_skips_missing_or_invalid_dates_without_hard_failure() -> None:
    from groundguard.checkers import RelativeFreshnessChecker

    gate = FactGate(session_id="freshness_invalid", clock=lambda: 100.0)
    gate.record_fact(
        key="missing_date",
        value=Decimal("10.00"),
        unit="CNY",
        source_tool="market_data",
        source_call_id="call_missing",
        subject="SSE.600000",
        fact_type="quote",
    )
    gate.record_fact(
        key="invalid_date",
        value=Decimal("10.50"),
        unit="CNY",
        source_tool="market_data",
        source_call_id="call_invalid",
        subject="SSE.600000",
        as_of="not-a-date",
        fact_type="quote",
    )
    checker = RelativeFreshnessChecker(
        fact_groups={"missing_date": "quote", "invalid_date": "quote"}
    )

    report = gate.check(
        "The price was CNY 10.00 [fact:missing_date].",
        checkers=(checker,),
    )

    assert report.passed is True
    assert report.issues == ()
