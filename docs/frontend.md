# Helix frontend

Helix is a separate custom browser interface for the existing Gene–Disease Research Assistant. Run `python web_server.py` from an environment containing the project's backend dependencies, then open `http://127.0.0.1:8000`. No build step is required.

## Components

- `frontend/index.html`: semantic workspace, conversation navigation, onboarding prompts, evidence inspector, and dialogs.
- `frontend/styles.css`: navy/teal visual system, desktop workspace, narrow-screen navigation, accessible focus, and reduced-motion styles.
- `frontend/app.js`: API client, polling, per-answer evidence inspection, safe limited Markdown rendering, and client-side exports.
- `web_server.py`: loopback HTTP service, browser-scoped sessions, bounded research workers, progress reporting, and static asset serving.
- `agents/orchestrator.py`: runs the research workflow for the web server and terminal. The web server uses the optional `on_progress(stage, detail)` callback.

The server lazy-loads the research pipeline inside a worker. A slow dependency import does not prevent the browser from loading or responding. Up to two research requests can run concurrently across conversations; each conversation permits only one active request. Additional submissions are rejected with an actionable message.

## API

All responses are JSON except frontend assets. Successful session requests create or reuse an HttpOnly `SameSite=Strict` cookie. Session identifiers from another browser are not accessible. The service accepts only its loopback Host and rejects cross-origin requests; it does not expose CORS access.

| Method | Path | Result |
|---|---|---|
| GET | `/api/health` | Local server state and whether an API key appears configured; does not check upstream connectivity |
| GET | `/api/sessions` | Conversation summaries belonging to this browser |
| POST | `/api/sessions` | Creates an empty conversation |
| GET | `/api/sessions/{id}` | Conversation, turns, current progress, results, memory count, and explanation style |
| DELETE | `/api/sessions/{id}` | Deletes an idle conversation and its research memory |
| POST | `/api/sessions/{id}/research` | Starts research; body: `{"question":"What is PKD1?"}`; returns HTTP 202 |

Turns have `running`, `completed`, `withheld`, or `error` status. Progress contains actual stage events rather than an estimated completion percentage. The frontend polls every 1.5 seconds while active, and every seven seconds when idle. It can reconnect to ongoing work after a page refresh while the server remains running.

Results retain the backend's `review`, `claim_review`, `decision`, and `research_state` fields. The server removes `answer` unless both status and decision permit display. Memory is copied before a request and committed only for an allowed result. Failed requests show a generic message in the app and record a traceback locally. The evidence inspector may display labeled claim-review excerpts for withheld results.

## Interaction details

Starter cards populate the composer without making a paid API call. Enter submits, Shift+Enter inserts a line break, and `N` starts a new conversation when focus is outside an input. Evidence tabs support arrow keys, Home, and End. Escape closes the inspector or mobile navigation; native dialogs retain their standard keyboard behavior.

Article cards distinguish retrieval from actual citation and show journal, date, authors, and abstracts. Gene cards show official symbols, descriptions, identifiers, and source summaries. The review tab explains citation issues, heuristic relevance flags, narrow statistical checks, and each scientific claim assessment. The plan tab exposes genes, disease context, tool selection, PubMed query, and recorded workflow stages.

Ask “Explain that in simpler terms” to rewrite the latest answer that passed review. The assistant reuses that answer’s evidence and reviews the rewrite before displaying it. A new factual question still goes through normal planning and retrieval. Requests for beginner or technical language set the style for later questions in the same conversation after a successful response.

Ask “What does penetrance mean?” to look up a standalone definition. Helix searches NIH reference sources for the term and shows a short excerpt with its source link. If the term is unclear or no reference matches, Helix explains how to refine the lookup. The Evidence Explorer and exports include the retrieved references.

Markdown export includes questions, approved summaries (or withheld/error notices), and retrieved source references. JSON export contains a single turn and all available evidence/review metadata. Neither exports a withheld draft. The browser renderer escapes raw HTML and only creates HTTP(S) links; generated content cannot execute scripts. No external fonts, scripts, or analytics are loaded.

## Limits

Sessions are in memory, not durable storage. Idle sessions older than 24 hours are pruned when a new session is created. The server caps total sessions at 100 and each browser at 20. Each conversation supports 50 questions. There is no login, remote hosting, human-review queue, cancellation of in-flight LLM requests, or persistent database. These would require separate backend work.

Retrieval still uses up to three PubMed articles, and claim review is conditional. The UI does not imply full-text access, comprehensive literature coverage, or a numerical confidence score that the backend does not provide. This application is designed for research and education, not clinical use.

## Validation

```bash
python -m unittest discover -s tests -p test_web_server.py
node tests/test_frontend.mjs
node --check frontend/app.js
python -m py_compile web_server.py agents/orchestrator.py
```

The API tests use injected runners and never invoke external research services. They verify answer withholding, memory commits, failures, concurrent-request rejection, browser isolation, cross-origin rejection, and static-file boundaries. Frontend checks verify safe text/link rendering, citation links, and allow/withhold behavior in presentation and exports. The [README](../README.md#run-automated-tests) lists the full offline suite and separate live checks.

For optional browser QA without API calls, run `python tests/preview_fixture.py` and open `http://127.0.0.1:8001`. All its result content is labeled synthetic. Questions containing `withhold` or `error` exercise those states. This test server is separate from the live application on port 8000.

### Slow first startup on macOS

If a request remains at “Preparing the research engine” for several minutes, check whether the virtual environment is in a cloud-synced Desktop/Documents folder. During development, some existing `.venv` package files had macOS `dataless` flags, and import timing showed roughly one-second delays per restored file. Ensure the environment is downloaded locally, or recreate it in a non-synced local directory and run this project using that environment. The UI can load independently while research imports initialize. An “API key configured” check does not validate OpenAI or NCBI connectivity.
