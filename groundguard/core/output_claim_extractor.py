from __future__ import annotations

import re
from decimal import Decimal
from uuid import uuid4

from groundguard.core.models import OutputClaim


_NUMERIC_CLAIM_RE = re.compile(
    r"(?P<number>\d[\d,]*(?:\.\d+)?)\s*"
    r"(?P<magnitude>亿|万|千)?\s*"
    r"(?P<unit>%|美元|元|股|倍)?"
    r"(?:\s*\[fact:(?P<fact_key>[A-Za-z0-9_.:-]+)\])?"
)


def extract_output_claims(text: str) -> list[OutputClaim]:
    """Extract deterministic numeric claims from generated output."""

    claims: list[OutputClaim] = []
    for match in _NUMERIC_CLAIM_RE.finditer(text):
        if _inside_fact_marker(text, match.start()):
            continue
        unit_text = match.group("unit")
        magnitude_text = match.group("magnitude")
        if unit_text is None and magnitude_text is None:
            continue
        value, unit = _normalize_numeric_value(
            match.group("number"),
            magnitude=magnitude_text,
            unit=unit_text,
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
) -> tuple[Decimal, str | None]:
    value = Decimal(number_text.replace(",", ""))
    value *= _magnitude_multiplier(magnitude)
    return value, _normalized_unit(unit)


def _magnitude_multiplier(magnitude: str | None) -> Decimal:
    if magnitude == "亿":
        return Decimal("100000000")
    if magnitude == "万":
        return Decimal("10000")
    if magnitude == "千":
        return Decimal("1000")
    return Decimal("1")


def _normalized_unit(unit: str | None) -> str | None:
    if unit in {"元"}:
        return "CNY"
    if unit == "美元":
        return "USD"
    return unit


def _claim_text_span(text: str, match: re.Match[str]) -> str:
    start = max(0, match.start() - 8)
    return text[start : match.end()].strip("，。,. ")


def _inside_fact_marker(text: str, index: int) -> bool:
    marker_start = text.rfind("[fact:", 0, index + 1)
    if marker_start == -1:
        return False
    marker_end = text.find("]", marker_start)
    return marker_end != -1 and marker_start < index < marker_end
