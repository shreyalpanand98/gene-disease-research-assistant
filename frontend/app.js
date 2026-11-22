'use strict';

const $ = (selector) => document.querySelector(selector);
const icons = {
  chat: '<path d="M5 5h14v11H9l-4 3V5Z"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/>',
  external: '<path d="M14 4h6v6M20 4l-9 9M10 4H4v16h16v-6"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .6-1.5 1-1.5 2M12 17h.01"/>',
  download: '<path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5"/>',
  book: '<path d="M12 5v15M3 4c3-1 6 0 9 2 3-2 6-3 9-2v14c-3-1-6 0-9 2-3-2-6-3-9-2V4Z"/>',
  shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
  dna: '<path d="M7 2c0 9 10 11 10 20M17 2C17 11 7 13 7 22M7 4h10M9 8h6M9 16h6M7 20h10"/>',
  compare: '<rect x="3" y="5" width="6" height="14" rx="1"/><rect x="15" y="5" width="6" height="14" rx="1"/><path d="M12 3v18"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  spark: '<path d="m12 3 2.7 6.3L21 12l-6.3 2.7L12 21l-2.7-6.3L3 12l6.3-2.7L12 3Z"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  trash: '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
  copy: '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  retry: '<path d="M4 10a8 8 0 1 1 1 7M4 3v7h7"/>',
};
function icon(name) { return `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.spark}</svg>`; }
document.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = icon(el.dataset.icon); });
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = { sessions: [], current: null, selected: null, tab: 'sources', sourceFilter: 'all', sending: false, online: false, deleting: null, loading: false };
let toastTimer;
let pollTimer;
let selectionVersion = 0;
let lastConversation = '';
let lastEvidence = '';
let lastHistory = '';
function toast(message) { $('#toast').textContent = message; $('#toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 6000); }
function setConnection(message, ok) { $('#connection').innerHTML = `<span class="connection-dot"></span>${escapeHTML(message)}`; $('#connection').classList.toggle('offline', !ok); }
async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json' }, signal: controller.signal });
    const data = await response.json();
    if (!response.ok) { const error = new Error(data.error || 'The request could not be completed.'); error.status = response.status; throw error; }
    state.online = true;
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The connection timed out. Your research may still be running; reconnect before submitting again.');
    if (error instanceof TypeError) throw new Error('Cannot reach the local server. Start web_server.py and try again.');
    throw error;
  } finally { clearTimeout(timeout); }
}
const post = (path, body = {}) => api(path, { method: 'POST', body: JSON.stringify(body) });
function allowed(turn) { return turn?.status === 'completed' && turn.result?.status === 'completed' && turn.result?.decision?.action === 'allow'; }
function safeURL(value) { try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : null; } catch { return null; } }
function link(url, label) { const safe = safeURL(url); return safe ? `<a href="${escapeHTML(safe)}" target="_blank" rel="noopener noreferrer">${escapeHTML(label)}</a>` : escapeHTML(label); }
function pubmed(pmid) { return /^\d+$/.test(String(pmid)) ? `https://pubmed.ncbi.nlm.nih.gov/${pmid}/` : ''; }

// Deliberately small Markdown renderer: never insert model-generated HTML.
function inline(text) {
  const tokens = [];
  const hold = html => { tokens.push(html); return `\u0000${tokens.length - 1}\u0000`; };
  text = String(text).replace(/\u0000/g, '');
  text = text.replace(/`([^`]+)`/g, (_, code) => hold(`<code>${escapeHTML(code)}</code>`));
  text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, label, url) => hold(link(url, label)));
  text = text.replace(/https?:\/\/[^\s<>]+/g, url => {
    const trimmed = url.replace(/[).,;]+$/, '');
    return hold(link(trimmed, trimmed)) + url.slice(trimmed.length);
  });
  text = text.replace(/\b(PMIDs?\s*:?\s*)(\d{5,9}(?:\s*[,;]\s*\d{5,9})*)/gi, (_, prefix, ids) => hold(escapeHTML(prefix) + ids.replace(/\d{5,9}/g, id => link(pubmed(id), id))));
  text = escapeHTML(text).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
  return text.replace(/\u0000(\d+)\u0000/g, (_, index) => tokens[Number(index)] || '');
}
function markdown(text) {
  const lines = String(text || '').split('\n');
  let html = '', paragraph = [], list = null, code = null;
  const flush = () => { if (paragraph.length) { html += `<p>${inline(paragraph.join(' '))}</p>`; paragraph = []; } if (list) { html += `</${list}>`; list = null; } };
  for (const line of lines) {
    if (/^```/.test(line)) { flush(); if (code !== null) { html += `<pre><code>${escapeHTML(code.join('\n'))}</code></pre>`; code = null; } else code = []; continue; }
    if (code !== null) { code.push(line); continue; }
    if (!line.trim()) { flush(); continue; }
    const heading = line.match(/^#{1,6}\s+(.+)/);
    const bullet = line.match(/^\s*[-*+]\s+(.+)/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.+)/);
    if (heading) { flush(); html += `<h3>${inline(heading[1])}</h3>`; }
    else if (bullet || numbered) { const tag = bullet ? 'ul' : 'ol'; if (paragraph.length || (list && list !== tag)) flush(); if (!list) { html += `<${tag}>`; list = tag; } html += `<li>${inline((bullet || numbered)[1])}</li>`; }
    else if (line.startsWith('> ')) { flush(); html += `<blockquote>${inline(line.slice(2))}</blockquote>`; }
    else { if (list) flush(); paragraph.push(line); }
  }
  flush();
  if (code !== null) html += `<pre><code>${escapeHTML(code.join('\n'))}</code></pre>`;
  return html;
}

function sources(turn) {
  const research = turn?.result?.research_state || {};
  const geneData = research.gene_evidence || [];
  const literature = research.literature_evidence || {};
  return { genes: (Array.isArray(geneData) ? geneData : [geneData]).filter(g => g && g.status === 'found'), articles: (Array.isArray(literature) ? literature : literature.articles || []).filter(a => a && typeof a === 'object') };
}
function badge(turn) {
  const definition = turn.result?.research_state?.definition_lookup;
  if (allowed(turn) && definition) {
    const labels = { found: 'Reference definition', clarify: 'Clarification needed', not_found: 'No matching definition', unavailable: 'Sources unavailable' };
    return `<span class="badge ${definition.status === 'found' ? '' : 'neutral'}">${labels[definition.status] || 'Definition lookup'}</span>`;
  }
  if (allowed(turn)) return '<span class="badge">Automated checks passed</span>';
  if (turn.status === 'running') return '<span class="badge neutral">Research in progress</span>';
  if (turn.status === 'error') return '<span class="badge error">Request failed</span>';
  return '<span class="badge warning">Answer withheld</span>';
}
function dateLabel(timestamp) { return new Date(timestamp * 1000).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); }
function renderHistory() {
  const term = $('#history-search').value.toLowerCase().trim();
  const sessions = state.sessions.filter(s => s.title.toLowerCase().includes(term));
  const signature = JSON.stringify([sessions, state.current?.id, state.sending, term]);
  if (signature === lastHistory) return;
  lastHistory = signature;
  $('#session-count').textContent = state.sessions.length;
  $('#session-list').innerHTML = sessions.length ? sessions.map(s => `<div class="session-item ${s.id === state.current?.id ? 'selected' : ''}"><button class="session-select" data-session="${escapeHTML(s.id)}" ${state.sending ? 'disabled' : ''} ${s.id === state.current?.id ? 'aria-current="page"' : ''}><span>${escapeHTML(s.title)}</span><small>${s.busy ? 'Researching…' : `${dateLabel(s.updated_at)} · ${s.turn_count} question${s.turn_count === 1 ? '' : 's'}`}</small></button><button class="session-delete" data-delete="${escapeHTML(s.id)}" aria-label="Delete ${escapeHTML(s.title)}" ${s.busy || state.sending ? 'disabled' : ''}>${icon('trash')}</button></div>`).join('') : `<p class="history-empty">${term ? 'No matching conversations.' : 'A space for your questions.<br>Your conversations will appear here.'}</p>`;
}
function currentTurn() { return state.current?.turns.find(t => t.id === state.selected); }
function renderConversation() {
  const turns = state.current?.turns || [];
  const signature = JSON.stringify([turns, state.selected]);
  if (signature === lastConversation) return;
  lastConversation = signature;
  $('#conversation').innerHTML = turns.map(turn => {
    const { genes, articles } = sources(turn);
    const definition = turn.result?.research_state?.definition_lookup;
    const references = definition?.sources || [];
    const sourceCount = genes.length + articles.length + references.length;
    const sourceSummary = definition ? `${references.length} reference${references.length === 1 ? '' : 's'}` : `${genes.length} gene record${genes.length === 1 ? '' : 's'} · ${articles.length} article${articles.length === 1 ? '' : 's'}`;
    let content;
    if (turn.status === 'running') content = `<div class="research-progress" role="status"><div class="progress-title"><span class="spinner"></span>Following the evidence</div><div class="progress-stage">${escapeHTML(turn.detail)}</div><div class="progress-events">${turn.events.map(e => `<span>${escapeHTML(e.stage)}</span>`).join('')}</div></div>`;
    else if (allowed(turn)) content = `<div class="answer-text">${markdown(turn.result.answer || 'No summary was returned.')}</div>`;
    else if (turn.status === 'error') content = `<div class="status-message error"><strong>We couldn’t complete this research.</strong><p>${escapeHTML(turn.error)}</p></div>`;
    else content = `<div class="status-message"><strong>This answer needs further review.</strong><p>${escapeHTML(turn.result?.decision?.reason || 'The available evidence did not pass the required checks.')} The draft answer has been withheld. You can still inspect the retrieved sources and review findings.</p></div>`;
    const elapsed = turn.finished_at ? Math.max(1, Math.round(turn.finished_at - turn.started_at)) : null;
    return `<article class="turn" id="turn-${escapeHTML(turn.id)}"><div class="question-block"><span class="avatar" aria-hidden="true">R</span><p>${escapeHTML(turn.question)}</p></div><div class="answer-block"><div class="answer-heading"><span class="avatar assistant" aria-hidden="true">✳</span><strong>Helix</strong>${badge(turn)}</div>${content}${turn.status !== 'running' ? `<div class="answer-actions">${turn.result ? `<button class="subtle-button ${state.selected === turn.id ? 'selected' : ''}" data-evidence="${escapeHTML(turn.id)}">${icon('layers')} Explore evidence <span>${sourceCount}</span></button>` : ''}${allowed(turn) ? `<button class="subtle-button" data-copy="${escapeHTML(turn.id)}" aria-label="Copy research summary">${icon('copy')} Copy</button><button class="subtle-button" data-export="${escapeHTML(turn.id)}" aria-label="Download research summary">${icon('download')}</button>` : `<button class="subtle-button" data-retry="${escapeHTML(turn.id)}" ${state.current.busy ? 'disabled' : ''}>${icon('retry')} ${turn.status === 'error' ? 'Retry' : 'Refine question'}</button>`}<span class="answer-meta">${elapsed ? `${elapsed}s · ` : ''}${sourceSummary}</span></div>` : ''}</div></article>`;
  }).join('');
}
function render() {
  const hasTurns = !!state.current?.turns.length;
  $('#main-panel').classList.toggle('has-conversation', hasTurns);
  $('#welcome').hidden = hasTurns;
  $('#conversation').hidden = !hasTurns;
  $('#page-title').textContent = hasTurns ? 'Follow the evidence.' : 'A little curiosity. A lot of evidence.';
  $('#page-description').textContent = hasTurns ? 'Your questions, the findings, and the sources behind them.' : 'Explore the connections between genes, disease, and discovery.';
  $('#export-session').hidden = !hasTurns;
  $('#export-session').disabled = !!state.current?.busy;
  $('#new-session').disabled = state.sending;
  $('#submit-question').disabled = state.sending || state.loading || !!state.current?.busy || !$('#question').value.trim();
  $('#submit-question span:first-child').textContent = state.current?.busy ? 'Researching' : state.sending ? 'Starting' : 'Research';
  $('#question').placeholder = hasTurns ? 'Ask a follow-up, compare genes, or explore a new question…' : 'Ask about a gene, a disease, or the science connecting them…';
  const style = state.current?.explanation_style;
  const conversationHint = style === 'beginner' ? 'Plain language for this conversation' : style === 'technical' ? 'Technical explanations for this conversation' : 'Try “Explain that in simpler terms” as a follow-up.';
  const contextHint = state.current?.busy ? 'Working on your answer. You can draft a follow-up while you wait.' : hasTurns ? conversationHint : 'Your next discovery starts with a good question.';
  $('#context-line').innerHTML = `${icon('spark')}<span>${escapeHTML(contextHint)}</span>`;
  renderHistory(); renderConversation(); renderEvidence();
}
function renderEvidence(force = false) {
  const turn = currentTurn();
  const visible = !!turn?.result;
  $('#evidence-panel').hidden = !visible;
  $('#workspace-body').classList.toggle('inspector-open', visible);
  if (!visible) { lastEvidence = ''; return; }
  const signature = JSON.stringify([turn, state.tab, state.sourceFilter]);
  if (!force && signature === lastEvidence) return;
  lastEvidence = signature;
  const reuseNote = turn.result.research_state?.evidence_reused ? '<p class="inspector-note">This explanation uses the sources from the previous answer.</p>' : '';
  $('#evidence-summary').innerHTML = `<p class="inspector-question">${escapeHTML(turn.question)}</p>${badge(turn)}${reuseNote}`;
  document.querySelectorAll('[data-tab]').forEach(button => { const selected = button.dataset.tab === state.tab; button.setAttribute('aria-selected', String(selected)); button.tabIndex = selected ? 0 : -1; });
  $('#evidence-content').setAttribute('aria-labelledby', `tab-${state.tab}`);
  const renderers = { sources: renderSources, review: renderReview, plan: renderPlan };
  $('#evidence-content').innerHTML = renderers[state.tab](turn) + `<div class="inspector-note"><button class="subtle-button" data-json="${escapeHTML(turn.id)}">${icon('download')} Download research data</button></div>`;
}
function renderSources(turn) {
  const definition = turn.result.research_state?.definition_lookup;
  if (definition) {
    return definition.sources.length ? definition.sources.map(source => `<article class="source-card"><div class="source-card-top">${escapeHTML(source.publisher)}</div><h3>${link(source.url, source.title)}</h3><p>${escapeHTML(source.text)}</p></article>`).join('') : '<p class="inspector-note">No matching reference was available for this request.</p>';
  }
  const { genes, articles } = sources(turn);
  const cited = new Set((turn.result.review?.cited_pmids || []).map(String));
  const relevance = new Map((turn.result.review?.article_relevance || []).map(a => [String(a.pmid), a.relevance]));
  const visible = state.sourceFilter === 'cited' ? articles.filter(a => cited.has(String(a.pmid))) : articles;
  return `<div class="evidence-counts"><div class="evidence-count"><strong>${genes.length}</strong>Gene records</div><div class="evidence-count"><strong>${articles.length}</strong>Articles retrieved</div><div class="evidence-count"><strong>${articles.filter(a => cited.has(String(a.pmid))).length}</strong>${allowed(turn) ? 'Articles cited' : 'Cited in draft'}</div></div>${genes.length ? '<h3 class="evidence-section-title">NCBI GENE</h3>' : ''}${genes.map(g => `<article class="source-card"><div class="source-card-top"><span>HOMO SAPIENS</span><span>Gene ID ${escapeHTML(g.gene_id)}</span></div><h3>${link(g.source, g.symbol)}</h3><p>${escapeHTML(g.description)}</p>${g.summary ? `<details><summary>Read gene summary</summary><p>${escapeHTML(g.summary)}</p></details>` : ''}</article>`).join('')}${articles.length ? `<h3 class="evidence-section-title">PUBMED LITERATURE</h3><div class="source-filters"><button data-filter="all" class="filter-button ${state.sourceFilter === 'all' ? 'active' : ''}" aria-pressed="${state.sourceFilter === 'all'}">All retrieved</button><button data-filter="cited" class="filter-button ${state.sourceFilter === 'cited' ? 'active' : ''}" aria-pressed="${state.sourceFilter === 'cited'}">${allowed(turn) ? 'Cited only' : 'Cited in draft'}</button></div>` : ''}${visible.map(a => `<article class="source-card"><div class="source-card-top"><span>PMID ${escapeHTML(a.pmid)}</span><span class="badge ${cited.has(String(a.pmid)) ? '' : 'neutral'}">${cited.has(String(a.pmid)) ? (allowed(turn) ? 'Cited' : 'Draft citation') : 'Retrieved'}</span></div><h3>${link(pubmed(a.pmid), a.title || 'Untitled article')}</h3><p class="source-meta">${escapeHTML(a.journal || 'Journal unavailable')} · ${escapeHTML(a.publication_date || 'Date unavailable')}</p><p class="source-meta">${escapeHTML((a.authors || []).slice(0, 3).join(', '))}${a.authors?.length > 3 ? ' et al.' : ''}</p>${relevance.get(String(a.pmid)) === 'potentially_irrelevant' ? '<span class="badge warning">Relevance flagged</span>' : ''}<details><summary>Read abstract</summary><p>${escapeHTML(a.abstract || 'Abstract unavailable')}</p></details></article>`).join('')}${!genes.length && !articles.length ? '<p class="inspector-note">No usable source records were returned for this question. Check the review for more context.</p>' : !visible.length && articles.length ? '<p class="inspector-note">No retrieved articles were cited in this answer.</p>' : ''}<p class="inspector-note">The backend retrieves up to three PubMed articles. This is a focused evidence sample, not a systematic literature review.</p>`;
}
function renderReview(turn) {
  if (turn.result.research_state?.definition_lookup) {
    const review = turn.result.review;
    if (!review) return '<p class="inspector-note">This lookup ended before a definition was available to review.</p>';
    if (review.invalid_reference_citation) return '<p class="inspector-note">The source citation was missing or did not match a retrieved reference.</p>';
    if (!turn.result.research_state.evidence_reused) return '<p class="inspector-note">Helix displayed an excerpt from a matching NIH reference and checked the source link.</p>';
  }
  const { review = {}, claim_review: claims, decision = {} } = turn.result;
  const assessments = claims?.assessments || [];
  const invalid = review.invalid_pmids || [];
  const irrelevant = review.potentially_irrelevant_pmids || [];
  const issues = review.statistical_issues || [];
  const human = { supported: 'Supported', contradicted: 'Contradicted', insufficient_evidence: 'Insufficient evidence' };
  return `<div class="review-summary"><strong>${allowed(turn) ? 'Available automated checks passed' : 'Additional review is required'}</strong><p>${escapeHTML(decision.reason)}</p></div><div class="review-check"><span>Evidence review</span><span class="badge ${review.status === 'passed' ? '' : 'warning'}">${escapeHTML((review.status || 'Unavailable').replaceAll('_', ' '))}</span></div><div class="review-check"><span>Invalid PubMed citations</span><span>${invalid.length}</span></div>${invalid.length ? `<p class="inspector-note">Flagged identifiers: ${invalid.map(escapeHTML).join(', ')}</p>` : ''}<div class="review-check"><span>Potentially irrelevant articles</span><span>${irrelevant.length}</span></div>${irrelevant.length ? `<p class="inspector-note">${irrelevant.map(id => link(pubmed(id), `PMID ${id}`)).join(' · ')}</p>` : ''}<div class="review-check"><span>Statistical issues flagged</span><span>${issues.length}</span></div>${issues.map(issue => `<div class="claim-card"><span class="badge warning">Statistical consistency</span><blockquote>${escapeHTML(issue.claim)}</blockquote><p>${escapeHTML(issue.reason)}</p></div>`).join('')}<h3 class="evidence-section-title">SCIENTIFIC CLAIM ASSESSMENTS</h3>${claims ? `<p class="inspector-note">${escapeHTML(claims.overall_assessment || '')}</p>${!allowed(turn) ? '<p class="inspector-note">The following are review excerpts from a withheld draft, not approved findings.</p>' : ''}${assessments.map(c => `<article class="claim-card"><span class="badge ${c.verdict === 'supported' ? '' : 'warning'}">${escapeHTML(human[c.verdict] || c.verdict)}</span><blockquote>${escapeHTML(c.claim)}</blockquote><p>${escapeHTML(c.explanation)}</p><div class="claim-links">${(c.supporting_pmids || []).map(id => link(pubmed(id), `PMID ${id}`)).join('')}</div></article>`).join('')}${!assessments.length ? '<p class="inspector-note">No scientific claims were assessed.</p>' : ''}` : `<p class="inspector-note">${turn.result.research_state?.plan?.use_pubmed_tool ? 'Scientific claim review was not completed. It can be skipped when earlier evidence checks fail or usable abstracts are unavailable.' : 'Scientific claim review was not required for this gene-only workflow. Citation and evidence checks still apply.'}</p>`}<p class="inspector-note">These checks screen for selected problems. They do not guarantee scientific accuracy or replace expert review.</p>`;
}
function renderPlan(turn) {
  const plan = turn.result.research_state?.plan || {};
  return `<div class="plan-field"><label>RESEARCH OBJECTIVE</label><p>${escapeHTML(plan.research_goal || 'No plan available.')}</p></div><div class="plan-field"><label>GENES IN FOCUS</label>${plan.genes?.length ? plan.genes.map(g => `<span class="gene-chip">${escapeHTML(g)}</span>`).join('') : '<p>No specific gene identified.</p>'}</div><div class="plan-field"><label>DISEASE CONTEXT</label><p>${escapeHTML(plan.disease || 'No specific disease identified.')}</p></div><div class="plan-field"><label>SELECTED SOURCES</label><p>${[plan.use_gene_tool ? 'NCBI Gene' : null, plan.use_pubmed_tool ? 'PubMed' : null].filter(Boolean).join(' + ') || (plan.intent === 'definition' || turn.result.research_state?.definition_lookup ? 'NIH reference sources' : 'No retrieval tools selected.')}</p></div>${plan.pubmed_query ? `<div class="plan-field"><label>PUBMED SEARCH QUERY</label><code class="query-code">${escapeHTML(plan.pubmed_query)}</code></div>` : ''}<h3 class="evidence-section-title">RESEARCH ACTIVITY</h3>${turn.events.map(e => `<div class="plan-field"><label>${escapeHTML(e.stage.toUpperCase())}</label><p>${escapeHTML(e.detail)}</p></div>`).join('')}<p class="inspector-note">Follow-up planning uses recent questions and their gene and disease context.</p>`;
}

async function refreshSessions() { state.sessions = (await api('/api/sessions')).sessions; renderHistory(); }
async function selectSession(id) {
  if (state.sending) return;
  const version = ++selectionVersion;
  state.loading = true; render();
  try {
    const session = await api(`/api/sessions/${encodeURIComponent(id)}`);
    if (version !== selectionVersion) return;
    state.current = session; state.selected = null; state.sourceFilter = 'all';
    try { sessionStorage.setItem('helix-session', id); } catch { /* Storage is optional. */ }
    $('#sidebar').classList.remove('open'); $('#menu-button').setAttribute('aria-expanded', 'false');
    render();
    $('#main-panel').scrollIntoView({ block: 'start' });
  } catch (error) { if (version === selectionVersion) toast(error.message); }
  finally { if (version === selectionVersion) { state.loading = false; render(); } }
}
function newSession() {
  if (state.sending) return;
  selectionVersion++; state.current = null; state.selected = null; state.loading = false;
  try { sessionStorage.removeItem('helix-session'); } catch { /* Optional. */ }
  $('#question').value = ''; $('#sidebar').classList.remove('open'); $('#menu-button').setAttribute('aria-expanded', 'false');
  render(); $('#question').focus(); window.scrollTo({ top: 0 });
}
async function submitQuestion(event) {
  event?.preventDefault();
  const question = $('#question').value.trim();
  if (!question || state.sending || state.loading || state.current?.busy) return;
  state.sending = true; render();
  try {
    if (!state.current) {
      state.current = await post('/api/sessions');
      try { sessionStorage.setItem('helix-session', state.current.id); } catch { /* Optional. */ }
    }
    state.current = await post(`/api/sessions/${state.current.id}/research`, { question });
    state.selected = null;
    if ($('#question').value.trim() === question) $('#question').value = '';
    await refreshSessions(); render();
    $('#conversation').lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) { toast(error.message); }
  finally { state.sending = false; render(); }
}
async function poll() {
  const pollingId = state.current?.id;
  try {
    if (!state.sending && !state.loading) {
      const id = state.current?.id;
      const version = selectionVersion;
      if (id) {
        const updated = await api(`/api/sessions/${id}`);
        if (id === state.current?.id && version === selectionVersion && !state.sending) {
          const wasBusy = state.current.busy;
          state.current = updated;
          if (wasBusy && !updated.busy) {
            const latest = updated.turns.at(-1);
            const definition = latest?.result?.research_state?.definition_lookup;
            if (latest?.result && (!definition || definition.sources.length)) {
              state.selected = latest.id; state.tab = 'sources'; state.sourceFilter = 'all';
            }
            if (definition && latest.status === 'completed') {
              toast(definition.status === 'found' ? 'Definition ready. You can open the source for more detail.' : 'Definition lookup complete. See the conversation for details.');
            } else {
              toast(latest.status === 'completed' ? 'Research complete. Explore the evidence behind your answer.' : latest.status === 'withheld' ? 'Research finished. The answer was withheld; review details are available.' : 'Research failed. You can retry this question.');
            }
          }
          render();
        }
      }
      await refreshSessions();
      const health = await api('/api/health');
      setConnection(health.configured ? 'Local server connected' : 'API key required', health.configured);
    }
  } catch (error) {
    state.online = false; setConnection('Connection interrupted', false);
    if (error.status === 404 && state.current?.id === pollingId) { newSession(); toast('This research session is no longer available. The server may have restarted.'); }
  } finally { pollTimer = setTimeout(poll, state.current?.busy || !state.online ? 1500 : 7000); }
}
function exportText(turn) {
  const { genes, articles } = sources(turn);
  const references = turn.result?.research_state?.definition_lookup?.sources || [];
  return `## ${turn.question}\n\n${allowed(turn) ? turn.result.answer : turn.status === 'error' ? 'Request failed. No research answer was produced.' : 'Answer withheld. ' + (turn.result?.decision?.reason || '')}\n\n### Sources retrieved\n\n${genes.map(g => `- ${g.symbol}: ${g.source}`).join('\n')}\n${articles.map(a => `- ${a.title} (${a.journal || ''}, ${a.publication_date || ''}). PMID ${a.pmid}: ${pubmed(a.pmid)}`).join('\n')}\n${references.map(source => `- ${source.publisher}: ${source.url}`).join('\n')}\n\nAutomated evidence review: ${turn.result?.review?.status || 'Not completed'}.\n`;
}
function download(filename, content, type) { const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
function exportMarkdown(turns) {
  const now = new Date();
  const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  download(`helix-research-${date}.md`, `# Helix research notes\n\nFor research and education only. Automated checks do not guarantee scientific accuracy.\n\n${turns.map(exportText).join('\n---\n\n')}`, 'text/markdown;charset=utf-8');
}

$('#question-form').addEventListener('submit', submitQuestion);
$('#question').addEventListener('input', () => { $('#submit-question').disabled = state.sending || state.loading || !!state.current?.busy || !$('#question').value.trim(); });
$('#question').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); submitQuestion(); } });
$('#new-session').addEventListener('click', newSession);
$('#workspace-button').addEventListener('click', () => { $('#sidebar').classList.remove('open'); $('#question').focus(); });
$('#history-search').addEventListener('input', renderHistory);
$('#menu-button').addEventListener('click', () => { const open = $('#sidebar').classList.toggle('open'); $('#menu-button').setAttribute('aria-expanded', String(open)); });
$('#close-evidence').addEventListener('click', () => { const turnId = state.selected; state.selected = null; render(); document.querySelector(`[data-evidence="${turnId}"]`)?.focus(); });
['#about-button', '#help-button'].forEach(id => $(id).addEventListener('click', () => $('#about-dialog').showModal()));
$('#close-about').addEventListener('click', () => $('#about-dialog').close());
$('#cancel-delete').addEventListener('click', () => $('#delete-dialog').close());
$('#confirm-delete').addEventListener('click', async () => {
  const id = state.deleting;
  $('#confirm-delete').disabled = true;
  try { await api(`/api/sessions/${id}`, { method: 'DELETE' }); if (state.current?.id === id) newSession(); await refreshSessions(); $('#delete-dialog').close(); toast('Conversation deleted.'); }
  catch (error) { toast(error.message); }
  finally { $('#confirm-delete').disabled = false; }
});
$('#export-session').addEventListener('click', () => { if (state.current) exportMarkdown(state.current.turns.filter(t => t.status !== 'running')); });
document.addEventListener('click', async event => {
  const button = event.target.closest('button');
  if (!button || button.disabled) return;
  const data = button.dataset;
  if (data.prompt) { $('#question').value = data.prompt; $('#question').focus(); render(); }
  if (data.session) selectSession(data.session);
  if (data.delete) { state.deleting = data.delete; $('#delete-dialog').showModal(); }
  if (data.evidence) { state.selected = data.evidence; state.tab = 'sources'; state.sourceFilter = 'all'; render(); $('#close-evidence').focus(); }
  if (data.tab) { state.tab = data.tab; renderEvidence(); }
  if (data.filter) { state.sourceFilter = data.filter; renderEvidence(); document.querySelector(`[data-filter="${data.filter}"]`)?.focus(); }
  const turnId = data.copy || data.export || data.retry || data.json;
  const turn = state.current?.turns.find(t => t.id === turnId);
  if (!turn) return;
  if (data.copy && allowed(turn)) { try { await navigator.clipboard.writeText(turn.result.answer); toast('Research summary copied.'); } catch { toast('Clipboard access is unavailable. Use Download to save the summary.'); } }
  if (data.export && allowed(turn)) exportMarkdown([turn]);
  if (data.retry) { $('#question').value = turn.question; $('#question').focus(); render(); if (turn.status === 'error') submitQuestion(); }
  if (data.json) { const clean = structuredClone(turn); if (!allowed(turn) && clean.result) clean.result.answer = null; download(`helix-evidence-${turn.id}.json`, JSON.stringify(clean, null, 2), 'application/json'); }
});
$('.inspector-tabs').addEventListener('keydown', event => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  event.preventDefault(); const tabs = ['sources', 'review', 'plan']; const index = tabs.indexOf(state.tab);
  state.tab = event.key === 'Home' ? tabs[0] : event.key === 'End' ? tabs[2] : tabs[(index + (event.key === 'ArrowRight' ? 1 : 2)) % 3];
  renderEvidence(); $(`#tab-${state.tab}`).focus();
});
document.addEventListener('keydown', event => {
  const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || document.activeElement.isContentEditable;
  if (!typing && !event.metaKey && !event.ctrlKey && !event.altKey && event.key.toLowerCase() === 'n' && !document.querySelector('dialog[open]')) { event.preventDefault(); newSession(); }
  if (event.key === 'Escape') { $('#sidebar').classList.remove('open'); $('#menu-button').setAttribute('aria-expanded', 'false'); if (!document.querySelector('dialog[open]')) { state.selected = null; render(); } }
});
document.addEventListener('pointerdown', event => { if (window.innerWidth <= 760 && !event.target.closest('#sidebar, #menu-button')) { $('#sidebar').classList.remove('open'); $('#menu-button').setAttribute('aria-expanded', 'false'); } });
async function init() {
  render();
  try {
    await refreshSessions();
    const health = await api('/api/health');
    setConnection(health.configured ? 'Local server connected' : 'API key required', health.configured);
    if (!health.configured) toast('Add OPENAI_API_KEY to the project .env file to enable live research.');
    let saved; try { saved = sessionStorage.getItem('helix-session'); } catch { /* Optional. */ }
    if (saved && state.sessions.some(s => s.id === saved)) await selectSession(saved);
  } catch (error) { setConnection('Server unavailable', false); toast(error.message); }
  pollTimer = setTimeout(poll, 1500);
}
init();
