import assert from "node:assert/strict";
import * as savedSiteUI from "../static/js/saved-sites.js";

export function runSavedSiteTests(ui = savedSiteUI) {
  const { bindComparePicker, bindSaveAction, bindComparisonScroll } = ui;
  const original = { document: globalThis.document, window: globalThis.window };
  const passed = [];
  try {
    const events = {}, pageEvents = {}, label = { textContent: "Save snapshot" };
    const name = { value: "Candidate", setAttribute() {}, focus() { this.focused = true; } };
    const location = { value: "Aurora", setAttribute() {}, focus() { this.focused = true; } };
    const button = { disabled: false, querySelector: () => label };
    const token = { value: "signed" }, status = { hidden: true, textContent: "" };
    const nodes = { "[data-save-submit]": button, "[data-snapshot-token]": token, "#saved-site-name": name,
      "#saved-location-label": location, "[data-save-status]": status };
    globalThis.document = { querySelector: s => nodes[s], addEventListener: (e, f) => { events[e] = f; } };
    globalThis.window = { addEventListener: (e, f) => { pageEvents[e] = f; } };
    const form = { addEventListener: (e, f) => { events[e] = f; } };
    bindSaveAction(form);
    const submit = (save = true, prevented = false) => {
      const event = { defaultPrevented: prevented, submitter: { hasAttribute: n => n === "data-save-submit" && save },
        preventDefault() { this.defaultPrevented = true; } };
      events.submit(event); return event;
    };
    submit(false); assert.equal(button.disabled, false); passed.push("analysis submission bypasses saving");
    submit(true, true); assert.equal(button.disabled, false); passed.push("previously prevented event is respected");
    name.value = " "; assert.equal(submit().defaultPrevented, true); assert.equal(name.focused, true);
    passed.push("blank saved name focuses field without a request");
    name.value = "Candidate"; location.value = ""; assert.equal(submit().defaultPrevented, true);
    assert.equal(location.focused, true); passed.push("user location label is required without copying provider data");
    location.value = "Aurora"; assert.equal(submit().defaultPrevented, false);
    assert.equal(button.disabled, true); assert.match(status.textContent, /no provider refresh/);
    passed.push("valid save disables duplicate submissions without analysis loading");
    assert.equal(submit().defaultPrevented, true); assert.equal(token.value, "");
    passed.push("duplicate busy save cannot submit again");
    token.value = "signed"; button.disabled = false; events["venuebite:analysis-invalidated"]();
    assert.equal(token.value, ""); assert.equal(button.disabled, true);
    passed.push("editing analysis invalidates the signed save token");
    token.value = "signed"; button.disabled = false; pageEvents.pageshow({ persisted: true });
    assert.equal(token.value, ""); passed.push("back-forward cache cannot save stale analysis");
    bindSaveAction(null); passed.push("missing save surfaces are harmless");

    const handlers = [], choices = Array.from({ length: 5 }, () => ({ checked: false, disabled: false,
      addEventListener: (e, f) => handlers.push(f), closest: () => ({ classList: { toggle() {} } }) }));
    const compareButton = {}, selection = {};
    const picker = { querySelectorAll: () => choices, querySelector: s => s === "[data-compare-submit]" ? compareButton : selection };
    bindComparePicker(picker); assert.equal(compareButton.disabled, true); passed.push("empty comparison cannot submit");
    choices[0].checked = true; handlers[0](); assert.equal(compareButton.disabled, true);
    passed.push("one selected site cannot submit");
    choices[1].checked = true; handlers[1](); assert.equal(compareButton.disabled, false);
    passed.push("two selected sites enable comparison");
    choices[2].checked = choices[3].checked = true; handlers[2]();
    assert.equal(choices[4].disabled, true); assert.equal(compareButton.disabled, false);
    assert.equal(selection.textContent, "4 / 4 selected"); passed.push("four selections disable unchecked choices and announce count");
    choices[4].checked = true; handlers[4](); assert.equal(compareButton.disabled, true);
    passed.push("programmatic over-selection also disables submission");
    choices[4].checked = choices[3].checked = false; handlers[3](); assert.equal(choices[4].disabled, false);
    passed.push("deselection releases choices");
    bindComparePicker(null); passed.push("missing comparison surfaces are harmless");
    let onKey;
    const scrolls = [], panel = { clientWidth: 350, addEventListener: (e, f) => { onKey = f; },
      querySelector: () => ({ getBoundingClientRect: () => ({ width: 220 }) }), scrollBy: value => scrolls.push(value) };
    bindComparisonScroll(panel);
    let prevented = 0;
    const key = (name, changes = {}) => onKey({ key: name, target: panel, preventDefault: () => prevented++, ...changes });
    key("ArrowRight"); assert.deepEqual(scrolls.pop(), { left: 220, behavior: "instant" });
    passed.push("focused matrix right arrow reveals next site without motion");
    key("ArrowLeft"); assert.deepEqual(scrolls.pop(), { left: -220, behavior: "instant" });
    passed.push("focused matrix left arrow reveals previous site");
    key("ArrowRight", { target: {} }); key("ArrowLeft", { altKey: true }); key("Tab");
    assert.equal(scrolls.length, 0); assert.equal(prevented, 2);
    passed.push("child controls browser shortcuts and unrelated keys keep native behavior");
    panel.querySelector = () => null; key("ArrowRight"); assert.equal(scrolls.pop().left, 350);
    passed.push("matrix scroll has a viewport fallback for missing headers");
    bindComparisonScroll(null); passed.push("missing comparison matrix is harmless");
    return passed;
  } finally {
    for (const [key, value] of Object.entries(original)) {
      if (value === undefined) delete globalThis[key]; else globalThis[key] = value;
    }
  }
}

if (import.meta.main) console.log(runSavedSiteTests());
