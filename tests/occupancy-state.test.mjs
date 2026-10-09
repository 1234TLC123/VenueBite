import assert from "node:assert/strict";

export async function runOccupancyStateTests() {
  const { bindAnalysisState } = await import("../static/js/analysis-state.js");
  const original = { document: globalThis.document, window: globalThis.window, CustomEvent: globalThis.CustomEvent };
  const passed = [];
  try {
    const handlers = {};
    const names = ["property_address", "space_size_sqft", "asking_rent", "asking_rent_basis", "lease_structure",
      "additional_occupancy_rate", "additional_occupancy_basis", "monthly_occupancy_budget", "source_url", "source_label", "occupancy_notes"];
    const fields = names.map(name => ({ addEventListener: (event, callback) => { handlers[`${name}:${event}`] = callback; } }));
    const score = { hidden: false }, coverage = { hidden: false }, costs = { hidden: false, dataset: { occupancyStatus: "complete" } };
    const explanations = { hidden: false }, site = { hidden: false, dataset: {} }, census = { hidden: false, dataset: {} };
    const outputs = [score, coverage, costs, explanations, site, census];
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
      querySelectorAll: selector => ({ "[data-analysis-output]": outputs, "[data-occupancy-status]": [costs],
        "[data-site-status]": [site], "[data-census-status]": [census], "[data-occupancy-input]": fields }[selector] || []),
      addEventListener: (event, callback) => { handlers[event] = callback; },
      dispatchEvent: event => { assert.equal(event.type, "venuebite:analysis-invalidated"); invalidations++; },
    };
    globalThis.window = { addEventListener: (event, callback) => { handlers[event] = callback; } };
    globalThis.CustomEvent = class { constructor(type) { this.type = type; } };
    const restore = () => {
      for (const output of outputs) output.hidden = false;
      costs.dataset.occupancyStatus = "complete";
      census.dataset.censusStatus = "available"; census.dataset.censusGeoid = "test-tract";
      site.dataset.siteStatus = "exact"; site.dataset.siteId = "test-parcel";
      frame.dataset.competition = "old-pois"; frame.dataset.parcel = "old-parcel";
      nodes["#parcel-legend"].hidden = nodes["#competition-legend"].hidden = false;
      pending.hidden = true;
    };
    const check = () => {
      assert.ok(outputs.every(output => output.hidden));
      assert.equal(costs.dataset.occupancyStatus, "stale");
      assert.equal(census.dataset.censusGeoid, undefined);
      assert.equal(site.dataset.siteId, undefined);
      assert.equal(frame.dataset.competition, undefined);
      assert.equal(frame.dataset.parcel, undefined);
      assert.equal(pending.hidden, false);
      assert.equal(heading.textContent, "Analysis pending");
      assert.equal(nodes["#parcel-legend"].hidden, true);
      assert.equal(nodes["#competition-legend"].hidden, true);
    };
    bindAnalysisState();
    for (const name of names) {
      for (const event of ["input", "change"]) {
        restore(); handlers[`${name}:${event}`](); check();
      }
      passed.push(`${name} edits clear score coverage costs explanations and map overlays`);
    }
    for (const event of ["venuebite:location-selected", "venuebite:location-cleared", "concept", "radius"]) {
      restore(); handlers[event](); check(); passed.push(`${event} invalidates occupancy with the rest of the report`);
    }
    restore(); handlers.pageshow({ persisted: true }); check();
    passed.push("back-forward restoration invalidates all report evidence");
    assert.equal(invalidations, names.length * 2 + 5);
    return passed;
  } finally {
    for (const [key, value] of Object.entries(original)) {
      if (value === undefined) delete globalThis[key]; else globalThis[key] = value;
    }
  }
}

if (import.meta.main) console.log(await runOccupancyStateTests());
