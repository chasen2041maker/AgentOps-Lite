from __future__ import annotations

from decimal import Decimal

from groundguard import GroundedResult, Ledger, Policy, grounded, tool_call


REQUIRED_FACT_KEYS = ["net_profit_2025", "revenue_2025"]


def run_demo() -> GroundedResult:
    with Ledger(session_id="decorator_demo") as ledger:
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

        @grounded(
            ledger=ledger,
            required_fact_keys=REQUIRED_FACT_KEYS,
            policy=Policy(),
            return_report=True,
        )
        def summarize_financials() -> str:
            return (
                "Revenue was 3830 亿元 [fact:revenue_2025], "
                "and net profit was 823.2 亿元 [fact:net_profit_2025]."
            )

        result = summarize_financials()
        if not isinstance(result, GroundedResult):
            raise TypeError("decorator demo expected GroundedResult")
        return result


def main() -> None:
    result = run_demo()
    print(result.answer)
    print(f"passed: {result.report.passed}")
    print(f"verified: {result.report.verified_count}")
    print(f"omitted_required: {result.report.omitted_required_count}")


if __name__ == "__main__":
    main()
