import os
import unittest
from unittest.mock import patch

with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test-key"}):
    from agents import orchestrator
    from agents.planner_agent import ResearchPlan
from core.session_memory import ResearchMemory
from retrieval import definition_tools


class DefinitionTests(unittest.TestCase):
    def setUp(self):
        self.plan = ResearchPlan(
            intent="definition", definition_term="test term", genes=[], disease="",
            use_gene_tool=False, use_pubmed_tool=False, pubmed_query="", research_goal="Define test term",
        )

    def test_definition_uses_verified_reference_without_research_or_synthesis(self):
        source = {"title": "Test term", "publisher": "Example reference",
                  "url": "https://www.genome.gov/genetics-glossary/Test-Term", "text": "An example definition."}
        memory = ResearchMemory()
        with (
            patch.object(orchestrator, "create_research_plan", return_value=self.plan),
            patch.object(orchestrator, "lookup_definition", return_value={"status": "found", "sources": [source]}),
            patch.object(orchestrator, "stdio_client", side_effect=AssertionError("Unexpected retrieval")),
            patch.object(orchestrator, "synthesize_research", side_effect=AssertionError("Unexpected synthesis")),
        ):
            result = orchestrator.process_research_question("Define test term", memory)
        self.assertEqual(result["decision"]["action"], "allow")
        self.assertIn(source["url"], result["answer"])
        self.assertEqual(memory.get_history()[0]["evidence"]["definition_lookup"]["sources"], [source])

    def test_missing_and_ambiguous_definitions_return_helpful_notices(self):
        for status, phrase in [("not_found", "couldn’t find"), ("clarify", "spell out")]:
            memory = ResearchMemory()
            with (
                patch.object(orchestrator, "create_research_plan", return_value=self.plan),
                patch.object(orchestrator, "lookup_definition", return_value={"status": status, "sources": []}),
                patch.object(orchestrator, "review_evidence", side_effect=AssertionError("Notice reviewed as an answer")),
            ):
                result = orchestrator.process_research_question("What does that mean?", memory)
            self.assertEqual(result["status"], "completed")
            self.assertIn(phrase, result["answer"])
            self.assertEqual(memory.get_history(), [])

    def test_ambiguous_abbreviation_does_not_use_planners_guessed_expansion(self):
        guessed = self.plan.model_copy(update={"definition_term": "multiple sclerosis"})
        with patch.object(orchestrator, "create_research_plan", return_value=guessed):
            result = orchestrator.process_research_question("What does MS stand for?", ResearchMemory())
        self.assertEqual(result["research_state"]["definition_lookup"]["status"], "clarify")

    def test_medlineplus_discards_unrelated_results_and_accepts_exact_alias(self):
        xml = b'''<nlmSearchResult><list>
        <document url="https://medlineplus.gov/related.html"><content name="title">Related</content>
        <content name="FullSummary">Wrong topic.</content></document>
        <document url="https://medlineplus.gov/topic.html"><content name="title">Correct topic</content>
        <content name="altTitle">test &lt;span&gt;term&lt;/span&gt;</content>
        <content name="FullSummary">&lt;p&gt;Correct description.&lt;/p&gt;</content></document>
        </list></nlmSearchResult>'''
        with patch.object(definition_tools, "_get") as get:
            get.return_value.content = xml
            results = definition_tools._medlineplus("test term")
        self.assertEqual([source["text"] for source in results], ["Correct description."])
