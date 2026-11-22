
class ResearchMemory:
    """Store research conversation history during one session."""

    def __init__(self, max_turns=5):
        self.max_turns = max_turns
        self.history = []
        self.explanation_style = "standard"

    def add_turn(self, question, plan, answer, *, evidence=None):
        """Save a completed research interaction."""

        turn = {
            "question": question,
            "plan": plan,
            "answer": answer
        }
        if evidence is not None:
            turn["evidence"] = evidence

        self.history.append(turn)

        # Keep only the most recent interactions
        self.history = self.history[-self.max_turns:]

    def get_history(self):
        """Return recent research interactions."""
        return self.history.copy()

    def clear(self):
        """Clear the current research session."""
        self.history = []
        self.explanation_style = "standard"
