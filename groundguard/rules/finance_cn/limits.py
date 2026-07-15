"""Price-limit checks backed by an explicit, dated SH/SZ rule table."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence

from groundguard.core.checker import CheckRequest
from groundguard.core.models import Issue
from groundguard.rules.finance_cn.aliases import coherent_numeric_facts
from groundguard.rules.finance_cn.context import FinanceCNContext


SSE_RULE_SOURCE = "https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml"
SZSE_RULE_SOURCE = "https://docs.static.szse.cn/www/lawrules/rule/trade/W020260424690713155663.pdf"
RULE_EFFECTIVE_FROM = date(2026, 7, 6)
_A_SHARE_PRICE_TICK = Decimal("0.01")


@dataclass(frozen=True)
class PriceLimitRule:
    exchange: str
    board: str
    listing_phase: str
    effective_from: date
    limit_ratio: Decimal | None
    price_tick: Decimal
    source_url: str


# The July 2026 exchange rules set 10% for SH/SZ main boards and 20% for
# SSE STAR and SZSE ChiNext during normal trading. The exchanges round the
# calculated A-share limit to the 0.01 CNY minimum price tick using half-up.
# Explicit special phases have no normal percentage limit in this checker.
PRICE_LIMIT_RULES: tuple[PriceLimitRule, ...] = (
    PriceLimitRule("SSE", "main", "normal", RULE_EFFECTIVE_FROM, Decimal("0.10"), _A_SHARE_PRICE_TICK, SSE_RULE_SOURCE),
    PriceLimitRule("SSE", "star", "normal", RULE_EFFECTIVE_FROM, Decimal("0.20"), _A_SHARE_PRICE_TICK, SSE_RULE_SOURCE),
    PriceLimitRule("SZSE", "main", "normal", RULE_EFFECTIVE_FROM, Decimal("0.10"), _A_SHARE_PRICE_TICK, SZSE_RULE_SOURCE),
    PriceLimitRule("SZSE", "chinext", "normal", RULE_EFFECTIVE_FROM, Decimal("0.20"), _A_SHARE_PRICE_TICK, SZSE_RULE_SOURCE),
    PriceLimitRule("SSE", "main", "ipo_first_five_days", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SSE_RULE_SOURCE),
    PriceLimitRule("SSE", "star", "ipo_first_five_days", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SSE_RULE_SOURCE),
    PriceLimitRule("SZSE", "main", "ipo_first_five_days", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SZSE_RULE_SOURCE),
    PriceLimitRule("SZSE", "chinext", "ipo_first_five_days", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SZSE_RULE_SOURCE),
    PriceLimitRule("SSE", "main", "relisting_first_day", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SSE_RULE_SOURCE),
    PriceLimitRule("SSE", "star", "relisting_first_day", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SSE_RULE_SOURCE),
    PriceLimitRule("SZSE", "main", "relisting_first_day", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SZSE_RULE_SOURCE),
    PriceLimitRule("SZSE", "chinext", "relisting_first_day", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SZSE_RULE_SOURCE),
    PriceLimitRule("SSE", "main", "delisting_first_day", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SSE_RULE_SOURCE),
    PriceLimitRule("SSE", "star", "delisting_first_day", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SSE_RULE_SOURCE),
    PriceLimitRule("SZSE", "main", "delisting_first_day", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SZSE_RULE_SOURCE),
    PriceLimitRule("SZSE", "chinext", "delisting_first_day", RULE_EFFECTIVE_FROM, None, _A_SHARE_PRICE_TICK, SZSE_RULE_SOURCE),
)

_SUPPORTED_EXCHANGES = frozenset({"SSE", "SZSE"})


class PriceLimitChecker:
    """Check one subject's price against its explicit dated rule."""

    name = "price_limit"

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        context = FinanceCNContext.from_mapping(request.context)
        if context.exchange and context.exchange not in _SUPPORTED_EXCHANGES:
            return (_unsupported_market_issue(context.exchange),)

        prefix_issue = _prefix_conflict_issue(context)
        rule = _select_rule(context)
        if rule is None:
            issue = _insufficient_context_issue(("effective_price_limit_rule",))
            return (prefix_issue, issue) if prefix_issue is not None else (issue,)
        if rule.limit_ratio is None:
            return (prefix_issue,) if prefix_issue is not None else ()

        fields = ("price",) if context.previous_close is not None else ("price", "previous_close")
        values = coherent_numeric_facts(request.facts, fields, subject=context.subject)
        price = values.get("price") if values is not None else None
        previous_close_fact = values.get("previous_close") if values is not None else None
        previous_close = context.previous_close
        if previous_close is None and previous_close_fact is not None:
            previous_close = previous_close_fact[1]
        missing = _missing_context_fields(context, price, previous_close)
        if missing:
            issue = _insufficient_context_issue(missing)
            return (prefix_issue, issue) if prefix_issue is not None else (issue,)

        assert price is not None
        assert previous_close is not None
        price_fact, price_value = price
        upper_limit = _rounded_limit(previous_close, rule.limit_ratio, Decimal("1"), rule.price_tick)
        lower_limit = _rounded_limit(previous_close, rule.limit_ratio, Decimal("-1"), rule.price_tick)
        if lower_limit <= price_value <= upper_limit:
            return (prefix_issue,) if prefix_issue is not None else ()
        issue = Issue(
            code="price_limit_conflict",
            severity="hard",
            message="Price falls outside the configured price-limit range.",
            checker=self.name,
            related_fact_keys=(price_fact.key,)
            + ((previous_close_fact[0].key,) if previous_close_fact is not None else ()),
            details={
                "exchange": rule.exchange,
                "board": rule.board,
                "listing_phase": rule.listing_phase,
                "trade_date": context.trade_date.isoformat(),
                "previous_close": str(previous_close),
                "price": str(price_value),
                "lower_limit": str(lower_limit),
                "upper_limit": str(upper_limit),
                "limit_ratio": str(rule.limit_ratio),
                "price_tick": str(rule.price_tick),
                "source_url": rule.source_url,
            },
        )
        return (prefix_issue, issue) if prefix_issue is not None else (issue,)


def _rounded_limit(
    previous_close: Decimal,
    limit_ratio: Decimal,
    direction: Decimal,
    price_tick: Decimal,
) -> Decimal:
    calculated = previous_close * (Decimal("1") + direction * limit_ratio)
    rounded = calculated.quantize(price_tick, rounding=ROUND_HALF_UP)
    if abs(rounded - previous_close) < price_tick:
        rounded = previous_close + direction * price_tick
    return max(rounded, price_tick)


def _missing_context_fields(
    context: FinanceCNContext,
    price: tuple[object, Decimal] | None,
    previous_close: Decimal | None,
) -> tuple[str, ...]:
    values = {
        "exchange": context.exchange,
        "board": context.board,
        "listing_phase": context.listing_phase,
        "trade_date": context.trade_date,
        "price": price,
        "previous_close": previous_close,
    }
    return tuple(name for name, value in values.items() if value is None)


def _select_rule(context: FinanceCNContext) -> PriceLimitRule | None:
    if context.trade_date is None:
        return None
    matches = [
        rule
        for rule in PRICE_LIMIT_RULES
        if rule.exchange == context.exchange
        and rule.board == context.board
        and rule.listing_phase == context.listing_phase
        and rule.effective_from <= context.trade_date
    ]
    return max(matches, key=lambda rule: rule.effective_from, default=None)


def _unsupported_market_issue(exchange: str) -> Issue:
    return Issue(
        code="unsupported_market",
        severity="soft",
        message="finance_cn supports only SSE and SZSE in this release.",
        checker=PriceLimitChecker.name,
        details={"exchange": exchange},
    )


def _insufficient_context_issue(missing_fields: tuple[str, ...]) -> Issue:
    return Issue(
        code="insufficient_rule_context",
        severity="soft",
        message="Insufficient explicit context for a finance_cn price-limit check.",
        checker=PriceLimitChecker.name,
        details={"missing_fields": list(missing_fields)},
    )


def _prefix_conflict_issue(context: FinanceCNContext) -> Issue | None:
    if context.listing_phase != "normal" or not context.has_listing_prefix_signal():
        return None
    return Issue(
        code="insufficient_rule_context",
        severity="soft",
        message="Structured listing_phase was used despite a conflicting name prefix signal.",
        checker=PriceLimitChecker.name,
        details={"reason": "listing_phase_conflicts_with_name_prefix"},
    )
