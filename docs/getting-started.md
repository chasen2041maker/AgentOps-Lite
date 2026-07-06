# Getting Started

## Install

Current release:

```bash
python -m pip install "git+https://github.com/chasen2041maker/GroundGuard.git@v0.2.1"
```

Development install:

```bash
git clone https://github.com/chasen2041maker/GroundGuard.git
cd GroundGuard
python -m pip install -e ".[dev]"
python -m pytest
```

## Run the Demo

```bash
groundguard-demo
```

Expected signal:

```text
Before GroundGuard correction: passed False, omitted_required 2
After fact-key correction: passed True, verified 2
```

Run the packaged benchmark:

```bash
groundguard-benchmark
```

## Use a Config File

```yaml
required_facts:
  - revenue_2025
  - net_profit_2025
policy:
  on_unverified: block
  max_unverified_ratio: 0.0
report:
  schema: assertion
  fail_on_policy: true
```

```bash
groundguard-report \
  --config groundguard.yml \
  --ledger-jsonl facts.jsonl \
  --answer-file answer.txt
```
