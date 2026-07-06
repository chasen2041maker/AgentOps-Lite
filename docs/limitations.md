# Limitations

GroundGuard is deliberately narrow.

- It does not trace full agent sessions.
- It does not judge semantic quality.
- It does not use a second LLM for v1 policy decisions.
- It does not require a database or hosted service.
- It does not guarantee that every number in free text can be extracted.

Bare numbers without units are exposed through `uncovered_numbers`, but they are
not treated as verified claims by default. This avoids false positives while
making the extraction boundary visible.

