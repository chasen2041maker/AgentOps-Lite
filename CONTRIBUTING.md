# Contributing to GroundGuard

GroundGuard is intentionally small: a local-first fact gate for tool-using AI
agents. Contributions are welcome when they make that core loop more reliable,
easier to adopt, or easier to test.

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest
```

On macOS or Linux, replace the Python path with `python -m pytest` after
activating your virtual environment.

## Scope Rules

GroundGuard v1 should stay deterministic and local-first.

- Keep runtime dependencies empty unless there is a strong reason.
- Do not add hosted services, databases, vector stores, or dashboards to the core.
- Do not use LLM-as-judge for v1 policy decisions.
- Prefer explicit fact registration over automatic JSON guessing.
- Treat candidate numeric matches as debugging hints, not verified facts.

## Tests

Every behavior change should include tests. The core suite is:

```powershell
.venv\Scripts\python.exe -B -m pytest
git diff --check
```

When adding matching, extraction, or policy behavior, include both a positive
case and a failure or boundary case.

## Sensitive Data

Examples and fixtures must be synthetic or clearly anonymized. Do not commit
company-internal names, prompts, tool payloads, customer data, or proprietary
implementation details.

## Pull Requests

Please keep pull requests focused. A good PR usually changes one of these:

- core ledger/extraction/matching/policy behavior
- adapter ergonomics
- CLI/CI integration
- documentation or examples

For larger changes, open an issue first with the proposed API and a small
example of the failure mode it addresses.
