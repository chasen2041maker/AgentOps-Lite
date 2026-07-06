# GroundGuard Launch Kit

This is a lightweight launch checklist for the first public distribution pass.
It keeps the message focused on the concrete failure mode GroundGuard catches:
the model had the tool data but still said it was unavailable.

## Channels

- Hacker News: Show HN
- Reddit: r/LocalLLaMA or a narrowly relevant AI engineering community

## 30-Second Demo Script

```text
$ python examples/financial_report_demo/run.py

Before GroundGuard correction
passed: False
omitted_required: 2
policy_reason: omitted_required_count=2 > max_omitted_required=0

After fact-key correction
passed: True
verified: 2
omitted_required: 0
```

Narration:

```text
The tool returned revenue and net profit.
The model said the data was unavailable.
GroundGuard caught the omitted required facts.
After the answer cites the registered fact keys, the deterministic gate passes.
```

## Show HN Draft

```text
Show HN: GroundGuard, a local fact gate for tool-using AI agents

I built GroundGuard after seeing a recurring failure in tool-using agents:
the tool call returns the right data, but the final answer still says the data
was unavailable or silently omits the key numbers.

GroundGuard is intentionally small. It is not a tracing dashboard and not an
LLM-as-judge. You explicitly register facts from tool calls, then GroundGuard
checks whether the final answer cites and covers those facts before you release
it.

The current v0.1.0 release includes:
- in-memory Ledger + JSONL persistence
- explicit tool_call(...).record_facts(...)
- deterministic numeric claim extraction
- omitted-required-fact detection
- CLI JSON reports and assertion-style output for eval tools
- OpenAI/LangChain/LangGraph-style examples
- a reusable GitHub Action

The core demo is the failure mode:

Before: passed=False, omitted_required=2
After:  passed=True, verified=2

Repo: https://github.com/chasen2041maker/GroundGuard
```

## Feedback To Watch

- If people ask how this differs from Langfuse, Phoenix, promptfoo, or DeepEval,
  sharpen the README comparison table.
- If people ask whether it supports non-numeric claims, point them to the v0.1.0
  limit: numeric claims with units or magnitude markers only.
- If people ask for automatic fact extraction from arbitrary JSON, keep the v1
  boundary: explicit mapping first, optional extraction later.
