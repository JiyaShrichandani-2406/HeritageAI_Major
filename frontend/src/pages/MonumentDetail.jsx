import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Card from "../components/ui/Card.jsx";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/button.jsx";
import MonumentPhoto from "../components/MonumentPhoto.jsx";
import MapView from "../components/MapView.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { api } from "../lib/api.js";
import { findMonument } from "../lib/catalog.js";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "history", label: "History" },
  { key: "architecture", label: "Architecture" },
  { key: "sources", label: "Sources" },
];

function rememberRecent(entry) {
  try {
    const key = "heritageai:recent-monuments";
    const raw = localStorage.getItem(key);
    const list = raw ? JSON.parse(raw) : [];
    const filtered = list.filter((x) => x.id !== entry.id);
    filtered.unshift(entry);
    localStorage.setItem(key, JSON.stringify(filtered.slice(0, 8)));
  } catch { /* ignore */ }
}

export default function MonumentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState("overview");
  const [state, setState] = useState({ loading: true, error: null, data: null });
  const [favourite, setFavourite] = useState(false);
  const catalogHint = findMonument(id);

  async function load() {
    setState({ loading: true, error: null, data: null });
    try {
      const data = await api.getMonument(id);
      setState({ loading: false, error: null, data });
      rememberRecent({
        id: data.id,
        name: data.name,
        tags: ["History", "Architecture"],
        art: catalogHint?.art || "taj",
        palette: catalogHint?.palette || "dusk",
      });
    } catch (e) {
      setState({ loading: false, error: e, data: null });
    }
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); /* reload on id */ }, [id]);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("heritageai:favourites") || "[]");
      setFavourite(saved.includes(id));
    } catch { /* ignore */ }
  }, [id]);

  function toggleFavourite() {
    try {
      const saved = JSON.parse(localStorage.getItem("heritageai:favourites") || "[]");
      const next = saved.includes(id) ? saved.filter((x) => x !== id) : [...saved, id];
      localStorage.setItem("heritageai:favourites", JSON.stringify(next));
      setFavourite(next.includes(id));
    } catch { /* ignore */ }
  }

  const art = catalogHint?.art || "taj";
  const palette = catalogHint?.palette || "dusk";
  const d = state.data;

  return (
    <div>
      <NavBar />

      {/* Hero */}
      <div className="relative overflow-hidden">
        <MonumentPhoto image={catalogHint?.image} art={art} palette={palette} rounded="rounded-none" className="absolute inset-0 w-full h-[360px]" withTrees={false} />
        <div className="absolute inset-0 bg-gradient-to-b from-teal-950/60 via-teal-950/30 to-teal-950/85 h-[360px]" />
        <div className="relative container-page pt-5 pb-14 text-white">
          <div className="text-xs text-white/70">
            <Link to="/monuments" className="hover:text-white">Monuments</Link>
            <span className="mx-1.5">/</span>
            <span className="text-white">{d?.name || catalogHint?.name || "Monument"}</span>
          </div>

          <div className="mt-20 md:mt-24 flex flex-col md:flex-row md:items-end md:justify-between gap-5">
            <div>
              <div className="flex flex-wrap gap-2 mb-3">
                {catalogHint?.tags.filter((t) => t !== "UNESCO").map((t) => (
                  <Badge key={t} variant="dot" size="sm">{t}</Badge>
                ))}
              </div>
              <h1 className="font-heading text-5xl md:text-6xl font-bold leading-[1.02]">{d?.name || catalogHint?.name || "Loading..."}</h1>
              {d && (
                <div className="mt-3 flex items-center gap-1 text-white/80 text-sm">
                  <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>
                  {d.city}, {d.state}, {d.country}
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <Button variant="darkGhost" onClick={toggleFavourite}>
                <svg viewBox="0 0 24 24" className="w-4 h-4" fill={favourite ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2"><path d="M12 21s-7-4.5-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 6c-2.5 4.5-9.5 9-9.5 9z"/></svg>
                {favourite ? "Favourited" : "Favourite"}
              </Button>
              <Button onClick={() => navigate(`/chat?monument=${encodeURIComponent(id)}`)}>Ask AI</Button>
            </div>
          </div>
        </div>
      </div>

      <main className="container-page py-8">
        {state.error ? (
          <ErrorBanner
            title="Could not load this monument"
            message={state.error.message}
            onRetry={load}
          />
        ) : null}

        {/* Tabs */}
        <div className="border-b border-cream-300 flex gap-6 overflow-x-auto">
          {TABS.map((t) => {
            const active = tab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`relative py-3 text-sm font-semibold transition ${active ? "text-ink-900" : "text-ink-500 hover:text-ink-700"}`}
              >
                {t.label}
                {active && <span className="absolute left-0 right-0 -bottom-px h-[2px] bg-saffron-500 rounded-full" />}
              </button>
            );
          })}
        </div>

        <div className="grid lg:grid-cols-[2fr_1fr] gap-6 mt-6">
          <div>
            {state.loading && !d ? (
              <Card><div className="animate-pulse h-5 w-32 bg-cream-200 rounded mb-4" />
                <div className="animate-pulse h-3 w-full bg-cream-200 rounded mb-2" />
                <div className="animate-pulse h-3 w-5/6 bg-cream-200 rounded" />
              </Card>
            ) : d && tab === "overview" ? (
              <div className="space-y-5">
                <section>
                  <div className="eyebrow">Overview</div>
                  <h2 className="font-heading text-2xl md:text-3xl font-bold mt-2">A monument of marble and memory</h2>
                  <p className="mt-3 text-ink-700 leading-relaxed">{d.summary}</p>
                </section>
                <Card>
                  <div className="eyebrow">History</div>
                  <p className="mt-2 text-ink-700 leading-relaxed">{d.history}</p>
                </Card>
                <Card>
                  <div className="eyebrow">Architecture</div>
                  <p className="mt-2 text-ink-700 leading-relaxed">{d.architecture}</p>
                </Card>
              </div>
            ) : d && tab === "history" ? (
              <Card>
                <div className="eyebrow">History</div>
                <p className="mt-2 text-ink-700 leading-relaxed whitespace-pre-line">{d.history}</p>
              </Card>
            ) : d && tab === "architecture" ? (
              <Card>
                <div className="eyebrow">Architecture</div>
                <p className="mt-2 text-ink-700 leading-relaxed whitespace-pre-line">{d.architecture}</p>
              </Card>
            ) : d && tab === "sources" ? (
              <Card>
                <div className="eyebrow">Sources</div>
                <ul className="mt-3 space-y-2">
                  {d.sources.map((s, i) => (
                    <li key={i}>
                      <a href={s.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-teal-800 hover:text-saffron-600 font-medium">
                        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 14a5 5 0 0 1 0-7l3-3a5 5 0 0 1 7 7l-1 1"/><path d="M14 10a5 5 0 0 1 0 7l-3 3a5 5 0 0 1-7-7l1-1"/></svg>
                        {s.title}
                      </a>
                    </li>
                  ))}
                </ul>
                {d.last_verified && (
                  <div className="mt-4 text-xs text-ink-500">Facts last verified: {d.last_verified}</div>
                )}
              </Card>
            ) : null}
          </div>

          <aside className="space-y-5">
            {d && Number.isFinite(d.latitude) && Number.isFinite(d.longitude) ? (
              <Card padding="p-0" className="overflow-hidden">
                <MapView
                  center={[d.latitude, d.longitude]}
                  zoom={14}
                  markers={[{ id: d.id, position: [d.latitude, d.longitude], title: d.name, subtitle: `${d.city}, ${d.state}`, label: "1" }]}
                  height={220}
                  className="rounded-none"
                />
                <div className="p-4 text-sm font-semibold text-ink-900">{d.city}, {d.state}</div>
              </Card>
            ) : null}

            {d && d.sources?.length ? (
              <Card>
                <div className="eyebrow">Sources</div>
                <ul className="mt-3 space-y-2">
                  {d.sources.slice(0,3).map((s, i) => (
                    <li key={i}>
                      <a href={s.url} target="_blank" rel="noreferrer" className="flex items-start gap-2 text-ink-700 hover:text-saffron-600 text-sm">
                        <svg viewBox="0 0 24 24" className="w-4 h-4 mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 14a5 5 0 0 1 0-7l3-3a5 5 0 0 1 7 7l-1 1"/><path d="M14 10a5 5 0 0 1 0 7l-3 3a5 5 0 0 1-7-7l1-1"/></svg>
                        <span className="font-semibold">{s.title}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}

            <Card className="bg-teal-900 text-white border-none">
              <div className="font-heading text-xl font-bold">Want to know more?</div>
              <p className="text-white/70 text-sm mt-1">Ask our AI guide about this monument.</p>
              <div className="mt-4 flex items-center gap-2">
                <Button as={Link} to={`/chat?monument=${encodeURIComponent(id)}`}>Ask AI</Button>
                <Button variant="darkGhost" as={Link} to={`/plan?destination=${encodeURIComponent(d?.city || catalogHint?.city || "")}`}>Plan a trip</Button>
              </div>
            </Card>
          </aside>
        </div>
      </main>

      <Footer />
    </div>
  );
}
