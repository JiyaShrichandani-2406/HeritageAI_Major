// Thin fetch wrapper for the HeritageAI backend.
// All paths are mounted under /api/v1 by the backend's router.
// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js).

const BASE = import.meta.env.VITE_API_BASE || "/api/v1";

async function request(path, { method = "GET", body, params, signal } = {}) {
  let url = `${BASE}${path}`;
  if (params) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") qs.set(k, v);
    });
    const q = qs.toString();
    if (q) url += `?${q}`;
  }

  let response;
  try {
    response = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (e) {
    const err = new Error("The service is unreachable. Please check your connection and try again.");
    err.cause = e;
    err.network = true;
    throw err;
  }

  let payload = null;
  const text = await response.text();
  if (text) {
    try { payload = JSON.parse(text); } catch { payload = { detail: text }; }
  }

  if (!response.ok) {
    const msg = payload?.detail
      ? (Array.isArray(payload.detail) ? payload.detail.map(d => d.msg || d).join("; ") : String(payload.detail))
      : `Request failed (${response.status})`;
    const err = new Error(msg);
    err.status = response.status;
    err.payload = payload;
    throw err;
  }
  return payload;
}

export const api = {
  health: () => request("/health"),
  chat: (body, opts) => request("/chat", { method: "POST", body, ...opts }),
  getMonument: (id, opts) => request(`/monuments/${encodeURIComponent(id)}`, opts),
  createItinerary: (body, opts) => request("/itinerary", { method: "POST", body, ...opts }),
  nearbyPlaces: (params, opts) => request("/places/nearby", { params, ...opts }),
  routes: (body, opts) => request("/routes", { method: "POST", body, ...opts }),
  services: (params, opts) => request("/services", { params, ...opts }),
};

// Small helpers
export function formatINR(n) {
  if (n === null || n === undefined) return "Not available";
  try {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
  } catch {
    return `Rs. ${Math.round(n).toLocaleString("en-IN")}`;
  }
}
