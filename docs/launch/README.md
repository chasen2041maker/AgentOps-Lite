# GroundGuard Launch Kit

This is a lightweight launch checklist for the first public distribution pass.
It keeps the message focused on the concrete failure mode GroundGuard catches:
the model had the tool data but still said it was unavailable.

## Channels

- Hacker News: Show HN
- Reddit: r/LocalLLaMA or a narrowly relevant AI engineering community

## Brand Assets

- README wordmark: [`assets/brand/groundguard-logo-wordmark.png`](../../assets/brand/groundguard-logo-wordmark.png)
- Square icon: [`assets/brand/groundguard-icon.png`](../../assets/brand/groundguard-icon.png)
- Full brand board: [`assets/brand/groundguard-brand-board.png`](../../assets/brand/groundguard-brand-board.png)

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

I built GroundGuard after seeing a recurring failure in my own workflow:
tools returned the numbers I needed, but the model's final answer did not have
a reliable fact check. Sometimes the generated number differed from the tool
result. Sometimes the model acted as if the returned data did not exist.

I wanted the path from tool data to final answer to be transparent and
traceable. GroundGuard registers key facts from tool calls in a local ledger,
then checks whether the final answer covers and cites those facts before it is
released.

GroundGuard is intentionally small. It is not a tracing dashboard and not an
LLM-as-judge. It adds one narrow gate before release: did the generated answer
actually match the facts your tools provided?

The current v0.1.1 release includes:
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
- If people ask whether it supports non-numeric claims, point them to the v0.1.1
  limit: numeric claims with units or magnitude markers only.
- If people ask for automatic fact extraction from arbitrary JSON, keep the v1
  boundary: explicit mapping first, optional extraction later.
