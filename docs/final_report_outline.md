# Gene–Disease Research Assistant — Final Capstone Report Outline

## 1. Introduction and Problem Statement (150 words)

- Explain the challenges of biomedical literature research.
- Describe hallucinations, unreliable citations, and information overload.
- Introduce the Gene–Disease Research Assistant.
- Define the initial research scope: ADPKD, PKD1, and PKD2.

## 2. Agentic AI Architecture and Design (200 words)

- Explain why a multi-agent system was selected instead of a single-agent workflow.
- Describe the Planner, Orchestrator, Synthesis, and Evidence Review components.
- Explain the coordination strategy.
- Describe the ReAct-inspired planning, tool-use, and observation workflow.
- Explain short-term session memory.
- Explain how the planner distinguishes new research, a standalone definition, and a request to rewrite the previous answer.

## 3. Implementation and Tool Integration (200 words)

- Describe the Python-based implementation.
- Explain how the MCP server exposes biomedical retrieval tools.
- Discuss NCBI Gene and PubMed integration.
- Describe the Helix frontend, local HTTP API, and Evidence Explorer.
- Describe the NIH reference lookup and how plain-language follow-ups reuse evidence.
- Explain structured planning with Pydantic and LLM responses.
- Describe how retrieved evidence flows between components.
- Include an architecture diagram in the final report.

## 4. Safety, Guardrails, and Human Intervention (200 words)

- Describe citation verification.
- Explain scientific claim validation and evidence relevance screening.
- Discuss statistical inconsistency detection.
- Describe the allow/withhold intervention policy.
- Explain when the system requires human review.
- Acknowledge that a human-review queue is not implemented.

## 5. Evaluation and Results (200 words)

- Describe the testing methodology.
- Report the 20 original safety checks as a prototype milestone.
- Discuss the two original live research workflows and the later Helix validation for definitions, follow-ups, and API behavior.
- Explain how unsupported citations and fabricated scientific claims were tested.
- Describe the limitations of these results and what they do not establish.

## 6. Challenges, Limitations, and Future Work (150 words)

- Discuss reliability challenges in biomedical evidence retrieval.
- Explain limitations of LLM-based claim verification.
- Identify improvements to evidence ranking and evaluation coverage.
- Discuss local session storage, the lack of in-flight request cancellation, and possible improvements to evidence browsing.
- Discuss future human-in-the-loop evaluation.

## 7. Conclusion (100 words)

- Summarize the completed system.
- Explain the benefits of combining specialized agents, external tools, and evidence verification.
- Reflect on what the project demonstrates about safe and reliable agentic AI systems.

## References

- NCBI Gene
- PubMed / NCBI E-utilities
- NHGRI Talking Glossary, NCI Dictionaries, and MedlinePlus
- Relevant ADPKD research publications
- MCP documentation
- Any external technical resources referenced in the report
