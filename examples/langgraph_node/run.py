from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from groundguard import Ledger, Policy, tool_call


REQUIRED_FACT_KEYS = ["net_profit_2025", "revenue_2025"]


@dataclass(frozen=True)
class DemoResult:
    before: dict[str, Any]
    after: dict[str, Any]


def groundguard_gate_node(state: dict[str, Any]) -> dict[str, Any]:
    """A minimal LangGraph-compatible node: state in, state out."""

    ledger = state["ledger"]
    if not isinstance(ledger, Ledger):
        raise TypeError("state['ledger'] must be a GroundGuard Ledger")
    answer = str(state["answer"])
    required_fact_keys = list(state.get("required_fact_keys", []))
    policy = state.get("policy", Policy())
    report = ledger.coverage_report(
        answer,
        required_fact_keys=required_fact_keys,
        policy=policy,
    )
    return {
        **state,
        "groundguard_report": report,
        "groundguard_passed": report.passed,
        "groundguard_reason": report.policy_reason,
    }


def run_demo() -> DemoResult:
    with Ledger(session_id="langgraph_node_demo") as ledger:
        with tool_call("get_company_financials", {"ticker": "ACME"}, ledger) as call:
            call.record_facts(
                {
                    "net_profit_2025": (Decimal("82320000000"), "CNY"),
                    "revenue_2025": (Decimal("383000000000"), "CNY"),
                },
                raw={
                    "ticker": "ACME",
                    "net_profit": "82320000000",
                    "revenue": "383000000000",
                },
            )

        base_state = {
            "ledger": ledger,
            "required_fact_keys": REQUIRED_FACT_KEYS,
            "policy": Policy(),
        }
        before = groundguard_gate_node(
            {
                **base_state,
                "answer": "The latest financial data was unavailable.",
            }
        )
        after = groundguard_gate_node(
            {
                **base_state,
                "answer": (
                    "Revenue was 3830 亿元 [fact:revenue_2025], "
                    "and net profit was 823.2 亿元 [fact:net_profit_2025]."
                ),
            }
        )
        return DemoResult(before=before, after=after)


def main() -> None:
    result = run_demo()
    for label, state in [("before", result.before), ("after", result.after)]:
        report = state["groundguard_report"]
        print(f"{label}: passed={report.passed}, verified={report.verified_count}, "
              f"omitted_required={report.omitted_required_count}")


if __name__ == "__main__":
    main()
