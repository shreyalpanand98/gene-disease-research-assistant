
from types import SimpleNamespace

from core.safety_guardrails import decide_intervention


def test_interventions():
    passed = {"requires_human_review": False}
    failed = {"requires_human_review": True}

    supported_claims = SimpleNamespace(
        requires_human_review=False,
        assessments=[
            SimpleNamespace(verdict="supported")
        ]
    )

    unsupported_claims = SimpleNamespace(
        requires_human_review=True,
        assessments=[
            SimpleNamespace(verdict="contradicted")
        ]
    )

    cases = [
        ("Valid NCBI-only answer", passed, None, False, "allow"),
        ("Invalid citation", failed, None, False, "withhold"),
        (
            "Unsupported scientific claim",
            passed, unsupported_claims, True, "withhold"
        ),
        (
            "Supported scientific claims",
            passed, supported_claims, True, "allow"
        ),
        (
            "Missing required claim review",
            passed, None, True, "withhold"
        ),
    ]

    for name, citation, claim, required, expected in cases:
        result = decide_intervention(
            citation_review=citation,
            claim_review=claim,
            claim_review_required=required
        )

        assert result["action"] == expected, (
            f"{name}: expected {expected}, got {result['action']}"
        )

        print(f"PASS: {name} -> {result['action']}")


if __name__ == "__main__":
    test_interventions()
