from decimal import Decimal


def _fact(key: str, value: Decimal, unit: str = "CNY"):
    from groundguard import Fact

    return Fact(
        id=f"fact_{key}",
        source_tool="tool",
        source_call_id="call_1",
        key=key,
        value=value,
        unit=unit,
    )


def _claim(value: Decimal, unit: str = "CNY", fact_key: str | None = None):
    from groundguard import OutputClaim

    return OutputClaim(
        id="claim_1",
        text_span="净利润为 823.2 亿元",
        claim_type="numeric",
        normalized_value=value,
        unit=unit,
        fact_key=fact_key,
    )


def test_explicit_fact_key_match_marks_claim_verified():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("82320000000"), fact_key="net_profit_2025")],
        [_fact("net_profit_2025", Decimal("82320000000"))],
    )

    assert claim.status == "verified"
    assert claim.matched_fact_id == "fact_net_profit_2025"
    assert claim.diff is None


def test_explicit_fact_key_value_mismatch_marks_claim_contradicted():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("80000000000"), fact_key="net_profit_2025")],
        [_fact("net_profit_2025", Decimal("82320000000"))],
    )

    assert claim.status == "contradicted"
    assert claim.matched_fact_id == "fact_net_profit_2025"
    assert "82320000000" in claim.diff
    assert "80000000000" in claim.diff


def test_explicit_fact_key_unit_mismatch_marks_claim_contradicted():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("10"), unit="USD", fact_key="cash_flow")],
        [_fact("cash_flow", Decimal("10"), unit="CNY")],
    )

    assert claim.status == "contradicted"
    assert claim.matched_fact_id == "fact_cash_flow"
    assert "unit" in claim.diff


def test_unkeyed_nearby_numeric_match_is_only_candidate_match():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("82300000000"))],
        [_fact("net_profit_2025", Decimal("82320000000"))],
    )

    assert claim.status == "candidate_match"
    assert claim.matched_fact_id == "fact_net_profit_2025"


def test_unkeyed_numeric_without_candidate_stays_unverified():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("12300000000"))],
        [_fact("net_profit_2025", Decimal("82320000000"))],
    )

    assert claim.status == "unverified"
    assert claim.matched_fact_id is None


def test_unit_mismatch_does_not_match_candidate():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("10"), unit="USD")],
        [_fact("net_profit_2025", Decimal("10"), unit="CNY")],
    )

    assert claim.status == "unverified"
    assert claim.matched_fact_id is None
