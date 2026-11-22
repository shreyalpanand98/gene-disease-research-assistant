# Gene–Disease Research Assistant

**An evidence-grounded, multi-agent biomedical research assistant powered by LLMs, MCP, NCBI Gene, and PubMed.**

## 1. Project Overview

The Gene–Disease Research Assistant helps users explore relationships between genes, genetic variants, and diseases by retrieving publicly available scientific information and synthesizing it into research summaries.

The initial use case focuses on **Autosomal Dominant Polycystic Kidney Disease (ADPKD)** and its associated genes, **PKD1 and PKD2**.

Instead of relying solely on an LLM's pretrained knowledge, the application retrieves evidence from authoritative biomedical databases and checks generated responses for citation accuracy and scientific support.

This project was developed as part of the Carnegie Mellon University Agentic AI Capstone.

## 2. Problem Statement

Biomedical research involves navigating multiple sources, identifying relevant literature, comparing findings, and evaluating the strength of scientific evidence.

General-purpose LLMs can generate unsupported conclusions, fabricate citations, or misinterpret study results.

This project investigates how a multi-agent architecture with external retrieval, evidence review, and safety intervention can improve the traceability and reliability of AI-assisted biomedical research.

## 3. System Architecture

The application uses multiple specialized components:

| Component | Responsibility |
|---|---|
| Helix web app | Displays conversations, progress, sources, and review results |
| Planner Agent | Distinguishes research, standalone definitions, and requests to rephrase an answer |
| MCP Server | Exposes the NCBI Gene and PubMed retrieval tools |
| NIH reference lookup | Finds matching definitions in the NHGRI glossary, NCI dictionaries, and MedlinePlus |
| Research Orchestrator | Coordinates planning, retrieval, synthesis, and validation |
| Synthesis Agent | Produces research summaries grounded in retrieved evidence |
| Evidence Review Agent | Checks citation validity and evidence relevance |
| Scientific Claim Verifier | Checks claims against retrieved evidence for PubMed research and rewrites of reference definitions |
| Safety Guardrails | Determines whether an answer can be presented or should be withheld |
| Session Memory | Maintains context across follow-up research questions |

### Research Workflow

1. The user submits a gene–disease research question.
2. The Planner Agent identifies relevant genes and determines which retrieval tools are needed.
3. The Orchestrator invokes biomedical retrieval tools through the MCP server.
4. NCBI Gene and PubMed return public scientific evidence.
5. The Synthesis Agent generates an evidence-grounded response.
6. The Evidence Review Agent validates citations and checks evidence relevance.
7. The Scientific Claim Verifier reviews supported and unsupported scientific statements when required.
8. The Safety Guardrails either allow the answer or withhold it for human review.
9. Approved interactions are saved in session memory to support follow-up questions.

For standalone definitions, Helix checks NIH references directly and returns a short excerpt with a source link. When the term is unclear or no source matches, it offers guidance. Requests to simplify the previous answer reuse its sources and send the rewrite through the applicable evidence checks.

## 4. Technologies Used

- **Python** — Core implementation
- **OpenAI API** — LLM-based planning, synthesis, and claim review
- **Model Context Protocol (MCP)** — Standardized tool integration
- **NCBI Gene** — Gene records and biological annotations
- **PubMed / NCBI E-utilities** — Biomedical publication retrieval
- **Pydantic** — Structured response validation
- **Git and GitHub** — Version control
- **HTML, CSS, and JavaScript** — Primary Helix web interface
- **Python HTTP server** — Local API, session state, and research progress

## 5. Getting Started

### Prerequisites

- Python 3.13 or a compatible Python version
- OpenAI API key
- Internet access for external biomedical retrieval

### Installation

Clone the repository:

```bash
git clone https://github.com/shreyalpanand98/gene-disease-research-assistant.git
cd gene-disease-research-assistant
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root with your OpenAI API key:

```text
OPENAI_API_KEY=your_api_key_here
```

Never commit `.env` or API credentials to GitHub.


### Run the Application

Launch the custom **Helix** research workspace from the project root:

```bash
source .venv/bin/activate
python web_server.py
```

Open **http://127.0.0.1:8000**. Use `python web_server.py --port 8080` to select a different port.

For a password-protected web link, see the [Render deployment guide](docs/deployment.md).

The custom frontend is plain HTML, CSS, and JavaScript; there is no Node installation or frontend build step. The local HTTP server uses Python's standard library and loads the existing OpenAI/MCP research pipeline on the first question. The first request can take longer while these dependencies initialize.

Helix includes:

- Responsive navigation and starter questions for gene lookup, gene comparison, and literature research.
- Separate conversations, conversation search, follow-up context, and conversation deletion.
- Standalone definitions from the NHGRI glossary, NCI dictionaries, and MedlinePlus, with links to the matching references.
- Live backend progress for planning, retrieval or evidence reuse, synthesis, review, and the final decision. Only stages actually executed are shown.
- An evidence explorer attached to each result: human gene records, publication metadata, expandable abstracts, retrieved/cited filters, claim assessments, and the generated research plan.
- Explicit failure and withheld-answer states, retry/refine controls, and protection against duplicate submissions.
- Copyable approved answers, Markdown research exports, and JSON evidence downloads.
- Keyboard navigation, responsive layouts, reduced-motion support, and safe rendering of generated text.

Conversations and their evidence are stored **in server memory**, scoped to the browser using an HttpOnly cookie. They are not saved across server restarts. Idle sessions may be removed after 24 hours; export important results. Up to 20 conversations per browser and 50 questions per conversation are supported. Research memory retains five successful turns. Follow-up planning uses the last three questions and their gene and disease context. Ask to simplify an answer to reuse the previous answer and sources. An explicit request for simpler or more technical explanations sets the style after a successful response for the rest of that conversation. Withheld drafts are excluded from API answers and exports, and failed/withheld turns do not update research memory.

The Python backend holds the OpenAI API key. It sends questions to OpenAI for planning and sends relevant search terms to NCBI Gene, PubMed, or an NIH reference service as needed. See [frontend architecture](docs/frontend.md) for the API contract and testing instructions.

The application requires an active internet connection and a valid OpenAI API key.

### Run Automated Tests

Install the test runner, then run the offline checks from the project root. The placeholder key lets the backend initialize its OpenAI client during offline testing.

```bash
python -m pip install pytest
OPENAI_API_KEY=offline-test-key python -m pytest -q --ignore=tests/test_claim_verification.py
node tests/test_frontend.mjs
```

The HTTP tests bind a temporary loopback port. Node is only needed for the JavaScript checks, not to run the application.

Run the model-based claim-verification tests separately with a valid API key and network access:

```bash
python -m pytest -q tests/test_claim_verification.py
```

These tests use synthetic evidence and call OpenAI. Results can vary across runs.


## 6. Example Research Questions

The application can investigate questions such as:

- What is the PKD1 gene?
- How do PKD1 mutations affect ADPKD progression?
- What differences have been reported between PKD1 and PKD2?
- What scientific evidence supports the relationship between PKD1 variants and kidney disease progression?
- What does penetrance mean?
- I’m new to biology. Can you explain that answer in simpler terms?

Results depend on the records, articles, or NIH reference entries available for the question.

## 7. Safety and Reliability

The system implements several safety mechanisms:

**Citation validation:** Checks whether cited PubMed identifiers correspond to retrieved publications.

**Evidence relevance:** Screens retrieved scientific literature for relevance to the research question.

**Scientific claim verification:** Compares generated scientific claims against retrieved evidence.

**Statistical consistency checks:** Identifies selected inconsistencies between reported statistical significance and p-values.

**Human-review intervention:** Withholds responses when required validation fails or unsupported claims are identified.

**Memory protection:** Prevents withheld responses from being recorded as successful research interactions.

These mechanisms reduce certain risks but do not guarantee scientific correctness.


## 8. Evaluation Results

The research assistant was evaluated using automated safety tests, controlled failure scenarios, and live research workflows.

### Automated Evaluation

- The original prototype passed 20 targeted safety checks during initial development.
- Current offline tests cover definitions, plain-language follow-ups, the HTTP API, evidence review, and session memory. JavaScript checks cover citation links, text rendering, and exports.

### Live Integration Testing

- Successfully retrieved PKD1 gene information from NCBI Gene.
- Successfully retrieved PubMed articles through the MCP server.
- Validated the planning, retrieval, synthesis, evidence-review, and safety-decision workflow.

### Frontend Testing

- Tested progress, evidence browsing, and exports in desktop and mobile layouts using offline fixtures.
- Verified a live plain-language PKD1 follow-up and a standalone definition through the Helix API.
- Verified that the API keeps withheld drafts out of responses and omits unsuccessful turns from research memory.

These results demonstrate successful operation in the tested scenarios. They do not establish overall biomedical accuracy or guarantee that every generated claim is correct.

For detailed results, see [Evaluation Documentation](docs/evaluation.md).


## 9. Project Structure

```text
gene-disease-research-assistant/
├── web_server.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── favicon.svg
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── planner_agent.py
│   ├── synthesis_agent.py
│   └── evidence_review_agent.py
├── core/
│   ├── __init__.py
│   ├── session_memory.py
│   └── safety_guardrails.py
├── retrieval/
│   ├── __init__.py
│   ├── mcp_server.py
│   ├── definition_tools.py
│   ├── gene_tools.py
│   ├── pubmed_tools.py
│   └── ncbi_utils.py
├── tests/
│   ├── preview_fixture.py
│   ├── test_claim_verification.py
│   ├── test_definition_lookup.py
│   ├── test_explanation_followup.py
│   ├── test_frontend.mjs
│   ├── test_intervention.py
│   ├── test_memory.py
│   ├── test_orchestrator_safety.py
│   ├── test_safety.py
│   └── test_web_server.py
├── docs/
│   ├── evaluation.md
│   ├── final_report_outline.md
│   └── frontend.md
├── outputs/
│   ├── helix-desktop.jpg
│   ├── helix-mobile.jpg
│   └── pkd1_research_summary.txt
├── mcp_client.py
├── requirements.txt
├── .gitignore
└── README.md
```

The project separates agent coordination, shared safety and memory functionality, biomedical retrieval, and automated testing into dedicated directories.

Run `web_server.py` for Helix or `mcp_client.py` to check the MCP tools independently.

## 10. Limitations and Future Improvements

Although the application includes evidence validation and safety checks, several limitations remain:

- **Limited evaluation dataset:** Expand testing to a larger and more diverse collection of biomedical research questions.
- **Scientific verification:** Benchmark generated claims against expert-reviewed biomedical evidence.
- **Evidence relevance:** Improve retrieval ranking beyond keyword-based relevance screening.
- **Source coverage:** Evaluate more sources for research questions and broaden term coverage for the definition lookup.
- **Human review:** Implement a dedicated interface where researchers can review withheld answers and supporting evidence.
- **Reliability:** Expand automated testing for network failures, incomplete evidence, and unavailable external services.
- **Usability:** Add persistent conversation history and improve comparison across sources.

The current system is intended as a research prototype, not a clinically validated decision-support tool.

## 11. Responsible Use

This application is intended for biomedical research assistance and educational exploration.

It is **not a medical device** and must not be used as a substitute for professional clinical judgment, diagnosis, or treatment advice.

The project uses publicly available, synthetic, or anonymized information and is not designed to process private patient records.

## 12. Data Sources

- [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [NHGRI Talking Glossary](https://www.genome.gov/genetics-glossary)
- [NCI Dictionaries](https://www.cancer.gov/publications/dictionaries)
- [MedlinePlus Web Service](https://medlineplus.gov/about/developers/webservices/)
