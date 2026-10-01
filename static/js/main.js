"use strict";

const form = document.querySelector("[data-analysis-form]");
const submitButton = document.querySelector("[data-submit-button]");
const submitLabel = document.querySelector("[data-submit-label]");

if (form && submitButton && submitLabel) {
  form.addEventListener("submit", () => {
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
