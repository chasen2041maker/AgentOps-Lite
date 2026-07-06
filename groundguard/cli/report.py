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
from groundguard.core.config import load_config
from groundguard.report import (
    render_github_pr_comment,
    render_html_report,
    render_markdown_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config) if args.config else None
    ledger = Ledger.from_jsonl(args.ledger_jsonl, session_id=args.session_id)
    answer = Path(args.answer_file).read_text(encoding="utf-8")
    policy = config.policy if config else Policy()
    if args.allow_candidate_matches:
        policy = Policy(
            max_unverified_ratio=policy.max_unverified_ratio,
            max_contradicted=policy.max_contradicted,
            max_ambiguous=policy.max_ambiguous,
            max_omitted_required=policy.max_omitted_required,
            allow_candidate_matches=True,
            on_unverified=policy.on_unverified,
            on_contradicted=policy.on_contradicted,
            on_omitted_required=policy.on_omitted_required,
        )
    required_facts = list(config.required_facts if config else [])
    required_facts.extend(args.required_fact)
    schema = args.schema or (config.report.schema if config else "groundguard")
    output_format = args.format or (config.report.format if config else "json")
    fail_on_policy = args.fail_on_policy or (
        config.report.fail_on_policy if config else False
    )
    report = ledger.coverage_report(
        answer,
        required_fact_keys=required_facts,
        policy=policy,
    )
    output = _render_report(report, schema=schema, output_format=output_format)
    if args.output:
        Path(args.output).write_text(f"{output}\n", encoding="utf-8")
    else:
        print(output)
    if fail_on_policy and not report.passed:
        return 1
    return 0


def report_to_dict(report: CoverageReport) -> dict[str, Any]:
    return _json_safe(asdict(report))


def report_to_assertion_dict(report: CoverageReport) -> dict[str, Any]:
    """Return a promptfoo/DeepEval-friendly assertion result payload."""

    reason = report.policy_reason or "GroundGuard policy passed."
    return {
        "pass": report.passed,
        "passed": report.passed,
        "success": report.passed,
        "score": _coverage_score(report),
        "reason": reason,
        "assertion": {
            "type": "groundguard.fact_coverage",
            "metric": "groundguard.fact_coverage",
        },
        "namedScores": {
            "groundguard.verified_count": report.verified_count,
            "groundguard.candidate_match_count": report.candidate_match_count,
            "groundguard.unverified_count": report.unverified_count,
            "groundguard.contradicted_count": report.contradicted_count,
            "groundguard.ambiguous_count": report.ambiguous_count,
            "groundguard.omitted_required_count": report.omitted_required_count,
            "groundguard.extraction_coverage": report.extraction_coverage,
        },
        "claims": _json_safe([asdict(claim) for claim in report.output_claims]),
        "componentResults": _claim_component_results(report),
        "metadata": {
            "groundguard": report_to_dict(report),
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="groundguard-report",
        description="Generate a GroundGuard coverage report from a ledger JSONL file.",
    )
    parser.add_argument("--ledger-jsonl", required=True, help="Path to Ledger JSONL facts.")
    parser.add_argument("--answer-file", required=True, help="Path to generated answer text.")
    parser.add_argument(
        "--config",
        help="Optional groundguard.yml or JSON config file.",
    )
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
        "--schema",
        choices=["groundguard", "assertion"],
        default=None,
        help=(
            "JSON schema to emit. 'assertion' includes promptfoo/DeepEval-style "
            "pass, score, reason, and metadata fields."
        ),
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "html", "github"],
        default=None,
        help="Output format. JSON preserves the selected schema; other formats render a human report.",
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


def _render_report(
    report: CoverageReport,
    *,
    schema: str,
    output_format: str,
) -> str:
    if output_format == "markdown":
        return render_markdown_report(report).rstrip()
    if output_format == "html":
        return render_html_report(report).rstrip()
    if output_format == "github":
        return render_github_pr_comment(report).rstrip()
    payload = (
        report_to_assertion_dict(report)
        if schema == "assertion"
        else report_to_dict(report)
    )
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _coverage_score(report: CoverageReport) -> float:
    total_claims = (
        report.verified_count
        + report.candidate_match_count
        + report.unverified_count
        + report.contradicted_count
        + report.ambiguous_count
    )
    if total_claims == 0:
        return 1.0 if report.passed else 0.0
    return report.verified_count / total_claims


def _claim_component_results(report: CoverageReport) -> list[dict[str, Any]]:
    return [
        {
            "pass": claim.status in {"verified", "candidate_match"},
            "score": 1.0 if claim.status in {"verified", "candidate_match"} else 0.0,
            "reason": claim.diff or claim.status,
            "metadata": _json_safe(asdict(claim)),
        }
        for claim in report.output_claims
    ]


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
