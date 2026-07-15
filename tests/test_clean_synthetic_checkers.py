from __future__ import annotations

from decimal import Decimal

import pytest

from groundguard import FactGate
from groundguard.checkers import OrphanNumberChecker, RelativeFreshnessChecker
from groundguard.rules.finance_cn import (
    AmplitudeChecker,
    FinancialSignChecker,
    PriceDirectionChecker,
    PriceLimitChecker,
    TurnoverRateChecker,
)


_MARKETS = (
    ("SSE", "main"),
    ("SSE", "star"),
    ("SZSE", "main"),
    ("SZSE", "chinext"),
)
_CHANGES = (Decimal("-5"), Decimal("0"), Decimal("5"), Decimal("-2"), Decimal("2"))
CLEAN_CASES = tuple(
    {
        "name": f"clean-{index:02d}",
        "exchange": _MARKETS[index % len(_MARKETS)][0],
        "board": _MARKETS[index % len(_MARKETS)][1],
        "previous_close": Decimal("10") + Decimal(index),
        "change_pct": _CHANGES[index % len(_CHANGES)],
        "subject": f"synthetic-{index:02d}",
    }
    for index in range(50)
)


@pytest.mark.parametrize("case", CLEAN_CASES, ids=lambda case: case["name"])
def test_clean_synthetic_checker_baseline_has_no_issues(case: dict[str, object]) -> None:
    previous_close = case["previous_close"]
    change_pct = case["change_pct"]
    subject = case["subject"]
    assert isinstance(previous_close, Decimal)
    assert isinstance(change_pct, Decimal)
    assert isinstance(subject, str)

    price = previous_close * (Decimal("1") + change_pct / Decimal("100"))
    high = price + Decimal("1")
    low = price - Decimal("1")
    amplitude = (high - low) / previous_close * Decimal("100")
    volume = Decimal("1000")
    float_shares = Decimal("100000")
    turnover_rate = volume / float_shares * Decimal("100")

    gate = FactGate(session_id=case["name"], clock=lambda: 100.0)
    for key, value, unit in (
        ("price", price, "CNY"),
        ("previous_close", previous_close, "CNY"),
        ("change_pct", change_pct, "%"),
        ("high", high, "CNY"),
        ("low", low, "CNY"),
        ("amplitude", amplitude, "%"),
        ("volume", volume, "shares"),
        ("float_shares", float_shares, "shares"),
        ("turnover_rate", turnover_rate, "%"),
        ("net_profit", Decimal("0"), "CNY"),
    ):
        gate.record_tool_result(key, value, unit, subject=subject, as_of="2026-07-15")

    report = gate.check(
        "Synthetic clean finance case.",
        checkers=(
            OrphanNumberChecker(),
            RelativeFreshnessChecker(
                fact_groups={"price": "quote", "previous_close": "quote"}
            ),
            PriceDirectionChecker(),
            PriceLimitChecker(),
            AmplitudeChecker(),
            TurnoverRateChecker(),
            FinancialSignChecker(expected_signs={"net_profit": "non_negative"}),
        ),
        context={
            "finance_cn": {
                "exchange": case["exchange"],
                "board": case["board"],
                "listing_phase": "normal",
                "trade_date": "2026-07-15",
                "subject": subject,
            }
        },
    )

    assert report.issues == ()
