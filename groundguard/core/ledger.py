from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, replace
from decimal import Decimal
from pathlib import Path
from typing import Callable

from groundguard.core.models import CoverageReport, Fact, RequiredFact
from groundguard.core.output_claim_extractor import ExtractorCollection
from groundguard.core.policy import Policy


Clock = Callable[[], float]


class Ledger:
    """In-memory store for explicitly registered facts.

    A Ledger is intended to be scoped to one request/session/tenant. Its in-memory
    indexes are protected by a re-entrant lock so parallel tool calls can record
    facts without corrupting the local snapshot.
    """

    def __init__(self, session_id: str, clock: Clock | None = None) -> None:
        self.session_id = session_id
        self._clock = clock or time.time
        self._facts: list[Fact] = []
        self._facts_by_key: dict[str, list[Fact]] = {}
        self._lock = threading.RLock()

    def __enter__(self) -> Ledger:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def register_fact(self, fact: Fact) -> None:
        recorded = fact
        if fact.recorded_at == 0.0:
            recorded = replace(fact, recorded_at=self._clock())
        with self._lock:
            self._append_fact(recorded)

    def query(self, key: str) -> list[Fact]:
        now = self._clock()
        with self._lock:
            return [
                fact
                for fact in self._facts_by_key.get(key, [])
                if not self._is_expired(fact, now)
            ]

    def all_facts(self, exclude_expired: bool = True) -> list[Fact]:
        now = self._clock()
        with self._lock:
            if not exclude_expired:
                return list(self._facts)
            return [fact for fact in self._facts if not self._is_expired(fact, now)]

    def to_jsonl(self, path: str | Path) -> None:
        output_path = Path(path)
        facts = self.all_facts(exclude_expired=False)
        with output_path.open("w", encoding="utf-8") as handle:
            for fact in facts:
                handle.write(json.dumps(_fact_to_jsonable(fact), ensure_ascii=False))
                handle.write("\n")

    @classmethod
    def from_jsonl(
        cls,
        path: str | Path,
        session_id: str,
        clock: Clock | None = None,
    ) -> Ledger:
        ledger = cls(session_id=session_id, clock=clock)
        input_path = Path(path)
        with input_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    ledger._append_fact(_fact_from_jsonable(json.loads(line)))
        return ledger

    def coverage_report(
        self,
        answer: str,
        required_fact_keys: list[str] | None = None,
        policy: Policy | None = None,
        extractors: ExtractorCollection | None = None,
        tolerance: float = 0.005,
    ) -> CoverageReport:
        from groundguard.core.coverage import build_coverage_report
        from groundguard.core.matcher import match_claims
        from groundguard.core.output_claim_extractor import (
            extract_output_claims,
            find_suspected_numbers,
        )
        from groundguard.core.policy import evaluate_policy

        active_policy = policy or Policy()
        facts = self.all_facts()
        extracted_claims = extract_output_claims(answer, extractors=extractors)
        output_claims = match_claims(extracted_claims, facts, tolerance=tolerance)
        suspected_numbers = find_suspected_numbers(answer, extracted_claims)
        required_facts = [
            RequiredFact(key=key) for key in (required_fact_keys or [])
        ]
        report = build_coverage_report(
            session_id=self.session_id,
            output_claims=output_claims,
            required_facts=required_facts,
            facts=facts,
            allow_candidate_matches=active_policy.allow_candidate_matches,
            suspected_numbers=suspected_numbers,
        )
        return evaluate_policy(report, active_policy)

    def _append_fact(self, fact: Fact) -> None:
        self._facts.append(fact)
        self._facts_by_key.setdefault(fact.key, []).append(fact)

    @staticmethod
    def _is_expired(fact: Fact, now: float) -> bool:
        if fact.ttl_seconds is None:
            return False
        return fact.recorded_at + fact.ttl_seconds < now


def _fact_to_jsonable(fact: Fact) -> dict[str, object]:
    payload = asdict(fact)
    payload["value"] = _value_to_jsonable(fact.value)
    return payload


def _fact_from_jsonable(payload: dict[str, object]) -> Fact:
    value = payload["value"]
    if isinstance(value, dict) and value.get("__type__") == "Decimal":
        value = Decimal(str(value["value"]))
    return Fact(
        id=str(payload["id"]),
        source_tool=str(payload["source_tool"]),
        source_call_id=str(payload["source_call_id"]),
        key=str(payload["key"]),
        value=value if isinstance(value, Decimal) else str(value),
        value_kind=payload.get("value_kind", "numeric"),  # type: ignore[arg-type]
        unit=_optional_str(payload.get("unit")),
        display_value=_optional_str(payload.get("display_value")),
        raw=payload.get("raw"),
        recorded_at=float(payload.get("recorded_at", 0.0)),
        ttl_seconds=_optional_int(payload.get("ttl_seconds")),
        confidence=float(payload.get("confidence", 1.0)),
        metadata=_dict_or_empty(payload.get("metadata")),
        schema_version=int(payload.get("schema_version", 1)),
    )


def _value_to_jsonable(value: Decimal | str) -> object:
    if isinstance(value, Decimal):
        return {"__type__": "Decimal", "value": str(value)}
    return value


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _dict_or_empty(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}
