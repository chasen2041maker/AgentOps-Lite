"""Optional integration helpers for downstream evaluation tools."""

from groundguard.integrations.deepeval import to_deepeval_result
from groundguard.integrations.langfuse import report_to_langfuse_payload
from groundguard.integrations.otel import report_to_otel_events
from groundguard.integrations.phoenix import report_to_phoenix_eval
from groundguard.integrations.promptfoo import to_promptfoo_assertion

__all__ = [
    "report_to_langfuse_payload",
    "report_to_otel_events",
    "report_to_phoenix_eval",
    "to_deepeval_result",
    "to_promptfoo_assertion",
]
