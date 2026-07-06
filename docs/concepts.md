# Concepts

## Ledger

The ledger is the evidence store. GroundGuard only treats facts explicitly
registered into the ledger as evidence.

## Output Claim

An output claim is a numeric claim extracted from generated text. Claims carry
text spans, offsets, normalized values, units, optional fact keys, and matching
status.

## Extractors

Extractors are deterministic functions that turn generated text into
`OutputClaim` objects. `register_extractor(...)` updates the process-global
registry and is best used during application startup.

For multi-tenant or concurrent services, pass request-scoped extractors instead:

```python
report = ledger.coverage_report(
    answer,
    extractors=registered_extractors() | {"domain": extract_domain_claims},
)
```

This keeps one tenant's extraction rules from changing another tenant's request
inside the same Python process.

## Required Fact

A required fact is a ledger key that the current answer must cover. This catches
the failure mode where a tool returned data but the model omitted it.

## Coverage Report

`CoverageReport` summarizes verified, candidate, unverified, contradicted,
ambiguous, and omitted claims. It also exposes `uncovered_numbers` so users can
see numeric-looking spans that were not covered by deterministic extractors.

## Policy

Policy decides whether to flag, strip, block, repair tagged contradictions, or
reask once.
