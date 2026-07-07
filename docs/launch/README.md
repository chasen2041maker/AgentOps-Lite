# GroundGuard Launch Kit

This is a lightweight launch checklist for the first public distribution pass.
It keeps the message focused on a falsifiable claim: GroundGuard catches agent
answers whose numeric claims do not match the facts recorded from tool calls,
without calling a second LLM judge.

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

## Proof Point

Use the bundled benchmark as the launch claim:

```text
GroundGuard catches 71/71 expected failures in a 200-case bilingual realistic
dataset, with 0 false positives and 0 false negatives, without LLM judging.
```

To reproduce:

```bash
python -m pip install groundguard-ai
groundguard-benchmark
```

The benchmark covers English and Chinese outputs, currencies, percentages,
basis points, users, orders, tickets, latency, storage units, candidate matches,
omitted required facts, contradictions, ambiguity, and bare-number limits.

## Headline Options

```text
Show HN: Assertions for AI agent answers, without an LLM judge
```

```text
Show HN: GroundGuard catches when an AI agent rewrites tool numbers
```

```text
AI agents can ignore the numbers they just fetched. I built a local fact gate.
```

## Show HN Draft

```text
Show HN: Assertions for AI agent answers, without an LLM judge

I built GroundGuard after seeing a recurring failure in my own workflow:
tools returned the numbers I needed, but the model's final answer did not have
a reliable fact check. Sometimes the generated number differed from the tool
result. Sometimes the model acted as if the returned data did not exist.

I wanted the path from tool data to final answer to be transparent and
traceable. GroundGuard registers key facts from tool calls in a local ledger,
then checks whether the final answer covers and cites those facts before it is
released.

GroundGuard is intentionally small. It is not a tracing dashboard, not a hosted
observability platform, and not an LLM-as-judge. It adds one narrow gate before
release: did the generated answer actually match the facts your tools provided?

The current v0.3.0 release includes:
- in-memory Ledger + JSONL persistence
- a high-level FactGate API
- explicit tool_call(...).record_facts(...) registration
- deterministic numeric claim extraction with Chinese and English units
- built-in finance, SaaS, ecommerce, and ops extractor packs
- omitted-required-fact detection
- CLI JSON, Markdown, HTML, GitHub comment, and assertion-style reports
- OpenAI, LangChain, LangGraph, promptfoo, DeepEval, Langfuse, and Phoenix helpers
- scoped extractor registration, fix/reask strategies, and extraction coverage
- a reusable GitHub Action

The bundled benchmark is small but reproducible:

200 bilingual realistic cases
71 expected failures
71 detected failures
0 false positives
0 false negatives

The core demo is the simplest failure mode:

Before: passed=False, omitted_required=2
After:  passed=True, verified=2

Repo: https://github.com/chasen2041maker/GroundGuard
```

## Feedback To Watch

- If people ask how this differs from Langfuse, Phoenix, promptfoo, or DeepEval,
  sharpen the README comparison table.
- If people ask whether it supports non-numeric claims, point them to the v0.3.0
  limit: numeric claims with units or magnitude markers only.
- If people ask for automatic fact extraction from arbitrary JSON, keep the v1
  boundary: explicit mapping first, optional extraction later.
