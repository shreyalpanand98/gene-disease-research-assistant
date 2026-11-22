"""Optional offline browser QA: python tests/preview_fixture.py (localhost:8001).

All answers and publication metadata are explicitly synthetic UI test data.
Use questions containing 'withhold' or 'error' to exercise other result states.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_server import ResearchServer, ResearchStore


def fixture_runner(question, memory, progress):
    for stage, detail in [
        ("planning", "UI fixture: preparing a test plan"),
        ("genes", "UI fixture: loading sample gene metadata"),
        ("literature", "UI fixture: loading synthetic article metadata"),
        ("synthesis", "UI fixture: preparing a sample response"),
        ("evidence", "UI fixture: checking the presentation"),
        ("claims", "UI fixture: loading sample assessments"),
    ]:
        progress(stage, detail)
        time.sleep(.3)
    if "error" in question.lower():
        raise RuntimeError("Intentional UI test failure")
    withheld = "withhold" in question.lower()
    plan = {"genes": ["PKD1", "PKD2"], "disease": "ADPKD (UI test fixture)", "research_goal": "Exercise the evidence explorer using synthetic presentation data.", "use_gene_tool": True, "use_pubmed_tool": True, "pubmed_query": "(PKD1 AND PKD2) AND ADPKD"}
    answer = "## UI test fixture\n\n**This is synthetic presentation data, not a research finding.** It exercises source cards, citations, abstracts, and claim review.\n\n- The first sample article is cited here (PMID 12345678).\n- A second retrieved article is intentionally not cited.\n\n### Limitations\nThis fixture makes no scientific claims. Use the normal server on port 8000 for live research."
    if not withheld:
        memory.add_turn(question, plan, answer)
    progress("decision", "UI fixture: final test decision")
    return {
        "status": "withheld" if withheld else "completed", "answer": None if withheld else answer,
        "decision": {"action": "withhold" if withheld else "allow", "reason": "Synthetic review requires attention." if withheld else "Synthetic automated checks passed."},
        "research_state": {"question": question, "plan": plan, "gene_evidence": [{"status": "found", "symbol": "PKD1", "gene_id": "5310", "description": "UI fixture gene card", "summary": "Synthetic summary for testing expansion and reading layout.", "source": "https://www.ncbi.nlm.nih.gov/gene/5310"}], "literature_evidence": {"status": "success", "articles": [{"pmid": "12345678", "title": "Synthetic article for UI testing — cited source", "journal": "UI Test Journal", "publication_date": "2026", "authors": ["Example A", "Example B"], "abstract": "Synthetic abstract for testing the evidence explorer. This is not a scientific source or a medical claim."}, {"pmid": "87654321", "title": "Synthetic article for UI testing — additional retrieved source", "journal": "UI Test Journal", "publication_date": "2025", "authors": ["Example C"], "abstract": "A second synthetic abstract for testing retrieved-versus-cited filtering."}]}},
        "review": {"status": "passed", "invalid_pmids": [], "cited_pmids": ["12345678"], "retrieved_pmids": ["12345678", "87654321"], "potentially_irrelevant_pmids": [], "statistical_issues": []},
        "claim_review": {"overall_assessment": "Synthetic UI test assessment only.", "requires_human_review": withheld, "assessments": [{"claim": "This is a sample claim-review card, not a scientific claim.", "verdict": "insufficient_evidence" if withheld else "supported", "explanation": "Synthetic explanation used to validate the review layout.", "supporting_pmids": ["12345678"]}]},
    }


if __name__ == "__main__":
    server = ResearchServer(("127.0.0.1", 8001), ResearchStore(fixture_runner))
    print("Synthetic UI fixture at http://127.0.0.1:8001 — no live research", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
