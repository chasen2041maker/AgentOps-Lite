"""Public generic fact aliases used by finance_cn checkers."""

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


def latest_numeric_fact(
    facts: Sequence[Fact],
    field: str,
    *,
    subject: str | None = None,
) -> tuple[Fact, Decimal] | None:
    aliases = FACT_ALIASES[field]
    if subject is None:
        subjects = {
            fact.subject
            for fact in facts
            if fact.key.casefold() in aliases and numeric_value(fact) is not None
        }
        if len(subjects) != 1:
            return None
        subject = next(iter(subjects))
    selected: tuple[Fact, Decimal] | None = None
    for fact in facts:
        if fact.key.casefold() not in aliases:
            continue
        if subject is not None and fact.subject != subject:
            continue
        value = numeric_value(fact)
        if value is None:
            continue
        if selected is None or fact.recorded_at >= selected[0].recorded_at:
            selected = (fact, value)
    return selected


def coherent_numeric_facts(
    facts: Sequence[Fact],
    fields: Sequence[str],
    *,
    subject: str | None = None,
) -> dict[str, tuple[Fact, Decimal]] | None:
    """Return latest values only when every field belongs to one subject."""

    possible_subjects: set[str | None] | None = None
    for field in fields:
        aliases = FACT_ALIASES[field]
        field_subjects = {
            fact.subject
            for fact in facts
            if fact.key.casefold() in aliases
            and (subject is None or fact.subject == subject)
            and numeric_value(fact) is not None
        }
        if not field_subjects:
            return None
        possible_subjects = (
            field_subjects
            if possible_subjects is None
            else possible_subjects.intersection(field_subjects)
        )
        if not possible_subjects:
            return None

    if possible_subjects is None or len(possible_subjects) != 1:
        return None

    selected_subject = next(iter(possible_subjects))
    selected: dict[str, tuple[Fact, Decimal]] = {}
    for field in fields:
        value = latest_numeric_fact(facts, field, subject=selected_subject)
        if value is None:
            return None
        selected[field] = value
    return selected


def numeric_value(fact: Fact) -> Decimal | None:
    if isinstance(fact.value, Decimal):
        return fact.value
    try:
        return Decimal(fact.value)
    except (InvalidOperation, ValueError):
        return None
