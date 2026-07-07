from decimal import Decimal


def _failed_report(**overrides):
    from groundguard import CoverageReport

    payload = {
        "session_id": "req_policy",
        "passed": False,
        "policy_reason": "failed",
    }
    payload.update(overrides)
    return CoverageReport(**payload)


def test_policy_action_prefers_repair_actions_before_blocking():
    from groundguard import Policy
    from groundguard.core.policy import policy_action

    assert (
        policy_action(
            _failed_report(contradicted_count=1),
            Policy(on_contradicted="fix"),
        )
        == "fix"
    )
    assert (
        policy_action(
            _failed_report(contradicted_count=1),
            Policy(on_contradicted="reask"),
        )
        == "reask"
    )


def test_policy_action_strips_unverified_when_configured():
    from groundguard import OutputClaim, Policy
    from groundguard.core.policy import policy_action

    report = _failed_report(
        output_claims=[
            OutputClaim(
                id="claim_cash",
                text_span="Cash was $120 million",
                claim_type="numeric",
                normalized_value=Decimal("120000000"),
                unit="USD",
                status="unverified",
            )
        ],
        unverified_count=1,
    )

    assert policy_action(report, Policy(on_unverified="strip")) == "strip"


def test_policy_action_blocks_non_repairable_failures():
    from groundguard import Policy
    from groundguard.core.policy import policy_action

    assert policy_action(_failed_report(omitted_required_count=1), Policy()) == "block"
    assert policy_action(_failed_report(passed=True), Policy()) == "pass"
