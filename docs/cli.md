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
units:
  tolerance: 0.005
report:
  schema: assertion
  format: json
  fail_on_policy: true
```

```bash
groundguard-report --config groundguard.yml --ledger-jsonl facts.jsonl --answer-file answer.txt
```

CLI flags extend or override the config where appropriate. For example,
additional `--required-fact` values are appended to `required_facts`.

## Render Human Reports

```bash
groundguard-report \
  --config groundguard.yml \
  --ledger-jsonl facts.jsonl \
  --answer-file answer.txt \
  --format markdown \
  --output groundguard-report.md
```

Supported formats are `json`, `markdown`, `html`, and `github`. The `github`
format is a compact Markdown body designed for PR comments.

Reports include `matched_fact_key`, `ledger_value`, `answer_value`, and
`start:end` spans for claim highlighting and review UIs.

## Scoped Extractor Packs

```yaml
extractors:
  packs:
    - finance
    - saas
    - ops
```

Extractor packs are resolved per report run. They do not mutate the global
process registry, so they are safe to use in multi-tenant services.

Built-in packs cover common labels for finance (`revenue`, `gross_margin`,
`eps`), SaaS (`arr`, `mrr`, `churn`, `nrr`, `cac`, `ltv`), ecommerce (`gmv`,
`orders`, `conversion_rate`, `aov`), and ops (`p95_latency`, `error_rate`,
`uptime`, `throughput`, `storage`).
