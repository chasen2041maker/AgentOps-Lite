# GroundGuard v0.1 Draft Release Notes

GroundGuard is a local-first fact gate for tool-using AI agents. It checks the
final answer before release: every important numeric claim should trace back to
an explicitly registered tool fact, and every required fact should be used.

## What Works Now

- In-memory Ledger with JSONL persistence.
- Explicit `tool_call` fact registration.
- Deterministic numeric claim extraction with `[fact:key]` support.
- Claim matching with verified, candidate, unverified, and contradicted states.
- Coverage reports for output claims and required fact omissions.
- Policy evaluation with block, flag, and strip behavior.
- `grounded_generate()` wrapper with optional `GroundedResult` reports.
- CLI JSON reporting through `groundguard-report`.
- Minimal OpenAI-compatible callable wrapper.
- Minimal LangChain-compatible callback handler with explicit fact mapping.
- Financial report demo showing omitted required facts before correction.

## Try It

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe examples\financial_report_demo\run.py
```

## What It Is Not

- Not a tracing dashboard.
- Not an LLM-as-judge evaluator.
- Not a database-backed observability platform.
- Not token-level generation control.

## Safety Note

Ledger entries may contain prompts, tool outputs, or sensitive business data.
Keep examples synthetic or anonymized before sharing reports.
