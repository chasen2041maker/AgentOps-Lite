# CLI and Config

## Generate a Report

```bash
groundguard-report \
  --ledger-jsonl facts.jsonl \
  --answer-file answer.txt \
  --required-fact revenue_2025 \
  --schema assertion \
  --fail-on-policy
```

## Use `groundguard.yml`

Start from the repository sample:

```bash
cp groundguard.example.yml groundguard.yml
```

```yaml
required_facts:
  - revenue_2025
policy:
  allow_candidate_matches: false
  on_contradicted: block
  on_unverified: flag
report:
  schema: assertion
  fail_on_policy: true
```

```bash
groundguard-report --config groundguard.yml --ledger-jsonl facts.jsonl --answer-file answer.txt
```

CLI flags extend or override the config where appropriate. For example,
additional `--required-fact` values are appended to `required_facts`.
