# Concepts

## Ledger

The ledger is the evidence store. GroundGuard only treats facts explicitly
registered into the ledger as evidence.

## Output Claim

An output claim is a numeric claim extracted from generated text. Claims carry
text spans, offsets, normalized values, units, optional fact keys, and matching
status.

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

