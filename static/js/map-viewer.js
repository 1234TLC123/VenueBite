import { CompetitionMarkers } from "./competition-markers.js";
import { ParcelLayer } from "./parcel-layer.js";

const SDK_URL = "https://api.mapbox.com/mapbox-gl-js/v3.30.0/mapbox-gl.js";
const STYLES = {
  standard: "mapbox://styles/mapbox/standard",
  satellite: "mapbox://styles/mapbox/satellite-streets-v12",
};

function loadSdk() {
  if (window.mapboxgl) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    const timer = setTimeout(() => {
      script.remove();
      reject(new Error("Mapbox took too long to load. Check your connection and retry."));
    }, 15000);
    script.src = SDK_URL;
    script.onload = () => { clearTimeout(timer); resolve(); };
    script.onerror = () => {
      clearTimeout(timer);
      script.remove();
      reject(new Error("Mapbox could not be loaded. Check your connection and retry."));
    };
    document.head.append(script);
  });
}

export class MapViewer {
  constructor(config) {
    this.config = config;
    this.frame = document.querySelector("#map-frame");
    this.overlay = document.querySelector("#map-overlay");
    this.retry = document.querySelector("#retry-map");
    this.mode = "standard";
    this.location = null;
    this.styleReady = false;
    this.competition = new CompetitionMarkers(this.frame);
    this.parcel = new ParcelLayer(this.frame);
    this.reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (this.frame.dataset.initialLocation) {
      try { this.location = JSON.parse(this.frame.dataset.initialLocation); } catch { this.location = null; }
    }
    document.addEventListener("venuebite:location-selected", event => this.updateLocation(event.detail));
    document.addEventListener("venuebite:location-cleared", () => this.updateLocation(null));
    document.addEventListener("venuebite:analysis-invalidated", () => {
      this.competition.clear();
      this.parcel.clear(this.styleReady ? this.map : null);
    });
    document.querySelector("#recenter-map").addEventListener("click", () => this.centerLocation());
    document.querySelector("#focus-parcel").addEventListener("click", () => {
      if (this.styleReady) this.parcel.focus(this.map, this.location, this.reduceMotion.matches);
    });
    this.retry.addEventListener("click", () => this.initialize());
    for (const button of document.querySelectorAll("[data-map-style]")) {
      button.addEventListener("click", () => this.switchStyle(button.dataset.mapStyle));
    }
    window.addEventListener("pageshow", () => this.map?.resize());
  }

  showState(title, message, retry = false) {
    this.overlay.hidden = false;
    document.querySelector("#map-state-title").textContent = title;
    document.querySelector("#map-state-message").textContent = message;
    this.retry.hidden = !retry;
  }

  watchLoad() {
    clearTimeout(this.loadTimer);
    this.loadTimer = setTimeout(() => this.showState("Map unavailable", "This view took too long to load. Check your connection and retry.", true), 20000);
  }

  async initialize() {
    if (!this.config.enabled) {
      this.showState("Mapbox is not configured", this.config.message);
      return;
    }
    this.retry.disabled = true;
    this.showState("Loading geographic view", "Connecting to Mapbox");
    clearTimeout(this.loadTimer);
    this.competition.clear();
    this.parcel.clear(this.map);
    this.styleReady = false;
    this.map?.remove();
    this.map = null;
    this.marker = null;
    this.observer?.disconnect();
    for (const button of document.querySelectorAll("[data-map-style]")) button.disabled = true;
    document.querySelector("#recenter-map").disabled = true;
    let errorMessage = "Mapbox could not be loaded. Check your connection and retry.";
    try {
      await loadSdk();
      errorMessage = "Your browser cannot render this map. Check WebGL support.";
      if (!window.mapboxgl?.supported()) throw new Error("Your browser cannot render this map. Check WebGL support.");
      errorMessage = "Map initialization failed. Check the public token, connection, and browser graphics support.";
      this.map = new window.mapboxgl.Map({
        container: "location-map", accessToken: this.config.access_token,
        style: STYLES[this.mode], center: [0, 20], zoom: 1.3,
        ...(this.mode === "standard" ? { config: { basemap: { lightPreset: "dusk", showPointOfInterestLabels: false, showTransitLabels: false } } } : {}),
        attributionControl: true,
      });
      this.map.addControl(new window.mapboxgl.NavigationControl({ showCompass: false }), "top-right");
      this.map.on("style.load", () => {
        clearTimeout(this.loadTimer);
        this.styleReady = true;
        if (this.mode === "standard") {
          this.map.setConfigProperty("basemap", "lightPreset", "dusk");
          this.map.setConfigProperty("basemap", "showPointOfInterestLabels", false);
          this.map.setConfigProperty("basemap", "showTransitLabels", false);
        }
        this.overlay.hidden = true;
        for (const button of document.querySelectorAll("[data-map-style]")) button.disabled = false;
        this.updateLocation(this.location);
      });
      this.map.on("error", () => {
        clearTimeout(this.loadTimer);
        this.showState("Map unavailable", "Mapbox could not load this view. Check the public token, network connection, or browser graphics support.", true);
      });
      this.observer = new ResizeObserver(() => {
        this.map?.resize();
        this.centerLocation(false);
      });
      this.observer.observe(this.frame);
      this.watchLoad();
    } catch {
      this.showState("Map unavailable", errorMessage, true);
    } finally {
      this.retry.disabled = false;
    }
  }

  updateLocation(location) {
    this.location = location;
    const badge = document.querySelector("#geographic-data-badge");
    badge.hidden = !location;
    document.querySelector("#selected-location-name").textContent = location?.display_name || "No resolved location";
    document.querySelector("#selected-location-coordinates").textContent = location
      ? `${location.latitude.toFixed(5)}, ${location.longitude.toFixed(5)}` : "Geographic coordinates unavailable";
    document.querySelector("#recenter-map").disabled = !location || !this.map;
    this.marker?.remove();
    this.marker = null;
    this.competition.update(this.map, location);
    this.parcel.update(this.styleReady ? this.map : null, location);
    if (!this.map) return;
    if (location) {
      const marker = document.createElement("div");
      marker.className = "candidate-marker";
      marker.setAttribute("role", "img");
      marker.setAttribute("aria-label", "Candidate site");
      const icon = document.createElement("img");
      icon.src = "/static/icons/map-pin.svg";
      icon.alt = "";
      marker.append(icon);
      const content = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = location.display_name;
      const detail = document.createElement("p");
      detail.textContent = "Candidate site / real location data";
      content.append(title, detail);
      this.marker = new window.mapboxgl.Marker({ element: marker })
        .setLngLat([location.longitude, location.latitude])
        .setPopup(new window.mapboxgl.Popup({ offset: 24 }).setDOMContent(content))
        .addTo(this.map);
      this.centerLocation();
    } else {
      this.map.flyTo({ center: [0, 20], zoom: 1.3, duration: this.reduceMotion.matches ? 0 : 800 });
    }
  }

  centerLocation(animate = true) {
    if (!this.location || !this.map) return;
    const duration = this.reduceMotion.matches || !animate ? 0 : 1000;
    const payload = this.competition.currentPayload(this.location);
    if (payload?.pois.length) {
      const bounds = new window.mapboxgl.LngLatBounds();
      bounds.extend([this.location.longitude, this.location.latitude]);
      for (const poi of payload.pois) bounds.extend([poi.longitude, poi.latitude]);
      this.map.fitBounds(bounds, { padding: 48, maxZoom: 15, duration });
    } else if (this.location.bbox?.length === 4) {
      this.map.fitBounds(this.location.bbox, { padding: 48, maxZoom: 16, duration });
    } else {
      const zoom = { country: 4, region: 6, place: 10, locality: 12, neighborhood: 13, postcode: 12, street: 14 }[this.location.place_type] || 16;
      this.map.flyTo({ center: [this.location.longitude, this.location.latitude], zoom, duration });
    }
  }

  switchStyle(mode) {
    if (!this.map || mode === this.mode || !STYLES[mode]) return;
    this.mode = mode;
    for (const button of document.querySelectorAll("[data-map-style]")) {
      button.setAttribute("aria-pressed", String(button.dataset.mapStyle === mode));
    }
    this.showState("Loading map style", mode === "satellite" ? "Loading satellite imagery" : "Loading VenueBite map");
    this.watchLoad();
    this.styleReady = false;
    document.querySelector("#focus-parcel").disabled = true;
    try { this.map.setStyle(STYLES[mode], { diff: false }); } catch {
      clearTimeout(this.loadTimer);
      this.showState("Map unavailable", "This style could not be loaded. Retry the map.", true);
    }
  }
}
