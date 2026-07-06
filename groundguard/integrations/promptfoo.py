from __future__ import annotations

from typing import Any

from groundguard.cli.report import report_to_assertion_dict
from groundguard.core.models import CoverageReport


def to_promptfoo_assertion(report: CoverageReport) -> dict[str, Any]:
    """Return a promptfoo-compatible assertion result payload."""

    return report_to_assertion_dict(report)

