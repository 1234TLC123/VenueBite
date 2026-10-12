import assert from "node:assert/strict";

export async function runRegulatoryStateTests() {
  const { bindAnalysisState } = await import("../static/js/analysis-state.js");
  const original = { document: globalThis.document, window: globalThis.window, CustomEvent: globalThis.CustomEvent };
  const passed = [];
  try {
    const handlers = {};
    const names = ["type", "alcohol", "outdoor_seating", "drive_through", "renovation", "change_of_use"];
    const inputs = names.map(name => ({ addEventListener: (event, callback) => { handlers[`${name}:${event}`] = callback; } }));
    const score = { hidden: false }, coverage = { hidden: false }, save = { hidden: false };
    const regulatory = { hidden: false, dataset: {} }, census = { hidden: false, dataset: {} }, site = { hidden: false, dataset: {} };
    const outputs = [score, coverage, save, regulatory, census, site];
    const frame = { dataset: {} }, heading = { textContent: "" }, pending = { hidden: true, querySelector: () => heading };
    const nodes = {
      "#map-frame": frame, "[data-analysis-pending]": pending,
      "#parcel-legend": { hidden: false }, "#competition-legend": { hidden: false },
      "#concept": { addEventListener: (event, callback) => { handlers.concept = callback; } },
      "#radius-miles": { addEventListener: (event, callback) => { handlers.radius = callback; } },
    };
    let invalidations = 0;
    globalThis.document = {
      querySelector: selector => nodes[selector],
      querySelectorAll: selector => ({ "[data-analysis-output]": outputs, "[data-regulatory-status]": [regulatory],
        "[data-site-status]": [site], "[data-census-status]": [census], "[data-regulatory-input]": inputs }[selector] || []),
      addEventListener: (event, callback) => { handlers[event] = callback; },
      dispatchEvent: event => { assert.equal(event.type, "venuebite:analysis-invalidated"); invalidations++; },
    };
    globalThis.window = { addEventListener: (event, callback) => { handlers[event] = callback; } };
    globalThis.CustomEvent = class { constructor(type) { this.type = type; } };
    const restore = () => {
      outputs.forEach(output => { output.hidden = false; });
      regulatory.dataset.regulatoryStatus = "use_review_required";
      census.dataset.censusStatus = "available"; census.dataset.censusGeoid = "old-tract";
      site.dataset.siteStatus = "exact"; site.dataset.siteId = "old-parcel";
      frame.dataset.competition = "old-pois"; frame.dataset.parcel = "old-parcel";
      nodes["#parcel-legend"].hidden = nodes["#competition-legend"].hidden = false;
      pending.hidden = true;
    };
    const check = () => {
      assert.ok(outputs.every(output => output.hidden));
      assert.equal(regulatory.dataset.regulatoryStatus, "stale");
      assert.equal(census.dataset.censusGeoid, undefined);
      assert.equal(site.dataset.siteId, undefined);
      assert.equal(frame.dataset.competition, undefined);
      assert.equal(frame.dataset.parcel, undefined);
      assert.equal(pending.hidden, false);
      assert.equal(heading.textContent, "Analysis pending");
      assert.ok(nodes["#parcel-legend"].hidden && nodes["#competition-legend"].hidden);
    };
    bindAnalysisState();
    for (const name of names) {
      for (const event of ["input", "change"]) {
        restore(); handlers[`${name}:${event}`](); check();
      }
      passed.push(`${name} project edits invalidate regulatory evidence, save controls, scores and map overlays`);
    }
    for (const event of ["venuebite:location-selected", "venuebite:location-cleared", "concept", "radius"]) {
      restore(); handlers[event](); check(); passed.push(`${event} invalidates regulatory evidence`);
    }
    restore(); handlers.pageshow({ persisted: true }); check();
    passed.push("back-forward restoration invalidates regulatory evidence");
    restore(); handlers.pageshow({ persisted: false });
    assert.ok(outputs.every(output => !output.hidden));
    passed.push("ordinary page load preserves current regulatory evidence");
    assert.equal(invalidations, 17);
    return passed;
  } finally {
    for (const [key, value] of Object.entries(original)) {
      if (value === undefined) delete globalThis[key]; else globalThis[key] = value;
    }
  }
}

if (import.meta.main) console.log(await runRegulatoryStateTests());
