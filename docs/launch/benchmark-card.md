# Benchmark Card

Use this as the source text for a screenshot, terminal card, or image post.

## Command

```bash
python -m pip install groundguard-ai
groundguard-benchmark
```

## Card Copy

```text
GroundGuard benchmark

200 bilingual realistic cases
71/71 expected failures caught
0 false positives
0 false negatives

No LLM judge. Local deterministic checks.
```

## Terminal Output To Capture

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

## Visual Rule

Keep the image focused on the claim. Do not show the whole README. The strongest
frame is the command at the top and the `71/71` line in the center.
