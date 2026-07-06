from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from groundguard.core.ledger import Ledger
from groundguard.core.models import CoverageReport
from groundguard.core.policy import Policy


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    ledger = Ledger.from_jsonl(args.ledger_jsonl, session_id=args.session_id)
    answer = Path(args.answer_file).read_text(encoding="utf-8")
    policy = Policy(allow_candidate_matches=args.allow_candidate_matches)
    report = ledger.coverage_report(
        answer,
        required_fact_keys=args.required_fact,
        policy=policy,
    )
    payload = report_to_dict(report)
    output = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(f"{output}\n", encoding="utf-8")
    else:
        print(output)
    if args.fail_on_policy and not report.passed:
        return 1
    return 0


def report_to_dict(report: CoverageReport) -> dict[str, Any]:
    return _json_safe(asdict(report))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="groundguard-report",
        description="Generate a GroundGuard coverage report from a ledger JSONL file.",
    )
    parser.add_argument("--ledger-jsonl", required=True, help="Path to Ledger JSONL facts.")
    parser.add_argument("--answer-file", required=True, help="Path to generated answer text.")
    parser.add_argument(
        "--required-fact",
        action="append",
        default=[],
        help="Required fact key that must be covered. May be repeated.",
    )
    parser.add_argument(
        "--session-id",
        default="groundguard_cli",
        help="Session id to place in the generated report.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write JSON output. Defaults to stdout.",
    )
    parser.add_argument(
        "--allow-candidate-matches",
        action="store_true",
        help="Allow candidate numeric matches to cover required facts.",
    )
    parser.add_argument(
        "--fail-on-policy",
        action="store_true",
        help="Exit with status 1 when the evaluated policy does not pass.",
    )
    return parser


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def cli() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
