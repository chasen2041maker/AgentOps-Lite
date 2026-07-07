from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


TEMPLATE_NAMES = (
    "github-action",
    "openai",
    "promptfoo",
    "langgraph",
    "pydanticai",
    "crewai",
    "autogen",
    "fastapi",
)


@dataclass(frozen=True)
class StarterFile:
    path: str
    content: str


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    files = _starter_files(args.template)
    existing = [
        output_dir / starter.path
        for starter in files
        if (output_dir / starter.path).exists()
    ]
    if existing and not args.force:
        print(
            "GroundGuard init refused to overwrite existing files: "
            + ", ".join(str(path) for path in existing),
            file=sys.stderr,
        )
        print("Re-run with --force to overwrite them.", file=sys.stderr)
        return 2
    for starter in files:
        target = output_dir / starter.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(starter.content, encoding="utf-8")
    print(f"Created GroundGuard {args.template} starter in {output_dir}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="groundguard-init",
        description="Create starter GroundGuard config, sample data, and integration files.",
    )
    parser.add_argument(
        "--template",
        choices=TEMPLATE_NAMES,
        default="github-action",
        help="Starter template to create.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory where files should be written.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing starter files.",
    )
    return parser


def _starter_files(template: str) -> list[StarterFile]:
    files = [
        StarterFile("groundguard.yml", _CONFIG),
        StarterFile("groundguard-ledger.jsonl", _LEDGER_JSONL),
        StarterFile("answer.txt", _ANSWER),
    ]
    if template == "github-action":
        files.append(StarterFile(".github/workflows/groundguard.yml", _GITHUB_ACTION))
    elif template == "openai":
        files.append(StarterFile("examples/openai_groundguard.py", _OPENAI_EXAMPLE))
    elif template == "promptfoo":
        files.append(StarterFile("examples/promptfoo_groundguard.py", _PROMPTFOO_EXAMPLE))
    elif template == "langgraph":
        files.append(StarterFile("examples/langgraph_groundguard.py", _LANGGRAPH_EXAMPLE))
    elif template == "pydanticai":
        files.append(StarterFile("examples/pydanticai_groundguard.py", _PYDANTICAI_EXAMPLE))
    elif template == "crewai":
        files.append(StarterFile("examples/crewai_groundguard.py", _CREWAI_EXAMPLE))
    elif template == "autogen":
        files.append(StarterFile("examples/autogen_groundguard.py", _AUTOGEN_EXAMPLE))
    elif template == "fastapi":
        files.append(StarterFile("examples/fastapi_groundguard.py", _FASTAPI_EXAMPLE))
    return files


_CONFIG = """required_facts:
  - q3_revenue
policy:
  allow_candidate_matches: false
  max_unverified_ratio: 0.0
  max_contradicted: 0
  max_ambiguous: 0
  max_omitted_required: 0
  on_unverified: block
  on_contradicted: block
  on_omitted_required: block
extractors:
  packs:
    - finance
units:
  tolerance: 0.005
report:
  schema: assertion
  format: github
  fail_on_policy: true
"""


_LEDGER_JSONL = (
    json.dumps(
        {
            "id": "fact_q3_revenue",
            "source_tool": "finance_api",
            "source_call_id": "call_001",
            "key": "q3_revenue",
            "value": "5.2",
            "value_kind": "numeric",
            "unit": "billion_usd",
            "display_value": "$5.2B",
            "recorded_at": 0,
            "confidence": 1.0,
            "metadata": {"example": True},
            "schema_version": 1,
        },
        ensure_ascii=False,
    )
    + "\n"
)


_ANSWER = "Q3 revenue came in at $4.8 billion [fact:q3_revenue].\n"


_GITHUB_ACTION = """name: GroundGuard

on:
  pull_request:
  workflow_dispatch:

jobs:
  fact-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run GroundGuard
        uses: chasen2041maker/GroundGuard@v0.3.1
        with:
          ledger-jsonl: groundguard-ledger.jsonl
          answer-file: answer.txt
          config: groundguard.yml
          required-facts: q3_revenue
          schema: assertion
          fail-on-policy: "true"
"""


_OPENAI_EXAMPLE = '''"""Minimal OpenAI-style GroundGuard starter.

Replace `call_model(...)` with your OpenAI SDK call. Record facts from tools
before checking the final answer.
"""

from groundguard import FactGate


def call_model() -> str:
    return "Q3 revenue came in at $4.8 billion [fact:q3_revenue]."


gate = FactGate.from_config("groundguard.yml")
gate.record_tool_result("q3_revenue", "5.2", "billion_usd", source_tool="finance_api")
report = gate.check(call_model(), required=["q3_revenue"])
print(report.output_claims[0].status)
'''


_PROMPTFOO_EXAMPLE = '''"""Emit a promptfoo-friendly assertion payload."""

from groundguard import FactGate
from groundguard.integrations.promptfoo import to_promptfoo_assertion

gate = FactGate.from_config("groundguard.yml")
gate.record_tool_result("q3_revenue", "5.2", "billion_usd")
report = gate.check("Q3 revenue came in at $4.8 billion [fact:q3_revenue].")
print(to_promptfoo_assertion(report))
'''


_LANGGRAPH_EXAMPLE = '''"""Minimal LangGraph-style node starter."""

from groundguard import FactGate


def groundguard_node(state: dict) -> dict:
    gate = FactGate.from_config("groundguard.yml")
    gate.record_tool_result("q3_revenue", state["q3_revenue"], "billion_usd")
    report = gate.check(state["answer"], required=["q3_revenue"])
    return {**state, "groundguard_report": report, "groundguard_passed": report.passed}
'''


_PYDANTICAI_EXAMPLE = '''"""PydanticAI-style result validator starter.

Keep this file dependency-free: paste the `validate_agent_result(...)` body into
your PydanticAI result validator or output hook.
"""

from groundguard import FactGate


gate = FactGate.from_config("groundguard.yml")


def validate_agent_result(answer: str) -> str:
    gate.record_tool_result("q3_revenue", "5.2", "billion_usd")
    report = gate.check(answer, required=["q3_revenue"])
    if not report.passed:
        raise ValueError(report.policy_reason or "GroundGuard policy failed")
    return answer
'''


_CREWAI_EXAMPLE = '''"""CrewAI-style task callback starter.

Call `check_crew_output(...)` from a CrewAI task callback before returning the
final task output to a user or downstream workflow.
"""

from groundguard import FactGate


gate = FactGate.from_config("groundguard.yml")


def check_crew_output(output_text: str) -> dict:
    gate.record_tool_result("q3_revenue", "5.2", "billion_usd")
    report = gate.check(output_text, required=["q3_revenue"])
    return {"output": output_text, "groundguard_passed": report.passed, "report": report}
'''


_AUTOGEN_EXAMPLE = '''"""AutoGen-style reply guard starter.

Use `guard_reply(...)` in a reply hook or before sending the final assistant
message back to the user.
"""

from groundguard import FactGate


gate = FactGate.from_config("groundguard.yml")


def guard_reply(reply: str) -> str:
    gate.record_tool_result("q3_revenue", "5.2", "billion_usd")
    report = gate.check(reply, required=["q3_revenue"])
    if not report.passed:
        return f"GroundGuard blocked this reply: {report.policy_reason}"
    return reply
'''


_FASTAPI_EXAMPLE = '''"""FastAPI endpoint starter for guarding final agent answers.

Install FastAPI separately if you want to run this file as an API server.
GroundGuard itself stays dependency-free.
"""

from groundguard import FactGate


gate = FactGate.from_config("groundguard.yml")


def check_answer_payload(payload: dict) -> dict:
    gate.record_tool_result("q3_revenue", payload["q3_revenue"], "billion_usd")
    report = gate.check(payload["answer"], required=["q3_revenue"])
    return {
        "passed": report.passed,
        "policy_reason": report.policy_reason,
        "answer": payload["answer"] if report.passed else None,
    }
'''


def cli() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
