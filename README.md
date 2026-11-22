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
| Planner Agent | Interprets research questions and chooses retrieval tools |
| MCP Server | Exposes tools for accessing biomedical data |
| Research Orchestrator | Coordinates planning, retrieval, synthesis, and validation |
| Synthesis Agent | Produces research summaries grounded in retrieved evidence |
| Evidence Review Agent | Checks citation validity and evidence relevance |
| Scientific Claim Verifier | Assesses claims against retrieved NCBI and PubMed evidence |
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

## 4. Technologies Used

- **Python** — Core implementation
- **OpenAI API** — LLM-based planning, synthesis, and claim review
- **Model Context Protocol (MCP)** — Standardized tool integration
- **NCBI Gene** — Gene records and biological annotations
- **PubMed / NCBI E-utilities** — Biomedical publication retrieval
- **Pydantic** — Structured response validation
- **Git and GitHub** — Version control
- **Streamlit** — Interactive chatbot interface and research dashboard

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

Launch the Streamlit chatbot from the project root:

```bash
streamlit run app.py
```

The application opens in your browser and provides:

- A chat interface for gene–disease research questions.
- Multi-turn conversation memory for follow-up research.
- NCBI Gene and PubMed evidence retrieval through MCP.
- Research source links and evidence-review results.
- Safety decisions that withhold answers when required checks fail.
- A Clear Conversation button to reset the research session.

The application requires an active internet connection and a valid OpenAI API key.

### Run Automated Tests

From the project root, run:

```bash
python -m pytest -q
```

The automated tests cover scientific claim verification, safety intervention, evidence validation, orchestration safety, and conversation memory.


## 6. Example Research Questions

The application can investigate questions such as:

- What is the PKD1 gene?
- How do PKD1 mutations affect ADPKD progression?
- What differences have been reported between PKD1 and PKD2?
- What scientific evidence supports the relationship between PKD1 variants and kidney disease progression?

The specific retrieved results depend on available NCBI and PubMed information.

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

- 20 of 20 targeted safety checks passed during initial development.
- 15 of 15 automated pytest tests passed after repository reorganization.
- Tests cover citation validation, evidence relevance, scientific claim verification, safety intervention, orchestration, and conversation memory.

### Live Integration Testing

- Successfully retrieved PKD1 gene information from NCBI Gene.
- Successfully retrieved PubMed articles through the MCP server.
- Validated the planning, retrieval, synthesis, evidence-review, and safety-decision workflow.

### Frontend Testing

- Verified multi-turn PKD1 and PKD2 research conversations.
- Confirmed that Clear Conversation resets chat history and research memory.
- Verified that backend failures produce a user-friendly error message.
- Confirmed that withheld answers are not displayed or saved to conversation memory.

These results demonstrate successful operation in the tested scenarios. They do not establish overall biomedical accuracy or guarantee that every generated claim is correct.

For detailed results, see [Evaluation Documentation](docs/evaluation.md).


## 9. Project Structure

```text
gene-disease-research-assistant/
├── app.py
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
│   ├── gene_tools.py
│   ├── pubmed_tools.py
│   └── ncbi_utils.py
├── tests/
│   ├── test_claim_verification.py
│   ├── test_intervention.py
│   ├── test_memory.py
│   ├── test_orchestrator_safety.py
│   └── test_safety.py
├── docs/
│   ├── evaluation.md
│   └── final_report_outline.md
├── outputs/
│   └── pkd1_research_summary.txt
├── mcp_client.py
├── requirements.txt
├── .gitignore
└── README.md
```

The project separates agent coordination, shared safety and memory functionality, biomedical retrieval, and automated testing into dedicated directories.

The `app.py` file provides the Streamlit interface, while `mcp_client.py` supports independent MCP integration testing.

## 10. Limitations and Future Improvements

Although the application includes evidence validation and safety checks, several limitations remain:

- **Limited evaluation dataset:** Expand testing to a larger and more diverse collection of biomedical research questions.
- **Scientific verification:** Benchmark generated claims against expert-reviewed biomedical evidence.
- **Evidence relevance:** Improve retrieval ranking beyond keyword-based relevance screening.
- **Source coverage:** Expand retrieval beyond NCBI Gene and PubMed to additional authoritative biomedical resources.
- **Human review:** Implement a dedicated interface where researchers can review withheld answers and supporting evidence.
- **Reliability:** Expand automated testing for network failures, incomplete evidence, and unavailable external services.
- **Usability:** Improve research history navigation, evidence comparison, and exportable research summaries.

The current system is intended as a research prototype, not a clinically validated decision-support tool.

## 11. Responsible Use

This application is intended for biomedical research assistance and educational exploration.

It is **not a medical device** and must not be used as a substitute for professional clinical judgment, diagnosis, or treatment advice.

The project uses publicly available, synthetic, or anonymized information and is not designed to process private patient records.

## 12. Data Sources

- [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)