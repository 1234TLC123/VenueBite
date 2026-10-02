import { fetchJson } from "./api.js";
import { LocationSearch } from "./location-search.js";
import { MapViewer } from "./map-viewer.js";

const form = document.querySelector("[data-analysis-form]");
const submitButton = document.querySelector("[data-submit-button]");
const submitLabel = document.querySelector("[data-submit-label]");

if (form && submitButton && submitLabel) {
  form.addEventListener("submit", event => {
    const demoOnly = Boolean(event.submitter?.hasAttribute("data-demo-fallback"));
    if (demoOnly) {
      for (const id of ["selection-token", "latitude", "longitude"]) document.getElementById(id).value = "";
    } else if (form.dataset.geographyEnabled === "true" && !document.querySelector("#selection-token").value) {
      event.preventDefault();
      document.querySelector("#location-search-status").textContent = "Select a resolved location suggestion first.";
      document.querySelector("#location").focus();
      return;
    }
    submitButton.disabled = true;
    submitButton.classList.add("is-loading");
    submitLabel.textContent = "Analyzing...";
    form.setAttribute("aria-busy", "true");
  });

  window.addEventListener("pageshow", () => {
    submitButton.disabled = false;
    submitButton.classList.remove("is-loading");
    submitLabel.textContent = "Analyze Location";
    form.removeAttribute("aria-busy");
  });

  const invalidField = form.querySelector('[aria-invalid="true"]');
  if (invalidField) invalidField.focus();
}

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
