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
    policy: Policy = Policy(max_unverified_ratio=0.0, on_unverified="block")


CASES = [
    BenchmarkCase(
        name="verified_revenue_and_profit",
        answer=(
            "Revenue was $3.83 billion [fact:revenue_2025], "
            "and net profit was $823.2 million [fact:net_profit_2025]."
        ),
        expected_passed=True,
        required_facts=["revenue_2025", "net_profit_2025"],
    ),
    BenchmarkCase(
        name="verified_gross_margin_percent_symbol",
        answer="Gross margin was 21.5% [fact:gross_margin_2025].",
        expected_passed=True,
        required_facts=["gross_margin_2025"],
    ),
    BenchmarkCase(
        name="verified_gross_margin_percent_word",
        answer="Gross margin was 21.5 percent [fact:gross_margin_2025].",
        expected_passed=True,
        required_facts=["gross_margin_2025"],
    ),
    BenchmarkCase(
        name="verified_cash_and_debt",
        answer=(
            "Cash was $400 million [fact:cash_2025], "
            "and debt was $1.2 billion [fact:debt_2025]."
        ),
        expected_passed=True,
        required_facts=["cash_2025", "debt_2025"],
    ),
    BenchmarkCase(
        name="verified_operating_cash_flow_abbrev",
        answer="Operating cash flow was US$910M [fact:operating_cash_flow_2025].",
        expected_passed=True,
        required_facts=["operating_cash_flow_2025"],
    ),
    BenchmarkCase(
        name="verified_free_cash_flow_million",
        answer="Free cash flow was $650 million [fact:free_cash_flow_2025].",
        expected_passed=True,
        required_facts=["free_cash_flow_2025"],
    ),
    BenchmarkCase(
        name="verified_revenue_comma_million",
        answer="Revenue was $3,830 million [fact:revenue_2025].",
        expected_passed=True,
        required_facts=["revenue_2025"],
    ),
    BenchmarkCase(
        name="verified_churn_rate",
        answer="Customer churn was 3.2% [fact:churn_rate_2025].",
        expected_passed=True,
        required_facts=["churn_rate_2025"],
    ),
    BenchmarkCase(
        name="candidate_match_allowed_revenue",
        answer="Revenue was $3.83 billion.",
        expected_passed=True,
        required_facts=["revenue_2025"],
        policy=Policy(
            max_unverified_ratio=0.0,
            on_unverified="block",
            allow_candidate_matches=True,
        ),
    ),
    BenchmarkCase(
        name="candidate_match_allowed_margin",
        answer="Gross margin was 21.5%.",
        expected_passed=True,
        required_facts=["gross_margin_2025"],
        policy=Policy(
            max_unverified_ratio=0.0,
            on_unverified="block",
            allow_candidate_matches=True,
        ),
    ),
    BenchmarkCase(
        name="no_required_facts_no_numeric_claims",
        answer="The report contains no numeric claims.",
        expected_passed=True,
        required_facts=[],
    ),
    BenchmarkCase(
        name="omitted_required_profit",
        answer="Revenue was $3.83 billion [fact:revenue_2025].",
        expected_passed=False,
        required_facts=["revenue_2025", "net_profit_2025"],
    ),
    BenchmarkCase(
        name="omitted_all_required_facts",
        answer="The model could not verify the financial data.",
        expected_passed=False,
        required_facts=["revenue_2025", "net_profit_2025"],
    ),
    BenchmarkCase(
        name="omitted_one_of_three_required_facts",
        answer=(
            "Revenue was $3.83 billion [fact:revenue_2025], "
            "and net profit was $823.2 million [fact:net_profit_2025]."
        ),
        expected_passed=False,
        required_facts=["revenue_2025", "net_profit_2025", "cash_2025"],
    ),
    BenchmarkCase(
        name="contradicted_revenue",
        answer=(
            "Revenue was $3.80 billion [fact:revenue_2025], "
            "and net profit was $823.2 million [fact:net_profit_2025]."
        ),
        expected_passed=False,
        required_facts=["revenue_2025", "net_profit_2025"],
    ),
    BenchmarkCase(
        name="contradicted_net_profit",
        answer="Net profit was $800 million [fact:net_profit_2025].",
        expected_passed=False,
        required_facts=["net_profit_2025"],
    ),
    BenchmarkCase(
        name="contradicted_margin",
        answer="Gross margin was 22.5% [fact:gross_margin_2025].",
        expected_passed=False,
        required_facts=["gross_margin_2025"],
    ),
    BenchmarkCase(
        name="contradicted_unit",
        answer="Net profit was 823.2 percent [fact:net_profit_2025].",
        expected_passed=False,
        required_facts=["net_profit_2025"],
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
    BenchmarkCase(
        name="invented_growth_rate",
        answer="Revenue growth was 12%.",
        expected_passed=False,
        required_facts=[],
    ),
    BenchmarkCase(
        name="candidate_match_not_allowed_for_required_fact",
        answer="Revenue was $3.83 billion.",
        expected_passed=False,
        required_facts=["revenue_2025"],
    ),
    BenchmarkCase(
        name="ambiguous_candidate_match",
        answer="Cash-like assets were $400.5 million.",
        expected_passed=False,
        required_facts=[],
    ),
    BenchmarkCase(
        name="bare_number_not_extracted",
        answer="Revenue was 3830000000 [fact:revenue_2025].",
        expected_passed=False,
        required_facts=["revenue_2025"],
    ),
    BenchmarkCase(
        name="unknown_fact_key",
        answer="Revenue was $3.83 billion [fact:unknown_revenue].",
        expected_passed=False,
        required_facts=["revenue_2025"],
    ),
    BenchmarkCase(
        name="invented_cash_after_verified_facts",
        answer=(
            "Revenue was $3.83 billion [fact:revenue_2025], "
            "net profit was $823.2 million [fact:net_profit_2025], "
            "and one-time gains were $77 million."
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
            policy=case.policy,
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
    ledger.register_fact(
        Fact(
            id="fact_gross_margin_2025",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="gross_margin_2025",
            value=Decimal("21.5"),
            unit="%",
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_operating_cash_flow_2025",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="operating_cash_flow_2025",
            value=Decimal("910000000"),
            unit="USD",
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_free_cash_flow_2025",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="free_cash_flow_2025",
            value=Decimal("650000000"),
            unit="USD",
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_cash_2025",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="cash_2025",
            value=Decimal("400000000"),
            unit="USD",
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_restricted_cash_2025",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="restricted_cash_2025",
            value=Decimal("401000000"),
            unit="USD",
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_debt_2025",
            source_tool="get_company_financials",
            source_call_id="call_1",
            key="debt_2025",
            value=Decimal("1200000000"),
            unit="USD",
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_churn_rate_2025",
            source_tool="get_company_metrics",
            source_call_id="call_2",
            key="churn_rate_2025",
            value=Decimal("3.2"),
            unit="%",
        )
    )
    return ledger


def main() -> None:
    print(json.dumps(run_benchmark(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
