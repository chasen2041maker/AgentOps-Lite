# GroundGuard

GroundGuard is a deterministic, local-first fact gate for tool-using AI agents.
It checks whether the final answer uses the facts that tools already returned.

The core loop is small:

1. Register tool facts in a local `Ledger`.
2. Extract numeric claims from the final answer.
3. Match claims against the ledger.
4. Apply a policy before the answer is released.

GroundGuard is not a tracing dashboard, hosted observability service, or
LLM-as-judge evaluator. It is the narrow gate that catches "the tool had the
number, but the model ignored or rewrote it."

## Start Here

```bash
python -m pip install "git+https://github.com/chasen2041maker/GroundGuard.git@v0.2.1"
groundguard-demo
groundguard-benchmark
```

PyPI publishing is prepared through GitHub Trusted Publishing. Until the PyPI
project is claimed, install from the GitHub tag.
