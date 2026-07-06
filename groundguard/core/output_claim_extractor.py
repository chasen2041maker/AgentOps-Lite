from __future__ import annotations

import re
from decimal import Decimal
from uuid import uuid4

from groundguard.core.models import OutputClaim
from groundguard.core.units import (
    magnitude_multiplier,
    normalized_currency_prefix,
    normalized_unit,
)


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
        start, end = _claim_match_span(text, match)
        claims.append(
            OutputClaim(
                id=f"claim_{uuid4().hex}",
                text_span=_claim_text_span(text, match),
                claim_type="numeric",
                normalized_value=value,
                unit=unit,
                fact_key=match.group("fact_key"),
                start=start,
                end=end,
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
    value *= magnitude_multiplier(magnitude)
    return value, normalized_unit(unit) or normalized_currency_prefix(currency_prefix)


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


def _claim_match_span(text: str, match: re.Match[str]) -> tuple[int, int]:
    start = match.start()
    end = match.end()
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _inside_fact_marker(text: str, index: int) -> bool:
    marker_start = text.rfind("[fact:", 0, index + 1)
    if marker_start == -1:
        return False
    marker_end = text.find("]", marker_start)
    return marker_end != -1 and marker_start < index < marker_end
