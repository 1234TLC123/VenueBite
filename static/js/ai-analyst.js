const MAX_MESSAGE = 1200;
const MAX_HISTORY = 6;
const EVIDENCE_LABELS = { model: "Model output", real: "Real evidence", partial: "Partial / user supplied", demo: "Demo", fallback: "Fallback / demo", unavailable: "Unavailable", unsupported: "Unsupported", unknown: "Unknown", user_supplied: "User supplied", verified_official_fact: "Official fact", interpretation_requires_confirmation: "Needs official confirmation", general_guidance: "Government guidance" };

function element(doc, tag, text, className = "") {
  const node = doc.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}

export function safeEvidenceURL(value) {
  try {
    const url = new URL(value);
    const official = new Set(["www.census.gov", "denvergov.org", "www.denvergov.org", "opendata-geospatialdenver.hub.arcgis.com", "www.arcgis.com", "gis.denvergov.org"]);
    return url.protocol === "https:" && !url.username && !url.password && official.has(url.hostname) ? url.href : "";
  } catch { return ""; }
}

export function renderAnswer(doc, answer) {
  if (!answer || !Array.isArray(answer.answer_blocks) || !answer.answer_blocks.length || answer.answer_blocks.length > 5 || !Array.isArray(answer.limitations)) throw new Error("Invalid answer");
  const article = element(doc, "article", "", "analyst-message analyst");
  article.append(element(doc, "h3", "SiteWise"));
  for (const block of answer.answer_blocks) {
    if (typeof block.text !== "string" || block.text.length > 4000 || !Array.isArray(block.evidence) || !block.evidence.length || block.evidence.length > 6) throw new Error("Invalid evidence");
    article.append(element(doc, "p", block.text));
    for (const item of block.evidence) {
      const details = element(doc, "details", "", "analyst-evidence");
      const statusLabel = EVIDENCE_LABELS[item.status] || "Unknown";
      const value = [item.display, item.units].filter(Boolean).join(" ");
      details.append(element(doc, "summary", `${item.label}: ${value} / ${statusLabel}`));
      const facts = element(doc, "dl", "");
      for (const [label, value] of [["Evidence", statusLabel], ["Source", item.source], ["As of", item.date || "Not supplied"], ["Limits", item.limitation || "Model context only"]]) {
        facts.append(element(doc, "dt", label), element(doc, "dd", String(value)));
      }
      details.append(facts);
      const url = safeEvidenceURL(item.source_url);
      if (url) {
        const link = element(doc, "a", "Official source");
        link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer";
        details.append(link);
      }
      article.append(details);
    }
  }
  const limits = element(doc, "details", "", "analyst-limits");
  limits.append(element(doc, "summary", "Evidence limits & verification"));
  for (const limit of answer.limitations.slice(0, 7)) limits.append(element(doc, "p", String(limit)));
  article.append(limits);
  return article;
}

export function bindAIAnalyst(doc = document, win = window, request = fetch) {
  const dialog = doc.querySelector("[data-ai-dialog]");
  const launch = doc.querySelector("[data-ai-open]");
  if (!dialog || !launch) return null;
  const node = name => dialog.querySelector(`[data-ai-${name}]`);
  const input = node("input"), send = node("send"), messages = node("messages"), status = node("status"), error = node("error"), starters = node("starters");
  let history = [], busy = false, generation = 0, abort = null;
  const enabled = dialog.dataset.aiEnabled === "true";
  const update = () => {
    input.disabled = !enabled || !dialog.dataset.aiToken;
    send.disabled = input.disabled || busy || !input.value.trim() || input.value.length > MAX_MESSAGE;
    node("count").textContent = `${input.value.length} / ${MAX_MESSAGE}`;
    dialog.setAttribute("aria-busy", busy ? "true" : "false");
  };
  const reset = () => {
    generation++; abort?.abort(); abort = null; busy = false; history = [];
    messages.replaceChildren(); input.value = ""; error.hidden = true;
    status.textContent = enabled ? "" : "SiteWise is unavailable because the server AI provider is not configured. Your analysis remains available.";
    starters.hidden = false;
    update();
  };
  const close = () => { dialog.close(); launch.focus(); };
  launch.addEventListener("click", () => { dialog.showModal(); (input.disabled ? node("close") : input).focus(); });
  node("close").addEventListener("click", close);
  dialog.addEventListener("cancel", event => { event.preventDefault(); close(); });
  dialog.addEventListener("keydown", event => {
    if (event.key !== "Tab") return;
    const focusable = [...dialog.querySelectorAll('button, input, textarea, select, summary, a[href], [tabindex]')]
      .filter(control => !control.disabled && control.tabIndex >= 0 && control.getClientRects().length);
    const first = focusable[0], last = focusable.at(-1);
    if (event.shiftKey && doc.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && doc.activeElement === last) { event.preventDefault(); first?.focus(); }
  });
  node("reset").addEventListener("click", () => { reset(); (input.disabled ? node("close") : input).focus(); });
  input.addEventListener("input", update);
  for (const button of dialog.querySelectorAll("[data-ai-starter]")) button.addEventListener("click", () => {
    if (!input.disabled && !busy) { input.value = button.textContent.trim(); update(); input.focus(); }
  });
  node("form").addEventListener("submit", async event => {
    event.preventDefault();
    update();
    if (send.disabled || busy) return;
    const question = input.value.trim(), currentGeneration = generation;
    busy = true; error.hidden = true; status.textContent = "Reviewing selected evidence..."; starters.hidden = true;
    abort = new AbortController();
    const controller = abort;
    const timeout = win.setTimeout(() => controller.abort(), 50000);
    update();
    const user = element(doc, "article", "", "analyst-message user");
    user.append(element(doc, "h3", "You"), element(doc, "p", question)); messages.append(user);
    try {
      const response = await request("/api/ai/chat", { method: "POST", credentials: "same-origin", cache: "no-store", signal: controller.signal,
        headers: { "Content-Type": "application/json", "X-CSRF-Token": dialog.dataset.aiCsrf },
        body: JSON.stringify({ context_token: dialog.dataset.aiToken, message: question, history, request_id: win.crypto.randomUUID() }) });
      const answer = await response.json();
      if (generation !== currentGeneration) return;
      if (!response.ok) {
        if (["stale_context", "invalid_session"].includes(answer.code)) dialog.dataset.aiToken = "";
        throw new Error(answer.error || "The analyst is unavailable. Please try again.");
      }
      const rendered = renderAnswer(doc, answer); messages.append(rendered);
      history = [...history, { role: "user", content: question }, { role: "assistant", content: answer.answer_blocks.map(block => block.text).join("\n").slice(0, MAX_MESSAGE) }].slice(-MAX_HISTORY);
      input.value = ""; status.textContent = "Grounded in the selected evidence. No location providers refreshed.";
      rendered.scrollIntoView?.({ block: "nearest", behavior: "instant" });
    } catch (failure) {
      if (generation !== currentGeneration) return;
      error.textContent = failure.name === "AbortError" ? "The analyst took too long. Please try again." : failure.message;
      error.hidden = false; status.textContent = "";
    } finally {
      win.clearTimeout(timeout);
      if (generation === currentGeneration) { busy = false; abort = null; update(); if (dialog.open && !input.disabled) input.focus(); }
    }
  });
  const invalidate = () => {
    reset(); dialog.dataset.aiToken = ""; launch.hidden = true;
    status.textContent = "Inputs changed. Analyze again before asking about this location.";
    update(); if (dialog.open) close();
  };
  if (dialog.dataset.aiKind === "current") doc.addEventListener("venuebite:analysis-invalidated", invalidate);
  doc.querySelector("[data-compare-picker]")?.addEventListener("change", invalidate);
  win.addEventListener("pageshow", event => { if (event.persisted) { if (dialog.dataset.aiKind === "current") invalidate(); else reset(); } });
  reset();
  return { reset, invalidate, get history() { return history.map(item => ({ ...item })); }, get busy() { return busy; } };
}

if (typeof document !== "undefined") bindAIAnalyst();
