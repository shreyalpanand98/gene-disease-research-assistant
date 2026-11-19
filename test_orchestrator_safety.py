
from safety_guardrails import decide_intervention
from session_memory import ResearchMemory


def test_withheld_answer_not_saved():
    memory = ResearchMemory(max_turns=5)

    # Simulate an invalid citation review
    citation_review = {
        "status": "failed",
        "requires_human_review": True,
        "invalid_pmids": ["99999999"]
    }

    decision = decide_intervention(
        citation_review=citation_review,
        claim_review=None,
        claim_review_required=True
    )

    # Simulate the orchestrator's save policy:
    # Only approved answers are stored.
    if decision["action"] == "allow":
        memory.add_turn(
            question="How do PKD1 mutations affect ADPKD?",
            plan={"genes": ["PKD1"]},
            answer="Synthetic research answer"
        )

    assert decision["action"] == "withhold"
    assert len(memory.get_history()) == 0

    print("PASS: Invalid answer withheld.")
    print("PASS: Withheld answer not saved to memory.")


if __name__ == "__main__":
    test_withheld_answer_not_saved()
