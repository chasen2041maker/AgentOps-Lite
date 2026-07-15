"""Pure Decimal consistency checks for explicitly recorded finance facts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Literal

from groundguard.core.checker import CheckRequest
from groundguard.core.models import Issue
from groundguard.rules.finance_cn.aliases import coherent_numeric_facts, numeric_value
from groundguard.rules.finance_cn.context import FinanceCNContext


class PriceDirectionChecker:
    """Detect inconsistent price and percentage-change directions."""

    name = "price_direction"

    def __init__(
        self,
        *,
        price_tolerance: Decimal = Decimal("0.0001"),
        percent_tolerance: Decimal = Decimal("0.0001"),
    ) -> None:
        self._price_tolerance = price_tolerance
        self._percent_tolerance = percent_tolerance

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        context = FinanceCNContext.from_mapping(request.context)
        values = coherent_numeric_facts(
            request.facts,
            ("price", "previous_close", "change_pct"),
            subject=context.subject,
        )
        if values is None:
            return ()
        price = values["price"]
        previous_close = values["previous_close"]
        change_pct = values["change_pct"]
        price_direction = _direction(price[1] - previous_close[1], self._price_tolerance)
        percentage_direction = _direction(change_pct[1], self._percent_tolerance)
        if price_direction == percentage_direction:
            return ()
        return (
            Issue(
                code="price_direction_conflict",
                severity="hard",
                message="Price direction conflicts with the recorded percentage change.",
                checker=self.name,
                related_fact_keys=(price[0].key, previous_close[0].key, change_pct[0].key),
                details={
                    "price": str(price[1]),
                    "previous_close": str(previous_close[1]),
                    "change_pct": str(change_pct[1]),
                    "price_direction": price_direction,
                    "percentage_direction": percentage_direction,
                },
            ),
        )


class AmplitudeChecker:
    """Validate amplitude = (high - low) / previous_close * 100."""

    name = "amplitude"

    def __init__(self, *, tolerance: Decimal = Decimal("0.01")) -> None:
        self._tolerance = tolerance

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        context = FinanceCNContext.from_mapping(request.context)
        values = coherent_numeric_facts(
            request.facts,
            ("high", "low", "previous_close", "amplitude"),
            subject=context.subject,
        )
        if values is None:
            return ()
        high = values["high"]
        low = values["low"]
        previous_close = values["previous_close"]
        amplitude = values["amplitude"]
        if previous_close[1] == 0:
            return ()
        expected = (high[1] - low[1]) / previous_close[1] * Decimal("100")
        if abs(expected - amplitude[1]) <= self._tolerance:
            return ()
        return (
            Issue(
                code="amplitude_conflict",
                severity="hard",
                message="Recorded amplitude conflicts with high, low, and previous close.",
                checker=self.name,
                related_fact_keys=(high[0].key, low[0].key, previous_close[0].key, amplitude[0].key),
                details={"expected_amplitude": str(expected), "actual_amplitude": str(amplitude[1])},
            ),
        )


class TurnoverRateChecker:
    """Validate turnover_rate = volume / float_shares * 100 when explicit."""

    name = "turnover_rate"

    def __init__(self, *, tolerance: Decimal = Decimal("0.01")) -> None:
        self._tolerance = tolerance

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        context = FinanceCNContext.from_mapping(request.context)
        values = coherent_numeric_facts(
            request.facts,
            ("volume", "float_shares", "turnover_rate"),
            subject=context.subject,
        )
        if values is None:
            return ()
        volume = values["volume"]
        float_shares = values["float_shares"]
        turnover_rate = values["turnover_rate"]
        if float_shares[1] <= 0:
            return ()
        expected = volume[1] / float_shares[1] * Decimal("100")
        if abs(expected - turnover_rate[1]) <= self._tolerance:
            return ()
        return (
            Issue(
                code="turnover_rate_conflict",
                severity="hard",
                message="Recorded turnover rate conflicts with volume and float shares.",
                checker=self.name,
                related_fact_keys=(volume[0].key, float_shares[0].key, turnover_rate[0].key),
                details={"expected_turnover_rate": str(expected), "actual_turnover_rate": str(turnover_rate[1])},
            ),
        )


class FinancialSignChecker:
    """Validate financial signs only when callers supply their semantics."""

    name = "financial_sign"

    def __init__(
        self,
        *,
        expected_signs: Mapping[str, Literal["non_negative", "non_positive"]] | None = None,
        tolerance: Decimal = Decimal("0"),
    ) -> None:
        self._expected_signs = {
            key.casefold(): sign for key, sign in (expected_signs or {}).items()
        }
        invalid_signs = set(self._expected_signs.values()).difference({"non_negative", "non_positive"})
        if invalid_signs:
            raise ValueError("expected_signs values must be 'non_negative' or 'non_positive'")
        self._tolerance = tolerance

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        issues: list[Issue] = []
        for fact in request.facts:
            expected_sign = self._expected_signs.get(fact.key.casefold())
            value = numeric_value(fact)
            if expected_sign is None or value is None:
                continue
            conflicts = (expected_sign == "non_negative" and value < -self._tolerance) or (
                expected_sign == "non_positive" and value > self._tolerance
            )
            if not conflicts:
                continue
            issues.append(
                Issue(
                    code="financial_sign_conflict",
                    severity="hard",
                    message="Recorded financial value conflicts with caller-provided sign semantics.",
                    checker=self.name,
                    related_fact_keys=(fact.key,),
                    details={"expected_sign": expected_sign, "value": str(value)},
                )
            )
        return tuple(issues)


def _direction(value: Decimal, tolerance: Decimal) -> int:
    if value > tolerance:
        return 1
    if value < -tolerance:
        return -1
    return 0
