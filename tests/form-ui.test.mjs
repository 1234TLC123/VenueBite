import assert from "node:assert/strict";
import { bindAnalysisForm, bindReportArrival } from "../static/js/form-ui.js";

export function runFormUITests() {
  const original = { document: globalThis.document, window: globalThis.window };
  const passed = [];
  try {
    const setup = (enabled = true, token = "signed-selection") => {
      const events = {}, attrs = {}, classes = new Set(), messages = [];
      const form = { dataset: { geographyEnabled: String(enabled) }, addEventListener: (name, fn) => { events[name] = fn; },
        setAttribute: (k, v) => { attrs[k] = v; }, removeAttribute: k => { delete attrs[k]; },
        getAttribute: k => attrs[k], querySelector: () => null };
      const button = { disabled: false, classList: { add: v => classes.add(v), remove: v => classes.delete(v) } };
      const label = { textContent: "Analyze Location" }, progress = { hidden: true };
      const nodes = { "[data-submit-button]": button, "[data-submit-label]": label, "[data-analysis-progress]": progress,
        "#selection-token": { value: token }, "#latitude": { value: "39.74" }, "#longitude": { value: "-104.83" },
        "#location-search-status": {}, "#location": { focus: () => { nodes.focused = true; } } };
      globalThis.document = { querySelector: selector => nodes[selector], getElementById: id => nodes["#" + id] };
      globalThis.window = { addEventListener: (name, fn) => { events[name] = fn; } };
      bindAnalysisForm(form, message => messages.push(message));
      const submit = (demo = false, prevented = false) => {
        const event = { defaultPrevented: prevented, submitter: { hasAttribute: name => name === "data-demo-fallback" && demo },
          preventDefault() { this.defaultPrevented = true; } };
        events.submit(event);
        return event;
      };
      return { events, attrs, classes, messages, nodes, button, label, progress, submit, form };
    };
    let state = setup();
    assert.equal(state.submit().defaultPrevented, false);
    assert.equal(state.button.disabled, true);
    assert.equal(state.attrs["aria-busy"], "true");
    assert.equal(state.label.textContent, "Analyzing location...");
    assert.equal(state.progress.hidden, false);
    assert.deepEqual(state.messages, ["Reading location evidence..."]);
    passed.push("valid analysis shows accessible loading without fabricated percentages");

    assert.equal(state.submit().defaultPrevented, true);
    assert.equal(state.messages.length, 1);
    passed.push("duplicate submissions are prevented while busy");

    state.events.pageshow({ persisted: true });
    assert.equal(state.button.disabled, false);
    assert.equal(state.attrs["aria-busy"], undefined);
    assert.equal(state.progress.hidden, true);
    assert.equal(state.classes.size, 0);
    assert.equal(state.label.textContent, "Analyze Location");
    passed.push("navigation and back-forward restoration clear loading state");

    state = setup(true, "");
    assert.equal(state.submit().defaultPrevented, true);
    assert.equal(state.nodes.focused, true);
    assert.match(state.nodes["#location-search-status"].textContent, /Select a resolved/);
    assert.equal(state.messages.length, 0);
    assert.equal(state.progress.hidden, true);
    passed.push("unresolved geography does not start loading or invalidate current evidence");

    state = setup();
    assert.equal(state.submit(true).defaultPrevented, false);
    for (const id of ["#selection-token", "#latitude", "#longitude"]) assert.equal(state.nodes[id].value, "");
    assert.deepEqual(state.messages, ["Analyzing demo data..."]);
    state.events.pageshow({});
    assert.equal(state.button.disabled, true);
    passed.push("explicit demo clears selection and preserves truthful fallback state");

    state = setup(false, "");
    state.submit();
    assert.deepEqual(state.messages, ["Analyzing demo data..."]);
    state.events.pageshow({});
    assert.equal(state.button.disabled, false);
    passed.push("unconfigured geography still supports server-rendered demo analysis");

    state = setup();
    state.submit(false, true);
    assert.equal(state.messages.length, 0);
    assert.equal(state.progress.hidden, true);
    passed.push("another prevented submission is respected");

    let focused = false;
    state.form.querySelector = () => ({ focus: () => { focused = true; } });
    bindAnalysisForm(state.form, () => {});
    assert.equal(focused, true);
    passed.push("server validation focuses the first invalid field");

    bindAnalysisForm(null, () => {});
    globalThis.document.querySelector = () => null;
    bindAnalysisForm(state.form, () => {});
    passed.push("missing form surfaces are harmless");

    const arrivalCalls = [];
    const heading = { focus: options => arrivalCalls.push(["focus", options]),
      scrollIntoView: options => arrivalCalls.push(["scroll", options]) };
    globalThis.document = { readyState: "complete", querySelector: () => heading };
    bindReportArrival();
    assert.deepEqual(arrivalCalls, [["focus", { preventScroll: true }], ["scroll", { block: "start", behavior: "instant" }]]);
    passed.push("fresh reports focus their heading and arrive without animation");

    globalThis.document.readyState = "interactive";
    let arrivalHandler;
    globalThis.window.addEventListener = (name, fn, options) => {
      assert.equal(name, "pageshow"); assert.equal(options.once, true); arrivalHandler = fn;
    };
    bindReportArrival();
    assert.equal(arrivalCalls.length, 2);
    arrivalHandler({ persisted: true });
    assert.equal(arrivalCalls.length, 2);
    passed.push("back-forward restoration does not re-focus a stale report");

    arrivalHandler({ persisted: false });
    assert.equal(arrivalCalls.length, 4);
    globalThis.document.querySelector = () => null;
    bindReportArrival();
    assert.equal(arrivalCalls.length, 4);
    passed.push("initial report arrival waits for page readiness and ignores empty pages");
    return passed;
  } finally {
    for (const [key, value] of Object.entries(original)) {
      if (value === undefined) delete globalThis[key]; else globalThis[key] = value;
    }
  }
}

if (import.meta.main) console.log(runFormUITests());
