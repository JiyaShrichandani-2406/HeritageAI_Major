import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Button from "../components/ui/button.jsx";
import Card from "../components/ui/Card.jsx";
import Badge from "../components/ui/Badge.jsx";
import MonumentArt from "../components/MonumentArt.jsx";
import MonumentPhoto from "../components/MonumentPhoto.jsx";
import { MONUMENT_CATALOG, DESTINATION_HINTS, POPULAR_SEARCHES } from "../lib/catalog.js";

function Feature({ label }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-6 h-6 rounded-full bg-saffron-500 text-white grid place-items-center">
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 12l5 5L20 7" />
        </svg>
      </span>
      <span className="text-white/90">{label}</span>
    </div>
  );
}

export default function Home() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  function onExplore(e) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return navigate("/monuments");
    const match = MONUMENT_CATALOG.find((m) => m.name.toLowerCase().includes(q.toLowerCase()));
    if (match) return navigate(`/monuments/${match.id}`);
    navigate(`/chat?q=${encodeURIComponent(q)}`);
  }

  const featured = MONUMENT_CATALOG.slice(0, 4);

  return (
    <div>
      {/* HERO */}
      <div className="hero-glow text-white">
        <NavBar variant="dark" />
        <section className="container-page relative pt-10 pb-20 md:pt-20 md:pb-28">
          <div className="grid lg:grid-cols-[1.1fr_1fr] gap-10 items-center">
            <div>
              <div className="text-saffron-400 text-xs font-bold tracking-[0.2em] uppercase">A new way to experience India</div>
              <h1 className="font-heading font-bold leading-[1.02] text-5xl md:text-6xl lg:text-7xl mt-4">
                Discover India's<br />
                <span className="serif-italic">Timeless Heritage</span>
              </h1>
              <p className="mt-5 text-white/80 max-w-xl text-lg">
                Explore monuments, ask source-backed questions and plan budget-aware journeys, all in one place.
              </p>

              <form onSubmit={onExplore} className="mt-8 bg-white rounded-full p-1.5 flex items-center gap-1 shadow-[0_18px_40px_rgba(0,0,0,0.35)] max-w-2xl">
                <div className="flex items-center gap-3 pl-4 pr-2 flex-1">
                  <svg viewBox="0 0 24 24" className="w-5 h-5 text-ink-400" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" />
                  </svg>
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search a monument, city or story..."
                    className="flex-1 py-2.5 bg-transparent outline-none text-ink-900 placeholder:text-ink-400 text-sm"
                  />
                </div>
                <div className="hidden sm:flex items-center gap-2 px-4 border-l border-cream-300 text-ink-500 text-sm">
                  <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 10h18" /><path d="M3 6h18" /><path d="M3 14h12" /></svg>
                  All categories
                </div>
                <Button type="submit" size="md">Explore</Button>
              </form>

              <div className="mt-5 flex flex-wrap items-center gap-2 text-white/70 text-sm">
                <span className="mr-1">Popular:</span>
                {POPULAR_SEARCHES.map((s) => (
                  <button key={s} onClick={() => { setQuery(s); }} className="px-3 py-1 rounded-full bg-white/10 border border-white/15 hover:bg-white/15 text-xs">{s}</button>
                ))}
              </div>

              <div className="mt-8 flex flex-wrap gap-6">
                <Feature label="Source-backed AI answers" />
                <Feature label="Transparent trip costs" />
                <Feature label="Nearby places and maps" />
              </div>
            </div>

            <div className="relative hidden lg:block">
              <MonumentPhoto image={MONUMENT_CATALOG[0].image} art="taj" palette="night" rounded="rounded-[32px]" className="aspect-[5/4] shadow-[0_30px_80px_rgba(0,0,0,0.45)]" />
            </div>
          </div>
        </section>
      </div>

      {/* FEATURED MONUMENTS */}
      <section className="container-page py-16">
        <div className="flex items-end justify-between mb-6">
          <div>
            <div className="eyebrow">Featured monuments</div>
            <h2 className="font-heading text-3xl md:text-4xl font-bold mt-2">Iconic places, rich stories</h2>
          </div>
          <Link to="/monuments" className="hidden sm:inline-flex items-center gap-1 text-teal-800 font-semibold hover:text-teal-700">
            View all monuments <span aria-hidden>›</span>
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {featured.map((m) => (
            <div key={m.id} className="group">
              <Card padding="p-0" className="overflow-hidden hover:-translate-y-0.5 transition">
                <MonumentPhoto image={m.image} art={m.art} palette={m.palette} linkTo={`/monuments/${m.id}`} linkLabel={`Explore ${m.name}`} rounded="rounded-none" className="aspect-[4/3]"
                  overlay={
                    <button
                      type="button"
                      aria-label="Save"
                      className="pointer-events-auto absolute top-3 right-3 w-8 h-8 rounded-full bg-white/90 grid place-items-center hover:bg-white"
                    >
                      <svg viewBox="0 0 24 24" className="w-4 h-4 text-saffron-600" fill="currentColor"><path d="M12 21s-7-4.5-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 6c-2.5 4.5-9.5 9-9.5 9z"/></svg>
                    </button>
                  }
                />
                <div className="p-4">
                  <h3 className="font-heading font-bold text-lg text-ink-900">
                    <Link to={`/monuments/${m.id}`} className="hover:text-teal-800">{m.name}</Link>
                  </h3>
                  <div className="text-xs text-ink-500 flex items-center gap-1 mt-1">
                    <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>
                    {m.city}{m.state && `, ${m.state}`}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {m.tags.filter((t) => t !== "UNESCO").slice(0,2).map((t) => (
                      <Badge key={t} variant="teal" size="sm">{t}</Badge>
                    ))}
                  </div>
                </div>
              </Card>
            </div>
          ))}
        </div>
      </section>

      {/* POPULAR DESTINATIONS */}
      <section className="container-page pb-16">
        <div className="eyebrow">Popular destinations</div>
        <h2 className="font-heading text-3xl md:text-4xl font-bold mt-2 mb-6">Start your journey</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
          {DESTINATION_HINTS.map((d) => (
            <div
              key={d.name}
              className="group block"
            >
              <MonumentPhoto
                image={MONUMENT_CATALOG.find((monument) => monument.id === d.monumentId)?.image}
                art={d.art}
                palette={d.palette}
                linkTo={d.monumentId ? `/monuments/${d.monumentId}` : `/plan?destination=${encodeURIComponent(d.name)}`}
                linkLabel={`Explore ${d.name}`}
                rounded="rounded-2xl"
                className="aspect-[5/4]"
              />
              <div className="pt-3">
                <Link
                  to={d.monumentId ? `/monuments/${d.monumentId}` : `/plan?destination=${encodeURIComponent(d.name)}`}
                  className="font-heading text-xl font-bold hover:text-teal-800"
                >
                  {d.name}
                </Link>
                <div className="text-xs text-ink-500">{d.summary}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* AI CHAT CTA */}
      <section className="container-page pb-16">
        <Card className="bg-teal-900 text-white border-none p-8 md:p-10" padding="">
          <div className="grid lg:grid-cols-2 gap-8 items-center">
            <div>
              <div className="text-saffron-400 text-xs font-bold tracking-[0.18em] uppercase">AI heritage chat</div>
              <h2 className="font-heading text-3xl md:text-4xl font-bold mt-2">
                Ask anything about India's<br />
                <span className="serif-italic">heritage, with sources.</span>
              </h2>
              <p className="mt-3 text-white/70 max-w-md">Answers grounded in indexed sources, with clickable citations.</p>
              <div className="mt-5">
                <Button as={Link} to="/chat">Start chatting</Button>
              </div>
            </div>

            <div className="space-y-3">
              <div className="ml-auto max-w-sm bg-teal-700 text-white rounded-2xl rounded-br-sm px-4 py-2.5 text-sm">
                Who built the Taj Mahal?
              </div>
              <div className="bg-white text-ink-900 rounded-2xl rounded-bl-sm p-4 text-sm shadow-[0_10px_30px_rgba(0,0,0,0.25)]">
                <p>The Taj Mahal was commissioned by Mughal emperor Shah Jahan...</p>
                <div className="mt-3 flex items-center gap-2 text-[11px]">
                  <Badge variant="verified" size="sm">Grounded</Badge>
                  <Badge variant="teal" size="sm">2 sources</Badge>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </section>

      {/* PLAN TRIP CTA */}
      <section className="container-page pb-16">
        <div className="relative overflow-hidden rounded-card bg-teal-900 text-white">
          <MonumentArt art="minar" palette="night" rounded="rounded-card" className="absolute inset-0 opacity-70" />
          <div className="relative p-8 md:p-10 flex flex-col md:flex-row md:items-center md:justify-between gap-5">
            <div>
              <h2 className="font-heading text-3xl md:text-4xl font-bold">Plan your heritage trip</h2>
              <p className="text-white/75 mt-2 max-w-xl">Day-wise itineraries with verified, estimated and unknown costs shown honestly.</p>
            </div>
            <Button as={Link} to="/plan">Plan your trip</Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
