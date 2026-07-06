from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from groundguard.core.ledger import Ledger
from groundguard.core.models import CoverageReport
from groundguard.core.policy import Policy


@dataclass(frozen=True)
class GroundedResult:
    answer: str
    report: CoverageReport


class GroundingPolicyError(RuntimeError):
    def __init__(self, answer: str, report: CoverageReport) -> None:
        self.answer = answer
        self.report = report
        super().__init__(report.policy_reason or "Grounding policy blocked output")


def grounded_generate(
    prompt: str,
    llm_call: Callable[[str], str],
    ledger: Ledger,
    required_fact_keys: list[str] | None = None,
    policy: Policy | None = None,
    return_report: bool = False,
) -> str | GroundedResult:
    """Call a user-provided LLM function with fact-key guidance."""

    active_policy = policy or Policy()
    active_required_fact_keys = required_fact_keys or []
    grounded_prompt = _build_grounded_prompt(prompt, active_required_fact_keys)
    answer = llm_call(grounded_prompt)
    return _finalize_grounded_answer(
        answer=answer,
        ledger=ledger,
        required_fact_keys=active_required_fact_keys,
        policy=active_policy,
        return_report=return_report,
    )


def grounded(
    *,
    ledger: Ledger,
    required_fact_keys: list[str] | None = None,
    policy: Policy | None = None,
    return_report: bool = False,
) -> Callable[[Callable[..., str]], Callable[..., str | GroundedResult]]:
    """Decorate a framework-free function with GroundGuard verification."""

    active_required_fact_keys = list(required_fact_keys or [])
    active_policy = policy or Policy()

    def decorator(func: Callable[..., str]) -> Callable[..., str | GroundedResult]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> str | GroundedResult:
            answer = func(*args, **kwargs)
            return _finalize_grounded_answer(
                answer=answer,
                ledger=ledger,
                required_fact_keys=active_required_fact_keys,
                policy=active_policy,
                return_report=return_report,
            )

        return wrapper

    return decorator


def _finalize_grounded_answer(
    *,
    answer: str,
    ledger: Ledger,
    required_fact_keys: list[str],
    policy: Policy,
    return_report: bool,
) -> str | GroundedResult:
    report = ledger.coverage_report(
        answer,
        required_fact_keys=required_fact_keys,
        policy=policy,
    )
    if policy.on_unverified == "strip" and report.unverified_count:
        answer = _strip_unverified_claims(answer, report)
        report = ledger.coverage_report(
            answer,
            required_fact_keys=required_fact_keys,
            policy=policy,
        )
    if _should_block(report):
        raise GroundingPolicyError(answer=answer, report=report)
    if return_report:
        return GroundedResult(answer=answer, report=report)
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


def _strip_unverified_claims(answer: str, report: CoverageReport) -> str:
    stripped = answer
    for claim in report.output_claims:
        if claim.status == "unverified":
            stripped = _strip_claim_span(stripped, claim.text_span)
    return _cleanup_stripped_text(stripped)


def _strip_claim_span(answer: str, text_span: str) -> str:
    span_start = answer.find(text_span)
    if span_start == -1:
        return answer
    number_match = re.search(r"\d", text_span)
    if number_match is None:
        return answer.replace(text_span, "", 1)
    number_index = span_start + number_match.start()
    remove_start = _claim_clause_start(answer, number_index)
    remove_end = span_start + len(text_span)
    return f"{answer[:remove_start]}{answer[remove_end:]}"


def _claim_clause_start(answer: str, number_index: int) -> int:
    delimiters = "，。,.；;\n"
    delimiter_index = max(answer.rfind(delimiter, 0, number_index) for delimiter in delimiters)
    if delimiter_index == -1:
        return max(0, number_index - 8)
    return delimiter_index + 1


def _cleanup_stripped_text(text: str) -> str:
    while "，，" in text:
        text = text.replace("，，", "，")
    while "  " in text:
        text = text.replace("  ", " ")
    return text.replace("，。", "。").strip(" ，")


def _should_block(report: CoverageReport) -> bool:
    return not report.passed
