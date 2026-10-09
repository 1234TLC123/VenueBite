import { fetchJson } from "./api.js";
import { LocationSearch } from "./location-search.js";
import { MapViewer } from "./map-viewer.js";
import { bindAnalysisState, invalidateAnalysis } from "./analysis-state.js";
import { bindAnalysisForm, bindReportArrival } from "./form-ui.js";
import { bindSaveAction } from "./saved-sites.js";

const form = document.querySelector("[data-analysis-form]");
bindAnalysisState();

bindAnalysisForm(form, invalidateAnalysis);
bindReportArrival();
bindSaveAction(form);

new LocationSearch(form.dataset.geographyEnabled === "true");
try {
  const config = await fetchJson("/api/map-config");
  const viewer = new MapViewer(config);
  await viewer.initialize();
} catch {
  document.querySelector("#map-state-title").textContent = "Map unavailable";
  document.querySelector("#map-state-message").textContent = "Map configuration could not be loaded. Demo analysis is still available.";
  document.querySelector("[data-demo-fallback]").hidden = false;
}
