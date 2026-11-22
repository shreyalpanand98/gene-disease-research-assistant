from agents.evidence_review_agent import verify_scientific_claims

def test_incorrect_sample_size():

    # Synthetic evidence for testing
    research_state = {
        "question": (
            "How do PKD1 mutations affect ADPKD progression?"
        ),
        "literature_evidence": {
            "status": "success",
            "articles": [
                {
                    "pmid": "12345678",
                    "title": "PKD1 mutations and ADPKD progression",
                    "abstract": (
                        "This observational study included "
                        "436 patients with ADPKD. "
                        "The study examined PKD1 variants "
                        "and renal function decline."
                    )
                }
            ]
        }
    }

    # Deliberately incorrect answer
    answer = (
        "A study of 4,360 ADPKD patients found "
        "that PKD1 variants affect renal function "
        "decline (PMID 12345678)."
    )

    result = verify_scientific_claims(
        research_state,
        answer
    )

    print("\nCLAIM VERIFICATION RESULT")
    print("=" * 50)

    for assessment in result.assessments:
        print("\nClaim:", assessment.claim)
        print("Verdict:", assessment.verdict)
        print("Explanation:", assessment.explanation)
        print("Supporting PMIDs:", assessment.supporting_pmids)

    print("\nOverall:", result.overall_assessment)
    print("Human review:", result.requires_human_review)

    assert result.requires_human_review is True

    assert any(
        assessment.verdict == "contradicted"
        for assessment in result.assessments
    ), "Expected the incorrect sample size to be contradicted."

    print("\nPASS: Incorrect sample size detected.")


def test_supported_claim():
    research_state = {
        "question": "How many patients were included?",
        "literature_evidence": {
            "status": "success",
            "articles": [{
                "pmid": "12345678",
                "title": "PKD1 and ADPKD progression",
                "abstract": (
                    "This observational study included "
                    "436 patients with ADPKD."
                )
            }]
        }
    }

    answer = (
        "The observational study included 436 "
        "patients with ADPKD (PMID 12345678)."
    )

    result = verify_scientific_claims(
        research_state, answer
    )

    print("\nTEST: Supported Claim")

    for assessment in result.assessments:
        print(assessment.verdict, "-", assessment.explanation)

    assert result.assessments
    assert all(
        item.verdict == "supported"
        for item in result.assessments
    )
    assert result.requires_human_review is False

    print("PASS: Supported claim accepted.")


def test_insufficient_evidence():
    research_state = {
        "question": "Does this study prove treatment efficacy?",
        "literature_evidence": {
            "status": "success",
            "articles": [{
                "pmid": "12345678",
                "title": "PKD1 and ADPKD progression",
                "abstract": (
                    "This observational study included "
                    "436 patients with ADPKD and examined "
                    "PKD1 variants."
                )
            }]
        }
    }

    answer = (
        "The study demonstrated that a new drug "
        "cures ADPKD (PMID 12345678)."
    )

    result = verify_scientific_claims(
        research_state, answer
    )

    print("\nTEST: Insufficient Evidence")

    for assessment in result.assessments:
        print(assessment.verdict, "-", assessment.explanation)

    assert result.assessments
    assert any(
        item.verdict in {
            "insufficient_evidence",
            "contradicted"
        }
        for item in result.assessments
    )
    assert result.requires_human_review is True

    print("PASS: Unsupported treatment claim flagged.")

if __name__ == "__main__":
    test_incorrect_sample_size()
    test_supported_claim()
    test_insufficient_evidence()

    print("\nAll 3 claim verification tests passed!")
