export function invalidateAnalysis(message = "Analysis pending") {
  for (const output of document.querySelectorAll("[data-analysis-output]")) output.hidden = true;
  for (const context of document.querySelectorAll("[data-census-status]")) {
    delete context.dataset.censusGeoid;
    context.dataset.censusStatus = "stale";
  }
  for (const context of document.querySelectorAll("[data-site-status]")) {
    delete context.dataset.siteId;
    context.dataset.siteStatus = "stale";
  }
  const pending = document.querySelector("[data-analysis-pending]");
  if (pending) {
    pending.hidden = false;
    pending.querySelector("h2").textContent = message;
  }
  const frame = document.querySelector("#map-frame");
  if (frame) {
    delete frame.dataset.competition;
    delete frame.dataset.parcel;
  }
  document.querySelector("#competition-legend").hidden = true;
  document.querySelector("#parcel-legend").hidden = true;
  document.dispatchEvent(new CustomEvent("venuebite:analysis-invalidated"));
}

export function bindAnalysisState() {
  for (const name of ["venuebite:location-selected", "venuebite:location-cleared"]) {
    document.addEventListener(name, () => invalidateAnalysis());
  }
  document.querySelector("#concept").addEventListener("input", () => invalidateAnalysis());
  document.querySelector("#radius-miles").addEventListener("change", () => invalidateAnalysis());
  window.addEventListener("pageshow", event => {
    if (event.persisted) invalidateAnalysis();
  });
}
