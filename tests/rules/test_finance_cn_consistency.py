from __future__ import annotations

from decimal import Decimal

from groundguard import FactGate


def _report(values: dict[str, str], checker: object):
    gate = FactGate(session_id="finance_consistency", clock=lambda: 100.0)
    for key, value in values.items():
        gate.record_tool_result(key, Decimal(value), "CNY")
    return gate.check("No numeric answer claims.", checkers=(checker,))


def test_price_direction_detects_conflict_but_not_equal_price_boundary() -> None:
    from groundguard.rules.finance_cn import PriceDirectionChecker

    conflict = _report(
        {"price": "11.00", "previous_close": "10.00", "change_pct": "-1.00"},
        PriceDirectionChecker(),
    )
    boundary = _report(
        {"price": "10.00", "previous_close": "10.00", "change_pct": "0"},
        PriceDirectionChecker(),
    )

    assert conflict.passed is False
    assert [issue.code for issue in conflict.issues] == ["price_direction_conflict"]
    assert boundary.issues == ()


def test_price_direction_detects_zero_value_direction_conflicts() -> None:
    from groundguard.rules.finance_cn import PriceDirectionChecker

    unchanged_but_negative = _report(
        {"price": "10.00", "previous_close": "10.00", "change_pct": "-1.00"},
        PriceDirectionChecker(),
    )
    increased_but_zero = _report(
        {"price": "11.00", "previous_close": "10.00", "change_pct": "0"},
        PriceDirectionChecker(),
    )

    assert [issue.code for issue in unchanged_but_negative.issues] == ["price_direction_conflict"]
    assert [issue.code for issue in increased_but_zero.issues] == ["price_direction_conflict"]


def test_price_direction_never_combines_facts_from_different_subjects() -> None:
    from groundguard.rules.finance_cn import PriceDirectionChecker

    gate = FactGate(session_id="subject_isolation", clock=lambda: 100.0)
    gate.record_tool_result("price", Decimal("11.00"), "CNY", subject="stock_a")
    gate.record_tool_result("change_pct", Decimal("-1.00"), "%", subject="stock_a")
    gate.record_tool_result("previous_close", Decimal("10.00"), "CNY", subject="stock_b")

    report = gate.check("Synthetic answer.", checkers=(PriceDirectionChecker(),))

    assert report.issues == ()


def test_latest_numeric_fact_requires_one_subject_or_an_explicit_selection() -> None:
    from groundguard.rules.finance_cn.aliases import latest_numeric_fact

    gate = FactGate(session_id="subject_selection", clock=lambda: 100.0)
    stock_a = gate.record_tool_result("price", Decimal("11.00"), "CNY", subject="stock_a")
    gate.record_tool_result("price", Decimal("12.00"), "CNY", subject="stock_b")

    assert latest_numeric_fact(gate.ledger.all_facts(), "price") is None
    assert latest_numeric_fact(gate.ledger.all_facts(), "price", subject="stock_a") == (
        stock_a,
        Decimal("11.00"),
    )


def test_amplitude_requires_all_values_and_uses_decimal_formula() -> None:
    from groundguard.rules.finance_cn import AmplitudeChecker

    valid = _report(
        {"high": "11", "low": "9", "previous_close": "10", "amplitude": "20"},
        AmplitudeChecker(),
    )
    conflict = _report(
        {"high": "11", "low": "9", "previous_close": "10", "amplitude": "10"},
        AmplitudeChecker(),
    )
    missing = _report(
        {"high": "11", "low": "9", "amplitude": "20"},
        AmplitudeChecker(),
    )

    assert valid.issues == ()
    assert [issue.code for issue in conflict.issues] == ["amplitude_conflict"]
    assert missing.issues == ()


def test_turnover_requires_float_shares_and_does_not_substitute_total_shares() -> None:
    from groundguard.rules.finance_cn import TurnoverRateChecker

    valid = _report(
        {"volume": "100", "float_shares": "1000", "turnover_rate": "10"},
        TurnoverRateChecker(),
    )
    conflict = _report(
        {"volume": "100", "float_shares": "1000", "turnover_rate": "20"},
        TurnoverRateChecker(),
    )
    missing_float = _report(
        {"volume": "100", "total_shares": "1000", "turnover_rate": "10"},
        TurnoverRateChecker(),
    )

    assert valid.issues == ()
    assert [issue.code for issue in conflict.issues] == ["turnover_rate_conflict"]
    assert missing_float.issues == ()


def test_financial_sign_requires_explicit_caller_sign_semantics() -> None:
    from groundguard.rules.finance_cn import FinancialSignChecker

    gate = FactGate(session_id="finance_sign", clock=lambda: 100.0)
    gate.record_fact(
        key="net_profit",
        value=Decimal("-10"),
        unit="CNY",
        fact_type="profit",
    )
    gate.record_fact(
        key="net_loss",
        value=Decimal("-10"),
        unit="CNY",
        fact_type="loss",
    )
    gate.record_fact(
        key="unclassified_metric",
        value=Decimal("-10"),
        unit="CNY",
    )

    default_report = gate.check("No numeric answer claims.", checkers=(FinancialSignChecker(),))
    explicit_report = gate.check(
        "No numeric answer claims.",
        checkers=(FinancialSignChecker(expected_signs={"net_profit": "non_negative"}),),
    )

    assert default_report.issues == ()
    assert [issue.code for issue in explicit_report.issues] == ["financial_sign_conflict"]
    assert explicit_report.issues[0].related_fact_keys == ("net_profit",)
