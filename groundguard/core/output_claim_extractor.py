from __future__ import annotations

import re
from decimal import Decimal
from uuid import uuid4

from groundguard.core.models import OutputClaim


_NUMERIC_CLAIM_RE = re.compile(
    r"(?P<currency_prefix>US\$|USD|\$)?\s*"
    r"(?P<number>\d[\d,]*(?:\.\d+)?)\s*"
    r"(?P<magnitude>亿|万|千|billion|bn|million|mn|thousand|b|m|k)?\s*"
    r"(?P<unit>%|percentage points?|percent|美元|元|股|倍|US dollars?|USD|dollars?)?"
    r"(?:\s*\[fact:(?P<fact_key>[A-Za-z0-9_.:-]+)\])?",
    re.IGNORECASE,
)


def extract_output_claims(text: str) -> list[OutputClaim]:
    """Extract deterministic numeric claims from generated output."""

    claims: list[OutputClaim] = []
    for match in _NUMERIC_CLAIM_RE.finditer(text):
        if _inside_fact_marker(text, match.start()):
            continue
        currency_prefix = match.group("currency_prefix")
        unit_text = match.group("unit")
        magnitude_text = match.group("magnitude")
        if currency_prefix is None and unit_text is None and magnitude_text is None:
            continue
        value, unit = _normalize_numeric_value(
            match.group("number"),
            magnitude=magnitude_text,
            unit=unit_text,
            currency_prefix=currency_prefix,
        )
        claims.append(
            OutputClaim(
                id=f"claim_{uuid4().hex}",
                text_span=_claim_text_span(text, match),
                claim_type="numeric",
                normalized_value=value,
                unit=unit,
                fact_key=match.group("fact_key"),
            )
        )
    return claims


def _normalize_numeric_value(
    number_text: str,
    magnitude: str | None,
    unit: str | None,
    currency_prefix: str | None = None,
) -> tuple[Decimal, str | None]:
    value = Decimal(number_text.replace(",", ""))
    value *= _magnitude_multiplier(magnitude)
    return value, _normalized_unit(unit) or _normalized_currency_prefix(currency_prefix)


def _magnitude_multiplier(magnitude: str | None) -> Decimal:
    if magnitude is None:
        return Decimal("1")
    normalized = magnitude.lower()
    if magnitude == "亿":
        return Decimal("100000000")
    if magnitude == "万":
        return Decimal("10000")
    if magnitude == "千":
        return Decimal("1000")
    if normalized in {"billion", "bn", "b"}:
        return Decimal("1000000000")
    if normalized in {"million", "mn", "m"}:
        return Decimal("1000000")
    if normalized in {"thousand", "k"}:
        return Decimal("1000")
    return Decimal("1")


def _normalized_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    normalized = unit.lower()
    if unit in {"元"}:
        return "CNY"
    if unit == "美元":
        return "USD"
    if normalized in {"usd", "dollar", "dollars", "us dollar", "us dollars"}:
        return "USD"
    if normalized in {"percent", "percentage point", "percentage points"}:
        return "%"
    return unit


def _normalized_currency_prefix(currency_prefix: str | None) -> str | None:
    if currency_prefix is None:
        return None
    normalized = currency_prefix.lower()
    if normalized in {"$", "us$", "usd"}:
        return "USD"
    return currency_prefix


def _claim_text_span(text: str, match: re.Match[str]) -> str:
    context_start = max(0, match.start() - 16)
    delimiter_index = max(
        text.rfind(delimiter, context_start, match.start())
        for delimiter in "，。,.；;\n"
    )
    start = delimiter_index + 1 if delimiter_index != -1 else context_start
    while start > 0 and text[start - 1].isascii() and text[start - 1].isalnum():
        start -= 1
    return text[start : match.end()].strip("，。,. ")


def _inside_fact_marker(text: str, index: int) -> bool:
    marker_start = text.rfind("[fact:", 0, index + 1)
    if marker_start == -1:
        return False
    marker_end = text.find("]", marker_start)
    return marker_end != -1 and marker_start < index < marker_end
