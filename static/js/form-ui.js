export function bindAnalysisForm(form, invalidateAnalysis) {
  const button = document.querySelector("[data-submit-button]");
  const label = document.querySelector("[data-submit-label]");
  const progress = document.querySelector("[data-analysis-progress]");
  if (!form || !button || !label || !progress) return;

  const reset = () => {
    button.disabled = form.dataset.geographyEnabled === "true" && !document.querySelector("#selection-token").value;
    button.classList.remove("is-loading");
    label.textContent = "Analyze Location";
    form.removeAttribute("aria-busy");
    progress.hidden = true;
  };
  form.addEventListener("submit", event => {
    if (event.defaultPrevented) return;
    if (event.submitter?.hasAttribute("data-save-submit")) return;
    if (form.getAttribute("aria-busy") === "true") {
      event.preventDefault();
      return;
    }
    const demoOnly = Boolean(event.submitter?.hasAttribute("data-demo-fallback"));
    if (demoOnly) {
      for (const id of ["selection-token", "latitude", "longitude"]) document.getElementById(id).value = "";
    } else if (form.dataset.geographyEnabled === "true" && !document.querySelector("#selection-token").value) {
      event.preventDefault();
      document.querySelector("#location-search-status").textContent = "Select a resolved location suggestion first.";
      document.querySelector("#location").focus();
      return;
    }
    button.disabled = true;
    button.classList.add("is-loading");
    label.textContent = "Analyzing location...";
    const message = demoOnly || form.dataset.geographyEnabled !== "true" ? "Analyzing demo data..." : "Reading location evidence...";
    invalidateAnalysis(message);
    progress.textContent = message;
    progress.hidden = false;
    form.setAttribute("aria-busy", "true");
  });
  window.addEventListener("pageshow", reset);
  const invalidField = form.querySelector('[aria-invalid="true"]');
  if (invalidField) invalidField.focus();
}

export function bindReportArrival() {
  const heading = document.querySelector("[data-report-start]");
  if (!heading) return;
  const reveal = () => {
    heading.focus({ preventScroll: true });
    heading.scrollIntoView({ block: "start", behavior: "instant" });
  };
  if (document.readyState === "complete") reveal();
  else window.addEventListener("pageshow", event => { if (!event.persisted) reveal(); }, { once: true });
}
