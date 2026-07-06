# Benchmark

GroundGuard includes a small deterministic benchmark. It is designed to be
reproducible, not broad.

```bash
groundguard-benchmark
```

The benchmark checks four cases:

- fully verified answer,
- omitted required fact,
- contradicted tagged fact,
- invented unregistered number under a blocking unverified policy.

Current expected result:

```text
cases_total: 4
expected_failures: 3
detected_failures: 3
false_positives: 0
```
