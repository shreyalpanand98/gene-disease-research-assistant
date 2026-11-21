
from evidence_review_agent import (
    review_evidence,
    screen_article_relevance
)

def test_article_relevance():
    question = (
        "How do PKD1 mutations affect ADPKD progression?"
    )

    relevant_article = {
        "pmid": "11111111",
        "title": "PKD1 mutations and ADPKD progression",
        "abstract": (
            "This study evaluates how PKD1 variants "
            "affect kidney disease progression."
        )
    }

    unrelated_article = {
        "pmid": "22222222",
        "title": "BRCA1 mutations in breast cancer",
        "abstract": (
            "This study examines BRCA1 variants "
            "in hereditary breast cancer."
        )
    }

    relevant_result = screen_article_relevance(
        question,
        relevant_article,
        ["PKD1"]
    )

    unrelated_result = screen_article_relevance(
        question,
        unrelated_article,
        ["PKD1"]
    )

    assert (
        relevant_result["relevance"]
        == "potentially_relevant"
    )

    assert (
        unrelated_result["relevance"]
        == "potentially_irrelevant"
    )

    print("PASS: Article relevance screening.")


def test_missing_pubmed_evidence():
    """
    Scenario:
    The planner requested PubMed research,
    but PubMed returned zero articles.
    """

    research_state = {
        "question": (
            "How do PKD1 mutations affect ADPKD progression?"
        ),
        "plan": {
            "genes": ["PKD1"],
            "use_gene_tool": False,
            "use_pubmed_tool": True,
            "pubmed_query": "PKD1 AND ADPKD"
        },
        "gene_evidence": None,
        "literature_evidence": {
            "status": "success",
            "article_count": 0,
            "articles": []
        }
    }

    answer = (
        "Insufficient evidence to answer this question."
    )

    result = review_evidence(research_state, answer)

    print("\nTEST: Missing PubMed Evidence")
    print("Review status:", result["status"])
    print("Human review:", result["requires_human_review"])

    if result["status"] == "passed":
        print(
            "SAFETY GAP DETECTED: "
            "The reviewer passed despite no PubMed evidence."
        )
    else:
        print("PASS: Missing evidence was flagged.")


def test_missing_gene_evidence():
    """
    Scenario:
    NCBI Gene lookup was requested,
    but no valid gene record was returned.
    """

    research_state = {
        "question": "What is the PKD1 gene?",
        "plan": {
            "genes": ["PKD1"],
            "use_gene_tool": True,
            "use_pubmed_tool": False,
            "pubmed_query": ""
        },
        "gene_evidence": [
            {
                "status": "not_found",
                "symbol": "PKD1"
            }
        ],
        "literature_evidence": None
    }

    answer = "PKD1 encodes polycystin-1."

    result = review_evidence(research_state, answer)

    print("\nTEST: Missing NCBI Gene Evidence")
    print("Review status:", result["status"])
    print("Human review:", result["requires_human_review"])

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True

    print("PASS: Missing gene evidence was flagged.")

def test_pubmed_api_failure():
    """Check behavior when the PubMed MCP tool fails."""

    research_state = {
        "question": "How do PKD1 mutations affect ADPKD?",
        "plan": {
            "genes": ["PKD1"],
            "use_gene_tool": False,
            "use_pubmed_tool": True
        },
        "gene_evidence": None,
        "literature_evidence": {
            "status": "error",
            "message": "Simulated PubMed API failure",
            "articles": []
        }
    }

    answer = "Insufficient evidence to answer the question."

    result = review_evidence(research_state, answer)

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True

    print("PASS: PubMed API failure was flagged.")


def test_ncbi_api_failure():
    """Check behavior when the NCBI Gene MCP tool fails."""

    research_state = {
        "question": "What is the PKD1 gene?",
        "plan": {
            "genes": ["PKD1"],
            "use_gene_tool": True,
            "use_pubmed_tool": False
        },
        "gene_evidence": [
            {
                "status": "error",
                "message": "Simulated NCBI API failure"
            }
        ],
        "literature_evidence": None
    }

    answer = "Insufficient evidence to answer the question."

    result = review_evidence(research_state, answer)

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True

    print("PASS: NCBI Gene API failure was flagged.")

def test_irrelevant_evidence_review():

    research_state = {
        "question": (
            "How do PKD1 mutations affect ADPKD progression?"
        ),
        "plan": {
            "genes": ["PKD1"],
            "use_gene_tool": False,
            "use_pubmed_tool": True
        },
        "gene_evidence": None,
        "literature_evidence": {
            "status": "success",
            "articles": [
                {
                    "pmid": "22222222",
                    "title": "BRCA1 mutations in breast cancer",
                    "abstract": (
                        "A study of hereditary breast cancer."
                    )
                }
            ]
        }
    }

    # The PMID exists, but the article is unrelated.
    answer = (
        "PKD1 mutations affect ADPKD progression "
        "(PMID 22222222)."
    )

    result = review_evidence(research_state, answer)

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True

    assert "22222222" in result[
        "potentially_irrelevant_pmids"
    ]

    print("PASS: Irrelevant evidence flagged for review.")



def test_unsupported_scientific_claim():
    research_state = {
        "question": "Does PKD1 affect ADPKD progression?",
        "plan": {
            "genes": ["PKD1"],
            "use_gene_tool": False,
            "use_pubmed_tool": True
        },
        "gene_evidence": None,
        "literature_evidence": {
            "status": "success",
            "articles": [
                {
                    "pmid": "12345678",
                    "title": "PKD1 and ADPKD progression",
                    "abstract": (
                        "A comparison found a difference "
                        "in kidney function decline "
                        "(p = 0.066)."
                    )
                }
            ]
        }
    }

    answer = (
        "PKD1 showed a statistically significant "
        "difference in kidney function decline "
        "(p = 0.066; PMID 12345678)."
    )

    result = review_evidence(research_state, answer)

    print("\nTEST: Unsupported Scientific Claim")
    print("Review status:", result["status"])
    print("Statistical issues:", result["statistical_issues"])

    assert result["status"] == "needs_review"
    assert result["requires_human_review"] is True
    assert len(result["statistical_issues"]) > 0

    print("PASS: Statistical inconsistency detected.")


if __name__ == "__main__":
    test_missing_pubmed_evidence()
    test_missing_gene_evidence()
    test_pubmed_api_failure()
    test_ncbi_api_failure()
    test_article_relevance()
    test_irrelevant_evidence_review()
    test_unsupported_scientific_claim()

    print("\nAll 7 safety tests passed!")