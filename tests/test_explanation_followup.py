import asyncio
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test-key"}):
    from agents import orchestrator
from agents.planner_agent import ResearchPlan
from core.session_memory import ResearchMemory


class ExplanationFollowupTests(unittest.TestCase):
    def setUp(self):
        self.memory = ResearchMemory()
        self.plan = ResearchPlan(
            genes=["PKD1"], disease="", use_gene_tool=True,
            use_pubmed_tool=False, pubmed_query="", research_goal="Explain PKD1",
        )
        self.evidence = {
            "evidence_question": "What is PKD1?",
            "gene_evidence": [{"status": "found", "symbol": "PKD1"}],
            "literature_evidence": None,
        }

    def test_rewrite_reuses_latest_answer_and_sources_and_persists_style(self):
        self.memory.add_turn("What is PKD1?", self.plan.model_dump(), "Earlier answer", evidence=self.evidence)
        revision = self.plan.model_copy(update={
            "intent": "rephrase", "explanation_style": "beginner", "use_gene_tool": False,
        })
        with (
            patch.object(orchestrator, "create_research_plan", return_value=revision),
            patch.object(orchestrator, "stdio_client", side_effect=AssertionError("Rewrite attempted retrieval")),
            patch.object(orchestrator, "synthesize_research", return_value="Plain explanation") as synthesize,
        ):
            result = orchestrator.process_research_question("Can you explain that more simply?", self.memory)

        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["research_state"]["evidence_reused"])
        self.assertEqual(result["research_state"]["gene_evidence"], self.evidence["gene_evidence"])
        self.assertEqual(synthesize.call_args.kwargs["previous_answer"], "Earlier answer")
        self.assertEqual(self.memory.explanation_style, "beginner")

        next_plan = self.plan.model_copy(update={"use_gene_tool": False})
        with patch.object(orchestrator, "create_research_plan", return_value=next_plan):
            state = asyncio.run(orchestrator.run_research("What about PKD2?", self.memory))
        self.assertFalse(state.get("evidence_reused"))
        self.assertEqual(state["plan"]["explanation_style"], "beginner")
        self.memory.clear()
        self.assertEqual(self.memory.explanation_style, "standard")

    def test_rewrite_with_unverified_literature_claims_is_withheld(self):
        self.plan.use_pubmed_tool = True
        self.evidence["literature_evidence"] = {"status": "success", "articles": [{
            "pmid": "12345678", "title": "PKD1", "abstract": "PKD1 study abstract",
        }]}
        self.memory.add_turn("What is PKD1?", self.plan.model_dump(), "Earlier answer", evidence=self.evidence)
        revision = self.plan.model_copy(update={
            "intent": "rephrase", "explanation_style": "beginner", "use_pubmed_tool": False,
        })
        claims = SimpleNamespace(assessments=[], requires_human_review=True, model_dump=lambda: {})
        with (
            patch.object(orchestrator, "create_research_plan", return_value=revision),
            patch.object(orchestrator, "synthesize_research", return_value="Plain explanation (PMID 12345678)"),
            patch.object(orchestrator, "verify_scientific_claims", return_value=claims) as verify,
        ):
            result = orchestrator.process_research_question("Explain it in simple terms", self.memory)

        verify.assert_called_once()
        self.assertEqual(result["status"], "withheld")
        self.assertIsNone(result["answer"])
        self.assertEqual(len(self.memory.get_history()), 1)
