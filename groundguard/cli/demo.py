from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from decimal import Decimal
from typing import Any

from groundguard.cli.report import _json_safe
from groundguard.core.ledger import Ledger
from groundguard.core.models import CoverageReport
from groundguard.core.policy import Policy
from groundguard.core.tool_call import tool_call


REQUIRED_FACT_KEYS = ["revenue_2025", "net_profit_2025"]


def run_demo() -> dict[str, Any]:
    """Run a packaged before/after demo with no external fixtures."""

    bad_answer = "No reliable revenue or net profit data was available."
    corrected_answer = (
        "Revenue was $3.83 billion [fact:revenue_2025], "
        "and net profit was $823.2 million [fact:net_profit_2025]."
    )

    with Ledger(session_id="groundguard_demo") as ledger:
        with tool_call(
            "get_company_financials",
            args={"company": "ACME", "period": "FY2025"},
            ledger=ledger,
        ) as call:
            call.record_facts(
                {
                    "revenue_2025": (Decimal("3830000000"), "USD"),
                    "net_profit_2025": (Decimal("823200000"), "USD"),
                },
                raw={
                    "company": "ACME",
                    "period": "FY2025",
                    "revenue": "3830000000",
                    "net_profit": "823200000",
                },
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
    return {
        "before": _summary(before),
        "after": _summary(after),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="groundguard-demo",
        description="Run the packaged GroundGuard before/after fact-gate demo.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a terminal summary.",
    )
    args = parser.parse_args(argv)
    result = run_demo()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_terminal_summary(result)
    return 0


def cli() -> None:
    raise SystemExit(main())


def _summary(report: CoverageReport) -> dict[str, Any]:
    return {
        "passed": report.passed,
        "verified": report.verified_count,
        "unverified": report.unverified_count,
        "contradicted": report.contradicted_count,
        "omitted_required": report.omitted_required_count,
        "policy_reason": report.policy_reason,
        "report": _json_safe(asdict(report)),
    }


def _print_terminal_summary(result: dict[str, Any]) -> None:
    _print_block("Before GroundGuard correction", result["before"])
    _print_block("After fact-key correction", result["after"])


def _print_block(title: str, summary: dict[str, Any]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    print(f"passed: {summary['passed']}")
    print(f"verified: {summary['verified']}")
    print(f"unverified: {summary['unverified']}")
    print(f"contradicted: {summary['contradicted']}")
    print(f"omitted_required: {summary['omitted_required']}")
    if summary["policy_reason"]:
        print(f"policy_reason: {summary['policy_reason']}")


if __name__ == "__main__":
    cli()
