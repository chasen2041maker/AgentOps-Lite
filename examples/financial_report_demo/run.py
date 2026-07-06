from __future__ import annotations

import json
import os
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
    _enable_windows_ansi()
    print(f"\n{_style(title, bold=True)}")
    print("-" * len(title))
    status_color = "green" if report.passed else "red"
    print(f"passed: {_style(str(report.passed), status_color, bold=True)}")
    print(f"verified: {_style(str(report.verified_count), 'green')}")
    print(f"unverified: {report.unverified_count}")
    print(f"contradicted: {_style_if_nonzero(report.contradicted_count, 'red')}")
    print(f"omitted_required: {_style_if_nonzero(report.omitted_required_count, 'red')}")
    if report.policy_reason:
        print(f"policy_reason: {_style(report.policy_reason, 'yellow')}")


def _style_if_nonzero(value: int, color: str) -> str:
    if value == 0:
        return str(value)
    return _style(str(value), color)


def _style(text: str, color: str | None = None, *, bold: bool = False) -> str:
    if os.getenv("NO_COLOR"):
        return text
    codes: list[str] = []
    if color == "red":
        codes.append("91")
    elif color == "green":
        codes.append("92")
    elif color == "yellow":
        codes.append("93")
    if bold:
        codes.append("1")
    if not codes:
        return text
    prefix = "".join(f"\033[{code}m" for code in codes)
    return f"{prefix}{text}\033[0m"


def _enable_windows_ansi() -> None:
    if os.name == "nt":
        os.system("")


if __name__ == "__main__":
    main()
