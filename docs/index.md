# GroundGuard

GroundGuard provides deterministic assertions for AI agent answers. It checks
whether the final answer uses the facts that tools already returned, without
calling a second LLM judge.

The core loop is small:

1. Register tool facts in a local `Ledger`.
2. Extract numeric claims from the final answer.
3. Match claims against the ledger.
4. Apply a policy before the answer is released.

GroundGuard is not a tracing dashboard, hosted observability service, or
LLM-as-judge evaluator. It is the narrow gate that catches "the tool had the
number, but the model ignored or rewrote it."

## Start Here

```python
from groundguard import FactGate

gate = FactGate()
gate.record_tool_result("q3_revenue", "5.2", "billion_usd")
report = gate.check("Q3 revenue came in at $4.8 billion [fact:q3_revenue].", required=["q3_revenue"])
print(report.output_claims[0].status)  # contradicted
```

```bash
python -m pip install groundguard-ai
groundguard-init --template github-action
groundguard-demo
groundguard-benchmark
```

The PyPI distribution name is `groundguard-ai`; the Python import name remains
`groundguard`.
