import { useEffect, useState } from "react";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Card from "../components/ui/Card.jsx";
import Button from "../components/ui/button.jsx";
import Input from "../components/ui/Input.jsx";
import Badge from "../components/ui/Badge.jsx";
import MapView from "../components/MapView.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { api } from "../lib/api.js";
import { MONUMENT_CATALOG } from "../lib/catalog.js";

const CATEGORIES = ["", "monument", "garden", "museum", "religious", "nature", "viewpoint", "market", "restaurant"];

export default function Nearby() {
  const [monumentId, setMonumentId] = useState(MONUMENT_CATALOG[0].id);
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [radius, setRadius] = useState(10);
  const [category, setCategory] = useState("");
  const [limit, setLimit] = useState(10);
  const [state, setState] = useState({ loading: false, data: null, error: null, anchorName: "" });

  // On mount and whenever monument changes, resolve its coords from backend.
  useEffect(() => {
    if (!monumentId) return;
    let cancelled = false;
    (async () => {
      try {
        const m = await api.getMonument(monumentId);
        if (cancelled) return;
        setLatitude(String(m.latitude));
        setLongitude(String(m.longitude));
        setState((s) => ({ ...s, anchorName: m.name }));
      } catch { /* ignore, user can still enter coords manually */ }
    })();
    return () => { cancelled = true; };
  }, [monumentId]);

  async function search(e) {
    if (e) e.preventDefault();
    const lat = Number(latitude);
    const lng = Number(longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      setState({ loading: false, data: null, error: new Error("Enter valid latitude and longitude, or pick a monument."), anchorName: "" });
      return;
    }
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const resp = await api.nearbyPlaces({
        latitude: lat,
        longitude: lng,
        radius_km: Number(radius) || 10,
        category: category || undefined,
        limit: Number(limit) || 10,
      });
      setState({ loading: false, data: resp, error: null, anchorName: state.anchorName });
    } catch (err) {
      setState((s) => ({ ...s, loading: false, data: null, error: err }));
    }
  }

  useEffect(() => {
    // auto-search when coords land
    if (latitude && longitude) search();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latitude, longitude, category, radius, limit]);

  const lat = Number(latitude), lng = Number(longitude);
  const hasCoords = Number.isFinite(lat) && Number.isFinite(lng);
  const places = state.data?.places || [];

  return (
    <div>
      <NavBar />
      <main className="container-page py-8">
        <div className="eyebrow">Nearby places</div>
        <h1 className="font-heading text-4xl md:text-5xl font-bold mt-2">Find what's around a monument</h1>
        <p className="mt-2 text-ink-500 max-w-xl">Pick a monument to anchor the search, or paste coordinates. Filter by category and distance.</p>

        <div className="mt-7 grid lg:grid-cols-[1fr_2fr] gap-6">
          <form onSubmit={search}>
            <Card>
              <div className="space-y-4">
                <div>
                  <label className="block mb-1.5 text-xs font-semibold tracking-wide text-ink-500 uppercase">Anchor monument</label>
                  <select
                    value={monumentId}
                    onChange={(e) => setMonumentId(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-field border border-cream-300 bg-white outline-none focus:border-saffron-500"
                  >
                    {MONUMENT_CATALOG.map((m) => (
                      <option key={m.id} value={m.id}>{m.name} — {m.city}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Input label="Latitude" value={latitude} onChange={(e) => setLatitude(e.target.value)} />
                  <Input label="Longitude" value={longitude} onChange={(e) => setLongitude(e.target.value)} />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Input label="Radius" value={radius} onChange={(e) => setRadius(e.target.value)} type="number" min="0.5" max="200" suffix="km" />
                  <Input label="Limit" value={limit} onChange={(e) => setLimit(e.target.value)} type="number" min="1" max="50" suffix="places" />
                </div>

                <div>
                  <label className="block mb-1.5 text-xs font-semibold tracking-wide text-ink-500 uppercase">Category</label>
                  <div className="flex flex-wrap gap-2">
                    {CATEGORIES.map((c) => {
                      const active = c === category;
                      const label = c === "" ? "All" : c.charAt(0).toUpperCase() + c.slice(1);
                      return (
                        <button
                          type="button"
                          key={c || "all"}
                          onClick={() => setCategory(c)}
                          className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border transition ${active ? "bg-teal-800 text-white border-teal-800" : "bg-white text-ink-700 border-cream-300 hover:border-teal-700"}`}
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <Button type="submit" className="w-full" disabled={state.loading}>{state.loading ? "Searching..." : "Search"}</Button>
              </div>
            </Card>
          </form>

          <div className="space-y-4">
            {state.error && <ErrorBanner title="Nearby places unavailable" message={state.error.message} onRetry={search} />}

            {hasCoords ? (
              <Card padding="p-0" className="overflow-hidden">
                <MapView
                  center={[lat, lng]}
                  zoom={13}
                  height={360}
                  markers={[
                    { id: "a", position: [lat, lng], title: state.anchorName || "Anchor", color: "#16504F", label: "A" },
                    ...places.map((p, i) => ({ id: p.id, position: [p.latitude, p.longitude], title: p.name, subtitle: `${p.distance_km.toFixed(1)} km · ${p.category}`, label: String(i + 1) })),
                  ]}
                />
              </Card>
            ) : (
              <Card>
                <div className="text-sm text-ink-500">Map shown only when valid coordinates are available.</div>
              </Card>
            )}

            <Card>
              <div className="flex items-center justify-between mb-3">
                <div className="eyebrow">Results</div>
                {state.data && <Badge variant="teal" size="sm">{state.data.count} place{state.data.count === 1 ? "" : "s"}</Badge>}
              </div>
              {places.length === 0 ? (
                <div className="text-sm text-ink-500">{state.loading ? "Searching..." : "No places found. Try a larger radius or a different category."}</div>
              ) : (
                <ul className="divide-y divide-cream-300">
                  {places.map((p, i) => (
                    <li key={p.id} className="py-3 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="w-7 h-7 rounded-full bg-saffron-500 text-white grid place-items-center text-xs font-bold">{i + 1}</span>
                        <div className="min-w-0">
                          <div className="font-semibold text-ink-900 truncate">{p.name}</div>
                          <div className="text-xs text-ink-500 truncate">{p.category} · {p.address}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-sm text-ink-700">{p.distance_km.toFixed(1)} km</span>
                        {p.source_url && (
                          <a href={p.source_url} target="_blank" rel="noreferrer" className="text-xs text-teal-800 hover:text-saffron-600 font-semibold">Source ↗</a>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
