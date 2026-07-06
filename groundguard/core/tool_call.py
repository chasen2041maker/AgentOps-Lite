from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable
from uuid import uuid4

from groundguard.core.ledger import Ledger
from groundguard.core.models import Fact, FactValueKind


Clock = Callable[[], float]
FactInput = Decimal | str | tuple[Decimal | str, str | None]


@dataclass
class ToolCall:
    """Context object for one tool call whose facts may be registered."""

    name: str
    args: dict[str, Any]
    ledger: Ledger
    clock: Clock
    id: str
    started_at: float | None = None
    ended_at: float | None = None

    def __enter__(self) -> ToolCall:
        self.started_at = self.clock()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.ended_at = self.clock()
        return None

    @property
    def elapsed_seconds(self) -> float | None:
        if self.started_at is None or self.ended_at is None:
            return None
        return self.ended_at - self.started_at

    def record_facts(
        self,
        facts: dict[str, FactInput],
        raw: Any = None,
    ) -> None:
        for key, value in facts.items():
            normalized_value, unit = _normalize_fact_input(value)
            self.ledger.register_fact(
                Fact(
                    id=f"fact_{uuid4().hex}",
                    source_tool=self.name,
                    source_call_id=self.id,
                    key=key,
                    value=normalized_value,
                    value_kind=_infer_value_kind(normalized_value),
                    unit=unit,
                    raw=raw,
                )
            )


def tool_call(
    name: str,
    args: dict[str, Any],
    ledger: Ledger,
    clock: Clock | None = None,
) -> ToolCall:
    return ToolCall(
        name=name,
        args=args,
        ledger=ledger,
        clock=clock or time.time,
        id=f"call_{uuid4().hex}",
    )


def _normalize_fact_input(value: FactInput) -> tuple[Decimal | str, str | None]:
    if isinstance(value, tuple):
        fact_value, unit = value
        return fact_value, unit
    return value, None


def _infer_value_kind(value: Decimal | str) -> FactValueKind:
    if isinstance(value, Decimal):
        return "numeric"
    return "text"
