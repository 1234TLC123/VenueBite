import { fetchJson } from "./api.js";

export class LocationSearch {
  constructor(enabled) {
    this.enabled = enabled;
    this.input = document.querySelector("#location");
    this.form = document.querySelector("[data-analysis-form]");
    this.button = document.querySelector("[data-submit-button]");
    this.status = document.querySelector("#location-search-status");
    this.list = document.querySelector("#location-suggestions");
    this.popover = document.querySelector("#suggestions-popover");
    this.clearButton = document.querySelector("#clear-location");
    this.fallback = document.querySelector("[data-demo-fallback]");
    this.suggestions = [];
    this.activeIndex = -1;
    this.sequence = 0;
    this.session = null;
    this.selected = Boolean(document.querySelector("#selection-token").value);
    this.form.classList.toggle("has-selection", this.selected);
    this.clearButton.hidden = !this.input.value;
    this.syncButton();

    this.input.addEventListener("input", () => this.onInput());
    this.input.addEventListener("keydown", event => this.onKeyDown(event));
    this.clearButton.addEventListener("click", () => {
      this.input.value = "";
      this.onInput();
      this.input.focus();
    });
    document.addEventListener("pointerdown", event => {
      if (!event.target.closest(".location-search")) this.close();
    });
    document.addEventListener("focusin", event => {
      if (!event.target.closest(".location-search")) this.close();
    });
    window.addEventListener("pageshow", () => this.syncButton());
  }

  syncButton() {
    this.button.disabled = this.enabled && !this.selected;
  }

  setStatus(message, state = "") {
    this.status.textContent = message;
    this.status.dataset.state = state;
    this.input.setAttribute("aria-busy", state === "loading" ? "true" : "false");
  }

  clearSelection() {
    this.selected = false;
    for (const id of ["selection-token", "latitude", "longitude"]) document.getElementById(id).value = "";
    this.form.classList.remove("has-selection");
    delete document.querySelector("#map-frame").dataset.initialLocation;
    this.syncButton();
    document.dispatchEvent(new CustomEvent("venuebite:location-cleared"));
  }

  onInput() {
    this.sequence += 1;
    clearTimeout(this.timer);
    this.controller?.abort();
    this.close();
    this.clearSelection();
    this.clearButton.hidden = !this.input.value;
    this.input.removeAttribute("aria-invalid");
    this.fallback.hidden = true;
    if (!this.enabled) return;
    const query = this.input.value.trim();
    if (query.length < 2) {
      this.setStatus(query ? "Enter at least two characters" : "No location selected");
      return;
    }
    this.timer = setTimeout(() => this.search(query, this.sequence), 300);
  }

  async search(query, sequence) {
    this.controller = new AbortController();
    this.setStatus("Searching locations...", "loading");
    try {
      this.session ||= crypto.randomUUID();
      const params = new URLSearchParams({ q: query, session_token: this.session });
      const data = await fetchJson(`/api/locations/suggestions?${params}`, { signal: this.controller.signal });
      if (sequence !== this.sequence) return;
      if (!Array.isArray(data.suggestions)) throw new Error("Location suggestions are unavailable. Try another search.");
      this.suggestions = data.suggestions;
      this.renderSuggestions(data.attribution);
      this.setStatus(this.suggestions.length ? `${this.suggestions.length} location suggestions` : "No locations found. Try a more specific search.");
    } catch (error) {
      if (error.name === "AbortError" || sequence !== this.sequence) return;
      this.setStatus(error.message, "error");
      this.fallback.hidden = false;
    }
  }

  renderSuggestions(attribution) {
    this.list.replaceChildren();
    this.activeIndex = -1;
    for (const [index, suggestion] of this.suggestions.entries()) {
      const option = document.createElement("li");
      option.id = `location-option-${index}`;
      option.setAttribute("role", "option");
      option.setAttribute("aria-selected", "false");
      const name = document.createElement("strong");
      name.textContent = suggestion.display_name;
      const type = document.createElement("span");
      type.textContent = suggestion.place_type;
      option.append(name, type);
      option.addEventListener("mousedown", event => event.preventDefault());
      option.addEventListener("pointerenter", () => this.setActive(index));
      option.addEventListener("click", () => this.select(index));
      this.list.append(option);
    }
    document.querySelector("#search-attribution").textContent = attribution || "Search by Mapbox";
    this.popover.hidden = this.suggestions.length === 0;
    this.input.setAttribute("aria-expanded", this.suggestions.length ? "true" : "false");
  }

  setActive(index) {
    this.activeIndex = index;
    for (const [optionIndex, option] of Array.from(this.list.children).entries()) {
      option.setAttribute("aria-selected", optionIndex === index ? "true" : "false");
    }
    const option = this.list.children[index];
    if (option) {
      this.input.setAttribute("aria-activedescendant", option.id);
      option.scrollIntoView({ block: "nearest" });
    }
  }

  onKeyDown(event) {
    if (!this.enabled) return;
    if (event.key === "Escape") this.close();
    if ((event.key === "ArrowDown" || event.key === "ArrowUp") && this.suggestions.length && !this.popover.hidden) {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      const next = this.activeIndex < 0 ? (direction > 0 ? 0 : this.suggestions.length - 1)
        : (this.activeIndex + direction + this.suggestions.length) % this.suggestions.length;
      this.setActive(next);
    }
    if (event.key === "Enter" && !this.popover.hidden && this.activeIndex >= 0) {
      event.preventDefault();
      this.select(this.activeIndex);
    }
  }

  close() {
    this.popover.hidden = true;
    this.input.setAttribute("aria-expanded", "false");
    this.input.removeAttribute("aria-activedescendant");
    this.activeIndex = -1;
  }

  async select(index) {
    const suggestion = this.suggestions[index];
    if (!suggestion) return;
    const sequence = ++this.sequence;
    this.controller?.abort();
    this.controller = new AbortController();
    this.close();
    this.setStatus("Resolving selected location...", "loading");
    try {
      const data = await fetchJson("/api/locations/retrieve", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider_id: suggestion.provider_id, session_token: this.session }),
        signal: this.controller.signal,
      });
      if (sequence !== this.sequence) return;
      const location = data.location;
      if (!location || !Number.isFinite(location.latitude) || !Number.isFinite(location.longitude) || typeof data.selection_token !== "string") {
        throw new Error("The selected location could not be resolved. Try another suggestion.");
      }
      this.input.value = location.display_name;
      document.querySelector("#map-frame").dataset.initialLocation = JSON.stringify(location);
      document.querySelector("#selection-token").value = data.selection_token;
      document.querySelector("#latitude").value = location.latitude;
      document.querySelector("#longitude").value = location.longitude;
      this.selected = true;
      this.session = null;
      this.form.classList.add("has-selection");
      this.fallback.hidden = true;
      this.syncButton();
      this.setStatus("Real location data selected", "selected");
      document.dispatchEvent(new CustomEvent("venuebite:location-selected", { detail: location }));
      this.input.focus();
    } catch (error) {
      if (error.name === "AbortError" || sequence !== this.sequence) return;
      this.setStatus(error.message, "error");
      this.fallback.hidden = false;
    }
  }
}
