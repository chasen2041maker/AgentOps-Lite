# Recipes

These recipes show where GroundGuard sits in common agent stacks. The same
pattern repeats: record tool facts, generate an answer, then check the answer
before release.

## Start From A Template

```bash
groundguard-init --template github-action
groundguard-init --template openai
groundguard-init --template promptfoo
groundguard-init --template langgraph
groundguard-init --template pydanticai
groundguard-init --template crewai
groundguard-init --template autogen
groundguard-init --template fastapi
```

Each template writes `groundguard.yml`, `groundguard-ledger.jsonl`,
`answer.txt`, and a small integration-specific starter file. Existing files are
not overwritten unless you pass `--force`.

## OpenAI Tool Use

Use the OpenAI SDK for the model call, but keep fact registration explicit in
your application code:

```python
from groundguard import FactGate

gate = FactGate.from_config("groundguard.yml")
gate.record_tool_result("q3_revenue", "5.2", "billion_usd", source_tool="finance_api")

answer = "Q3 revenue came in at $4.8 billion [fact:q3_revenue]."
report = gate.check(answer, required=["q3_revenue"])
assert not report.passed
```

See `examples/openai_demo/run.py` for a runnable deterministic demo and optional
live OpenAI SDK path.

## LangGraph Node

Put the check in a node after your tool and generation nodes:

```python
from groundguard import FactGate


def groundguard_node(state: dict) -> dict:
    gate = FactGate.from_config("groundguard.yml")
    gate.record_tool_result("q3_revenue", state["q3_revenue"], "billion_usd")
    report = gate.check(state["answer"], required=["q3_revenue"])
    return {**state, "groundguard_report": report, "groundguard_passed": report.passed}
```

## PydanticAI Result Validator

Use GroundGuard in the final result validator or output hook:

```python
from groundguard import FactGate

gate = FactGate.from_config("groundguard.yml")


def validate_agent_result(answer: str) -> str:
    gate.record_tool_result("q3_revenue", "5.2", "billion_usd")
    report = gate.check(answer, required=["q3_revenue"])
    if not report.passed:
        raise ValueError(report.policy_reason or "GroundGuard policy failed")
    return answer
```

## CrewAI Task Callback

Put the gate in a task callback before returning task output:

```python
from groundguard import FactGate

gate = FactGate.from_config("groundguard.yml")


def check_crew_output(output_text: str) -> dict:
    gate.record_tool_result("q3_revenue", "5.2", "billion_usd")
    report = gate.check(output_text, required=["q3_revenue"])
    return {"output": output_text, "groundguard_passed": report.passed}
```

## AutoGen Reply Guard

Use GroundGuard before sending a final reply:

```python
from groundguard import FactGate

gate = FactGate.from_config("groundguard.yml")


def guard_reply(reply: str) -> str:
    gate.record_tool_result("q3_revenue", "5.2", "billion_usd")
    report = gate.check(reply, required=["q3_revenue"])
    if not report.passed:
        return f"GroundGuard blocked this reply: {report.policy_reason}"
    return reply
```

## FastAPI Backend Endpoint

Keep the gate in the backend request path:

```python
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
```

## GitHub Action

For CI checks, generate or commit a ledger JSONL file and answer text file, then
run the composite action:

```yaml
- name: Run GroundGuard
  uses: chasen2041maker/GroundGuard@v0.3.1
  with:
    ledger-jsonl: groundguard-ledger.jsonl
    answer-file: answer.txt
    config: groundguard.yml
    required-facts: q3_revenue
    schema: assertion
    fail-on-policy: "true"
```

For a PR comment workflow, copy
`docs/examples/github-actions/pr-comment.yml`.

## promptfoo

Use GroundGuard as a deterministic assertion alongside promptfoo suites:

```python
from groundguard.integrations.promptfoo import to_promptfoo_assertion

payload = to_promptfoo_assertion(report)
```

See `examples/promptfoo_groundguard/run.py`.

## DeepEval

Use GroundGuard as a factual component beside broader semantic metrics:

```python
from groundguard.integrations.deepeval import to_deepeval_result

result = to_deepeval_result(report)
```

See `examples/deepeval_groundguard/run.py`.

## Langfuse, Phoenix, And OpenTelemetry

GroundGuard does not become your tracing platform. Export the report to the
platform you already use:

```python
from groundguard.integrations.langfuse import report_to_langfuse_payload
from groundguard.integrations.phoenix import report_to_phoenix_eval
from groundguard.integrations.otel import report_to_otel_events

langfuse_payload = report_to_langfuse_payload(report)
phoenix_eval = report_to_phoenix_eval(report)
otel_events = report_to_otel_events(report)
```
