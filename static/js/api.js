export async function fetchJson(url, options = {}) {
  let response;
  try {
    response = await fetch(url, { cache: "no-store", ...options });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("The location service could not connect. Check your connection and try again.");
  }
  let data;
  try {
    data = await response.json();
    if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error();
  } catch {
    throw new Error("The location service returned an unreadable response. Please try again.");
  }
  if (!response.ok) throw new Error(data.error || "Location search is unavailable. Please try again.");
  return data;
}
