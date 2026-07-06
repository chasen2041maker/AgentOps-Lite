# GroundGuard Benchmark

This tiny benchmark is intentionally modest. It is not a leaderboard; it is a
reproducible smoke test for GroundGuard's core claim:

- catch required facts that the model omitted,
- catch tagged numeric contradictions,
- catch unregistered numeric claims when the policy blocks unverified numbers,
- avoid failing a fully verified answer.

Run it locally:

```bash
groundguard-benchmark
```
