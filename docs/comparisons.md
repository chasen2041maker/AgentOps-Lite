# Comparisons

GroundGuard is intentionally narrow. It is not trying to replace broad eval,
observability, or guardrail platforms. Use it when your tools already returned
facts and the final answer must not rewrite, omit, or invent them.

## Quick Positioning

| Tool category | Use it when you need | Where GroundGuard fits |
| --- | --- | --- |
| Langfuse / Phoenix | Tracing, observability, spans, prompts, datasets, and team review workflows. | Export GroundGuard reports as deterministic fact-gate events or eval payloads. |
| DeepEval | Broad LLM quality metrics, RAG metrics, agent metrics, and LLM-as-judge workflows. | Add a deterministic assertion for tool-returned facts before or beside semantic metrics. |
| promptfoo | Prompt/model eval suites, red teaming, regression suites, and CI eval configs. | Use GroundGuard output as an assertion payload when tool facts must be covered. |
| Guardrails | General input/output validation, structured output checks, and validator chains. | Use GroundGuard for the narrower ledger-vs-answer numeric fact check. |
| LLM-as-judge | Subjective quality, semantic faithfulness, summarization, tone, or broad reasoning checks. | Avoid a second LLM when the expected facts are already in your tool results. |

## When To Use GroundGuard

Use GroundGuard when all of these are true:

- Your application calls tools, APIs, databases, or retrieval steps before the
  final answer.
- Some returned values are important enough to record explicitly.
- The final answer must not change, omit, or invent those values.
- You want a deterministic local check with no hosted service, database, or
  second LLM judge.

## When Not To Use GroundGuard

Do not use GroundGuard as the only layer when you need:

- Full tracing, prompt management, or observability.
- General hallucination detection for facts that were never recorded.
- Broad semantic scoring, style evaluation, or safety moderation.
- Token-level constrained decoding or structured output generation.

The practical pattern is to pair GroundGuard with the rest of your stack:

```text
Tool call / database / RAG result
  -> record facts in GroundGuard
  -> generate final answer
  -> GroundGuard fact gate
  -> optional Langfuse/Phoenix/promptfoo/DeepEval reporting
```
