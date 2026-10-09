export function bindSaveAction(form) {
  const button = document.querySelector("[data-save-submit]");
  const token = document.querySelector("[data-snapshot-token]");
  const name = document.querySelector("#saved-site-name");
  const location = document.querySelector("#saved-location-label");
  const status = document.querySelector("[data-save-status]");
  if (!form || !button || !token || !name || !location || !status) return;
  const invalidate = () => {
    token.value = "";
    button.disabled = true;
    status.hidden = false;
    status.textContent = "Analyze the current inputs again before saving.";
  };
  document.addEventListener("venuebite:analysis-invalidated", invalidate);
  form.addEventListener("submit", event => {
    if (!event.submitter?.hasAttribute("data-save-submit") || event.defaultPrevented) return;
    if (!token.value || button.disabled) {
      event.preventDefault();
      invalidate();
      return;
    }
    if (!name.value.trim()) {
      event.preventDefault();
      name.setAttribute("aria-invalid", "true");
      name.focus();
      status.hidden = false;
      status.textContent = "Enter a saved site name.";
      return;
    }
    if (!location.value.trim()) {
      event.preventDefault();
      location.setAttribute("aria-invalid", "true");
      location.focus();
      status.hidden = false;
      status.textContent = "Enter your own location label.";
      return;
    }
    button.disabled = true;
    button.querySelector("span").textContent = "Saving snapshot...";
    status.hidden = false;
    status.textContent = "Saving the completed analysis; no provider refresh.";
  });
  window.addEventListener("pageshow", event => {
    if (event.persisted) invalidate();
  });
}

export function bindComparePicker(form) {
  if (!form) return;
  const choices = [...form.querySelectorAll('[name="site_id"]')];
  const button = form.querySelector("[data-compare-submit]");
  const status = form.querySelector("[data-selection-status]");
  if (!button || !status) return;
  const update = () => {
    const count = choices.filter(input => input.checked).length;
    status.textContent = `${count} / 4 selected`;
    button.disabled = count < 2 || count > 4;
    for (const input of choices) {
      input.disabled = count >= 4 && !input.checked;
      input.closest("[data-site-choice]")?.classList.toggle("is-selected", input.checked);
    }
  };
  for (const input of choices) input.addEventListener("change", update);
  window.addEventListener("pageshow", update);
  update();
}

export function bindComparisonScroll(panel) {
  if (!panel) return;
  panel.addEventListener("keydown", event => {
    if (event.target !== panel || event.altKey || event.ctrlKey || event.metaKey) return;
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    const column = panel.querySelector("thead th:nth-child(2)");
    const step = column?.getBoundingClientRect().width || panel.clientWidth;
    event.preventDefault();
    panel.scrollBy({ left: (event.key === "ArrowRight" ? 1 : -1) * step, behavior: "instant" });
  });
}

if (typeof document !== "undefined") {
  bindComparePicker(document.querySelector("[data-compare-picker]"));
  bindComparisonScroll(document.querySelector(".comparison-scroll"));
}
