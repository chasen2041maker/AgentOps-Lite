# Production Guide

GroundGuard is designed to stay lightweight in production. Treat each request
or agent run as its own fact-gate session, record only the facts needed for the
answer, and export reports to the systems you already operate.

## Session Scoping

Create one `FactGate` or `Ledger` per request, conversation turn, batch item, or
agent run. Do not share a mutable ledger across unrelated users or tenants.

```python
gate = FactGate(session_id=request_id)
```

If your agent runs parallel tools, synchronize writes to a shared ledger or give
each branch a separate ledger and merge facts before the final answer check.

## Key Naming

Use descriptive fact keys that include the metric and enough context to avoid
accidental collisions:

```text
company.revenue[entity=ACME,period=2026Q3,unit=USD]
saas.arr[tenant=prod,period=2026-06,unit=USD]
ops.p95_latency[service=checkout,window=5m,unit=ms]
```

This is a convention, not a required parser. GroundGuard still accepts simple
keys such as `q3_revenue`, but structured keys make reports easier to review.

## Multi-Tenant Extractors

The global extractor registry is process-wide. For multi-tenant services,
prefer request-scoped extractor packs through `groundguard.yml` or
`FactGate.from_config(...)` instead of dynamically mutating global registry
state at request time.

```yaml
extractors:
  packs:
    - finance
    - saas
```

## Sensitive Data

GroundGuard does not require a hosted service. Keep raw tool payloads out of
reports when they contain secrets, customer data, or proprietary data. Prefer
recording minimal facts:

```python
gate.record_tool_result(
    "refund_amount",
    "268",
    "CNY",
    metadata={"source": "billing_api"},
)
```

Avoid putting tokens, full customer records, or private prompts in
`metadata`, `raw`, generated reports, or GitHub PR comments.

## Schema Compatibility

Public protocol objects carry `schema_version`, and the report schema is
published in `schemas/groundguard.report.v1.schema.json`. GroundGuard will not
remove or rename fields within a major version; new fields may be added with
defaults.

For CI and downstream tools, prefer the versioned report shape:

```bash
groundguard-report \
  --ledger-jsonl groundguard-ledger.jsonl \
  --answer-file answer.txt \
  --schema groundguard
```

## Failure Handling

Start with `flag` in low-risk flows so teams can observe real failures before
blocking users. Use `block` or `reask` when incorrect numbers create business,
compliance, or customer-support risk.

Recommended rollout:

```text
week 1: flag only, collect reports
week 2: block contradictions on tagged required facts
week 3: block omitted required facts in high-risk endpoints
```

## Operational Boundaries

GroundGuard is not a database, queue, trace store, or dashboard. Persist JSONL
facts or rendered reports only when your application needs auditability. Export
summaries to Langfuse, Phoenix, OpenTelemetry, promptfoo, or DeepEval when those
tools are already part of your workflow.
