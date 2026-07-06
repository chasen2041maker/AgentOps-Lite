from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from groundguard import Fact, Ledger, Policy
from groundguard.integrations.promptfoo import to_promptfoo_assertion


def run_demo() -> dict[str, Any]:
    ledger = Ledger(session_id="promptfoo_demo")
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
    report = ledger.coverage_report(
        "Revenue was $3.80 billion [fact:revenue_2025].",
        required_fact_keys=["revenue_2025"],
        policy=Policy(),
    )
    return to_promptfoo_assertion(report)


def main() -> None:
    print(json.dumps(run_demo(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

