const SOURCE = "venuebite-parcel";
const FILL = "venuebite-parcel-fill";
const OUTLINE = "venuebite-parcel-outline";

export class ParcelLayer {
  constructor(frame) { this.frame = frame; }

  currentPayload(location) {
    try {
      const payload = JSON.parse(this.frame.dataset.parcel || "null");
      if (!location || !payload || payload.latitude !== location.latitude || payload.longitude !== location.longitude
          || payload.concept !== document.querySelector("#concept").value
          || String(payload.radius_miles) !== document.querySelector("#radius-miles").value
          || !["exact", "nearby"].includes(payload.match_quality)
          || !["Polygon", "MultiPolygon"].includes(payload.geometry?.type)
          || !Array.isArray(payload.geometry.coordinates)) return null;
      return payload;
    } catch { return null; }
  }

  clear(map) {
    if (map) {
      for (const id of [OUTLINE, FILL]) if (map.getLayer(id)) map.removeLayer(id);
      if (map.getSource(SOURCE)) map.removeSource(SOURCE);
    }
    document.querySelector("#parcel-legend").hidden = true;
    document.querySelector("#focus-parcel").disabled = true;
  }

  update(map, location) {
    this.clear(map);
    const payload = this.currentPayload(location);
    if (!map || !payload) return;
    map.addSource(SOURCE, { type: "geojson", data: { type: "Feature", properties: {}, geometry: payload.geometry } });
    map.addLayer({ id: FILL, type: "fill", source: SOURCE,
      paint: { "fill-color": "#35b9cc", "fill-opacity": 0.14, "fill-emissive-strength": 1 } });
    map.addLayer({ id: OUTLINE, type: "line", source: SOURCE,
      paint: { "line-color": "#35b9cc", "line-width": 2.5, "line-emissive-strength": 1,
        ...(payload.match_quality === "nearby" ? { "line-dasharray": [3, 2] } : {}) } });
    document.querySelector("#parcel-match-label").textContent = payload.match_quality === "nearby"
      ? "Nearby parcel boundary - verify" : "Parcel boundary / exact point match";
    document.querySelector("#parcel-legend").hidden = false;
    document.querySelector("#focus-parcel").disabled = false;
  }

  focus(map, location, reducedMotion) {
    const payload = this.currentPayload(location);
    const bounds = payload?.bounds;
    if (!map || !Array.isArray(bounds) || bounds.length !== 4 || !bounds.every(Number.isFinite)
        || bounds[0] >= bounds[2] || bounds[1] >= bounds[3]
        || bounds[0] < -180 || bounds[2] > 180 || bounds[1] < -90 || bounds[3] > 90) return;
    map.fitBounds(bounds, { padding: 48, maxZoom: 18, duration: reducedMotion ? 0 : 700 });
  }
}
