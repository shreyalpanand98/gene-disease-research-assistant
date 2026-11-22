
class ResearchMemory:
    """Store research conversation history during one session."""

    def __init__(self, max_turns=5):
        self.max_turns = max_turns
        self.history = []

    def add_turn(self, question, plan, answer):
        """Save a completed research interaction."""

        turn = {
            "question": question,
            "plan": plan,
            "answer": answer
        }

        self.history.append(turn)

        # Keep only the most recent interactions
        self.history = self.history[-self.max_turns:]

    def get_history(self):
        """Return recent research interactions."""
        return self.history.copy()

    def clear(self):
        """Clear the current research session."""
        self.history = []
