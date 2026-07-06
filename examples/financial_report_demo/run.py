from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from groundguard import CoverageReport, Ledger, Policy, tool_call


DEMO_DIR = Path(__file__).parent
FIXTURES_DIR = DEMO_DIR / "fixtures"
REQUIRED_FACT_KEYS = ["net_profit_2025", "revenue_2025"]


@dataclass(frozen=True)
class DemoResult:
    before: CoverageReport
    after: CoverageReport


def run_demo() -> DemoResult:
    tool_response = _load_tool_response()
    bad_answer = (FIXTURES_DIR / "bad_model_output.txt").read_text(encoding="utf-8")
    corrected_answer = (
        "收入为 3830 亿元 [fact:revenue_2025]，"
        "净利润为 823.2 亿元 [fact:net_profit_2025]。"
    )

    with Ledger(session_id="financial_report_demo") as ledger:
        with tool_call(
            "get_company_financials",
            args={"company": tool_response["company"], "period": tool_response["period"]},
            ledger=ledger,
        ) as call:
            call.record_facts(
                {
                    "net_profit_2025": (Decimal(tool_response["net_profit"]), "CNY"),
                    "revenue_2025": (Decimal(tool_response["revenue"]), "CNY"),
                },
                raw=tool_response,
            )

        policy = Policy()
        before = ledger.coverage_report(
            bad_answer,
            required_fact_keys=REQUIRED_FACT_KEYS,
            policy=policy,
        )
        after = ledger.coverage_report(
            corrected_answer,
            required_fact_keys=REQUIRED_FACT_KEYS,
            policy=policy,
        )
    return DemoResult(before=before, after=after)


def main() -> None:
    result = run_demo()
    _print_report("Before GroundGuard correction", result.before)
    _print_report("After fact-key correction", result.after)


def _load_tool_response() -> dict[str, str]:
    return json.loads((FIXTURES_DIR / "tool_response.json").read_text(encoding="utf-8"))


def _print_report(title: str, report: CoverageReport) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    print(f"passed: {report.passed}")
    print(f"verified: {report.verified_count}")
    print(f"unverified: {report.unverified_count}")
    print(f"contradicted: {report.contradicted_count}")
    print(f"omitted_required: {report.omitted_required_count}")
    if report.policy_reason:
        print(f"policy_reason: {report.policy_reason}")


if __name__ == "__main__":
    main()
