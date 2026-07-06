# Integrations

## GitHub Actions

```yaml
- name: Run GroundGuard
  uses: chasen2041maker/GroundGuard@v0.2.4
  with:
    ledger-jsonl: groundguard-ledger.jsonl
    answer-file: answer.txt
    config: groundguard.yml
    required-facts: revenue_2025,net_profit_2025
    schema: assertion
    fail-on-policy: "true"
```

## promptfoo

```bash
python examples/promptfoo_groundguard/run.py
```

The example emits promptfoo-style assertion JSON with `pass`, `score`,
`reason`, `claims`, and `componentResults`.

## DeepEval

```bash
python examples/deepeval_groundguard/run.py
```

The helper returns a DeepEval-friendly metric result without requiring DeepEval
as a hard runtime dependency.

## OpenTelemetry-style Events

```python
from groundguard.integrations.otel import report_to_otel_events

events = report_to_otel_events(report)
for event in events:
    span.add_event(event["name"], event["attributes"])
```

The exporter returns plain dictionaries and does not add OpenTelemetry as a
runtime dependency.

## Langfuse and Phoenix Payloads

```python
from groundguard.integrations.langfuse import report_to_langfuse_payload
from groundguard.integrations.phoenix import report_to_phoenix_eval

langfuse_payload = report_to_langfuse_payload(report)
phoenix_eval = report_to_phoenix_eval(report)
```

These helpers return plain dictionaries. GroundGuard does not import Langfuse
or Phoenix at runtime; applications that already use those SDKs can attach the
payloads themselves.

## Gateway Mode

```bash
groundguard-server --config groundguard.yml --host 127.0.0.1 --port 8765
```

The server exposes `POST /check` with JSON fields `session_id`, `facts`,
`answer`, and `required_facts`. It is intentionally minimal and dependency-free.
