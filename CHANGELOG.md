# Changelog

All notable changes to GroundGuard will be documented in this file.

## Unreleased

### Added

- Expanded `groundguard-benchmark` from 4 smoke cases to 25 deterministic cases
  covering verified claims, omissions, contradictions, candidate matches,
  ambiguous matches, bare-number extraction limits, and invented numbers.
- `examples/openai_demo/run.py` now shows a blocked answer followed by a
  fact-key-corrected answer, with live OpenAI SDK support still optional.
- Added `groundguard/py.typed` and Python 3.13 CI coverage.

### Changed

- Updated launch and project-plan docs from old `v0.1.1` cold-start language to
  current `v0.2.x` language.
- Documented the exact PyPI Trusted Publisher values needed to publish from
  GitHub Actions.

## v0.2.2 - 2026-07-06

### Fixed

- Explicit `[fact:key]` matching now uses the latest registered fact for a key
  instead of the first one, avoiding false contradictions after tool retries or
  refreshed data.

### Added

- Request-scoped extractor support for `extract_output_claims(...)` and
  `Ledger.coverage_report(...)`, so multi-tenant services can use custom
  extractors without mutating process-global state.
- Regression tests for repeated fact-key updates, scoped extractor isolation,
  and module-level duplicate definitions.

### Changed

- `Ledger` now guards its in-memory fact list and key index with a re-entrant
  lock for safer parallel tool-call registration inside one session.
- Matcher numeric buckets are sorted and searched with `bisect` before final
  tolerance filtering.
- Removed shadowed duplicate implementations from `units.py` and
  `output_claim_extractor.py`.
- README and docs now document process-global extractor registration versus
  request-scoped extractor usage.

### Verified

```text
python -m pytest
```

## v0.2.1 - 2026-07-06

### Added

- Packaged `groundguard-demo` command for an install-and-run before/after demo.
- Packaged `groundguard-benchmark` command for deterministic fact-gate smoke
  metrics.
- `groundguard.example.yml` plus CLI `--config` documentation for repeatable CI
  and eval runs.
- Composite GitHub Action `config` input for using the same GroundGuard config
  file in CI.
- MkDocs documentation scaffold with getting started, concepts, CLI/config,
  integrations, benchmark, limitations, and publishing pages.
- PyPI Trusted Publishing workflow scaffold and GitHub Pages documentation
  workflow.
- Security policy, code of conduct, and issue template configuration.
- Runnable promptfoo and DeepEval integration examples.

### Changed

- README, Chinese README, and docs now point to `v0.2.1` and lead with
  installable commands instead of repository-only scripts.
- Package discovery now includes the benchmark package so the benchmark command
  works after installation.

### Verified

```text
python -m pytest
```

## v0.2.0 - 2026-07-06

### Added

- Coverage transparency fields on `CoverageReport`: `suspected_numbers`,
  `uncovered_numbers`, and `extraction_coverage`.
- Pluggable output-claim extractor registry with `register_extractor(...)`,
  `unregister_extractor(...)`, and `registered_extractors()`.
- `Policy(on_contradicted="fix")` to repair tagged contradictions from ledger
  `Fact.display_value`.
- `Policy(on_contradicted="reask")` to ask the supplied `llm_call` for one
  corrected rewrite when contradictions are detected.
- promptfoo and DeepEval helper adapters under `groundguard.integrations`.
- Per-claim `componentResults` in assertion JSON.
- Ledger key index and matcher fact buckets for lower-cost lookups at larger
  fact counts.

### Changed

- README and Chinese README now document uncovered-number transparency,
  pluggable extractors, fix/reask policy behavior, and dedicated eval adapters.
- Installation and GitHub Action examples now point to `v0.2.0`.

### Verified

```text
python -m pytest
68 passed
```

## v0.1.4 - 2026-07-06

### Added

- `OutputClaim.start` and `OutputClaim.end` offsets for precise downstream
  highlighting and text operations.
- `REFACTOR.md` roadmap, reviewed against the current codebase and committed as
  the living refactor plan.

### Changed

- Unverified-claim stripping now prefers span offsets and falls back to
  `text_span` search only when offsets are unavailable.
- Assertion JSON claim objects now expose `start` and `end` offsets.
- Installation and GitHub Action examples now point to `v0.1.4`.

### Verified

```text
python -m pytest
59 passed
```

## v0.1.3 - 2026-07-06

### Added

- README hero demo GIF plus a reproducible PowerShell renderer for regenerating
  it locally with ffmpeg.
- Shared numeric unit normalization for registered facts and matched claims,
  including CNY magnitude units such as `亿元` and `万元`.
- `ambiguous` claim status when multiple unkeyed facts match within tolerance.
- Top-level per-claim details in assertion JSON for downstream highlighting.

### Changed

- Financial report demo output now colorizes failed and passing gate states for
  recordings and terminal demos.
- English extraction coverage now includes compact magnitudes and percentages
  such as `1.2M`, `3,830 million dollars`, and `21.5 percent`.
- `on_unverified="strip"` now fails reports until unverified claims are actually
  removed, keeping policy behavior in one place.
- Installation and GitHub Action examples now point to `v0.1.3`.

## v0.1.2 - 2026-07-06

### Added

- English USD amount extraction for common agent outputs, including
  `$3.83 billion`, `USD 10.25M`, and `2.5 million dollars`.
- Regression tests for English currency prefixes, short magnitudes, and dollar
  suffixes.

### Changed

- README and Chinese README now state the concrete failure scenario more
  directly and document English amount support.
- Architecture docs now describe the current extraction boundary with both
  Chinese and English examples.

### Verified

```text
python -m pytest
50 passed
```

## v0.1.1 - 2026-07-06

### Added

- Framework-free `@grounded(...)` decorator for plain Python functions.
- Assertion-style CLI schema with `pass`, `success`, `score`, `reason`,
  `namedScores`, and `metadata.groundguard` fields.
- Runnable decorator, LangGraph-style node, and native OpenAI SDK examples.
- Composite `action.yml` for GitHub Actions fact gates.
- PR coverage comment workflow example and launch kit.
- GroundGuard logo, icon, and brand board assets.

### Changed

- README and Chinese README now lead with the before/after demo, comparison
  table, CI usage, and current project boundaries.
- README and launch copy now include the author's real workflow motivation.
- README now includes a plain-language "bookkeeping + reconciliation" explanation
  for new readers.
- Release references now point to `v0.1.1`, where the GitHub Action and latest
  examples actually exist.

### Verified

```text
python -m pytest
47 passed
```

## v0.1.0 - 2026-07-06

GroundGuard v0.1.0 is the first runnable pre-alpha release: a local-first fact
gate for tool-using AI agents. It checks the final answer before release so
important numeric claims can trace back to explicitly registered tool facts, and
required facts returned by tools are not silently omitted.

### Added

- In-memory `Ledger` with TTL filtering and JSONL persistence.
- Explicit `tool_call(...).record_facts(...)` fact registration.
- Deterministic numeric claim extraction with `[fact:key]` support.
- Claim matching with `verified`, `candidate_match`, `unverified`, and
  `contradicted` states.
- Coverage reports for output claims and required fact omissions.
- Policy evaluation with block, flag, and strip behavior.
- `grounded_generate()` wrapper with optional `GroundedResult` reports.
- CLI JSON reporting through `groundguard-report`.
- Minimal OpenAI-compatible callable wrapper.
- Minimal LangChain-compatible callback handler with explicit fact mapping.
- Financial report demo showing omitted required facts before correction.
- English and Simplified Chinese README files.

### Verified

```text
python -m pytest
39 passed
```

```text
python examples/financial_report_demo/run.py

Before GroundGuard correction
-----------------------------
passed: False
verified: 0
unverified: 0
contradicted: 0
omitted_required: 2
policy_reason: omitted_required_count=2 > max_omitted_required=0

After fact-key correction
-------------------------
passed: True
verified: 2
unverified: 0
contradicted: 0
omitted_required: 0
```

### Not Included

- No tracing dashboard.
- No LLM-as-judge evaluator.
- No database-backed observability platform.
- No token-level generation control.
