"""Compare explicitly grouped, answer-referenced facts without wall-clock time."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from groundguard.core.checker import CheckRequest
from groundguard.core.models import Fact, Issue, OutputClaim


class RelativeFreshnessChecker:
    """Flag an answer that cites an older fact than a known peer in its group."""

    name = "relative_freshness"

    def __init__(self, *, fact_groups: Mapping[str, str]) -> None:
        self._fact_groups = dict(fact_groups)

    def check(self, request: CheckRequest) -> Sequence[Issue]:
        facts_by_id = {fact.id: fact for fact in request.facts}
        latest_facts = self._latest_facts_by_subject_and_group(request.facts)
        issues: list[Issue] = []
        seen_fact_ids: set[str] = set()
        for claim in request.claims:
            fact = self._referenced_fact(claim, facts_by_id)
            if fact is None or fact.id in seen_fact_ids:
                continue
            seen_fact_ids.add(fact.id)
            group = self._fact_groups.get(fact.key)
            fact_date = _parse_as_of(fact.as_of)
            if not group or not fact.subject or fact_date is None:
                continue
            latest = latest_facts.get((fact.subject, group))
            if latest is None:
                continue
            latest_fact, latest_date = latest
            if fact_date >= latest_date:
                continue
            issues.append(
                Issue(
                    code="relative_stale_fact",
                    severity="soft",
                    message="Answer references an older fact than an available fact in the same group.",
                    checker=self.name,
                    related_fact_keys=(fact.key, latest_fact.key),
                    related_claim_ids=(claim.id,),
                    text_span=claim.text_span,
                    start=claim.start,
                    end=claim.end,
                    details={
                        "subject": fact.subject,
                        "fact_group": group,
                        "referenced_as_of": fact.as_of,
                        "latest_as_of": latest_fact.as_of,
                    },
                )
            )
        return tuple(issues)

    def _latest_facts_by_subject_and_group(
        self,
        facts: Sequence[Fact],
    ) -> dict[tuple[str, str], tuple[Fact, date]]:
        latest: dict[tuple[str, str], tuple[Fact, date]] = {}
        for fact in facts:
            group = self._fact_groups.get(fact.key)
            fact_date = _parse_as_of(fact.as_of)
            if not group or not fact.subject or fact_date is None:
                continue
            key = (fact.subject, group)
            existing = latest.get(key)
            if existing is None or fact_date > existing[1]:
                latest[key] = (fact, fact_date)
        return latest

    @staticmethod
    def _referenced_fact(
        claim: OutputClaim,
        facts_by_id: Mapping[str, Fact],
    ) -> Fact | None:
        if claim.status not in {"verified", "candidate_match"}:
            return None
        if claim.matched_fact_id is None:
            return None
        return facts_by_id.get(claim.matched_fact_id)


def _parse_as_of(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
