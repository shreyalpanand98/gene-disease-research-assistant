// Offline checks for safe rendering and withheld-answer handling. No browser required.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../frontend/app.js', import.meta.url), 'utf8');
const nodes = new Map();
const context = vm.createContext({
  URL,
  document: {
    querySelectorAll: () => [],
    querySelector: selector => { if (!nodes.has(selector)) nodes.set(selector, {}); return nodes.get(selector); },
  },
});
vm.runInContext(source.slice(0, source.indexOf("$('#question-form').addEventListener")), context);
const run = code => vm.runInContext(code, context);

assert.equal(run("safeURL('javascript:alert(1)')"), null);
assert.equal(run("safeURL('data:text/html,hello')"), null);
assert.match(run("markdown('<img src=x onerror=alert(1)>')"), /&lt;img/);
assert.doesNotMatch(run("markdown('<script>alert(1)</script>')"), /<script>/);
assert.match(run("markdown('**Finding** (PMID 12345678).')"), /https:\/\/pubmed.ncbi.nlm.nih.gov\/12345678\//);
assert.match(run("markdown('[Source](https://example.com/?q=\"x\")')"), /%22x%22/);
assert.equal(run("allowed({status:'completed',result:{status:'completed',decision:{action:'withhold'}}})"), false);
assert.equal(run("allowed({status:'completed',result:{status:'completed',decision:{action:'allow'}}})"), true);
run(`state.current = { turns: [{ id:'t', question:'Question', status:'withheld', events:[], result:{answer:'SECRET DRAFT',decision:{action:'withhold',reason:'Review required'}} }] }; renderConversation();`);
assert.doesNotMatch(nodes.get('#conversation').innerHTML, /SECRET DRAFT/);
assert.match(nodes.get('#conversation').innerHTML, /answer needs further review/);
assert.doesNotMatch(run("exportText(state.current.turns[0])"), /SECRET DRAFT/);
run(`state.current.turns[0] = {id:'t2', question:'Question',status:'completed',events:[],result:{status:'completed',answer:'Visible answer',decision:{action:'allow'}}}; renderConversation();`);
assert.match(nodes.get('#conversation').innerHTML, /Visible answer/);
console.log('Frontend checks passed: URL safety, HTML escaping, citations, allow/withhold rendering, exports.');
