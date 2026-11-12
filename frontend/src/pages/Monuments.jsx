import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Card from "../components/ui/Card.jsx";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/button.jsx";
import MonumentArt from "../components/MonumentArt.jsx";
import { MONUMENT_CATALOG, CATEGORIES } from "../lib/catalog.js";

const SORTS = [
  { key: "name-asc",  label: "Name A-Z" },
  { key: "name-desc", label: "Name Z-A" },
  { key: "state",     label: "State" },
];

export default function Monuments() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [sort, setSort] = useState("name-asc");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let list = MONUMENT_CATALOG.filter((m) => {
      if (q && !(m.name.toLowerCase().includes(q) || m.id.toLowerCase().includes(q) || m.city.toLowerCase().includes(q))) return false;
      if (category !== "All") {
        if (category === "UNESCO") return m.unesco;
        return m.tags.map((t) => t.toLowerCase()).includes(category.toLowerCase());
      }
      return true;
    });
    if (sort === "name-asc")  list = [...list].sort((a,b) => a.name.localeCompare(b.name));
    if (sort === "name-desc") list = [...list].sort((a,b) => b.name.localeCompare(a.name));
    if (sort === "state")     list = [...list].sort((a,b) => a.state.localeCompare(b.state));
    return list;
  }, [query, category, sort]);

  const featured = MONUMENT_CATALOG[0];

  return (
    <div>
      <NavBar />
      <main className="container-page py-8">
        <div className="eyebrow">Monument explorer</div>
        <h1 className="font-heading text-4xl md:text-5xl font-bold mt-2">Discover heritage monuments</h1>

        {/* Search + sort */}
        <Card padding="p-2" className="mt-6 flex items-center gap-2">
          <div className="flex items-center gap-3 px-3 flex-1">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-ink-400" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by monument name or ID..."
              className="flex-1 py-2.5 bg-transparent outline-none text-sm text-ink-900 placeholder:text-ink-400"
            />
          </div>
          <div className="hidden sm:flex items-center gap-2 px-3 border-l border-cream-300">
            <span className="text-xs text-ink-400">Sort:</span>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="bg-transparent text-sm font-semibold text-ink-900 outline-none"
            >
              {SORTS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
          </div>
          <Button variant="teal">Find</Button>
        </Card>

        {/* Category chips */}
        <div className="mt-5 flex flex-wrap gap-2">
          {CATEGORIES.map((c) => {
            const active = c === category;
            return (
              <button
                key={c}
                onClick={() => setCategory(c)}
                className={`px-4 py-1.5 rounded-full text-sm font-semibold border transition ${active ? "bg-teal-800 text-white border-teal-800" : "bg-white text-ink-700 border-cream-300 hover:border-teal-700"}`}
              >
                {c}
              </button>
            );
          })}
        </div>

        {/* Featured monument banner */}
        <div className="relative overflow-hidden rounded-card mt-6">
          <MonumentArt art={featured.art} palette="night" rounded="rounded-card" className="absolute inset-0 w-full h-full" />
          <div className="relative p-8 md:p-10 text-white min-h-[260px] flex flex-col justify-end">
            <Badge variant="gold" size="sm" className="self-start mb-3">Featured monument</Badge>
            <h2 className="font-heading text-4xl md:text-5xl font-bold">{featured.name}</h2>
            <div className="mt-2 text-white/80 flex items-center gap-1 text-sm">
              <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>
              {featured.city}, {featured.state}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {featured.tags.map((t) => (
                <Badge key={t} variant={t === "UNESCO" ? "unesco" : "dot"} size="sm">{t}</Badge>
              ))}
            </div>
            <div className="mt-5 flex items-center gap-3">
              <Button as={Link} to={`/monuments/${featured.id}`}>Explore details</Button>
              <Button variant="darkGhost">Save</Button>
            </div>
          </div>
        </div>

        {/* Grid */}
        {filtered.length === 0 ? (
          <div className="mt-8 text-ink-500 text-sm">No monuments match your filters.</div>
        ) : (
          <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((m) => (
              <Card key={m.id} padding="p-0" className="overflow-hidden group">
                <MonumentArt
                  art={m.art}
                  palette={m.palette}
                  rounded="rounded-none"
                  className="aspect-[5/3]"
                  overlay={
                    <>
                      {m.unesco && <div className="absolute top-3 left-3"><Badge variant="unesco" size="sm">UNESCO</Badge></div>}
                      <button aria-label="Save" className="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/90 grid place-items-center hover:bg-white">
                        <svg viewBox="0 0 24 24" className="w-4 h-4 text-saffron-600" fill="currentColor"><path d="M12 21s-7-4.5-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 6c-2.5 4.5-9.5 9-9.5 9z"/></svg>
                      </button>
                    </>
                  }
                />
                <div className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-heading font-bold text-lg">{m.name}</h3>
                      <div className="text-xs text-ink-500 flex items-center gap-1 mt-0.5">
                        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>
                        {m.city}{m.state && `, ${m.state}`}
                      </div>
                      <div className="mt-2">
                        <Badge variant="teal" size="sm">{m.tags.find((t) => t !== "UNESCO") || "Heritage"}</Badge>
                      </div>
                    </div>
                    <Button as={Link} to={`/monuments/${m.id}`} variant="outline" size="sm">Explore</Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
