import assert from "node:assert/strict";
import { ParcelLayer } from "../static/js/parcel-layer.js";
import { invalidateAnalysis, bindAnalysisState } from "../static/js/analysis-state.js";

export function runParcelTests() {
  const original = { document: globalThis.document, window: globalThis.window, CustomEvent: globalThis.CustomEvent };
  const passed = [];
  try {
    const frame = { dataset: {} };
    const legend = { hidden: true };
    const site = { hidden: false, dataset: { siteStatus: "exact", siteId: "synthetic-id" } };
    const census = { dataset: { censusStatus: "available", censusGeoid: "synthetic-tract" } };
    const heading = { textContent: "" };
    const pending = { hidden: true, querySelector: () => heading };
    const handlers = {};
    const nodes = {
      "#map-frame": frame, "#parcel-legend": legend, "#parcel-match-label": { textContent: "" },
      "#focus-parcel": { disabled: true },
      "#competition-legend": { hidden: false },
      "#concept": { value: "Indian", addEventListener: (event, callback) => { handlers.concept = callback; } },
      "#radius-miles": { value: "3", addEventListener: (event, callback) => { handlers.radius = callback; } },
      "[data-analysis-pending]": pending,
    };
    globalThis.document = {
      querySelector: selector => nodes[selector],
      querySelectorAll: selector => ({ "[data-analysis-output]": [site], "[data-census-status]": [census], "[data-site-status]": [site] }[selector] || []),
      addEventListener: (event, callback) => { handlers[event] = callback; },
      dispatchEvent: event => handlers[event.type]?.(event),
    };
    globalThis.window = { addEventListener: (event, callback) => { handlers[event] = callback; } };
    globalThis.CustomEvent = class { constructor(type) { this.type = type; } };
    const map = {
      sources: {}, layers: {}, calls: [],
      isStyleLoaded: () => false,
      getLayer(id) { return this.layers[id]; },
      getSource(id) { return this.sources[id]; },
      addSource(id, value) { assert.ok(!this.sources[id]); this.sources[id] = value; this.calls.push(["source", id]); },
      addLayer(value) { assert.ok(this.sources[value.source]); this.layers[value.id] = value; this.calls.push(["layer", value.id]); },
      removeLayer(id) { delete this.layers[id]; this.calls.push(["remove-layer", id]); },
      removeSource(id) { assert.equal(Object.keys(this.layers).length, 0); delete this.sources[id]; this.calls.push(["remove-source", id]); },
      fitBounds(bounds, options) { this.calls.push(["fit", bounds, options]); },
    };
    const location = { latitude: 39.5, longitude: -104.5 };
    const payload = { ...location, concept: "Indian", radius_miles: 3, match_quality: "exact", bounds: [-105, 39, -104, 40],
      geometry: { type: "Polygon", coordinates: [[[-105, 39], [-104, 39], [-104, 40], [-105, 40], [-105, 39]]] } };
    const layer = new ParcelLayer(frame);
    const restore = () => { frame.dataset.parcel = JSON.stringify(payload); };
    restore();
    layer.update(map, location);
    assert.equal(Object.keys(map.layers).length, 2);
    assert.equal(legend.hidden, false);
    assert.equal(map.sources["venuebite-parcel"].data.geometry.type, "Polygon");
    assert.equal(nodes["#focus-parcel"].disabled, false);
    assert.ok(!map.calls.some(call => call[0] === "fit"));
    passed.push("initial style.load adds geometry even while tiles are loading");

    map.layers = {}; map.sources = {};
    layer.update(map, location);
    assert.equal(Object.keys(map.layers).length, 2);
    passed.push("style reload re-adds source and layers");

    layer.update(map, null);
    assert.equal(Object.keys(map.layers).length + Object.keys(map.sources).length, 0);
    assert.equal(legend.hidden, true);
    assert.equal(nodes["#focus-parcel"].disabled, true);
    passed.push("clearing location removes layers before source");

    for (const [field, value] of [["concept", "Mexican"], ["radius_miles", 1], ["latitude", 40], ["longitude", -106], ["match_quality", "ambiguous"]]) {
      frame.dataset.parcel = JSON.stringify({ ...payload, [field]: value });
      layer.update(map, location);
      assert.equal(Object.keys(map.layers).length, 0);
      assert.equal(legend.hidden, true);
    }
    passed.push("location concept radius and ambiguous snapshot guards");

    frame.dataset.parcel = "not JSON";
    assert.equal(layer.currentPayload(location), null);
    frame.dataset.parcel = JSON.stringify({ ...payload, geometry: { type: "Point", coordinates: [-104, 39] } });
    assert.equal(layer.currentPayload(location), null);
    passed.push("invalid or nonpolygon payload rejected");

    frame.dataset.parcel = JSON.stringify({ ...payload, match_quality: "nearby" });
    layer.update(map, location);
    assert.deepEqual(map.layers["venuebite-parcel-outline"].paint["line-dasharray"], [3, 2]);
    assert.match(nodes["#parcel-match-label"].textContent, /Nearby.*verify/);
    passed.push("nearby uses dashed outline and warning");

    restore();
    layer.focus(map, location, true);
    assert.deepEqual(map.calls.at(-1), ["fit", payload.bounds, { padding: 48, maxZoom: 18, duration: 0 }]);
    const callCount = map.calls.length;
    frame.dataset.parcel = JSON.stringify({ ...payload, bounds: [100, 50, -100, -50] });
    layer.focus(map, location, false);
    assert.equal(map.calls.length, callCount);
    passed.push("parcel focus is explicit bounded and reduced-motion aware");

    restore();
    frame.dataset.competition = "synthetic";
    handlers["venuebite:analysis-invalidated"] = () => layer.clear(map);
    invalidateAnalysis();
    assert.equal(site.hidden, true);
    assert.equal(site.dataset.siteStatus, "stale");
    assert.equal(site.dataset.siteId, undefined);
    assert.equal(frame.dataset.parcel, undefined);
    assert.equal(frame.dataset.competition, undefined);
    assert.equal(census.dataset.censusGeoid, undefined);
    assert.equal(Object.keys(map.sources).length, 0);
    passed.push("invalidation clears parcel census competition and report");

    bindAnalysisState();
    for (const event of ["venuebite:location-selected", "venuebite:location-cleared", "concept", "radius"]) {
      restore(); site.hidden = false;
      handlers[event]();
      assert.equal(frame.dataset.parcel, undefined);
      assert.equal(site.hidden, true);
    }
    restore(); handlers.pageshow({ persisted: true });
    assert.equal(frame.dataset.parcel, undefined);
    passed.push("all input and back-forward restore events invalidate parcel");
    return passed;
  } finally {
    for (const [key, value] of Object.entries(original)) {
      if (value === undefined) delete globalThis[key]; else globalThis[key] = value;
    }
  }
}

if (import.meta.main) console.log(runParcelTests());
