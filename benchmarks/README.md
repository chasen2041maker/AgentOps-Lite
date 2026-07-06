# GroundGuard Benchmark

This benchmark is intentionally deterministic. It is not a leaderboard; it is a
reproducible check for GroundGuard's core claim:

- catch required facts that the model omitted,
- catch tagged numeric contradictions,
- catch ambiguous numeric matches,
- catch unregistered numeric claims when the policy blocks unverified numbers,
- avoid failing a fully verified answer.

It contains a 25-case smoke suite plus a 200-case bilingual realistic JSONL
dataset covering English and Chinese outputs, currencies, percentages, basis
points, business counts, latency, storage units, omissions, contradictions, and
candidate-match behavior.

Run it locally:

```bash
groundguard-benchmark
```
