
def decide_intervention(
    citation_review: dict,
    claim_review=None,
    claim_review_required: bool = False
) -> dict:
    """
    Decide whether an answer can be displayed.

    This does not independently validate scientific claims.
    It enforces the results of existing review components.
    """

    if citation_review.get("requires_human_review", True):
        missing_genes = citation_review.get("missing_gene_symbols") or []
        if missing_genes and citation_review.get("status") == "needs_review":
            return {
                "action": "withhold",
                "reason": "Required NCBI Gene records were missing for " + ", ".join(missing_genes) + ".",
            }
        return {
            "action": "withhold",
            "reason": "Citation or evidence review did not pass."
        }

    if claim_review_required and claim_review is None:
        return {
            "action": "withhold",
            "reason": "Required scientific claim review is missing."
        }

    if claim_review is not None:
        if claim_review.requires_human_review:
            return {
                "action": "withhold",
                "reason": "Scientific claims require review."
            }

        if not claim_review.assessments:
            return {
                "action": "withhold",
                "reason": "No scientific claims were assessed."
            }

    return {
        "action": "allow",
        "reason": "Available automated checks passed."
    }
