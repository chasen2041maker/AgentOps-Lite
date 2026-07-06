from decimal import Decimal


def _fact(
    key: str,
    value: Decimal,
    unit: str = "CNY",
    *,
    fact_id: str | None = None,
    recorded_at: float = 0.0,
):
    from groundguard import Fact

    return Fact(
        id=fact_id or f"fact_{key}",
        source_tool="tool",
        source_call_id="call_1",
        key=key,
        value=value,
        unit=unit,
        recorded_at=recorded_at,
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


def test_explicit_fact_key_uses_latest_registered_fact():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("150"), unit="CNY", fact_key="price")],
        [
            _fact("price", Decimal("100"), fact_id="fact_price_old", recorded_at=1.0),
            _fact("price", Decimal("150"), fact_id="fact_price_new", recorded_at=2.0),
        ],
    )

    assert claim.status == "verified"
    assert claim.matched_fact_id == "fact_price_new"
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


def test_explicit_fact_key_normalizes_fact_currency_magnitude_units():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("82320000000"), unit="CNY", fact_key="net_profit_2025")],
        [_fact("net_profit_2025", Decimal("823.2"), unit="亿元")],
    )

    assert claim.status == "verified"
    assert claim.matched_fact_id == "fact_net_profit_2025"


def test_unkeyed_nearby_numeric_match_is_only_candidate_match():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("82300000000"))],
        [_fact("net_profit_2025", Decimal("82320000000"))],
    )

    assert claim.status == "candidate_match"
    assert claim.matched_fact_id == "fact_net_profit_2025"


def test_unkeyed_numeric_match_marks_ambiguous_when_multiple_facts_are_nearby():
    from groundguard import match_claims

    [claim] = match_claims(
        [_claim(Decimal("100"))],
        [
            _fact("revenue_2025", Decimal("100.1")),
            _fact("net_profit_2025", Decimal("99.9")),
        ],
        tolerance=0.005,
    )

    assert claim.status == "ambiguous"
    assert claim.matched_fact_id is None
    assert "fact_revenue_2025" in claim.diff
    assert "fact_net_profit_2025" in claim.diff


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
