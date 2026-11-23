import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Card from "../components/ui/Card.jsx";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/button.jsx";
import MonumentArt from "../components/MonumentArt.jsx";
import MonumentPhoto from "../components/MonumentPhoto.jsx";
import { findMonument, MONUMENT_CATALOG } from "../lib/catalog.js";

const QUICK_ACTIONS = [
  { to: "/monuments", title: "Explore Monuments", subtitle: "Browse heritage sites", icon: "monument" },
  { to: "/chat", title: "AI Heritage Chat", subtitle: "Ask grounded questions", icon: "chat" },
  { to: "/plan", title: "Plan a Trip", subtitle: "Build an itinerary", icon: "map" },
  { to: "/nearby", title: "Nearby Places", subtitle: "Around a location", icon: "pin" },
];

const RECOMMENDED = [
  { name: "Jaipur", state: "Rajasthan", art: "ruins", palette: "sand" },
  { name: "Hampi", state: "Karnataka", art: "shikhara", palette: "sage" },
  { name: "Varanasi", state: "Uttar Pradesh", art: "fort", palette: "night" },
];

function Icon({ name }) {
  const common = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case "monument": return <svg {...common}><path d="M4 21h16"/><rect x="8" y="10" width="8" height="11"/><path d="M8 10 Q12 4 16 10"/><path d="M12 4v3"/></svg>;
    case "chat":     return <svg {...common}><path d="M4 5h16v10H9l-5 4V5z"/></svg>;
    case "map":      return <svg {...common}><circle cx="12" cy="10" r="7"/><path d="M12 17v4"/><path d="M8 17l-3 4"/><path d="M16 17l3 4"/></svg>;
    case "pin":      return <svg {...common}><path d="M12 22s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>;
    default: return null;
  }
}

function useRecentlyExplored() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    try {
      const raw = localStorage.getItem("heritageai:recent-monuments");
      if (raw) setItems(JSON.parse(raw).slice(0, 3));
    } catch { /* ignore */ }
  }, []);
  return items;
}

export default function Dashboard() {
  const recent = useRecentlyExplored();
  const fallbackRecent = MONUMENT_CATALOG.slice(0, 3);
  const recentCards = recent.length ? recent : fallbackRecent;

  return (
    <div>
      <NavBar />

      <main className="container-page py-8">
        {/* Hero welcome */}
        <div className="relative overflow-hidden rounded-card min-h-[280px] md:min-h-[340px]">
          <img
            src={MONUMENT_CATALOG[0].image.url}
            alt={MONUMENT_CATALOG[0].image.caption}
            className="absolute inset-0 w-full h-full object-cover"
            loading="eager"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-teal-950/85 via-teal-950/55 to-teal-950/20" />
          <div className="relative p-8 md:p-10 text-white">
            <div className="eyebrow !text-saffron-400">Welcome back</div>
            <h1 className="font-heading text-4xl md:text-5xl font-bold mt-2">Namaste, Explorer</h1>
            <p className="mt-2 text-white/80 max-w-md">Continue exploring India's heritage.</p>
            <div className="mt-5">
              <Button as={Link} to="/chat">Ask the AI guide</Button>
            </div>
          </div>
        </div>

        {/* Quick actions */}
        <section className="mt-8">
          <div className="eyebrow mb-3">Quick actions</div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {QUICK_ACTIONS.map((a) => (
              <Link key={a.to} to={a.to}>
                <Card className="hover:-translate-y-0.5 transition p-5 h-full">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-teal-50 text-teal-800 grid place-items-center">
                      <Icon name={a.icon} />
                    </div>
                    <div>
                      <div className="font-semibold text-ink-900">{a.title}</div>
                      <div className="text-xs text-ink-500">{a.subtitle}</div>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </section>

        <div className="grid lg:grid-cols-[2fr_1fr] gap-6 mt-8">
          <div className="space-y-6">
            {/* Recently explored */}
            <section>
              <div className="flex items-center gap-3 mb-3">
                <div className="eyebrow">Recently explored</div>
                <Badge variant="teal" size="sm">From this browser</Badge>
              </div>
              <div className="grid sm:grid-cols-3 gap-4">
                {recentCards.map((m) => (
                  <Card key={m.id || m.name} padding="p-0" className="overflow-hidden">
                    <MonumentPhoto image={findMonument(m.id)?.image} art={m.art} palette={m.palette} className="aspect-[5/3]" rounded="rounded-none" />
                    <div className="p-4">
                      <div className="font-semibold">{m.name}</div>
                      <div className="text-xs text-ink-500 mt-0.5">{(m.tags || ["History","Architecture"]).slice(0,2).join(" · ")}</div>
                      <Link to={m.id ? `/monuments/${m.id}` : "/monuments"} className="mt-3 inline-flex items-center gap-1 text-teal-800 font-semibold text-sm">
                        Continue <span aria-hidden>›</span>
                      </Link>
                    </div>
                  </Card>
                ))}
              </div>
            </section>

            {/* Recommended destinations */}
            <section>
              <div className="flex items-center gap-3 mb-3">
                <div className="eyebrow">Recommended destinations</div>
                <Badge variant="demo" size="sm">Demo data</Badge>
              </div>
              <div className="grid sm:grid-cols-3 gap-4">
                {RECOMMENDED.map((d) => (
                  <Link key={d.name} to={`/plan?destination=${encodeURIComponent(d.name)}`}>
                    <div className="relative overflow-hidden rounded-2xl aspect-[5/4]">
                      <MonumentArt art={d.art} palette={d.palette} rounded="rounded-2xl" className="w-full h-full" />
                      <div className="absolute inset-0 bg-gradient-to-t from-teal-950/85 via-teal-950/10 to-transparent" />
                      <div className="absolute inset-0 p-4 flex flex-col justify-end text-white">
                        <div className="font-heading font-bold text-lg">{d.name}</div>
                        <div className="text-xs text-white/70">{d.state}</div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          </div>

          <div className="space-y-6">
            {/* Travel statistics */}
            <Card>
              <div className="flex items-center justify-between">
                <div className="eyebrow">Travel statistics</div>
                <Badge variant="demo" size="sm">Demo data</Badge>
              </div>
              <div className="grid grid-cols-2 gap-5 mt-4">
                {[
                  { n: "12", l: "Monuments viewed" },
                  { n: "3",  l: "Chats this session" },
                  { n: "1",  l: "Trips planned" },
                  { n: "5",  l: "Places saved" },
                ].map((s) => (
                  <div key={s.l}>
                    <div className="font-heading text-3xl font-bold text-ink-900">{s.n}</div>
                    <div className="text-xs text-ink-500">{s.l}</div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Recent activity */}
            <Card>
              <div className="flex items-center justify-between">
                <div className="eyebrow">Recent activity</div>
                <Badge variant="demo" size="sm">Demo data</Badge>
              </div>
              <ul className="mt-3 space-y-2.5 text-sm">
                {[
                  "Asked about Taj Mahal architecture",
                  "Generated an Agra 1-day itinerary",
                  "Viewed Red Fort details",
                ].map((a) => (
                  <li key={a} className="flex items-start gap-2">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-saffron-500" />
                    <span className="text-ink-700">{a}</span>
                  </li>
                ))}
              </ul>
            </Card>

            {/* India map placeholder */}
            <Card padding="p-0" className="overflow-hidden">
              <div className="p-4 flex items-center justify-between">
                <div className="font-semibold text-sm">Explore India map</div>
                <Badge variant="muted" size="sm">Preview</Badge>
              </div>
              <div className="h-48 bg-leaf-100/50 relative">
                <svg viewBox="0 0 400 180" className="w-full h-full">
                  <rect width="400" height="180" fill="#EEF6F5" />
                  <path d="M0 110 Q 120 70 200 90 T 400 85" stroke="#C49A45" strokeWidth="3" fill="none" />
                  <path d="M0 150 Q 130 120 260 140 T 400 145" stroke="#9BC1C1" strokeWidth="2" fill="none" />
                  <circle cx="120" cy="90" r="9" fill="#39734D" />
                  <circle cx="230" cy="80" r="9" fill="#E37B40" />
                  <circle cx="320" cy="110" r="9" fill="#E37B40" />
                  <text x="120" y="94" textAnchor="middle" fontSize="10" fontWeight="700" fill="#fff">1</text>
                  <text x="230" y="84" textAnchor="middle" fontSize="10" fontWeight="700" fill="#fff">2</text>
                  <text x="320" y="114" textAnchor="middle" fontSize="10" fontWeight="700" fill="#fff">3</text>
                </svg>
              </div>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
