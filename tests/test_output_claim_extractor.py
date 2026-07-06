from decimal import Decimal


def test_extracts_explicit_fact_key_numeric_claim():
    from groundguard import extract_output_claims

    claims = extract_output_claims("净利润为 823.2 亿元 [fact:net_profit_2025]。")

    assert len(claims) == 1
    claim = claims[0]
    assert claim.text_span == "净利润为 823.2 亿元 [fact:net_profit_2025]"
    assert claim.claim_type == "numeric"
    assert claim.normalized_value == Decimal("82320000000")
    assert claim.unit == "CNY"
    assert claim.fact_key == "net_profit_2025"
    assert claim.status == "unverified"
    assert claim.id.startswith("claim_")


def test_extracts_numeric_claim_without_fact_key_as_unkeyed_candidate():
    from groundguard import extract_output_claims

    claims = extract_output_claims("收入达到 3830 亿元，现金流改善。")

    assert len(claims) == 1
    assert claims[0].text_span == "收入达到 3830 亿元"
    assert claims[0].normalized_value == Decimal("383000000000")
    assert claims[0].unit == "CNY"
    assert claims[0].fact_key is None


def test_extracts_percent_claim_without_scaling_value():
    from groundguard import extract_output_claims

    claims = extract_output_claims("毛利率提升至 21.5%。")

    assert len(claims) == 1
    assert claims[0].normalized_value == Decimal("21.5")
    assert claims[0].unit == "%"


def test_extracts_usd_claim_and_preserves_currency_unit():
    from groundguard import extract_output_claims

    claims = extract_output_claims("自由现金流为 10.25 亿美元 [fact:free_cash_flow].")

    assert len(claims) == 1
    assert claims[0].normalized_value == Decimal("1025000000")
    assert claims[0].unit == "USD"
    assert claims[0].fact_key == "free_cash_flow"


def test_extracts_usd_claim_with_dollar_prefix_and_english_magnitude():
    from groundguard import extract_output_claims

    claims = extract_output_claims("Revenue reached $3.83 billion [fact:revenue_2025].")

    assert len(claims) == 1
    assert claims[0].text_span == "Revenue reached $3.83 billion [fact:revenue_2025]"
    assert claims[0].normalized_value == Decimal("3830000000")
    assert claims[0].unit == "USD"
    assert claims[0].fact_key == "revenue_2025"


def test_extracts_usd_claim_with_currency_code_and_short_magnitude():
    from groundguard import extract_output_claims

    claims = extract_output_claims("Free cash flow was USD 10.25M [fact:free_cash_flow].")

    assert len(claims) == 1
    assert claims[0].text_span == "Free cash flow was USD 10.25M [fact:free_cash_flow]"
    assert claims[0].normalized_value == Decimal("10250000")
    assert claims[0].unit == "USD"
    assert claims[0].fact_key == "free_cash_flow"


def test_extracts_usd_claim_with_dollar_suffix():
    from groundguard import extract_output_claims

    claims = extract_output_claims("The contract value was 2.5 million dollars.")

    assert len(claims) == 1
    assert claims[0].text_span == "contract value was 2.5 million dollars"
    assert claims[0].normalized_value == Decimal("2500000")
    assert claims[0].unit == "USD"
    assert claims[0].fact_key is None


def test_extracts_common_english_magnitude_and_percent_claims():
    from groundguard import extract_output_claims

    claims = extract_output_claims(
        "Usage reached 1.2M, revenue was 3,830 million dollars, and margin was 21.5 percent."
    )

    assert [claim.normalized_value for claim in claims] == [
        Decimal("1200000"),
        Decimal("3830000000"),
        Decimal("21.5"),
    ]
    assert [claim.unit for claim in claims] == [None, "USD", "%"]


def test_extracts_multiple_numeric_claims_in_order():
    from groundguard import extract_output_claims

    claims = extract_output_claims(
        "收入为 3830 亿元 [fact:revenue_2025]，净利润为 823.2 亿元 [fact:net_profit_2025]。"
    )

    assert [claim.fact_key for claim in claims] == ["revenue_2025", "net_profit_2025"]
    assert [claim.normalized_value for claim in claims] == [
        Decimal("383000000000"),
        Decimal("82320000000"),
    ]


def test_ignores_numbers_that_are_part_of_fact_key_markers():
    from groundguard import extract_output_claims

    claims = extract_output_claims("该结论引用 [fact:net_profit_2025]，但没有写具体数字。")

    assert claims == []
