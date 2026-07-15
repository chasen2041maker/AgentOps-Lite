from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
import json

from groundguard import Checker, FactGate, Issue


class RecordingChecker:
    def __init__(self, name: str, calls: list[str], issues: tuple[Issue, ...] = ()) -> None:
        self.name = name
        self._calls = calls
        self._issues = issues
        self.request_context: dict[str, object] | None = None

    def check(self, request):  # type: ignore[no-untyped-def]
        self._calls.append(self.name)
        self.request_context = dict(request.context)
        assert isinstance(request.claims, tuple)
        assert isinstance(request.facts, tuple)
        assert isinstance(request.suspected_numbers, tuple)
        assert isinstance(request.uncovered_numbers, tuple)
        return self._issues


class FailingChecker:
    name = "failing"

    def check(self, request):  # type: ignore[no-untyped-def]
        raise RuntimeError("sensitive implementation detail must not escape")


class NestedContextMutationChecker:
    name = "nested-mutation"

    def check(self, request):  # type: ignore[no-untyped-def]
        try:
            request.context["nested"]["values"][0] = "mutated"
        except TypeError:
            pass
        return ()


class NestedContextRecordingChecker:
    name = "nested-recording"

    def __init__(self) -> None:
        self.observed: object | None = None

    def check(self, request):  # type: ignore[no-untyped-def]
        self.observed = request.context["nested"]["values"]
        return ()


def _verified_gate() -> FactGate:
    gate = FactGate(session_id="request_1", clock=lambda: 100.0)
    gate.record_fact(
        key="revenue",
        value=Decimal("3830000000"),
        unit="USD",
        source_tool="financials",
        source_call_id="call_1",
    )
    return gate


def _issue(code: str, severity: str) -> Issue:
    return Issue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        message=f"{code} detected",
        checker="test-checker",
        related_fact_keys=("revenue",),
        related_claim_ids=("claim_1",),
        text_span="$3.83 billion",
        start=12,
        end=25,
        details={"category": "synthetic", "count": 1},
    )


def _checker_name(checker: Checker) -> str:
    return checker.name


def test_checker_protocol_is_request_scoped_and_runs_in_caller_order() -> None:
    calls: list[str] = []
    first = RecordingChecker("first", calls)
    second = RecordingChecker("second", calls)
    gate = _verified_gate()

    report = gate.check(
        "Revenue was $3.83 billion [fact:revenue].",
        required_fact_keys=["revenue"],
        checkers=(first, second),
        context={"profile": "synthetic", "run": 1},
    )

    assert calls == ["first", "second"]
    assert first.request_context == {"profile": "synthetic", "run": 1}
    assert report.issues == ()
    assert report.hard_issue_count == 0
    assert report.soft_issue_count == 0
    assert _checker_name(first) == "first"


def test_checker_omission_and_empty_sequence_preserve_existing_report_behavior() -> None:
    gate = _verified_gate()

    without_checkers = gate.check("Revenue was $3.83 billion [fact:revenue].", required_fact_keys=["revenue"])
    with_empty_checkers = gate.check(
        "Revenue was $3.83 billion [fact:revenue].",
        required_fact_keys=["revenue"],
        checkers=(),
    )

    assert without_checkers.passed is True
    assert with_empty_checkers.passed is True
    assert without_checkers.issues == with_empty_checkers.issues == ()
    assert without_checkers.hard_issue_count == with_empty_checkers.hard_issue_count == 0
    assert without_checkers.soft_issue_count == with_empty_checkers.soft_issue_count == 0


def test_checkers_do_not_leak_between_requests() -> None:
    calls: list[str] = []
    checker = RecordingChecker("only-first", calls, (_issue("soft_first", "soft"),))
    gate = _verified_gate()

    first = gate.check("Revenue was $3.83 billion [fact:revenue].", checkers=(checker,))
    second = gate.check("Revenue was $3.83 billion [fact:revenue].")

    assert calls == ["only-first"]
    assert [issue.code for issue in first.issues] == ["soft_first"]
    assert second.issues == ()


def test_checker_failure_is_soft_fail_open_without_internal_exception_text() -> None:
    report = _verified_gate().check(
        "Revenue was $3.83 billion [fact:revenue].",
        checkers=(FailingChecker(),),
    )

    assert report.passed is True
    assert report.hard_issue_count == 0
    assert report.soft_issue_count == 1
    issue = report.issues[0]
    assert issue.code == "checker_failed"
    assert issue.severity == "soft"
    assert issue.checker == "failing"
    assert "sensitive implementation detail" not in issue.message
    assert issue.details == {"exception_type": "RuntimeError"}


def test_hard_issues_fail_the_report_and_soft_issues_do_not_change_existing_pass_result() -> None:
    hard_checker = RecordingChecker("hard", [], (_issue("hard_problem", "hard"),))
    soft_checker = RecordingChecker("soft", [], (_issue("soft_problem", "soft"),))

    hard_report = _verified_gate().check("Revenue was $3.83 billion [fact:revenue].", checkers=(hard_checker,))
    soft_report = _verified_gate().check("Revenue was $3.83 billion [fact:revenue].", checkers=(soft_checker,))

    assert hard_report.passed is False
    assert hard_report.hard_issue_count == 1
    assert hard_report.soft_issue_count == 0
    assert soft_report.passed is True
    assert soft_report.hard_issue_count == 0
    assert soft_report.soft_issue_count == 1


def test_issue_payload_is_json_serializable() -> None:
    issue = _issue("serializable", "soft")

    serialized = json.dumps(asdict(issue), ensure_ascii=False)

    assert '"code": "serializable"' in serialized


def test_checker_context_is_recursively_frozen_and_isolated_from_caller() -> None:
    caller_context = {"nested": {"values": ["original"]}}
    recording = NestedContextRecordingChecker()

    report = _verified_gate().check(
        "Revenue was $3.83 billion [fact:revenue].",
        checkers=(NestedContextMutationChecker(), recording),
        context=caller_context,
    )

    assert report.issues == ()
    assert recording.observed == ("original",)
    assert caller_context == {"nested": {"values": ["original"]}}
