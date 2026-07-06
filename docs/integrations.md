# Integrations

## GitHub Actions

```yaml
- name: Run GroundGuard
  uses: chasen2041maker/GroundGuard@v0.2.2
  with:
    ledger-jsonl: groundguard-ledger.jsonl
    answer-file: answer.txt
    config: groundguard.yml
    required-facts: revenue_2025,net_profit_2025
    schema: assertion
    fail-on-policy: "true"
```

## promptfoo

```bash
python examples/promptfoo_groundguard/run.py
```

The example emits promptfoo-style assertion JSON with `pass`, `score`,
`reason`, `claims`, and `componentResults`.

## DeepEval

```bash
python examples/deepeval_groundguard/run.py
```

The helper returns a DeepEval-friendly metric result without requiring DeepEval
as a hard runtime dependency.
