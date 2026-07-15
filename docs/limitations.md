# Limitations

GroundGuard is deliberately narrow.

- It does not trace full agent sessions.
- It does not judge semantic quality.
- It does not use a second LLM for v1 policy decisions.
- It does not require a database or hosted service.
- It does not guarantee that every number in free text can be extracted.
- It is an in-memory request/session ledger, not a cross-tenant fact store.
- The global extractor registry is process-wide; use scoped extractors for
  per-request or per-tenant customization.

Bare numbers without units are exposed through `uncovered_numbers`, but they are
not treated as verified claims by default. This avoids false positives while
making the extraction boundary visible.

## Deterministic Checker Boundaries

Checkers are synchronous and request-scoped. Callers construct the checker
tuple for an individual `FactGate.check(...)` call; GroundGuard does not keep a
global checker registry. Built-in checkers do not use a network, database, LLM,
or system wall-clock time.

`OrphanNumberChecker` consumes the existing `uncovered_numbers` transparency
output rather than performing another full numeric extraction or fact matcher.
`RelativeFreshnessChecker` compares only answer-referenced facts that share a
caller-supplied fact group and `subject`. Missing or invalid `as_of` dates are
skipped. It does not infer trading days, query a calendar, or calculate
freshness from the current time.

An `Issue` is diagnostic data. A hard issue changes the GroundGuard report to
`passed=false`; a soft issue leaves the report's prior pass/fail result alone.
Consumers choose their own handling after reading the report.

## finance_cn Scope

`groundguard.rules.finance_cn` is an explicit import, never a default core
dependency. Its first release supports only SSE and SZSE market context supplied
by the caller. It recognizes the `main`, `star`, and `chinext` board labels and
the `normal`, `ipo_first_five_days`, `relisting_first_day`, and
`delisting_first_day` listing-phase labels.

The normal-phase price-limit table is effective from 2026-07-06:

| Exchange | Board | Normal-phase limit |
| --- | --- | --- |
| SSE | main | 10% |
| SSE | star | 20% |
| SZSE | main | 10% |
| SZSE | chinext | 20% |

The normal-phase check is skipped for the IPO first five trading days,
relisting first day, and delisting first day. It also skips when required
structured context is missing. BSE is reported as unsupported and is never
treated as a 20% market. Hong Kong, US, and other markets are outside this
package's scope.

Price checks use an explicit local tolerance so a caller can avoid reporting
tiny representation differences. That tolerance is a GroundGuard sanity margin,
not an exchange price-tick rounding implementation or a claim of exact trading
eligibility.

Official references used for the table:

- [Shanghai Stock Exchange Trading Rules (2026 revision, effective 2026-07-06)](https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml)
- [Shenzhen Stock Exchange Trading Rules (2026 revision)](https://docs.static.szse.cn/www/lawrules/rule/trade/W020260424690713155663.pdf)
- [SZSE ChiNext risk disclosure clauses (2026 revision)](https://docs.static.szse.cn/www/lawrules/service/member/W020260424702381159118.pdf)
- [Beijing Stock Exchange reference, excluded from this scope](https://www.bse.cn/jygl_list/200028217.html)
