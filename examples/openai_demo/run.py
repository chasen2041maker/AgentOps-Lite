from __future__ import annotations

import argparse
import os
from collections.abc import Callable
from decimal import Decimal

from groundguard import GroundedResult, Ledger, Policy, grounded_generate, tool_call
from groundguard.adapters import openai_chat_llm


REQUIRED_FACT_KEYS = ["net_profit_2025", "revenue_2025"]


def run_demo(use_live_openai: bool | None = None) -> GroundedResult:
    with Ledger(session_id="openai_demo") as ledger:
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

        llm_call = _build_llm_call(use_live_openai)
        result = grounded_generate(
            prompt=(
                "Summarize ACME's latest financial performance in one sentence. "
                "Use only these registered facts: revenue_2025=383000000000 CNY "
                "(3830 亿元), net_profit_2025=82320000000 CNY (823.2 亿元)."
            ),
            llm_call=llm_call,
            ledger=ledger,
            required_fact_keys=REQUIRED_FACT_KEYS,
            policy=Policy(),
            return_report=True,
        )
        if not isinstance(result, GroundedResult):
            raise TypeError("OpenAI demo expected GroundedResult")
        return result


def _build_llm_call(use_live_openai: bool | None) -> Callable[[str], str]:
    live = bool(os.getenv("OPENAI_API_KEY")) if use_live_openai is None else use_live_openai
    if not live:
        return _offline_llm_call
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Install the OpenAI SDK with `python -m pip install openai` "
            "or run without --live-openai for the offline demo."
        ) from exc
    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    return openai_chat_llm(client.chat.completions.create, model=model, temperature=0)


def _offline_llm_call(prompt: str) -> str:
    return (
        "Revenue was 3830 亿元 [fact:revenue_2025], "
        "and net profit was 823.2 亿元 [fact:net_profit_2025]."
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the GroundGuard OpenAI demo.")
    parser.add_argument(
        "--live-openai",
        action="store_true",
        help="Use the native OpenAI SDK path. Requires OPENAI_API_KEY.",
    )
    args = parser.parse_args(argv)
    result = run_demo(use_live_openai=args.live_openai)
    print(result.answer)
    print(f"passed: {result.report.passed}")
    print(f"verified: {result.report.verified_count}")
    print(f"omitted_required: {result.report.omitted_required_count}")


if __name__ == "__main__":
    main()
