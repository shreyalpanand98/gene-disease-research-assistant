
import asyncio
import json
import sys
import traceback
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agents.planner_agent import create_research_plan
from agents.synthesis_agent import synthesize_research
from agents.evidence_review_agent import (
    review_evidence,
    verify_scientific_claims
)
from core.safety_guardrails import decide_intervention
from core.session_memory import ResearchMemory

# ==================================================
# 1. EXTRACT MCP TOOL RESULTS
# ==================================================

def extract_tool_result(result):
    """
    Convert MCP tool responses into Python dictionaries.
    """

    if result.isError:
        messages = [
            item.text
            for item in result.content
            if item.type == "text"
        ]

        return {
            "status": "error",
            "message": "\n".join(messages)
        }

    if result.structuredContent is not None:
        data = result.structuredContent

        if isinstance(data, dict) and set(data) == {"result"}:
            return data["result"]

        return data

    for item in result.content:
        if item.type == "text":
            try:
                return json.loads(item.text)

            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "Tool returned invalid JSON."
                }

    return {
        "status": "error",
        "message": "No usable tool response."
    }


# ==================================================
# 2. PLANNER + MCP RESEARCH EXECUTION
# ==================================================

async def run_research(
    question: str,
    memory: ResearchMemory | None = None
) -> dict:
    """
    Generate a research plan and retrieve relevant
    evidence from NCBI Gene and PubMed through MCP.
    """

    print("\nCreating research plan...", flush=True)

    history = (
        memory.get_history()
        if memory is not None
        else []
    )

    plan = create_research_plan(
        question,
        history
    )

    print("\nGenerated plan:")
    print(json.dumps(
        plan.model_dump(),
        indent=2
    ))

    research_state = {
        "question": question,
        "plan": plan.model_dump(),
        "gene_evidence": None,
        "literature_evidence": None
    }

    # Prevent unnecessary MCP calls
    if not plan.use_gene_tool and not plan.use_pubmed_tool:
        return research_state

    server_path = (
        Path(__file__).resolve().parent.parent
        / "retrieval"
        / "mcp_server.py"
    )

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "retrieval.mcp_server"]
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            available = await session.list_tools()

            tool_names = {
                tool.name
                for tool in available.tools
            }

            # --------------------------------------
            # NCBI Gene retrieval
            # --------------------------------------

            if plan.use_gene_tool and plan.genes:

                if "lookup_ncbi_gene" not in tool_names:
                    raise RuntimeError(
                        "NCBI Gene MCP tool unavailable."
                    )

                research_state["gene_evidence"] = []

                for gene in plan.genes:

                    print(
                        f"\nCalling NCBI Gene for {gene}...",
                        flush=True
                    )

                    gene_result = await session.call_tool(
                        "lookup_ncbi_gene",
                        {"gene_name": gene}
                    )

                    gene_data = extract_tool_result(
                        gene_result
                    )

                    research_state[
                        "gene_evidence"
                    ].append(gene_data)

            # --------------------------------------
            # PubMed literature retrieval
            # --------------------------------------

            if (
                plan.use_pubmed_tool
                and plan.pubmed_query.strip()
            ):

                if "search_pubmed_articles" not in tool_names:
                    raise RuntimeError(
                        "PubMed MCP tool unavailable."
                    )

                print("\nSearching PubMed...", flush=True)

                pubmed_result = await session.call_tool(
                    "search_pubmed_articles",
                    {
                        "query": plan.pubmed_query,
                        "max_results": 3
                    }
                )

                research_state["literature_evidence"] = (
                    extract_tool_result(pubmed_result)
                )

    return research_state


# ==================================================
# 3. COMPLETE RESEARCH WORKFLOW
# ==================================================

def process_research_question(
    question: str,
    memory: ResearchMemory
) -> dict:
    """
    Run the complete research workflow:

    Planner -> MCP Tools -> Synthesis ->
    Evidence Review -> Scientific Claim Review ->
    Human-Review Decision -> Memory
    """

    # ----------------------------------------------
    # Step 1: Plan and retrieve research evidence
    # ----------------------------------------------

    research_state = asyncio.run(
        run_research(question, memory)
    )

    # ----------------------------------------------
    # Step 2: Generate research answer
    # ----------------------------------------------

    answer = synthesize_research(
        research_state
    )

    # ----------------------------------------------
    # Step 3: Deterministic evidence review
    # ----------------------------------------------

    review = review_evidence(
        research_state,
        answer
    )

    print("\n" + "=" * 60)
    print("EVIDENCE REVIEW")
    print("=" * 60)

    print("Status:", review["status"])
    print("Retrieved PMIDs:", review["retrieved_pmids"])
    print("Cited PMIDs:", review["cited_pmids"])
    print("Invalid PMIDs:", review["invalid_pmids"])
    print("Statistical issues:", review["statistical_issues"])

    # ----------------------------------------------
    # Step 4: Scientific claim verification
    # ----------------------------------------------

    plan = research_state.get("plan") or {}

    claim_review_required = bool(
        plan.get("use_pubmed_tool", False)
    )

    claim_review = None

    if (
        claim_review_required
        and not review["requires_human_review"]
    ):

        literature = (
            research_state.get("literature_evidence") or {}
        )

        usable_abstracts = [
            article
            for article in literature.get("articles", [])
            if isinstance(article, dict)
            and article.get("abstract")
            and article["abstract"] != "Abstract unavailable"
        ]

        if usable_abstracts:

            print(
                "\nVerifying scientific claims...",
                flush=True
            )

            try:
                claim_review = verify_scientific_claims(
                    research_state,
                    answer
                )

                print("\n" + "=" * 60)
                print("SCIENTIFIC CLAIM REVIEW")
                print("=" * 60)

                for assessment in claim_review.assessments:
                    print("\nClaim:", assessment.claim)
                    print("Verdict:", assessment.verdict)
                    print(
                        "Explanation:",
                        assessment.explanation
                    )

            except Exception as error:
                print(
                    "\nClaim verification failed:",
                    error
                )

                # Leave claim_review as None so
                # the intervention policy withholds.
                claim_review = None

    # ----------------------------------------------
    # Step 5: Final safety decision
    # ----------------------------------------------

    decision = decide_intervention(
        citation_review=review,
        claim_review=claim_review,
        claim_review_required=claim_review_required
    )

    print("\n" + "=" * 60)
    print("SAFETY DECISION")
    print("=" * 60)

    print("Action:", decision["action"])
    print("Reason:", decision["reason"])

    # ----------------------------------------------
    # Step 6: Enforce safety decision
    # ----------------------------------------------

    if decision["action"] != "allow":

        print("\nDraft answer withheld for review.")

        return {
            "status": "withheld",
            "answer": None,
            "review": review,
            "claim_review": (
                claim_review.model_dump()
                if claim_review is not None
                else None
            ),
            "decision": decision,
            "research_state": research_state
        }

    # ----------------------------------------------
    # Step 7: Save successful research interaction
    # ----------------------------------------------

    memory.add_turn(
        question=question,
        plan=research_state["plan"],
        answer=answer
    )

    return {
        "status": "completed",
        "answer": answer,
        "review": review,
        "claim_review": (
            claim_review.model_dump()
            if claim_review is not None
            else None
        ),
        "decision": decision,
        "research_state": research_state
    }


# ==================================================
# 4. INTERACTIVE TERMINAL APPLICATION
# ==================================================

if __name__ == "__main__":

    memory = ResearchMemory(max_turns=5)

    print("Gene-Disease Research Assistant")
    print("Type 'exit' to quit or 'clear' to reset memory.")

    while True:

        try:
            question = input("\nYou: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if question.lower() == "clear":
            memory.clear()
            print("Conversation memory cleared.")
            continue

        if not question:
            continue

        try:

            result = process_research_question(
                question,
                memory
            )

            if result["status"] == "completed":

                print("\nAssistant:")
                print(result["answer"])

            else:

                print(
                    "\nAssistant: I couldn't provide a "
                    "sufficiently verified research answer."
                )

                print(
                    "Reason:",
                    result["decision"]["reason"]
                )

            print(
                f"\nMemory: {len(memory.get_history())} "
                "research turns stored."
            )

        except Exception as error:

            print("\nResearch failed:", error)

            traceback.print_exception(error)

            print(
                "This interaction was not saved."
            )
