from decimal import Decimal


def test_coverage_report_exposes_numbers_seen_but_not_extracted():
    from groundguard import Ledger, Policy

    ledger = Ledger(session_id="req_001")

    report = ledger.coverage_report(
        "Revenue was 3830, while margin was 21.5%.",
        policy=Policy(),
    )

    assert [number.text_span for number in report.suspected_numbers] == [
        "3830",
        "21.5%",
    ]
    assert [number.text_span for number in report.uncovered_numbers] == ["3830"]
    assert report.extraction_coverage == 0.5


def test_fact_marker_digits_do_not_count_as_uncovered_numbers():
    from groundguard import Fact, Ledger

    ledger = Ledger(session_id="req_001")
    ledger.register_fact(
        Fact(
            id="fact_revenue_2025",
            source_tool="tool",
            source_call_id="call_1",
            key="revenue_2025",
            value=Decimal("3830000000"),
            unit="USD",
        )
    )

    report = ledger.coverage_report(
        "Revenue was $3.83 billion [fact:revenue_2025].",
        required_fact_keys=["revenue_2025"],
    )

    assert report.uncovered_numbers == []
    assert report.extraction_coverage == 1.0

