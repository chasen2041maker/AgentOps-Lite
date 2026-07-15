"""Pure Decimal consistency checks for explicitly recorded finance facts."""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from groundguard.core.checker import CheckRequest
from groundguard.core.models import Issue
from groundguard.rules.finance_cn.aliases import latest_numeric_fact, metric_kind, numeric_value


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
        price = latest_numeric_fact(request.facts, "price")
        previous_close = latest_numeric_fact(request.facts, "previous_close")
        change_pct = latest_numeric_fact(request.facts, "change_pct")
        if price is None or previous_close is None or change_pct is None:
            return ()
        if (
            price[1] > previous_close[1] + self._price_tolerance
            and change_pct[1] < -self._percent_tolerance
        ) or (
            price[1] < previous_close[1] - self._price_tolerance
            and change_pct[1] > self._percent_tolerance
        ):
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
                    },
                ),
            )
        return ()


class AmplitudeChecker:
    """Validate amplitude = (high - low) / previous_close * 100."""

    name = "amplitude"

    def __init__(self, *, tolerance: Decimal = Decimal("0.01")) -> None:
        self._tolerance = tolerance

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        high = latest_numeric_fact(request.facts, "high")
        low = latest_numeric_fact(request.facts, "low")
        previous_close = latest_numeric_fact(request.facts, "previous_close")
        amplitude = latest_numeric_fact(request.facts, "amplitude")
        if high is None or low is None or previous_close is None or amplitude is None:
            return ()
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
        volume = latest_numeric_fact(request.facts, "volume")
        float_shares = latest_numeric_fact(request.facts, "float_shares")
        turnover_rate = latest_numeric_fact(request.facts, "turnover_rate")
        if volume is None or float_shares is None or turnover_rate is None:
            return ()
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
    """Check signs only for explicitly classified public financial metrics."""

    name = "financial_sign"

    def __init__(self, *, tolerance: Decimal = Decimal("0")) -> None:
        self._tolerance = tolerance

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        issues: list[Issue] = []
        for fact in request.facts:
            kind = metric_kind(fact)
            value = numeric_value(fact)
            if kind is None or value is None:
                continue
            conflicts = (
                kind == "profit" and value < -self._tolerance
            ) or (kind == "loss" and value > self._tolerance)
            if not conflicts:
                continue
            issues.append(
                Issue(
                    code="financial_sign_conflict",
                    severity="hard",
                    message="Recorded financial value conflicts with its explicit metric kind.",
                    checker=self.name,
                    related_fact_keys=(fact.key,),
                    details={"metric_kind": kind, "value": str(value)},
                )
            )
        return tuple(issues)
