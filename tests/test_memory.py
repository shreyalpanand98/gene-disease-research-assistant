
from session_memory import ResearchMemory


def test_add_turn():
    memory = ResearchMemory(max_turns=3)

    memory.add_turn(
        question="What is PKD1?",
        plan={"gene": "PKD1"},
        answer="PKD1 encodes polycystin-1."
    )

    history = memory.get_history()

    assert len(history) == 1
    assert history[0]["question"] == "What is PKD1?"
    assert history[0]["plan"] == {"gene": "PKD1"}
    assert history[0]["answer"] == "PKD1 encodes polycystin-1."


def test_memory_limit():
    memory = ResearchMemory(max_turns=2)

    for gene in ["PKD1", "PKD2", "BRCA1"]:
        memory.add_turn(
            question=f"What is {gene}?",
            plan={"gene": gene},
            answer=f"Research summary for {gene}"
        )

    history = memory.get_history()

    assert len(history) == 2
    assert [turn["plan"]["gene"] for turn in history] == [
        "PKD2", "BRCA1"
    ]


def test_clear_memory():
    memory = ResearchMemory()

    memory.add_turn(
        question="What is PKD1?",
        plan={"gene": "PKD1"},
        answer="PKD1 encodes polycystin-1."
    )

    memory.clear()

    assert memory.get_history() == []
