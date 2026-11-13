import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Card from "../components/ui/Card.jsx";
import Button from "../components/ui/button.jsx";
import Badge from "../components/ui/Badge.jsx";
import MonumentArt from "../components/MonumentArt.jsx";
import CostBadge from "../components/CostBadge.jsx";
import MapView from "../components/MapView.jsx";
import { api, formatINR } from "../lib/api.js";

const TRANSPORT_ICONS = {
  train: "train", bus: "bus", cab: "cab", taxi: "cab", car: "cab", flight: "plane",
};

function TransportIcon({ type }) {
  const common = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" };
  const t = TRANSPORT_ICONS[(type || "").toLowerCase()] || "cab";
  if (t === "train")
    return <svg {...common}><rect x="5" y="3" width="14" height="14" rx="2"/><path d="M5 12h14"/><circle cx="9" cy="16" r="1"/><circle cx="15" cy="16" r="1"/></svg>;
  if (t === "bus")
    return <svg {...common}><rect x="4" y="4" width="16" height="12" rx="2"/><path d="M4 10h16"/><circle cx="8" cy="18" r="1.5"/><circle cx="16" cy="18" r="1.5"/></svg>;
  if (t === "plane")
    return <svg {...common}><path d="M3 11l18-6-6 18-3-8-9-4z"/></svg>;
  return <svg {...common}><path d="M3 15l2-6h14l2 6"/><rect x="3" y="15" width="18" height="4" rx="1"/><circle cx="7" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/></svg>;
}

const ART_FOR_NAME = (name = "") => {
  const n = name.toLowerCase();
  if (n.includes("taj")) return { art: "taj", palette: "dusk" };
  if (n.includes("fort") || n.includes("red")) return { art: "fort", palette: "rust" };
  if (n.includes("temple") || n.includes("khajuraho") || n.includes("sun")) return { art: "shikhara", palette: "sage" };
  if (n.includes("minar") || n.includes("qutub") || n.includes("tower")) return { art: "minar", palette: "sand" };
  if (n.includes("hampi") || n.includes("ruin")) return { art: "ruins", palette: "sand" };
  if (n.includes("lunch") || n.includes("food") || n.includes("meal")) return { art: "ruins", palette: "mint" };
  return { art: "taj", palette: "dusk" };
};

export default function Itinerary() {
  const navigate = useNavigate();
  const [bundle, setBundle] = useState(null);
  const [nearby, setNearby] = useState({ loading: false, places: [], error: null });

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("heritageai:last-itinerary");
      if (raw) setBundle(JSON.parse(raw));
    } catch { /* ignore */ }
  }, []);

  // When we have an itinerary, grab a first activity's monument coords from the catalog to anchor "Nearby places".
  useEffect(() => {
    if (!bundle) return;
    // Attempt to look up the first activity by name on /monuments/{id} slugs.
    const firstName = bundle.result?.itinerary?.[0]?.activities?.[0]?.place_name || bundle.result?.destination;
    if (!firstName) return;
    const slug = firstName.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
    (async () => {
      setNearby((n) => ({ ...n, loading: true, error: null }));
      try {
        const monument = await api.getMonument(slug);
        const resp = await api.nearbyPlaces({
          latitude: monument.latitude,
          longitude: monument.longitude,
          radius_km: 10,
          limit: 6,
        });
        setNearby({
          loading: false,
          error: null,
          places: resp.places || [],
          center: [monument.latitude, monument.longitude],
          anchor: { name: monument.name, lat: monument.latitude, lng: monument.longitude },
        });
      } catch (e) {
        // Soft-fail — show map-less list only if the destination isn't in the catalog.
        setNearby({ loading: false, error: e, places: [] });
      }
    })();
  }, [bundle]);

  const req = bundle?.request;
  const res = bundle?.result;

  const costPct = useMemo(() => {
    if (!res) return { v: 0, e: 0, u: 0 };
    let verified = 0, estimated = 0, unknown = 0;
    const statuses = ["entry_cost_status"];
    if (req?.include_transport) statuses.push("transport_cost_status");
    if (req?.include_food) statuses.push("food_cost_status");
    if (req?.include_guides) statuses.push("guide_cost_status");
    if (req?.include_parking) statuses.push("parking_cost_status");
    for (const day of res.itinerary) for (const a of day.activities) {
      for (const s of statuses) {
        if (a[s] === "verified") verified++;
        else if (a[s] === "estimated") estimated++;
        else unknown++;
      }
    }
    const total = Math.max(1, verified + estimated + unknown);
    return { v: Math.round((verified/total)*100), e: Math.round((estimated/total)*100), u: Math.round((unknown/total)*100) };
  }, [req, res]);

  if (!bundle) {
    return (
      <div>
        
        <NavBar />
        <main className="container-page py-16 text-center">
          <h1 className="font-heading text-3xl font-bold">No itinerary yet</h1>
          <p className="mt-2 text-ink-500">Fill in the planner to generate your first heritage itinerary.</p>
          <div className="mt-5"><Button onClick={() => navigate("/plan")}>Open the planner</Button></div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div>
      <NavBar />

      <main className="container-page py-8">
        <div className="text-xs text-ink-500 mb-3">
          <Link to="/plan" className="hover:text-ink-700">Plan Trip</Link>
          <span className="mx-1.5">/</span>
          <span>Itinerary results</span>
        </div>

        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 className="font-heading text-4xl md:text-5xl font-bold">{res.destination} Heritage Trail</h1>
            <div className="mt-3 flex flex-wrap gap-2">
              {req.itinerary_mode && (
                <Badge variant="teal" size="sm">
                  {req.itinerary_mode === "place_to_place" ? "Place-to-Place" : "City-to-City"}
                </Badge>
              )}
              {req.origin && <Badge variant="teal" size="sm">From {req.origin}</Badge>}
              <Badge variant="teal" size="sm">To {res.destination}</Badge>
              <Badge variant="teal" size="sm">{res.days} day{res.days > 1 ? "s" : ""}</Badge>
              <Badge variant="teal" size="sm">{req.travelers} traveller{req.travelers > 1 ? "s" : ""}</Badge>
              <Badge variant="teal" size="sm">{req.travel_style} style</Badge>
            </div>
          </div>
          <Button variant="outline" onClick={() => navigate("/plan")}>Edit trip</Button>
        </div>

        {res.message && <p className="mt-3 text-sm text-ink-500 max-w-2xl">{res.message}</p>}

        <div className="grid lg:grid-cols-[2fr_1fr] gap-6 mt-7">
          {/* LEFT: days + transport + nearby */}
          <div className="space-y-6">
            {res.itinerary.map((day) => (
              <Card key={day.day} padding="p-6">
                <div className="eyebrow">Day {day.day}</div>
                <h2 className="font-heading text-2xl font-bold mt-1">{day.title}</h2>

                <ol className="mt-5 space-y-4">
                  {day.activities.map((a, i) => {
                    const art = ART_FOR_NAME(a.place_name);
                    const costSummary = (() => {
                      const fields = [
                        ["Entry", a.estimated_entry_cost, a.entry_cost_status],
                        ...(req.include_transport ? [["Transport", a.estimated_transport_cost, a.transport_cost_status]] : []),
                        ...(req.include_food ? [["Food", a.estimated_food_cost, a.food_cost_status]] : []),
                        ...(req.include_guides ? [["Guide", a.estimated_guide_cost, a.guide_cost_status]] : []),
                        ...(req.include_parking ? [["Parking", a.estimated_parking_cost, a.parking_cost_status]] : []),
                      ];
                      return fields.map(([label, value, status]) => ({ label, v: value, s: status }));
                    })();
                    const includedStatuses = [
                      a.entry_cost_status,
                      ...(req.include_transport ? [a.transport_cost_status] : []),
                      ...(req.include_food ? [a.food_cost_status] : []),
                      ...(req.include_guides ? [a.guide_cost_status] : []),
                      ...(req.include_parking ? [a.parking_cost_status] : []),
                    ];
                    const worstStatus =
                      includedStatuses.includes("unknown") ? "unknown" :
                      includedStatuses.includes("estimated") ? "estimated" :
                      "verified";
                    return (
                      <li key={i} className="flex items-start gap-4">
                        <div className="w-8 h-8 shrink-0 rounded-full bg-teal-800 text-white grid place-items-center font-semibold text-sm">{i + 1}</div>
                        <div className="flex-1 rounded-2xl border border-cream-300 bg-white p-3 flex gap-3">
                          <MonumentArt art={art.art} palette={art.palette} className="w-24 h-20 shrink-0" rounded="rounded-xl" withTrees={false} withHill />
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-ink-900">{a.place_name}</div>
                            <div className="text-sm text-ink-500 line-clamp-2">{a.description}</div>
                            <div className="mt-2 flex flex-wrap items-center gap-2">
                              <CostBadge status={worstStatus} />
                              <span className="text-xs text-ink-500">
                                Cost:{" "}
                                {costSummary.length === 0
                                  ? "Not available"
                                  : costSummary.map((p, j) => (
                                      <span key={j} className="inline-flex items-center gap-1 mr-2">
                                        <span className="text-ink-400">{p.label}</span>
                                        <span className={p.s === "unknown" || p.v == null ? "text-ink-400" : "text-ink-700 font-semibold"}>
                                          {p.s === "unknown" || p.v == null
                                            ? "Unknown"
                                            : p.s === "estimated" ? `about ${formatINR(p.v)}` : formatINR(p.v)}
                                        </span>
                                      </span>
                                    ))}
                              </span>
                            </div>
                            {req.include_guides && a.guide_source_url && (
                              <a href={a.guide_source_url} target="_blank" rel="noreferrer" className="mr-3 mt-1 inline-block text-xs text-teal-800 hover:text-saffron-600 font-semibold">Guide source</a>
                            )}
                            {req.include_parking && a.parking_source_url && (
                              <a href={a.parking_source_url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-teal-800 hover:text-saffron-600 font-semibold">Parking source</a>
                            )}
                            {(a.transport_type || a.estimated_travel_duration_minutes != null) && (
                              <div className="mt-1 text-xs text-ink-500">
                                Travel from previous stop
                                {a.transport_type ? ` · ${a.transport_type}` : ""}
                                {a.estimated_travel_duration_minutes != null
                                  ? ` · ${a.travel_duration_status === "estimated" ? "estimated " : a.travel_duration_status === "verified" ? "verified " : ""}${a.estimated_travel_duration_minutes < 60
                                    ? `${a.estimated_travel_duration_minutes} min`
                                    : `${Math.floor(a.estimated_travel_duration_minutes / 60)} h ${a.estimated_travel_duration_minutes % 60} min`}`
                                  : ""}
                              </div>
                            )}
                            {a.travel_duration_status === "unknown" && a.transport_type && i > 0 && (
                              <div className="mt-1 text-xs text-ink-400">
                                Travel duration unavailable or unverified.
                              </div>
                            )}
                            {a.transport_notes && (
                              <div className="mt-1 text-xs text-ink-400">
                                {a.transport_notes}
                              </div>
                            )}
                            {i > 0 && !a.transport_type && a.estimated_travel_duration_minutes == null && (
                              <div className="mt-1 text-xs text-ink-400">
                                No sourced local route is listed for this leg.
                              </div>
                            )}
                            {a.transport_source_url && (
                              <a
                                href={a.transport_source_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 mt-1 text-xs text-teal-800 hover:text-saffron-600 font-semibold"
                              >
                                Transport source
                              </a>
                            )}
                            {a.source_url && (
                              <a href={a.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 mt-1 text-xs text-teal-800 hover:text-saffron-600 font-semibold">
                                Source
                                <svg viewBox="0 0 24 24" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2"><path d="M7 17 17 7"/><path d="M8 7h9v9"/></svg>
                              </a>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ol>

                <div className="mt-5 flex items-center justify-between text-sm">
                  <span className="text-ink-500">Day estimated total</span>
                  <span className="font-semibold">
                    {day.estimated_cost == null
                      ? "Incomplete — included costs are unknown"
                      : formatINR(day.estimated_cost)}
                  </span>
                </div>
              </Card>
            ))}

            {(res.transport_options?.length > 0 || req.origin_id || req.destination_id) && (
              <Card>
                <div className="eyebrow mb-3">Transport options</div>
                {res.transport_options?.length > 0 ? (
                  <div className="grid sm:grid-cols-3 gap-3">
                  {res.transport_options.map((t) => (
                    <div key={t.id} className="p-4 rounded-2xl border border-cream-300 bg-white">
                      <div className="flex items-center gap-2 text-teal-800">
                        <TransportIcon type={t.transport_type} />
                        <span className="font-semibold capitalize">{t.transport_type}</span>
                      </div>
                      <div className="text-xs text-ink-500 mt-1">{t.origin} → {t.destination}</div>
                      <div className="mt-2 flex items-center justify-between text-sm">
                        <CostBadge status={t.cost_status} />
                        <span className="font-semibold">
                          {t.estimated_cost == null
                            ? "Fare unavailable or unverified"
                            : (t.cost_status === "estimated" ? `about ${formatINR(t.estimated_cost)}` : formatINR(t.estimated_cost))}
                        </span>
                      </div>
                      {t.estimated_duration_minutes != null && (
                        <div className="mt-1 text-xs text-ink-400">
                          {t.duration_status === "estimated"
                            ? "Estimated "
                            : t.duration_status === "verified"
                              ? "Verified "
                              : ""}
                          {t.estimated_duration_minutes < 60
                            ? `${t.estimated_duration_minutes} min`
                            : `${Math.floor(t.estimated_duration_minutes / 60)} h ${t.estimated_duration_minutes % 60} min`}
                        </div>
                      )}
                      {t.duration_status === "unknown" && (
                        <div className="mt-1 text-xs text-ink-400">
                          Duration unavailable or unverified.
                        </div>
                      )}
                      {t.notes && <div className="mt-2 text-xs text-ink-500">{t.notes}</div>}
                    </div>
                  ))}
                  </div>
                ) : (
                  <p className="text-sm text-ink-500">
                    No sourced transport options are currently listed for this exact route.
                  </p>
                )}
              </Card>
            )}

            <Card>
              <div className="eyebrow mb-3">Nearby places</div>
              {nearby.loading ? (
                <div className="text-sm text-ink-500">Looking up nearby places...</div>
              ) : nearby.places.length === 0 ? (
                <div className="text-sm text-ink-500">Map shown only when valid coordinates are available.</div>
              ) : (
                <>
                  <MapView
                    center={nearby.center}
                    zoom={13}
                    height={280}
                    markers={[
                      ...(nearby.anchor ? [{ id: "anchor", position: [nearby.anchor.lat, nearby.anchor.lng], title: nearby.anchor.name, color: "#16504F", label: "A" }] : []),
                      ...nearby.places.map((p, idx) => ({
                        id: p.id,
                        position: [p.latitude, p.longitude],
                        title: p.name,
                        subtitle: `${p.distance_km.toFixed(1)} km · ${p.category}`,
                        label: String(idx + 1),
                      })),
                    ]}
                  />
                  <ul className="mt-4 divide-y divide-cream-300">
                    {nearby.places.map((p, idx) => (
                      <li key={p.id} className="py-2.5 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="w-6 h-6 rounded-full bg-saffron-500 text-white grid place-items-center text-xs font-bold">{idx + 1}</span>
                          <div className="min-w-0">
                            <div className="font-semibold text-sm truncate">{p.name}</div>
                            <div className="text-xs text-ink-500 truncate">{p.category} · {p.address}</div>
                          </div>
                        </div>
                        <div className="text-sm text-ink-700 shrink-0">{p.distance_km.toFixed(1)} km</div>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </Card>
          </div>

          {/* RIGHT: budget + services + chat CTA */}
          <aside className="space-y-5">
            <Card>
              <div className="eyebrow mb-3">Budget breakdown</div>
              <div className="space-y-2 text-sm">
                <Row label="Budget" value={formatINR(res.budget)} />
                <Row label="Known cost subtotal" value={formatINR(res.known_cost_subtotal)} valueClass="text-teal-800 font-semibold" />
                <Row label="Priced subtotal" value={`${formatINR(res.priced_cost_subtotal)} (verified + estimated)`} />
                <Row
                  label="Estimated total cost"
                  value={res.estimated_total_cost == null
                    ? "Incomplete — included costs are unknown"
                    : `${formatINR(res.estimated_total_cost)} (est.)`}
                  valueClass={res.estimated_total_cost == null ? "text-ink-400" : "text-saffron-600 font-semibold"}
                />
                <Row label="Unknown cost items" value={res.unknown_cost_count} />
                <Row
                  label="Remaining budget"
                  value={res.remaining_budget == null ? "Cannot confirm" : formatINR(res.remaining_budget)}
                  valueClass={res.remaining_budget == null ? "text-ink-400" : "text-ink-900 font-semibold"}
                />
              </div>

              <div className="mt-4">
                <div className="text-xs text-ink-500 mb-1.5">Cost confidence</div>
                <div className="flex h-2 rounded-full overflow-hidden bg-cream-200">
                  <div className="bg-leaf-600" style={{ width: `${costPct.v}%` }} />
                  <div className="bg-saffron-500" style={{ width: `${costPct.e}%` }} />
                  <div className="bg-cream-300" style={{ width: `${costPct.u}%`, backgroundImage: "repeating-linear-gradient(45deg,#D9CFBB 0 4px,#E4DCCB 4px 8px)" }} />
                </div>
                <div className="mt-2 flex items-center gap-2 text-[11px]">
                  <Badge variant="verified" size="sm">Verified</Badge>
                  <Badge variant="estimated" size="sm">Estimated</Badge>
                  <Badge variant="unknown" size="sm">Unknown</Badge>
                </div>
              </div>

              <div className={`mt-4 p-3 rounded-2xl text-sm ${res.within_budget === null ? "bg-sand-100 text-sand-600" : res.within_budget ? "bg-leaf-100 text-leaf-600" : "bg-rose-100 text-rose-600"}`}>
                <div className="font-semibold">
                  {res.within_budget === null
                    ? "Budget status: cannot be confirmed"
                    : res.within_budget
                      ? "Budget status: within budget"
                      : "Budget status: over budget"}
                </div>
                <div className="text-xs mt-1 opacity-90">
                  {res.within_budget === null
                    ? res.priced_cost_subtotal > res.budget
                      ? "Priced costs already exceed the budget; unresolved costs prevent a complete total."
                      : res.unknown_cost_count > 0
                        ? "Unknown costs are excluded from the priced subtotal, so the complete trip total is unavailable."
                        : "The total includes estimates, so budget compliance is not verified."
                    : res.within_budget
                      ? "The estimated total is at or below your budget."
                      : "The estimated total exceeds your budget — adjust days, style or interests."}
                </div>
              </div>

              {res.assumptions?.length > 0 && (
                <div className="mt-4">
                  <div className="eyebrow mb-1">Assumptions</div>
                  <ul className="list-disc list-inside text-xs text-ink-500 space-y-0.5">
                    {res.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                  </ul>
                </div>
              )}
            </Card>

            {res.visitor_services?.length > 0 && (
              <Card>
                <div className="eyebrow mb-3">Visitor services</div>
                <div className="flex flex-wrap gap-2">
                  {res.visitor_services.map((s) => (
                    <span key={s.id} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-cream-300 bg-white text-xs text-ink-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-700" />
                      {s.name} <span className="text-ink-400">· {s.category}</span>
                    </span>
                  ))}
                </div>
              </Card>
            )}

            <Card className="bg-teal-900 text-white border-none">
              <div className="font-heading text-xl font-bold">Questions about this trip?</div>
              <p className="text-white/70 text-sm mt-1">Ask the AI guide about these places.</p>
              <div className="mt-4"><Button as={Link} to={`/chat?q=${encodeURIComponent("Tell me more about " + res.destination)}`}>Open AI chat</Button></div>
            </Card>
          </aside>
        </div>
      </main>

      <Footer />
    </div>
  );
}

function Row({ label, value, valueClass = "" }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-ink-500">{label}</span>
      <span className={valueClass || ""}>{value}</span>
    </div>
  );
}
