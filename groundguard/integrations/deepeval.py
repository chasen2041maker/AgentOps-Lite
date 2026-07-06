from __future__ import annotations

from typing import Any

from groundguard.cli.report import report_to_assertion_dict
from groundguard.core.models import CoverageReport


def to_deepeval_result(report: CoverageReport) -> dict[str, Any]:
    """Return a DeepEval-friendly metric result without requiring DeepEval."""

    payload = report_to_assertion_dict(report)
    return {
        "success": payload["success"],
        "score": payload["score"],
        "reason": payload["reason"],
        "metadata": payload["metadata"],
        "componentResults": payload["componentResults"],
    }

