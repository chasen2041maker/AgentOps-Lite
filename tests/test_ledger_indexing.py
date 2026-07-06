from decimal import Decimal
from pathlib import Path
from uuid import uuid4


def test_ledger_maintains_key_index_for_registered_and_loaded_facts():
    from groundguard import Fact, Ledger

    ledger = Ledger(session_id="req_001", clock=lambda: 10.0)
    ledger.register_fact(
        Fact(
            id="fact_old",
            source_tool="tool",
            source_call_id="call_1",
            key="revenue_2025",
            value=Decimal("1"),
            unit="USD",
            recorded_at=1.0,
            ttl_seconds=1,
        )
    )
    ledger.register_fact(
        Fact(
            id="fact_current",
            source_tool="tool",
            source_call_id="call_2",
            key="revenue_2025",
            value=Decimal("2"),
            unit="USD",
            recorded_at=10.0,
            ttl_seconds=10,
        )
    )

    assert list(ledger._facts_by_key) == ["revenue_2025"]
    assert [fact.id for fact in ledger.query("revenue_2025")] == ["fact_current"]

    path = Path(".tmp") / f"facts-index-{uuid4().hex}.jsonl"
    path.parent.mkdir(exist_ok=True)
    ledger.to_jsonl(path)
    loaded = Ledger.from_jsonl(path, session_id="req_001", clock=lambda: 10.0)

    assert list(loaded._facts_by_key) == ["revenue_2025"]
    assert [fact.id for fact in loaded.query("revenue_2025")] == ["fact_current"]

