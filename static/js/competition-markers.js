export class CompetitionMarkers {
  constructor(frame) {
    this.frame = frame;
    this.markers = [];
  }

  clear() {
    for (const marker of this.markers) marker.remove();
    this.markers = [];
    document.querySelector("#competition-legend").hidden = true;
  }

  currentPayload(location) {
    try {
      const payload = JSON.parse(this.frame.dataset.competition || "null");
      if (!location || !payload || payload.latitude !== location.latitude || payload.longitude !== location.longitude
          || payload.concept !== document.querySelector("#concept").value
          || String(payload.radius_miles) !== document.querySelector("#radius-miles").value
          || !Array.isArray(payload.pois)) return null;
      return payload;
    } catch { return null; }
  }

  update(map, location) {
    this.clear();
    const payload = this.currentPayload(location);
    if (!map || !payload) return;
    for (const poi of payload.pois) {
      const element = document.createElement("button");
      element.type = "button";
      element.className = `restaurant-marker ${poi.is_direct ? "direct-marker" : "general-marker"}`;
      const relationship = poi.is_direct ? "Direct match" : "Other restaurant";
      element.setAttribute("aria-label", `${poi.name}, ${relationship}, ${poi.distance}`);
      element.title = `${poi.name} / ${relationship}`;
      const icon = document.createElement("img");
      icon.src = "/static/icons/store.svg";
      icon.alt = "";
      element.append(icon);
      const content = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = poi.name;
      content.append(title);
      for (const text of [poi.address, `${poi.distance} straight-line distance`, `${relationship} / ${poi.match_basis}`]) {
        if (!text) continue;
        const paragraph = document.createElement("p");
        paragraph.textContent = text;
        content.append(paragraph);
      }
      const marker = new window.mapboxgl.Marker({ element })
        .setLngLat([poi.longitude, poi.latitude])
        .setPopup(new window.mapboxgl.Popup({ offset: 18 }).setDOMContent(content))
        .addTo(map);
      element.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          marker.togglePopup();
        }
      });
      this.markers.push(marker);
    }
    document.querySelector("#competition-legend").hidden = false;
  }
}
