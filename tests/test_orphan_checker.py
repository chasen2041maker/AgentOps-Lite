from __future__ import annotations

from decimal import Decimal

import pytest

from groundguard import CheckRequest, FactGate, SuspectedNumber


def test_orphan_checker_does_not_flag_covered_price_or_percentage() -> None:
    from groundguard.checkers import OrphanNumberChecker

    gate = FactGate(session_id="orphan_covered", clock=lambda: 100.0)
    gate.record_tool_result("price", Decimal("12.50"), "CNY")
    gate.record_tool_result("change", Decimal("3.2"), "%")

    report = gate.check(
        "The price is CNY 12.50 [fact:price], up 3.2% [fact:change].",
        checkers=(OrphanNumberChecker(),),
    )

    assert report.issues == ()


def test_orphan_checker_ignores_dates_years_times_codes_and_list_markers() -> None:
    from groundguard.checkers import OrphanNumberChecker

    report = FactGate(session_id="orphan_non_business", clock=lambda: 100.0).check(
        "1. On 2026-07-15 at 09:30, SSE 600519 was reviewed.",
        checkers=(OrphanNumberChecker(),),
    )

    assert report.issues == ()


@pytest.mark.parametrize(
    "stock_code",
    ("SH.600519", "SZ.000001", "SSE.600519", "SZSE.000001"),
)
def test_orphan_checker_ignores_dot_separated_stock_codes(stock_code: str) -> None:
    from groundguard.checkers import OrphanNumberChecker

    report = FactGate(session_id="orphan_dot_code", clock=lambda: 100.0).check(
        f"{stock_code} was reviewed.",
        checkers=(OrphanNumberChecker(),),
    )

    assert report.issues == ()


def test_orphan_checker_emits_soft_issue_for_uncovered_business_number() -> None:
    from groundguard.checkers import OrphanNumberChecker

    report = FactGate(session_id="orphan_uncovered", clock=lambda: 100.0).check(
        "Revenue reached 3830000000.",
        checkers=(OrphanNumberChecker(),),
    )

    assert report.passed is True
    assert report.soft_issue_count == 1
    issue = report.issues[0]
    assert issue.code == "orphan_number"
    assert issue.severity == "soft"
    assert issue.checker == "orphan_number"
    assert issue.text_span == "3830000000"


def test_orphan_checker_caps_issues_and_respects_explicit_ignore_predicate() -> None:
    from groundguard.checkers import OrphanNumberChecker

    request = CheckRequest(
        answer="Synthetic answer.",
        claims=(),
        facts=(),
        suspected_numbers=(),
        uncovered_numbers=(
            SuspectedNumber("USD 1 million", 0, 13),
            SuspectedNumber("USD 2 million", 20, 33),
            SuspectedNumber("USD 3 million", 40, 53),
        ),
    )
    checker = OrphanNumberChecker(
        max_issues=2,
        ignore_predicate=lambda number, _: number.text_span == "USD 2 million",
    )

    issues = checker.check(request)

    assert [issue.text_span for issue in issues] == ["USD 1 million", "USD 3 million"]


def test_orphan_checker_deduplicates_same_span_even_when_units_differ() -> None:
    from groundguard.checkers import OrphanNumberChecker

    request = CheckRequest(
        answer="Synthetic answer.",
        claims=(),
        facts=(),
        suspected_numbers=(),
        uncovered_numbers=(
            SuspectedNumber("10 USD", 4, 10),
            SuspectedNumber("10 CNY", 4, 10),
        ),
    )

    issues = OrphanNumberChecker().check(request)

    assert len(issues) == 1
    assert issues[0].text_span == "10 USD"


def test_orphan_checker_does_not_treat_cash_as_a_stock_prefix() -> None:
    from groundguard.checkers import OrphanNumberChecker

    report = FactGate(session_id="orphan_cash", clock=lambda: 100.0).check(
        "Cash was 123456.",
        checkers=(OrphanNumberChecker(),),
    )

    assert [issue.text_span for issue in report.issues] == ["123456"]


def test_orphan_checker_does_not_treat_sentence_period_as_list_marker() -> None:
    from groundguard.checkers import OrphanNumberChecker

    report = FactGate(session_id="orphan_sentence", clock=lambda: 100.0).check(
        "Revenue grew by 12.",
        checkers=(OrphanNumberChecker(),),
    )

    assert [issue.text_span for issue in report.issues] == ["12"]
