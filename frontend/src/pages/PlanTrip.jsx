import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Card from "../components/ui/Card.jsx";
import Button from "../components/ui/button.jsx";
import Input from "../components/ui/Input.jsx";
import MonumentArt from "../components/MonumentArt.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import { api, formatINR } from "../lib/api.js";

const INTERESTS = ["History", "Architecture", "Religion", "Food", "Nature", "Culture"];
const STYLES = [
  { key: "budget",      title: "Budget",      subtitle: "Low-cost options" },
  { key: "balanced",    title: "Standard",    subtitle: "Balanced comfort" },
  { key: "comfortable", title: "Luxury",      subtitle: "Premium choices" },
];

const DRAFT_KEY = "heritageai:plan-draft";

function loadDraft() {
  try { return JSON.parse(localStorage.getItem(DRAFT_KEY) || "null"); } catch { return null; }
}
function saveDraft(form) {
  try { localStorage.setItem(DRAFT_KEY, JSON.stringify(form)); } catch { /* ignore */ }
}

export default function PlanTrip() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  const initial = loadDraft() || {
    destination: params.get("destination") || "Agra",
    origin: "Delhi",
    budget: 5000,
    days: 1,
    travelers: 1,
    travel_style: "budget",
    interests: ["History", "Architecture"],
    include_food: true,
    include_transport: true,
  };

  const [form, setForm] = useState(initial);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => { saveDraft(form); }, [form]);

  function set(key, value) { setForm((f) => ({ ...f, [key]: value })); }

  function toggleInterest(name) {
    setForm((f) => ({
      ...f,
      interests: f.interests.includes(name) ? f.interests.filter((x) => x !== name) : [...f.interests, name],
    }));
  }

  function validate() {
    const errs = {};
    if (!form.destination?.trim() || form.destination.trim().length < 2) errs.destination = "Enter a destination (2+ characters).";
    if (!form.origin?.trim() || form.origin.trim().length < 2) errs.origin = "Enter a starting location.";
    if (form.origin && form.destination && form.origin.trim().toLowerCase() === form.destination.trim().toLowerCase()) errs.origin = "Origin and destination must differ.";
    const b = Number(form.budget);
    if (!(b > 0)) errs.budget = "Budget must be greater than 0.";
    const d = Number(form.days);
    if (!(d >= 1 && d <= 30)) errs.days = "Days must be between 1 and 30.";
    const t = Number(form.travelers);
    if (!(t >= 1 && t <= 100)) errs.travelers = "Travelers must be between 1 and 100.";
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function submit(e) {
    e.preventDefault();
    if (!validate()) return;
    setError(null);
    setLoading(true);
    try {
      const body = {
        destination: form.destination.trim(),
        origin: form.origin.trim() || null,
        budget: Number(form.budget),
        days: Number(form.days),
        travelers: Number(form.travelers),
        travel_style: form.travel_style,
        interests: form.interests,
        include_food: !!form.include_food,
        include_transport: !!form.include_transport,
      };
      const result = await api.createItinerary(body);
      sessionStorage.setItem("heritageai:last-itinerary", JSON.stringify({ request: body, result }));
      navigate("/plan/results");
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <NavBar />
      <main className="container-page py-8">
        <div className="eyebrow">Itinerary planner</div>
        <h1 className="font-heading text-4xl md:text-5xl font-bold mt-2">Plan your heritage journey</h1>
        <p className="mt-2 text-ink-500 max-w-xl">Tell us about your trip and we'll build a day-wise plan with transparent costs.</p>

        <div className="mt-8 grid lg:grid-cols-[2fr_1fr] gap-6">
          <form onSubmit={submit}>
            <Card padding="p-6 md:p-8">
              {/* Step 1 */}
              <div className="flex items-center gap-3 mb-4">
                <StepDot n={1} />
                <h2 className="font-heading text-xl font-bold">Where are you going?</h2>
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                <Input
                  label="Destination"
                  required
                  value={form.destination}
                  onChange={(e) => set("destination", e.target.value)}
                  placeholder="e.g. Agra"
                  error={fieldErrors.destination}
                />
                <Input
                  label="Starting location"
                  required
                  value={form.origin}
                  onChange={(e) => set("origin", e.target.value)}
                  placeholder="e.g. Delhi"
                  error={fieldErrors.origin}
                />
              </div>

              {/* Step 2 */}
              <div className="flex items-center gap-3 mb-4 mt-8">
                <StepDot n={2} />
                <h2 className="font-heading text-xl font-bold">Trip details</h2>
              </div>
              <div className="grid sm:grid-cols-3 gap-4">
                <Input
                  label="Budget (INR)"
                  required
                  type="number"
                  min="1"
                  value={form.budget}
                  onChange={(e) => set("budget", e.target.value)}
                  prefix={<span className="text-ink-500 text-sm">Rs.</span>}
                  error={fieldErrors.budget}
                />
                <Input
                  label="Days"
                  required
                  type="number"
                  min="1"
                  max="30"
                  value={form.days}
                  onChange={(e) => set("days", e.target.value)}
                  suffix="day(s)"
                  error={fieldErrors.days}
                />
                <Input
                  label="Travellers"
                  required
                  type="number"
                  min="1"
                  max="100"
                  value={form.travelers}
                  onChange={(e) => set("travelers", e.target.value)}
                  suffix="person"
                  error={fieldErrors.travelers}
                />
              </div>

              {/* Step 3 */}
              <div className="flex items-center gap-3 mb-4 mt-8">
                <StepDot n={3} />
                <h2 className="font-heading text-xl font-bold">Preferences</h2>
              </div>

              <div className="mb-4">
                <label className="block mb-2 text-xs font-semibold tracking-wide text-ink-500 uppercase">Interests</label>
                <div className="flex flex-wrap gap-2">
                  {INTERESTS.map((i) => {
                    const active = form.interests.includes(i);
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => toggleInterest(i)}
                        className={`px-4 py-1.5 rounded-full text-sm font-semibold border transition ${active ? "bg-teal-800 text-white border-teal-800" : "bg-white text-ink-700 border-cream-300 hover:border-teal-700"}`}
                      >
                        {i}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="mb-5">
                <label className="block mb-2 text-xs font-semibold tracking-wide text-ink-500 uppercase">Travel style</label>
                <div className="grid sm:grid-cols-3 gap-3">
                  {STYLES.map((s) => {
                    const active = form.travel_style === s.key;
                    return (
                      <button
                        key={s.key}
                        type="button"
                        onClick={() => set("travel_style", s.key)}
                        className={`text-left p-4 rounded-2xl border transition ${active ? "border-teal-700 bg-teal-50" : "border-cream-300 bg-white hover:border-teal-600"}`}
                      >
                        <div className="font-semibold">{s.title}</div>
                        <div className="text-xs text-ink-500">{s.subtitle}</div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex flex-wrap gap-6 mb-6">
                <Toggle label="Include food" value={form.include_food} onChange={(v) => set("include_food", v)} />
                <Toggle label="Include transport" value={form.include_transport} onChange={(v) => set("include_transport", v)} />
              </div>

              {error && (
                <div className="mb-4"><ErrorBanner title="We could not reach the planning service" message={error.message} onRetry={() => submit({ preventDefault: () => {} })} /></div>
              )}

              <Button type="submit" size="lg" className="w-full" disabled={loading}>
                {loading ? "Generating..." : "Generate itinerary"}
              </Button>
              <p className="mt-3 text-center text-xs text-ink-400">Validation runs before sending. Only supported fields are submitted. Your inputs are saved in this browser.</p>
            </Card>
          </form>

          <aside className="space-y-5">
            <div className="relative rounded-card overflow-hidden">
              <MonumentArt art="fort" palette="rust" rounded="rounded-card" className="w-full aspect-[5/4]" />
              <div className="absolute inset-0 bg-gradient-to-t from-teal-950/85 to-transparent" />
              <div className="absolute inset-0 p-5 flex flex-col justify-end text-white">
                <div className="font-heading text-2xl font-bold">Heritage trips,</div>
                <div className="serif-italic text-2xl">planned with context</div>
              </div>
            </div>

            <Card>
              <div className="eyebrow mb-2">What you'll get</div>
              <ul className="space-y-2 text-sm">
                {["Day-wise activities","Transport options","Food and visitor services","Verified / estimated / unknown costs"].map((t) => (
                  <li key={t} className="flex items-start gap-2 text-ink-700">
                    <span className="mt-0.5 w-4 h-4 rounded-full bg-leaf-100 text-leaf-600 grid place-items-center">
                      <svg viewBox="0 0 24 24" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="3"><path d="M5 12l5 5L20 7"/></svg>
                    </span>
                    {t}
                  </li>
                ))}
              </ul>
              <div className="mt-4 text-xs text-ink-500">Approximate budget hint: {formatINR(Number(form.budget || 0))}</div>
            </Card>

            {loading && (
              <Card className="!bg-sand-100/60 !border-sand-100">
                <div className="eyebrow !text-sand-600">Loading state</div>
                <div className="mt-2 h-2 rounded-full bg-sand-100 overflow-hidden">
                  <div className="h-full bg-saffron-500 animate-pulse" style={{ width: "60%" }} />
                </div>
                <div className="mt-2 text-xs text-sand-600">Generating your itinerary...</div>
              </Card>
            )}
          </aside>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function StepDot({ n }) {
  return (
    <span className="w-7 h-7 rounded-full bg-teal-800 text-white grid place-items-center text-sm font-semibold">{n}</span>
  );
}

function Toggle({ label, value, onChange }) {
  return (
    <label className="inline-flex items-center gap-3 cursor-pointer select-none">
      <span className={`relative w-10 h-6 rounded-full transition ${value ? "bg-teal-800" : "bg-cream-300"}`}>
        <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all ${value ? "left-[18px]" : "left-0.5"}`} />
      </span>
      <input type="checkbox" className="sr-only" checked={value} onChange={(e) => onChange(e.target.checked)} />
      <span className="text-sm text-ink-700 font-medium">{label}</span>
    </label>
  );
}
