
from session_memory import ResearchMemory

memory = ResearchMemory(max_turns=3)

memory.add_turn(
    question="What is PKD1?",
    plan={"gene": "PKD1"},
    answer="PKD1 encodes polycystin-1."
)

memory.add_turn(
    question="What is PKD2?",
    plan={"gene": "PKD2"},
    answer="PKD2 encodes polycystin-2."
)

print("Stored history:")

for turn in memory.get_history():
    print("\nQuestion:", turn["question"])
    print("Plan:", turn["plan"])
    print("Answer:", turn["answer"])
