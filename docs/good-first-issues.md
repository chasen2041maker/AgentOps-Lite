# Good First Issues

These are intentionally small contribution ideas that preserve GroundGuard's
boundaries: local-first, no database, and no second LLM judge in the default
path.

## Extractors

1. Add deterministic range percentage extraction for spans like `10-15%`.
2. Add tests for accounting-style negative numbers such as `($3.2M)` and `(3.2M)`.
3. Add Markdown table extraction fixtures for finance and SaaS metrics.
4. Improve basis-point versus percentage-point examples and tests.

## Integrations

5. Add an Anthropic tool-use recipe that records returned tool facts explicitly.
6. Add a LlamaIndex query-engine recipe that checks generated answers after retrieval.
7. Add a PydanticAI recipe showing `FactGate` in an agent result validator.
8. Add an MCP server/client recipe that sends GroundGuard reports over the minimal HTTP gateway.

## Reports And CI

9. Add a golden fixture test for `groundguard-report --format github`.
10. Add a small screenshot-ready PR comment example that shows a contradicted claim.

When opening an issue, include the smallest expected API or fixture first. Good
GroundGuard contributions are narrow, deterministic, and easy to test.
