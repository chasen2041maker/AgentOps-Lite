from __future__ import annotations

import json
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from groundguard import Fact, Ledger, Policy


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    answer: str
    expected_passed: bool
    required_facts: list[str]


CASES = [
    BenchmarkCase(
        name="verified_answer",
        answer=(
            "Revenue was $3.83 billion [fact:revenue_2025], "
            "and net profit was $823.2 million [fact:net_profit_2025]."
        ),
        expected_passed=True,
        required_facts=["revenue_2025", "net_profit_2025"],
    ),
    BenchmarkCase(
        name="omitted_required_fact",
        answer="Revenue was $3.83 billion [fact:revenue_2025].",
        expected_passed=False,
        required_facts=["revenue_2025", "net_profit_2025"],
    ),
    BenchmarkCase(
        name="contradicted_tagged_fact",
        answer=(
            "Revenue was $3.80 billion [fact:revenue_2025], "
            "and net profit was $823.2 million [fact:net_profit_2025]."
        ),
        expected_passed=False,
        required_facts=["revenue_2025", "net_profit_2025"],
    ),
    BenchmarkCase(
        name="invented_unregistered_number",
        answer=(
            "Revenue was $3.83 billion [fact:revenue_2025], "
            "and net profit was $823.2 million [fact:net_profit_2025]. "
            "Cash reserves were $120 million."
        ),
        expected_passed=False,
        required_facts=["revenue_2025", "net_profit_2025"],
    ),
]


def run_benchmark() -> dict[str, Any]:
    """Run a tiny deterministic benchmark for README and docs claims."""

    rows: list[dict[str, Any]] = []
    elapsed_ms: list[float] = []
    for case in CASES:
        ledger = _build_ledger()
        start = time.perf_counter()
        report = ledger.coverage_report(
            case.answer,
            required_fact_keys=case.required_facts,
            policy=Policy(max_unverified_ratio=0.0, on_unverified="block"),
        )
        elapsed_ms.append((time.perf_counter() - start) * 1000)
        rows.append(
            {
                "name": case.name,
                "expected_passed": case.expected_passed,
                "actual_passed": report.passed,
                "verified": report.verified_count,
                "contradicted": report.contradicted_count,
                "unverified": report.unverified_count,
                "omitted_required": report.omitted_required_count,
                "policy_reason": report.policy_reason,
            }
        )

    expected_failures = sum(1 for row in rows if row["expected_passed"] is False)
    detected_failures = sum(
        1
        for row in rows
        if row["expected_passed"] is False and row["actual_passed"] is False
    )
    false_positives = sum(
        1
        for row in rows
        if row["expected_passed"] is True and row["actual_passed"] is False
    )
    return {
        "cases_total": len(rows),
        "expected_failures": expected_failures,
        "detected_failures": detected_failures,
        "false_positives": false_positives,
        "mean_elapsed_ms": round(sum(elapsed_ms) / len(elapsed_ms), 3),
        "cases": rows,
    }


def _build_ledger() -> Ledger:
    ledger = Ledger(session_id="benchmark")
    ledger.register_fact(
        Fact(
            id="fact_revenue_2025",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="revenue_2025",
            value=Decimal("3830000000"),
            unit="USD",
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_net_profit_2025",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="net_profit_2025",
            value=Decimal("823200000"),
            unit="USD",
        )
    )
    return ledger


def main() -> None:
    print(json.dumps(run_benchmark(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

