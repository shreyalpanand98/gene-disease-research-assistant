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

### Run the Backend

```bash
python orchestrator.py
```

Enter a research question in the terminal and review the generated response and validation results.

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

Initial evaluation included 20 targeted checks across citation validation, evidence relevance, claim verification, intervention logic, and safety integration.

**Results:**

- 20 of 20 targeted safety checks passed.
- Two live backend research workflows completed successfully.
- The research workflow was validated using PKD1 and ADPKD questions.
- Unsupported claims, invalid citations, and selected statistical inconsistencies were detected in controlled test cases.

These results describe performance on the tested scenarios, not overall biomedical accuracy.

For detailed results, see [Evaluation Documentation](docs/evaluation.md).

## 9. Project Structure

```text
gene-disease-research-assistant/
├── gene_tools.py
├── pubmed_tools.py
├── ncbi_utils.py
├── mcp_server.py
├── planner_agent.py
├── orchestrator.py
├── synthesis_agent.py
├── evidence_review_agent.py
├── safety_guardrails.py
├── session_memory.py
├── test_safety.py
├── test_claim_verification.py
├── test_intervention.py
├── test_orchestrator_safety.py
├── test_memory.py
├── docs/
│   └── evaluation.md
├── outputs/
│   └── pkd1_research_summary.txt
├── requirements.txt
└── README.md
```

Additional prototype and development files are also included in the repository.

## 10. Limitations and Future Improvements

- Expand evaluation to larger and more diverse biomedical question sets.
- Test additional network failures, unavailable sources, and incomplete evidence.
- Improve relevance ranking beyond keyword-based screening.
- Benchmark scientific claim verification against human-reviewed examples.
- Implement a dedicated human-review workflow.
- Add a Streamlit-based chatbot interface.
- Improve usability and reporting for evidence sources.

## 11. Responsible Use

This application is intended for biomedical research assistance and educational exploration.

It is **not a medical device** and must not be used as a substitute for professional clinical judgment, diagnosis, or treatment advice.

The project uses publicly available, synthetic, or anonymized information and is not designed to process private patient records.

## 12. Data Sources

- [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)