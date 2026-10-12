import assert from "node:assert/strict";
import { bindAIAnalyst, renderAnswer, safeEvidenceURL } from "../static/js/ai-analyst.js";

class Node {
  constructor(tag = "div", text = "") { this.tag = tag; this.textContent = text; this.children = []; this.dataset = {}; this.attributes = {}; this.handlers = {}; this.value = ""; this.hidden = false; this.disabled = false; this.tabIndex = 0; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  addEventListener(name, action) { (this.handlers[name] ||= []).push(action); }
  async emit(name, event = {}) { for (const action of this.handlers[name] || []) await action({ preventDefault() {}, ...event }); }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() { this.owner.activeElement = this; }
  showModal() { this.open = true; }
  close() { this.open = false; }
  scrollIntoView() {}
  getClientRects() { return this.hidden ? [] : [{}]; }
}

const evidence = { id: "s1.score", label: "Opportunity Score", display: "48.3", units: "/ 100", status: "model", source: "VenueBite", date: "2026-10-11", limitation: "Not a prediction", source_url: "" };
const answer = { context_kind: "current", answer_blocks: [{ text: "Stored model evidence, not a recommendation.", evidence: [evidence] }], limitations: ["Coverage is not probability."] };
const flatten = node => [node.textContent, ...node.children.map(flatten)].join(" ");

function fixture({ kind = "current", enabled = true, request } = {}) {
  const nodes = Object.fromEntries(["dialog", "open", "close", "reset", "input", "send", "messages", "status", "error", "starters", "count", "form", "picker"].map(name => [name, new Node()]));
  const starter = new Node("button", "Explain the stored score.");
  const doc = new Node();
  doc.createElement = tag => { const node = new Node(tag); node.owner = doc; return node; };
  for (const node of [...Object.values(nodes), starter]) node.owner = doc;
  doc.querySelector = selector => selector === "[data-compare-picker]" ? nodes.picker : nodes[selector.slice(9, -1)];
  nodes.dialog.querySelector = selector => nodes[selector.slice(9, -1)];
  nodes.dialog.querySelectorAll = selector => selector === "[data-ai-starter]" ? [starter] : [nodes.reset, nodes.close, nodes.input, nodes.send];
  Object.assign(nodes.dialog.dataset, { aiEnabled: String(enabled), aiToken: "signed-context", aiCsrf: "session-csrf", aiKind: kind });
  const win = new Node();
  win.setTimeout = setTimeout; win.clearTimeout = clearTimeout; win.crypto = { randomUUID: () => "00000000-0000-4000-8000-000000000001" };
  const calls = [];
  const fetcher = async (...args) => { calls.push(args); return request ? request(...args) : { ok: true, json: async () => ({ ...answer, context_kind: kind }) }; };
  const binding = bindAIAnalyst(doc, win, fetcher);
  const send = async text => { nodes.input.value = text; await nodes.input.emit("input"); await nodes.form.emit("submit"); };
  return { nodes, starter, doc, win, calls, binding, send };
}

export async function runAIAnalystTests() {
  const passed = [];
  {
    const f = fixture(); await f.nodes.open.emit("click");
    assert.ok(f.nodes.dialog.open); assert.equal(f.doc.activeElement, f.nodes.input);
    await f.nodes.close.emit("click"); assert.ok(!f.nodes.dialog.open); assert.equal(f.doc.activeElement, f.nodes.open);
    passed.push("drawer open/close restores focus");
    await f.nodes.open.emit("click"); await f.nodes.dialog.emit("cancel");
    assert.ok(!f.nodes.dialog.open); assert.equal(f.doc.activeElement, f.nodes.open);
    passed.push("Escape/native modal cancellation restores focus");
    f.nodes.input.focus(); await f.nodes.dialog.emit("keydown", { key: "Tab", shiftKey: false });
    assert.equal(f.doc.activeElement, f.nodes.reset);
    passed.push("Tab wraps from the final enabled drawer control");
    await f.nodes.dialog.emit("keydown", { key: "Tab", shiftKey: true });
    assert.equal(f.doc.activeElement, f.nodes.input);
    passed.push("Shift-Tab wraps to the final enabled drawer control");
  }
  {
    const f = fixture({ enabled: false }); await f.nodes.open.emit("click");
    assert.equal(f.doc.activeElement, f.nodes.close); assert.ok(f.nodes.input.disabled && f.nodes.send.disabled);
    await f.send("Question"); assert.equal(f.calls.length, 0); assert.match(f.nodes.status.textContent, /not configured/);
    passed.push("no-key state is graceful and never sends");
  }
  {
    const f = fixture(); await f.starter.emit("click");
    assert.equal(f.nodes.input.value, f.starter.textContent); assert.equal(f.doc.activeElement, f.nodes.input);
    assert.equal(f.calls.length, 0); assert.ok(!f.nodes.send.disabled);
    passed.push("starter populates composer without automatic API call");
    await f.send(" "); await f.send("x".repeat(1201)); assert.equal(f.calls.length, 0);
    assert.match(f.nodes.count.textContent, /1201/);
    passed.push("empty and oversized questions are blocked");
  }
  for (const kind of ["current", "saved", "compare"]) {
    const f = fixture({ kind }); await f.send("Explain the score.");
    assert.equal(f.calls.length, 1); assert.equal(f.nodes.messages.children.length, 2);
    const [url, options] = f.calls[0]; const body = JSON.parse(options.body);
    assert.equal(url, "/api/ai/chat"); assert.equal(options.cache, "no-store"); assert.equal(options.credentials, "same-origin");
    assert.equal(options.headers["X-CSRF-Token"], "session-csrf"); assert.equal(body.context_token, "signed-context");
    assert.deepEqual(body.history, []); assert.equal(f.binding.history.length, 2);
    assert.equal(f.nodes.input.value, ""); assert.ok(!f.binding.busy);
    assert.match(flatten(f.nodes.messages), /Opportunity Score/);
    assert.match(flatten(f.nodes.messages), /SiteWise/);
    passed.push(`${kind} sends signed context and displays server evidence`);
    for (let i = 0; i < 5; i++) await f.send(`Question ${i}`);
    assert.equal(f.binding.history.length, 6); assert.equal(JSON.parse(f.calls.at(-1)[1].body).history.length, 6);
    passed.push(`${kind} history stays bounded in RAM`);
  }
  {
    let resolve;
    const pending = new Promise(done => { resolve = done; });
    const f = fixture({ request: () => pending });
    const first = f.send("Question");
    await Promise.resolve(); await Promise.resolve();
    assert.ok(f.binding.busy); assert.ok(f.nodes.send.disabled); assert.match(f.nodes.status.textContent, /Reviewing/);
    await f.nodes.form.emit("submit"); assert.equal(f.calls.length, 1);
    resolve({ ok: true, json: async () => answer }); await first;
    assert.ok(!f.binding.busy);
    passed.push("loading state prevents duplicate submissions");
  }
  for (const code of ["timeout", "rate_limited", "not_configured", "unsupported_answer", "stale_context", "invalid_session"]) {
    const f = fixture({ request: async () => ({ ok: false, json: async () => ({ error: "Safe server error.", code }) }) });
    await f.send("Question"); assert.equal(f.nodes.error.hidden, false); assert.equal(f.nodes.error.textContent, "Safe server error.");
    assert.equal(f.binding.history.length, 0); assert.ok(!f.binding.busy);
    if (["stale_context", "invalid_session"].includes(code)) assert.ok(f.nodes.input.disabled && !f.nodes.dialog.dataset.aiToken);
    passed.push(`${code} shows a recoverable error without fabricated answer`);
  }
  {
    const f = fixture({ request: async () => { const error = new Error(); error.name = "AbortError"; throw error; } });
    await f.send("Question"); assert.match(f.nodes.error.textContent, /too long/);
    passed.push("aborted request displays timeout state");
  }
  {
    const f = fixture({ request: async () => ({ ok: true, json: async () => ({ answer_blocks: [] }) }) });
    await f.send("Question"); assert.equal(f.nodes.error.hidden, false); assert.equal(f.binding.history.length, 0);
    passed.push("malformed answer is not rendered as analyst evidence");
  }
  {
    const f = fixture(); await f.send("Question"); await f.nodes.reset.emit("click");
    assert.equal(f.binding.history.length, 0); assert.equal(f.nodes.messages.children.length, 0); assert.equal(f.nodes.starters.hidden, false);
    passed.push("reset removes all ephemeral history");
    await f.doc.emit("venuebite:analysis-invalidated");
    assert.equal(f.nodes.dialog.dataset.aiToken, ""); assert.ok(f.nodes.open.hidden && f.nodes.input.disabled);
    await f.send("New question"); assert.equal(f.calls.length, 1);
    passed.push("analysis changes destroy chat context and disable stale requests");
  }
  {
    let resolve;
    const f = fixture({ request: () => new Promise(done => { resolve = done; }) });
    const pending = f.send("Question"); await Promise.resolve(); await Promise.resolve();
    await f.doc.emit("venuebite:analysis-invalidated");
    resolve({ ok: true, json: async () => answer }); await pending;
    assert.equal(f.nodes.messages.children.length, 0); assert.equal(f.binding.history.length, 0);
    passed.push("late replies cannot resurrect an invalidated conversation");
  }
  {
    const f = fixture({ kind: "compare" }); await f.send("Compare"); await f.nodes.picker.emit("change");
    assert.ok(!f.nodes.dialog.dataset.aiToken && f.nodes.open.hidden); assert.equal(f.binding.history.length, 0);
    passed.push("compare selection edits invalidate the old selected context");
  }
  for (const kind of ["current", "saved", "compare"]) {
    const f = fixture({ kind }); await f.send("Question"); await f.win.emit("pageshow", { persisted: true });
    assert.equal(f.binding.history.length, 0);
    assert.equal(Boolean(f.nodes.dialog.dataset.aiToken), kind !== "current");
    passed.push(`${kind} back-forward restoration resets appropriate context`);
  }
  {
    const f = fixture();
    const malicious = '<img src=x onerror="alert(1)">';
    const rendered = renderAnswer(f.doc, { answer_blocks: [{ text: malicious, evidence: [{ ...evidence, label: malicious, source_url: "javascript:alert(1)" }] }], limitations: [malicious] });
    assert.ok(flatten(rendered).includes(malicious));
    assert.equal(rendered.children[1].tag, "p"); assert.equal(rendered.children[1].textContent, malicious);
    assert.equal(rendered.children[2].children.some(node => node.tag === "a"), false);
    passed.push("model/source text is inert textContent, never executable HTML");
    for (const url of ["javascript:alert(1)", "http://denvergov.org", "https://evil.example", "https://denvergov.org.evil.example", "https://user:pass@denvergov.org"]) assert.equal(safeEvidenceURL(url), "");
    assert.equal(safeEvidenceURL("https://www.census.gov/programs-surveys/acs/"), "https://www.census.gov/programs-surveys/acs/");
    passed.push("evidence links enforce HTTPS official hosts and no URL credentials");
    assert.throws(() => renderAnswer(f.doc, { answer_blocks: [{ text: "Bad", evidence: [] }], limitations: [] }));
    passed.push("missing evidence cannot create a valid citation");
  }
  return passed;
}
