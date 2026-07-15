from __future__ import annotations

from decimal import Decimal
from pathlib import Path


def test_finance_context_reads_only_explicit_supported_fields() -> None:
    from groundguard.rules.finance_cn import FinanceCNContext

    context = FinanceCNContext.from_mapping(
        {
            "finance_cn": {
                "exchange": "SSE",
                "board": "main",
                "listing_phase": "normal",
                "trade_date": "2026-07-15",
                "previous_close": "10.00",
                "security_name": "Synthetic Co.",
            }
        }
    )

    assert context.exchange == "SSE"
    assert context.board == "main"
    assert context.listing_phase == "normal"
    assert context.trade_date.isoformat() == "2026-07-15"
    assert context.previous_close == Decimal("10.00")


def test_finance_context_keeps_missing_or_invalid_values_unset() -> None:
    from groundguard.rules.finance_cn import FinanceCNContext

    context = FinanceCNContext.from_mapping(
        {
            "finance_cn": {
                "exchange": "BSE",
                "board": "unknown",
                "listing_phase": "unknown",
                "trade_date": "not-a-date",
                "previous_close": "not-a-decimal",
            }
        }
    )

    assert context.exchange == "BSE"
    assert context.board == "unknown"
    assert context.listing_phase == "unknown"
    assert context.trade_date is None
    assert context.previous_close is None


def test_groundguard_core_does_not_import_opt_in_finance_package() -> None:
    core_root = Path("groundguard/core")
    imported_source = "groundguard" + ".rules.finance_cn"

    assert all(imported_source not in path.read_text(encoding="utf-8") for path in core_root.glob("*.py"))
