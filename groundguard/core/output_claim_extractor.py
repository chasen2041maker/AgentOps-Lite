from __future__ import annotations

import re
from collections.abc import Callable
from decimal import Decimal
from uuid import uuid4

from groundguard.core.models import OutputClaim, SuspectedNumber
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


# v0.2 extractor registry. The earlier numeric extractor is kept above for
# source compatibility, while the public extract_output_claims symbol below
# dispatches through this registry.
Extractor = Callable[[str], list[OutputClaim]]
_EXTRACTORS: dict[str, Extractor] = {}

_DEFAULT_NUMERIC_CLAIM_RE = re.compile(
    r"(?P<currency_prefix>US\$|USD|\$)?\s*"
    r"(?P<number>[+-]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?)\s*"
    r"(?P<magnitude>\u4ebf|\u4e07|\u5343|billion|bn|million|mn|thousand|b|m|k)?\s*"
    r"(?P<unit>%|percentage points?|percent|\u7f8e\u5143|\u5143|\u80a1|\u500d|US dollars?|USD|dollars?)?"
    r"(?:\s*\[fact:(?P<fact_key>[A-Za-z0-9_.:-]+)\])?",
    re.IGNORECASE,
)

_SUSPECTED_NUMBER_RE = re.compile(
    r"(?P<currency_prefix>US\$|USD|\$)?\s*"
    r"(?P<number>[+-]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?)\s*"
    r"(?P<suffix>"
    r"%|percentage points?|percent|"
    r"\u4ebf|\u4e07|\u5343|\u7f8e\u5143|\u5143|\u80a1|\u500d|"
    r"billion|bn|million|mn|thousand|US dollars?|USD|dollars?|[bmk]"
    r")?",
    re.IGNORECASE,
)


def register_extractor(
    name: str,
    extractor: Extractor | None = None,
) -> Callable[[Extractor], Extractor] | Extractor:
    """Register a deterministic output-claim extractor."""

    def decorator(candidate: Extractor) -> Extractor:
        _EXTRACTORS[name] = candidate
        return candidate

    if extractor is None:
        return decorator
    return decorator(extractor)


def unregister_extractor(name: str) -> None:
    """Remove a previously registered extractor."""

    _EXTRACTORS.pop(name, None)


def registered_extractors() -> dict[str, Extractor]:
    """Return registered extractors in execution order."""

    return dict(_EXTRACTORS)


@register_extractor("numeric")
def _default_numeric_extractor(text: str) -> list[OutputClaim]:
    claims: list[OutputClaim] = []
    for match in _DEFAULT_NUMERIC_CLAIM_RE.finditer(text):
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


def extract_output_claims(text: str) -> list[OutputClaim]:
    """Extract deterministic claims from generated output."""

    claims: list[OutputClaim] = []
    for extractor in _EXTRACTORS.values():
        claims.extend(extractor(text))
    return _sort_and_deduplicate_claims(claims, text)


def find_suspected_numbers(
    text: str,
    covered_claims: list[OutputClaim] | None = None,
) -> list[SuspectedNumber]:
    """Find numeric-looking spans and mark whether extraction covered them."""

    claims = covered_claims or []
    suspected: list[SuspectedNumber] = []
    for match in _SUSPECTED_NUMBER_RE.finditer(text):
        start, end = _claim_match_span(text, match)
        start, end = _trim_number_range(text, start, end)
        if _inside_fact_marker(text, start):
            continue
        text_span = text[start:end].strip()
        if not text_span:
            continue
        covered = any(_ranges_overlap(start, end, claim.start, claim.end) for claim in claims)
        suspected.append(
            SuspectedNumber(
                text_span=text_span,
                start=start,
                end=end,
                covered=covered,
                reason="covered" if covered else "not_extracted",
            )
        )
    return suspected


def _sort_and_deduplicate_claims(
    claims: list[OutputClaim],
    text: str,
) -> list[OutputClaim]:
    seen: set[tuple[object, ...]] = set()
    unique: list[OutputClaim] = []
    for claim in sorted(claims, key=lambda item: _claim_sort_key(item, text)):
        key = (
            claim.claim_type,
            claim.start,
            claim.end,
            claim.fact_key,
            claim.unit,
            str(claim.normalized_value),
        )
        if key in seen or _duplicates_existing_claim(claim, unique):
            continue
        seen.add(key)
        unique.append(claim)
    return unique


def _claim_sort_key(claim: OutputClaim, text: str) -> tuple[int, int]:
    start = claim.start if claim.start is not None else text.find(claim.text_span)
    if start == -1:
        start = len(text)
    end = claim.end if claim.end is not None else start + len(claim.text_span)
    return start, end


def _ranges_overlap(
    start: int,
    end: int,
    claim_start: int | None,
    claim_end: int | None,
) -> bool:
    if claim_start is None or claim_end is None:
        return False
    return start < claim_end and claim_start < end


def _duplicates_existing_claim(claim: OutputClaim, claims: list[OutputClaim]) -> bool:
    for existing in claims:
        if claim.claim_type != existing.claim_type:
            continue
        if claim.fact_key != existing.fact_key:
            continue
        if claim.unit != existing.unit:
            continue
        if not _claim_values_equal(claim.normalized_value, existing.normalized_value):
            continue
        if not _ranges_overlap(
            claim.start or 0,
            claim.end or 0,
            existing.start,
            existing.end,
        ):
            continue
        return True
    return False


def _claim_values_equal(left: object, right: object) -> bool:
    if isinstance(left, Decimal) and isinstance(right, Decimal):
        return left == right
    return left == right


def _trim_number_range(text: str, start: int, end: int) -> tuple[int, int]:
    trailing_punctuation = ",.;:\u3002\uff0c\uff1b\uff1a\uff1f\uff01"
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1] in trailing_punctuation:
        end -= 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _claim_text_span(text: str, match: re.Match[str]) -> str:
    context_start = max(0, match.start() - 16)
    delimiters = ",.;:\n\u3002\uff0c\uff1b\uff1a\uff1f\uff01"
    delimiter_index = max(
        text.rfind(delimiter, context_start, match.start()) for delimiter in delimiters
    )
    start = delimiter_index + 1 if delimiter_index != -1 else context_start
    while start > 0 and text[start - 1].isascii() and text[start - 1].isalnum():
        start -= 1
    return text[start : match.end()].strip(" ,.;:\n\u3002\uff0c\uff1b\uff1a\uff1f\uff01")
