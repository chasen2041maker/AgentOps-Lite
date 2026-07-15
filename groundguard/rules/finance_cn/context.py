"""Explicit context parsing for opt-in Shanghai and Shenzhen rules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class FinanceCNContext:
    """Caller-supplied market facts; absent or invalid values remain unset."""

    exchange: str | None = None
    board: str | None = None
    listing_phase: str | None = None
    trade_date: date | None = None
    previous_close: Decimal | None = None
    security_name: str | None = None

    @classmethod
    def from_mapping(cls, context: Mapping[str, Any]) -> FinanceCNContext:
        payload = context.get("finance_cn", context)
        if not isinstance(payload, Mapping):
            return cls()
        return cls(
            exchange=_optional_string(payload.get("exchange")),
            board=_optional_string(payload.get("board")),
            listing_phase=_optional_string(payload.get("listing_phase")),
            trade_date=_parse_date(payload.get("trade_date")),
            previous_close=_parse_decimal(payload.get("previous_close")),
            security_name=_optional_string(payload.get("security_name")),
        )

    def has_listing_prefix_signal(self) -> bool:
        if not self.security_name:
            return False
        return self.security_name.lstrip()[:1].upper() in {"N", "C"}


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
