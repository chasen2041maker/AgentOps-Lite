"""Public generic fact and metric aliases used by finance_cn checkers."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from groundguard.core.models import Fact


FACT_ALIASES: dict[str, frozenset[str]] = {
    "price": frozenset({"price", "last_price", "close"}),
    "previous_close": frozenset({"previous_close", "prev_close"}),
    "change_pct": frozenset({"change_pct", "change_percent", "pct_change"}),
    "high": frozenset({"high", "high_price"}),
    "low": frozenset({"low", "low_price"}),
    "amplitude": frozenset({"amplitude", "amplitude_pct"}),
    "volume": frozenset({"volume", "volume_shares"}),
    "float_shares": frozenset({"float_shares", "free_float_shares"}),
    "turnover_rate": frozenset({"turnover_rate", "turnover_pct"}),
}

METRIC_KIND_ALIASES: dict[str, frozenset[str]] = {
    "profit": frozenset({"profit", "net_profit", "operating_profit"}),
    "loss": frozenset({"loss", "net_loss", "operating_loss"}),
}


def latest_numeric_fact(
    facts: Sequence[Fact],
    field: str,
) -> tuple[Fact, Decimal] | None:
    aliases = FACT_ALIASES[field]
    selected: tuple[Fact, Decimal] | None = None
    for fact in facts:
        if fact.key.casefold() not in aliases:
            continue
        value = numeric_value(fact)
        if value is None:
            continue
        if selected is None or fact.recorded_at >= selected[0].recorded_at:
            selected = (fact, value)
    return selected


def metric_kind(fact: Fact) -> str | None:
    candidates = (fact.fact_type, fact.key)
    for candidate in candidates:
        if candidate is None:
            continue
        normalized = candidate.casefold()
        for kind, aliases in METRIC_KIND_ALIASES.items():
            if normalized in aliases:
                return kind
    return None


def numeric_value(fact: Fact) -> Decimal | None:
    if isinstance(fact.value, Decimal):
        return fact.value
    try:
        return Decimal(fact.value)
    except (InvalidOperation, ValueError):
        return None
