def test_custom_extractor_can_be_registered_and_unregistered():
    from groundguard import OutputClaim, extract_output_claims
    from groundguard.core.output_claim_extractor import (
        register_extractor,
        unregister_extractor,
    )

    def extract_entities(text: str) -> list[OutputClaim]:
        start = text.index("ACME Corp")
        return [
            OutputClaim(
                id="claim_entity_acme",
                text_span="ACME Corp",
                claim_type="entity",
                normalized_value="ACME Corp",
                unit=None,
                start=start,
                end=start + len("ACME Corp"),
            )
        ]

    register_extractor("test_entity", extract_entities)
    try:
        claims = extract_output_claims("ACME Corp reported revenue of $3.83 billion.")
    finally:
        unregister_extractor("test_entity")

    assert [claim.claim_type for claim in claims] == ["entity", "numeric"]
    assert claims[0].text_span == "ACME Corp"
    assert claims[1].text_span.endswith("revenue of $3.83 billion")


def test_duplicate_extractor_spans_are_deduplicated():
    from decimal import Decimal

    from groundguard import OutputClaim, extract_output_claims
    from groundguard.core.output_claim_extractor import (
        register_extractor,
        unregister_extractor,
    )

    def extract_duplicate(text: str) -> list[OutputClaim]:
        start = text.index("$3.83 billion")
        return [
            OutputClaim(
                id="claim_duplicate",
                text_span="$3.83 billion",
                claim_type="numeric",
                normalized_value=Decimal("3830000000"),
                unit="USD",
                start=start,
                end=start + len("$3.83 billion"),
            )
        ]

    register_extractor("test_duplicate", extract_duplicate)
    try:
        claims = extract_output_claims("Revenue was $3.83 billion.")
    finally:
        unregister_extractor("test_duplicate")

    assert len([claim for claim in claims if claim.claim_type == "numeric"]) == 1
