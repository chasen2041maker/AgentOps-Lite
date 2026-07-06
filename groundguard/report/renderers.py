from __future__ import annotations

from html import escape

from groundguard.core.models import CoverageReport
from groundguard.report.schema import report_to_versioned_dict


def render_markdown_report(report: CoverageReport) -> str:
    """Render a human-readable Markdown report."""

    payload = report_to_versioned_dict(report)
    summary = payload["summary"]
    lines = [
        "# GroundGuard Report",
        "",
        f"- Session: `{payload['session_id']}`",
        f"- Passed: `{summary['passed']}`",
        f"- Policy reason: {summary['policy_reason'] or 'none'}",
        f"- Verified: `{summary['verified_count']}`",
        f"- Contradicted: `{summary['contradicted_count']}`",
        f"- Unverified: `{summary['unverified_count']}`",
        f"- Omitted required: `{summary['omitted_required_count']}`",
        "",
        "| Status | Claim | Unit | Matched fact | Ledger value | Answer value | Span | Diff |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for claim in payload["claims"]:
        span = _span(claim.get("start"), claim.get("end"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(str(claim.get("status") or "")),
                    _md(str(claim.get("text_span") or "")),
                    _md(str(claim.get("unit") or "")),
                    _md(str(claim.get("matched_fact_key") or claim.get("fact_key") or claim.get("matched_fact_id") or "")),
                    _md(str(claim.get("ledger_value") or "")),
                    _md(str(claim.get("answer_value") or claim.get("normalized_value") or "")),
                    _md(span),
                    _md(str(claim.get("diff") or "")),
                ]
            )
            + " |"
        )
    if not payload["claims"]:
        lines.append("| none |  |  |  |  |  |  |  |")
    return "\n".join(lines) + "\n"


def render_github_pr_comment(report: CoverageReport) -> str:
    """Render a compact GitHub PR comment body."""

    status = "PASS" if report.passed else "FAIL"
    return (
        "## GroundGuard Fact Gate\n\n"
        f"Status: `{status}`\n\n"
        f"{report.policy_reason or 'GroundGuard policy passed.'}\n\n"
        + render_markdown_report(report)
    )


def render_html_report(report: CoverageReport) -> str:
    """Render a dependency-free HTML report."""

    payload = report_to_versioned_dict(report)
    summary = payload["summary"]
    rows = []
    for claim in payload["claims"]:
        rows.append(
            "<tr>"
            f"<td>{escape(str(claim.get('status') or ''))}</td>"
            f"<td>{escape(str(claim.get('text_span') or ''))}</td>"
            f"<td>{escape(str(claim.get('unit') or ''))}</td>"
            f"<td>{escape(str(claim.get('matched_fact_key') or claim.get('fact_key') or claim.get('matched_fact_id') or ''))}</td>"
            f"<td>{escape(str(claim.get('ledger_value') or ''))}</td>"
            f"<td>{escape(str(claim.get('answer_value') or claim.get('normalized_value') or ''))}</td>"
            f"<td>{escape(_span(claim.get('start'), claim.get('end')))}</td>"
            f"<td>{escape(str(claim.get('diff') or ''))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td>none</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>")
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>GroundGuard Report</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:2rem}"
        "table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #ddd;padding:.4rem;text-align:left}"
        "th{background:#f6f8fa}</style></head><body>"
        "<h1>GroundGuard Report</h1>"
        f"<p><strong>Session:</strong> {escape(str(payload['session_id']))}</p>"
        f"<p><strong>Passed:</strong> {escape(str(summary['passed']))}</p>"
        f"<p><strong>Policy reason:</strong> {escape(str(summary['policy_reason'] or 'none'))}</p>"
        "<table><thead><tr><th>Status</th><th>Claim</th><th>Unit</th>"
        "<th>Matched fact</th><th>Ledger value</th><th>Answer value</th>"
        "<th>Span</th><th>Diff</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>\n"
    )


def _md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _span(start: object, end: object) -> str:
    if start is None or end is None:
        return ""
    return f"{start}:{end}"
