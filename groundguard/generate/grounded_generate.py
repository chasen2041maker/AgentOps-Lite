from __future__ import annotations

from collections.abc import Callable

from groundguard.core.ledger import Ledger
from groundguard.core.policy import Policy


def grounded_generate(
    prompt: str,
    llm_call: Callable[[str], str],
    ledger: Ledger,
    required_fact_keys: list[str] | None = None,
    policy: Policy | None = None,
) -> str:
    """Call a user-provided LLM function with fact-key guidance."""

    grounded_prompt = _build_grounded_prompt(prompt, required_fact_keys or [])
    answer = llm_call(grounded_prompt)
    ledger.coverage_report(answer, required_fact_keys=required_fact_keys, policy=policy)
    return answer


def _build_grounded_prompt(prompt: str, required_fact_keys: list[str]) -> str:
    if not required_fact_keys:
        return prompt
    fact_key_lines = "\n".join(f"- [fact:{key}]" for key in required_fact_keys)
    return (
        f"{prompt}\n\n"
        "Use these fact markers when citing registered facts:\n"
        f"{fact_key_lines}"
    )
