# Evaluation Results — Gene–Disease Research Assistant

## Evaluation Objective

The evaluation assesses whether the multi-agent research assistant can retrieve publicly available biomedical evidence, generate source-grounded research summaries, validate citations and scientific claims, and withhold potentially unreliable answers.

The initial evaluation focuses on autosomal dominant polycystic kidney disease (ADPKD), particularly the PKD1 and PKD2 genes.

## Testing Methodology

The system was evaluated using synthetic test cases, controlled safety scenarios, and live queries against NCBI Gene and PubMed.

Tests covered citation validation, evidence relevance, scientific claim verification, safety interventions, conversation memory, and integration between the orchestrator and safety components.

## Test Results

| Evaluation Area | Result |
|---|---|
| Citation validation | 3/3 checks passed |
| Safety and evidence relevance | 7/7 checks passed |
| Scientific claim verification | 3/3 checks passed |
| Intervention decision logic | 5/5 checks passed |
| Orchestrator safety integration | 2/2 checks passed |
| **Total targeted safety checks** | **20/20 passed** |
| Live research workflows | 2 successful workflows |

The 100% pass rate applies only to these 20 targeted checks and should not be interpreted as a general scientific accuracy rate.

## Live Research Validation

**Scenario 1: PKD1 Gene Lookup**

The assistant correctly planned a gene-focused workflow, retrieved PKD1 information from NCBI Gene (Gene ID: 5310), produced a source-grounded response, and passed the evidence review.

**Scenario 2: PKD1 Mutations and ADPKD Progression**

The assistant selected both NCBI Gene and PubMed retrieval. Its synthesis cited retrieved PubMed articles, including PMIDs 27499327, 37509056, and 40126492. Citation review passed, and all six claims identified by the scientific claim reviewer were classified as supported.

Both live scenarios received an allow decision from the safety intervention component.

## Safety Behavior

The tests demonstrated that the system can:

- Detect nonexistent or unsupported PubMed citations.
- Identify missing required gene or literature evidence.
- Flag clearly irrelevant articles.
- Identify contradictions between statistical claims and reported p-values.
- Detect selected fabricated numerical claims and unsupported medical conclusions.
- Withhold answers when evidence review or required claim verification fails.
- Avoid saving withheld responses as successful research turns in conversation memory.

## Known Limitations

1. The test suite is relatively small and uses a limited set of scenarios.
2. LLM-based claim verification may miss subtle scientific inaccuracies or incorrectly classify evidence.
3. Keyword-based relevance screening may reject useful articles or accept superficially related articles.
4. Citation matching verifies source identifiers but does not independently prove every scientific statement.
5. Comprehensive live failure-injection testing, larger benchmark datasets, and expert review have not yet been completed.
6. Human review is represented by withholding and escalation decisions; an operational human-review queue has not been implemented.

## Evaluation Conclusion

The initial testing provides evidence that the backend's core workflow and safety controls function as intended for the selected ADPKD research scenarios. Further evaluation with broader questions, difficult negative cases, network failures, and human expert assessment is necessary before making stronger reliability claims.

The application is intended for biomedical literature research support, not clinical diagnosis or treatment recommendations.