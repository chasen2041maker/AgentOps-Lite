"""Detect uncovered numeric spans without reimplementing claim extraction."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from groundguard.core.checker import CheckRequest
from groundguard.core.models import Issue, SuspectedNumber


IgnorePredicate = Callable[[SuspectedNumber, CheckRequest], bool]


class OrphanNumberChecker:
    """Emit soft findings for business-like numbers uncovered by GroundGuard."""

    name = "orphan_number"

    def __init__(
        self,
        *,
        max_issues: int = 20,
        ignore_predicate: IgnorePredicate | None = None,
    ) -> None:
        if max_issues < 1:
            raise ValueError("max_issues must be at least 1")
        self._max_issues = max_issues
        self._ignore_predicate = ignore_predicate

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        issues: list[Issue] = []
        seen_spans: set[tuple[int, int]] = set()
        for number in request.uncovered_numbers:
            span = (number.start, number.end)
            if span in seen_spans:
                continue
            if self._should_ignore(number, request):
                continue
            seen_spans.add(span)
            issues.append(
                Issue(
                    code="orphan_number",
                    severity="soft",
                    message="Uncovered business number found.",
                    checker=self.name,
                    text_span=number.text_span,
                    start=number.start,
                    end=number.end,
                    details={"extraction_reason": number.reason},
                )
            )
            if len(issues) >= self._max_issues:
                break
        return tuple(issues)

    def _should_ignore(self, number: SuspectedNumber, request: CheckRequest) -> bool:
        if number.reason not in {"", "not_extracted"}:
            return True
        if self._ignore_predicate is not None and self._ignore_predicate(number, request):
            return True
        if _is_year(number.text_span) or _is_stock_code(number, request.answer):
            return True
        if _is_list_marker(number, request.answer):
            return True
        if _is_date_or_time_component(number, request.answer):
            return True
        return _is_percentage(number.text_span)


def _is_year(text_span: str) -> bool:
    return len(text_span) == 4 and text_span.isdigit() and 1900 <= int(text_span) <= 2099


def _is_stock_code(number: SuspectedNumber, answer: str) -> bool:
    if not (number.text_span.isdigit() and len(number.text_span) == 6):
        return False
    prefix = answer[max(0, number.start - 8) : number.start].upper()
    return any(marker in prefix for marker in ("SSE", "SZSE", "SH", "SZ", "STOCK"))


def _is_list_marker(number: SuspectedNumber, answer: str) -> bool:
    if not number.text_span.isdigit() or len(number.text_span) > 2:
        return False
    suffix = answer[number.end : number.end + 1]
    return suffix in {".", ")", "、"}


def _is_date_or_time_component(number: SuspectedNumber, answer: str) -> bool:
    numeric_text = number.text_span.lstrip("+-")
    if not numeric_text.isdigit():
        return False
    window = answer[max(0, number.start - 5) : min(len(answer), number.end + 5)]
    return ":" in window or window.count("/") >= 2 or window.count("-") >= 2


def _is_percentage(text_span: str) -> bool:
    normalized = text_span.casefold()
    return "%" in normalized or "percent" in normalized or "百分点" in text_span or "基点" in text_span
