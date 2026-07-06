from decimal import Decimal


def _fact(key: str, value: Decimal):
    from groundguard import Fact

    return Fact(
        id=f"fact_{key}",
        source_tool="tool",
        source_call_id="call_1",
        key=key,
        value=value,
        unit="CNY",
    )


def _claim(status: str, fact_key: str | None = None, matched_fact_id: str | None = None):
    from groundguard import OutputClaim

    return OutputClaim(
        id=f"claim_{status}",
        text_span="净利润为 823.2 亿元",
        claim_type="numeric",
        normalized_value=Decimal("82320000000"),
        unit="CNY",
        fact_key=fact_key,
        matched_fact_id=matched_fact_id,
        status=status,
    )


def test_build_coverage_report_counts_claim_statuses_and_omissions():
    from groundguard import RequiredFact, build_coverage_report

    report = build_coverage_report(
        session_id="req_001",
        output_claims=[
            _claim("verified", fact_key="net_profit_2025"),
            _claim("unverified"),
            _claim("contradicted", fact_key="revenue_2025"),
        ],
        required_facts=[
            RequiredFact("net_profit_2025"),
            RequiredFact("cash_flow_2025"),
        ],
    )

    assert report.verified_count == 1
    assert report.unverified_count == 1
    assert report.contradicted_count == 1
    assert report.candidate_match_count == 0
    assert report.omitted_required_count == 1
    assert [fact.key for fact in report.omitted_required_facts] == ["cash_flow_2025"]


def test_candidate_match_does_not_cover_required_fact_by_default():
    from groundguard import RequiredFact, build_coverage_report

    report = build_coverage_report(
        session_id="req_001",
        output_claims=[
            _claim(
                "candidate_match",
                matched_fact_id="fact_net_profit_2025",
            )
        ],
        required_facts=[RequiredFact("net_profit_2025")],
        facts=[_fact("net_profit_2025", Decimal("82320000000"))],
    )

    assert report.candidate_match_count == 1
    assert report.omitted_required_count == 1


def test_candidate_match_can_cover_required_fact_when_policy_allows_it():
    from groundguard import RequiredFact, build_coverage_report

    report = build_coverage_report(
        session_id="req_001",
        output_claims=[
            _claim(
                "candidate_match",
                matched_fact_id="fact_net_profit_2025",
            )
        ],
        required_facts=[RequiredFact("net_profit_2025")],
        facts=[_fact("net_profit_2025", Decimal("82320000000"))],
        allow_candidate_matches=True,
    )

    assert report.candidate_match_count == 1
    assert report.omitted_required_count == 0


def test_policy_blocks_contradictions_and_required_omissions_by_default():
    from groundguard import Policy, RequiredFact, build_coverage_report, evaluate_policy

    report = build_coverage_report(
        session_id="req_001",
        output_claims=[_claim("contradicted", fact_key="net_profit_2025")],
        required_facts=[RequiredFact("net_profit_2025"), RequiredFact("revenue_2025")],
    )

    evaluated = evaluate_policy(report, Policy())

    assert evaluated.passed is False
    assert "contradicted_count=1" in evaluated.policy_reason
    assert "omitted_required_count=1" in evaluated.policy_reason


def test_policy_blocks_when_unverified_ratio_exceeds_threshold():
    from groundguard import Policy, build_coverage_report, evaluate_policy

    report = build_coverage_report(
        session_id="req_001",
        output_claims=[
            _claim("verified", fact_key="net_profit_2025"),
            _claim("unverified"),
        ],
        required_facts=[],
    )

    evaluated = evaluate_policy(report, Policy(max_unverified_ratio=0.49))

    assert evaluated.passed is False
    assert "unverified_ratio=0.500" in evaluated.policy_reason
