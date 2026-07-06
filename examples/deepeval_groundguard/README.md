# DeepEval + GroundGuard

Run a dependency-free example that emits a DeepEval-friendly metric result:

```bash
python examples/deepeval_groundguard/run.py
```

The helper intentionally does not import DeepEval. It returns `success`,
`score`, `reason`, `metadata`, and `componentResults` so teams can wrap it in
their own DeepEval metric without adding a hard dependency to GroundGuard.

