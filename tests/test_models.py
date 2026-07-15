from decimal import Decimal


def test_fact_defaults_capture_registered_fact_metadata():
    from groundguard import Fact

    fact = Fact(
        id="fact_1",
        source_tool="get_company_financials",
        source_call_id="call_1",
        key="net_profit_2025",
        value=Decimal("82320000000"),
        unit="CNY",
    )

    assert fact.schema_version == 1
    assert fact.value_kind == "numeric"
    assert fact.display_value is None
    assert fact.raw is None
    assert fact.recorded_at == 0.0
    assert fact.ttl_seconds is None
    assert fact.confidence == 1.0
    assert fact.metadata == {}
    assert fact.subject is None
    assert fact.as_of is None
    assert fact.observed_at is None
    assert fact.source_field is None
    assert fact.fact_type is None


def test_fact_context_fields_are_optional_and_preserve_legacy_construction():
    from groundguard import Fact

    legacy_fact = Fact(
        id="fact_legacy",
        source_tool="tool",
        source_call_id="call",
        key="price",
        value=Decimal("10"),
    )
    enriched_fact = Fact(
        id="fact_enriched",
        source_tool="market_data",
        source_call_id="call_2",
        key="price",
        value=Decimal("123.45"),
        subject="SH.600519",
        as_of="2026-07-15",
        observed_at="2026-07-15T09:30:00+08:00",
        source_field="last_price",
        fact_type="quote",
    )

    assert legacy_fact.subject is None
    assert enriched_fact.subject == "SH.600519"
    assert enriched_fact.as_of == "2026-07-15"
    assert enriched_fact.observed_at == "2026-07-15T09:30:00+08:00"
    assert enriched_fact.source_field == "last_price"
    assert enriched_fact.fact_type == "quote"


def test_required_fact_defaults_to_required_severity():
    from groundguard import RequiredFact

    required = RequiredFact(key="revenue_2025", reason="user asked for latest revenue")

    assert required.key == "revenue_2025"
    assert required.reason == "user asked for latest revenue"
    assert required.severity == "required"


def test_output_claim_defaults_to_unverified_status():
    from groundguard import OutputClaim

    claim = OutputClaim(
        id="claim_1",
        text_span="净利润为 823.2 亿元 [fact:net_profit_2025]",
        claim_type="numeric",
        normalized_value=Decimal("82320000000"),
        unit="CNY",
        fact_key="net_profit_2025",
    )

    assert claim.fact_key == "net_profit_2025"
    assert claim.matched_fact_id is None
    assert claim.status == "unverified"
    assert claim.diff is None


def test_coverage_report_counts_start_at_zero():
    from groundguard import CoverageReport, RequiredFact

    required = RequiredFact(key="net_profit_2025")
    report = CoverageReport(session_id="req_001", required_facts=[required])

    assert report.session_id == "req_001"
    assert report.output_claims == []
    assert report.required_facts == [required]
    assert report.omitted_required_facts == []
    assert report.verified_count == 0
    assert report.candidate_match_count == 0
    assert report.unverified_count == 0
    assert report.contradicted_count == 0
    assert report.omitted_required_count == 0
    assert report.passed is True
    assert report.policy_reason == ""
    assert report.issues == ()
    assert report.hard_issue_count == 0
    assert report.soft_issue_count == 0
