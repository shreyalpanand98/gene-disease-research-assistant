
import streamlit as st
import traceback

from agents.orchestrator import process_research_question
from core.session_memory import ResearchMemory

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Gene–Disease Research Assistant",
    page_icon="🧬",
    layout="wide",
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "research_results" not in st.session_state:
    st.session_state.research_results = []

if "research_memory" not in st.session_state:
    st.session_state.research_memory = ResearchMemory(
        max_turns=5
    )

# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def extract_articles(literature_evidence):
    """
    Normalize PubMed evidence into a list of articles.

    Supports lists and dictionaries containing articles.
    """
    if isinstance(literature_evidence, list):
        return literature_evidence

    if isinstance(literature_evidence, dict):
        return literature_evidence.get("articles") or []

    return []


def display_research_sources(research_state):
    """Display NCBI Gene and PubMed source links."""

    gene_evidence = research_state.get("gene_evidence") or []
    literature_evidence = (
        research_state.get("literature_evidence") or []
    )

    articles = extract_articles(literature_evidence)
    source_count = 0

    # NCBI Gene sources
    for gene in gene_evidence:
        if not isinstance(gene, dict):
            continue

        symbol = gene.get("symbol", "Gene record")
        source = gene.get("source")

        if source:
            st.markdown(f"🧬 [{symbol}]({source})")
            source_count += 1

    # PubMed sources
    for article in articles:
        if not isinstance(article, dict):
            continue

        pmid = article.get("pmid") or article.get("PMID")
        title = article.get("title") or "PubMed article"

        if pmid:
            url = (
                f"https://pubmed.ncbi.nlm.nih.gov/"
                f"{pmid}/"
            )
            st.markdown(f"📚 [{title}]({url})")
            source_count += 1

    if source_count == 0:
        st.caption("No source records available.")


def display_review_details(latest):
    """Display the latest evidence and safety review."""

    decision = latest.get("decision") or {}
    review = latest.get("review") or {}
    claim_review = latest.get("claim_review") or {}

    action = decision.get("action", "unknown")
    review_status = review.get("status", "not available")

    if action == "allow":
        st.success("Safety decision: Approved")
    elif action == "withhold":
        st.warning("Safety decision: Withheld")
    else:
        st.info("Safety decision: Not available")

    st.write(f"**Evidence review:** {review_status}")

    if claim_review:
        st.write("**Scientific claim review:** Performed")
    else:
        st.caption("Scientific claim review: Not performed")

    with st.expander("Review details"):
        st.write("**Decision reason:**")
        st.write(
            decision.get("reason", "Not available")
        )

        st.write("**Invalid PubMed citations:**")
        st.write(
            review.get("invalid_pmids", [])
        )

        st.write("**Potentially irrelevant articles:**")
        st.write(
            review.get("potentially_irrelevant_pmids", [])
        )

        if claim_review:
            st.write("**Scientific claim review results:**")
            st.json(claim_review)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.header("🧬 Research Dashboard")

    st.subheader("Current Session")

    question_count = sum(
        1
        for message in st.session_state.messages
        if message["role"] == "user"
    )

    st.metric(
        "Research Questions",
        question_count,
    )

    st.metric(
        "Conversation Messages",
        len(st.session_state.messages),
    )

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.research_results = []
        st.session_state.research_memory.clear()
        st.rerun()

    st.divider()

    st.subheader("Research Sources")
    st.write("🧬 NCBI Gene")
    st.write("📚 PubMed")

    st.divider()

    st.subheader("Latest Research Review")

    if st.session_state.research_results:
        latest = st.session_state.research_results[-1]

        display_review_details(latest)

        st.divider()

        st.subheader("Retrieved Sources")

        research_state = (
            latest.get("research_state") or {}
        )

        display_research_sources(research_state)

    else:
        st.caption(
            "Run a research question to see "
            "evidence and safety review results."
        )


# --------------------------------------------------
# Main interface
# --------------------------------------------------

st.title("🧬 Gene–Disease Research Assistant")

st.write(
    "Explore relationships between genes, genetic variants, "
    "and diseases using scientific evidence from "
    "NCBI Gene and PubMed."
)

st.info(
    "For biomedical research and educational purposes only. "
    "Not intended for medical diagnosis or treatment."
)

# --------------------------------------------------
# Display conversation history
# --------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# --------------------------------------------------
# Chat input
# --------------------------------------------------

question = st.chat_input(
    "Ask a gene–disease research question..."
)

# --------------------------------------------------
# Research execution
# --------------------------------------------------

if question:
    # Save the user's question
    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner(
            "Researching NCBI Gene and PubMed..."
        ):
            try:
                # Call the existing synchronous orchestrator
                result = process_research_question(
                    question,
                    st.session_state.research_memory,
                )

                # Store metadata for research dashboard
                st.session_state.research_results.append({
                    "question": question,
                    "status": result.get("status"),
                    "review": result.get("review"),
                    "claim_review": result.get("claim_review"),
                    "decision": result.get("decision"),
                    "research_state": result.get("research_state"),
                })

                decision = result.get("decision") or {}

                # Display only safety-approved answers
                if (
                    result.get("status") == "completed"
                    and decision.get("action") == "allow"
                ):
                    response = result.get("answer") or (
                        "No research summary was generated."
                    )

                else:
                    response = (
                        "⚠️ The research answer was withheld "
                        "because the evidence or scientific claims "
                        "require additional review."
                    )

            except Exception:
                # Log the traceback locally, not in the UI
                print("\n--- STREAMLIT BACKEND ERROR ---")
                traceback.print_exc()

                response = (
                    "⚠️ The research request could not be "
                    "completed. Please try again."
                )

        st.write(response)

    # Save the displayed response in chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
    })

    # Refresh dashboard statistics and review results
    st.rerun()
