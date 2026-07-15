"""Request-scoped deterministic checker extension protocol."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Protocol

from groundguard.core.models import CoverageReport, Fact, Issue, OutputClaim, SuspectedNumber, _is_json_safe


@dataclass(frozen=True)
class CheckRequest:
    """The immutable, per-request data made available to deterministic checkers."""

    answer: str
    claims: tuple[OutputClaim, ...]
    facts: tuple[Fact, ...]
    suspected_numbers: tuple[SuspectedNumber, ...]
    uncovered_numbers: tuple[SuspectedNumber, ...]
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        context = dict(self.context)
        if not _is_json_safe(context):
            raise ValueError("checker context must be JSON-safe")
        object.__setattr__(self, "context", MappingProxyType(context))


class Checker(Protocol):
    """A synchronous, request-scoped deterministic report checker."""

    name: str

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        """Return deterministic issues without performing external I/O."""


def run_checkers(checkers: Sequence[Checker], request: CheckRequest) -> tuple[Issue, ...]:
    """Run checkers in caller order and convert checker failures into soft issues."""

    issues: list[Issue] = []
    for checker in checkers:
        checker_name = _checker_name(checker)
        try:
            produced = tuple(checker.check(request))
            if not all(isinstance(issue, Issue) for issue in produced):
                raise TypeError("checker returned a non-Issue value")
            issues.extend(produced)
        except Exception as exc:
            issues.append(
                Issue(
                    code="checker_failed",
                    severity="soft",
                    message=f"Checker '{checker_name}' failed.",
                    checker=checker_name,
                    details={"exception_type": type(exc).__name__},
                )
            )
    return tuple(issues)


def apply_issues(report: CoverageReport, issues: tuple[Issue, ...]) -> CoverageReport:
    """Attach checker findings and only let hard findings change pass/fail."""

    if not issues:
        return report
    hard_issue_count = sum(issue.severity == "hard" for issue in issues)
    soft_issue_count = sum(issue.severity == "soft" for issue in issues)
    return replace(
        report,
        issues=issues,
        hard_issue_count=hard_issue_count,
        soft_issue_count=soft_issue_count,
        passed=report.passed and hard_issue_count == 0,
    )


def _checker_name(checker: Checker) -> str:
    try:
        name = str(checker.name).strip()
    except Exception:
        name = "unknown_checker"
    return (name or "unknown_checker")[:120]
