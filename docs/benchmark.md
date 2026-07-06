# Benchmark

GroundGuard includes deterministic benchmarks. They are designed to be
reproducible, not a leaderboard.

```bash
groundguard-benchmark
```

The packaged command runs two suites:

- a 25-case smoke suite for the core fact-gate contract,
- a 200-case bilingual realistic dataset.

Together they cover:

- fully verified answers,
- English and Chinese outputs,
- USD, EUR, GBP, CNY, percentages, basis points, and common business units,
- users, customers, requests, orders, tickets, incidents, latency, storage,
- omitted required facts,
- contradicted tagged facts,
- candidate matches,
- ambiguous matches,
- bare-number extraction limits,
- invented unregistered numbers under a blocking unverified policy.

Current expected result:

```text
smoke.cases_total: 25
smoke.expected_failures: 14
smoke.detected_failures: 14
smoke.false_positives: 0
realistic_dataset.cases_total: 200
realistic_dataset.expected_failures: 71
realistic_dataset.detected_failures: 71
realistic_dataset.false_positives: 0
realistic_dataset.false_negatives: 0
```
