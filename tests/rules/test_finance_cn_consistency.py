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
        {"price": "10.00", "previous_close": "10.00", "change_pct": "-1.00"},
        PriceDirectionChecker(),
    )

    assert conflict.passed is False
    assert [issue.code for issue in conflict.issues] == ["price_direction_conflict"]
    assert boundary.issues == ()


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


def test_financial_sign_only_checks_explicit_metric_kind_or_public_alias() -> None:
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

    report = gate.check("No numeric answer claims.", checkers=(FinancialSignChecker(),))

    assert report.passed is False
    assert [issue.code for issue in report.issues] == ["financial_sign_conflict"]
    assert report.issues[0].related_fact_keys == ("net_profit",)
