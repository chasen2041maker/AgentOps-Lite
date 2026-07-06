# GroundGuard Benchmark

This small benchmark is intentionally modest. It is not a leaderboard; it is a
reproducible check for GroundGuard's core claim:

- catch required facts that the model omitted,
- catch tagged numeric contradictions,
- catch ambiguous numeric matches,
- catch unregistered numeric claims when the policy blocks unverified numbers,
- avoid failing a fully verified answer.

Run it locally:

```bash
groundguard-benchmark
```
