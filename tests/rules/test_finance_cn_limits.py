from __future__ import annotations

from decimal import Decimal

import pytest

from groundguard import FactGate


def _context(exchange: str, board: str, phase: str = "normal", **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "exchange": exchange,
        "board": board,
        "listing_phase": phase,
        "trade_date": "2026-07-15",
    }
    payload.update(extra)
    return {"finance_cn": payload}


def _limit_report(
    *,
    exchange: str,
    board: str,
    price: str,
    previous_close: str | None = "10.00",
    phase: str = "normal",
    **extra: object,
):
    from groundguard.rules.finance_cn import PriceLimitChecker

    gate = FactGate(session_id="finance_limit", clock=lambda: 100.0)
    gate.record_tool_result("price", Decimal(price), "CNY")
    if previous_close is not None:
        gate.record_tool_result("previous_close", Decimal(previous_close), "CNY")
    return gate.check(
        "No numeric answer claims.",
        checkers=(PriceLimitChecker(),),
        context=_context(exchange, board, phase, **extra),
    )


@pytest.mark.parametrize(
    ("exchange", "board", "at_limit", "beyond_limit"),
    [
        ("SSE", "main", "11.00", "11.01"),
        ("SSE", "star", "12.00", "12.01"),
        ("SZSE", "main", "11.00", "11.01"),
        ("SZSE", "chinext", "12.00", "12.01"),
    ],
)
def test_price_limit_uses_explicit_exchange_board_rule_table(
    exchange: str,
    board: str,
    at_limit: str,
    beyond_limit: str,
) -> None:
    allowed = _limit_report(
        exchange=exchange,
        board=board,
        price=at_limit,
    )
    rejected = _limit_report(
        exchange=exchange,
        board=board,
        price=beyond_limit,
    )

    assert allowed.issues == ()
    assert rejected.passed is False
    assert [issue.code for issue in rejected.issues] == ["price_limit_conflict"]


@pytest.mark.parametrize(
    "phase",
    ("ipo_first_five_days", "relisting_first_day", "delisting_first_day"),
)
def test_price_limit_skips_normal_limit_for_special_listing_phases(phase: str) -> None:
    report = _limit_report(
        exchange="SSE",
        board="main",
        price="20.00",
        phase=phase,
    )

    assert report.passed is True
    assert report.issues == ()


def test_price_limit_rounds_boundary_to_a_share_minimum_price_tick() -> None:
    allowed = _limit_report(
        exchange="SZSE",
        board="main",
        price="11.06",
        previous_close="10.05",
    )
    rejected = _limit_report(
        exchange="SZSE",
        board="main",
        price="11.07",
        previous_close="10.05",
    )

    assert allowed.issues == ()
    assert [issue.code for issue in rejected.issues] == ["price_limit_conflict"]


def test_price_limit_missing_context_skips_without_hard_issue() -> None:
    report = _limit_report(
        exchange="SSE",
        board="main",
        price="11.50",
        previous_close=None,
    )

    assert report.passed is True
    assert [issue.code for issue in report.issues] == ["insufficient_rule_context"]
    assert report.issues[0].severity == "soft"


def test_price_limit_marks_bse_as_unsupported_without_applying_twenty_percent() -> None:
    report = _limit_report(exchange="BSE", board="main", price="13.00")

    assert report.passed is True
    assert [issue.code for issue in report.issues] == ["unsupported_market"]
    assert report.issues[0].severity == "soft"


def test_explicit_listing_phase_wins_over_name_prefix_signal() -> None:
    report = _limit_report(
        exchange="SZSE",
        board="main",
        price="11.50",
        security_name="N Synthetic Co.",
    )

    assert report.passed is False
    assert [issue.code for issue in report.issues] == [
        "insufficient_rule_context",
        "price_limit_conflict",
    ]
