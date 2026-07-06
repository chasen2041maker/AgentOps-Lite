from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from groundguard.core.ledger import Ledger
from groundguard.core.tool_call import FactInput, tool_call


@dataclass(frozen=True)
class ToolRunContext:
    tool_name: str
    tool_input: Any = None
    run_id: str | None = None


FactMapper = Callable[[Any, ToolRunContext], dict[str, FactInput]]


class GroundGuardCallbackHandler:
    """Small LangChain-compatible callback handler for explicit fact registration."""

    def __init__(self, ledger: Ledger, fact_mapper: FactMapper) -> None:
        self.ledger = ledger
        self.fact_mapper = fact_mapper
        self._runs: dict[str, ToolRunContext] = {}

    def on_tool_start(
        self,
        serialized: dict[str, Any] | None,
        input_str: Any,
        *,
        run_id: Any = None,
        **_: Any,
    ) -> None:
        context = ToolRunContext(
            tool_name=_tool_name(serialized),
            tool_input=input_str,
            run_id=_optional_str(run_id),
        )
        if context.run_id is not None:
            self._runs[context.run_id] = context

    def on_tool_end(self, output: Any, *, run_id: Any = None, **_: Any) -> None:
        context = self._context_for(run_id)
        facts = self.fact_mapper(output, context)
        with tool_call(
            context.tool_name,
            args={"input": context.tool_input, "run_id": context.run_id},
            ledger=self.ledger,
        ) as call:
            call.record_facts(facts, raw=output)

    def _context_for(self, run_id: Any) -> ToolRunContext:
        key = _optional_str(run_id)
        if key is not None and key in self._runs:
            return self._runs.pop(key)
        return ToolRunContext(tool_name="langchain_tool", run_id=key)


def _tool_name(serialized: dict[str, Any] | None) -> str:
    if not serialized:
        return "langchain_tool"
    return str(serialized.get("name") or serialized.get("id") or "langchain_tool")


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
