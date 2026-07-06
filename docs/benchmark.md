# Benchmark

GroundGuard includes a small deterministic benchmark. It is designed to be
reproducible, not a leaderboard.

```bash
groundguard-benchmark
```

The benchmark checks 25 cases:

- fully verified answers,
- omitted required facts,
- contradicted tagged facts,
- candidate matches,
- ambiguous matches,
- bare-number extraction limits,
- invented unregistered numbers under a blocking unverified policy.

Current expected result:

```text
cases_total: 25
expected_failures: 14
detected_failures: 14
false_positives: 0
```
