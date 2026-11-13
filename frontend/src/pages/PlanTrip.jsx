import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
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

function locationId(type, value) {
  if (!value) return "";
  if (value.startsWith(`${type}-`)) return value;
  return `${type}-${value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
}

export default function PlanTrip() {
  const navigate = useNavigate();
  const savedDraft = loadDraft();
  const savedMode = savedDraft?.itinerary_mode === "place_to_place"
    ? "place_to_place"
    : "city_to_city";

  const initial = {
    ...{
      budget: 5000,
      days: 1,
      travelers: 1,
      travel_style: "budget",
      interests: ["History", "Architecture"],
      include_food: true,
      include_transport: true,
      include_guides: false,
      include_parking: false,
      parking_vehicle_type: "",
    },
    ...savedDraft,
    itinerary_mode: savedMode,
    destination: savedMode === "city_to_city"
      ? "Agra"
      : locationId("place", savedDraft?.destination || "agra-fort"),
    origin: savedMode === "city_to_city"
      ? locationId("city", savedDraft?.origin || "Fatehpur Sikri")
      : locationId("place", savedDraft?.origin || "taj-mahal"),
  };

  const [form, setForm] = useState(initial);
  const [locations, setLocations] = useState({
    cities: [],
    places: [],
    loading: true,
    error: null,
  });
  const [locationRetry, setLocationRetry] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => { saveDraft(form); }, [form]);

  useEffect(() => {
    let active = true;
    setLocations((current) => ({ ...current, loading: true, error: null }));
    api.locations().then((catalog) => {
      if (active) {
        setLocations({
          cities: catalog.cities,
          places: catalog.places,
          loading: false,
          error: null,
        });
      }
    }).catch((loadError) => {
      if (active) {
        setLocations({
          cities: [],
          places: [],
          loading: false,
          error: loadError,
        });
      }
    });
    return () => { active = false; };
  }, [locationRetry]);

  const originCities = useMemo(
    () => locations.cities.filter((city) => city.id !== "city-agra"),
    [locations.cities],
  );
  const selectablePlaces = useMemo(
    () => locations.places.filter((place) => place.category !== "transit_stop"),
    [locations.places],
  );

  useEffect(() => {
    if (locations.loading || locations.error) return;
    setForm((current) => {
      const originOptions = current.itinerary_mode === "city_to_city"
        ? originCities
        : selectablePlaces;
      const originIsValid = originOptions.some((location) => location.id === current.origin);
      const destinationIsValid = current.itinerary_mode === "city_to_city"
        || selectablePlaces.some((place) => place.id === current.destination);
      const nextOrigin = originIsValid
        ? current.origin
        : current.itinerary_mode === "city_to_city"
          ? originCities[0]?.id || ""
          : selectablePlaces.find((place) => place.id !== current.destination)?.id || "";
      const nextDestination = destinationIsValid
        ? current.itinerary_mode === "city_to_city" ? "Agra" : current.destination
        : selectablePlaces.find((place) => place.id !== nextOrigin)?.id || "";
      if (nextOrigin === current.origin && nextDestination === current.destination) {
        return current;
      }
      return { ...current, origin: nextOrigin, destination: nextDestination };
    });
  }, [locations, originCities, selectablePlaces]);

  function set(key, value) { setForm((f) => ({ ...f, [key]: value })); }

  function setMode(mode) {
    if (form.itinerary_mode === mode) return;
    const defaultOrigin = mode === "city_to_city"
      ? originCities[0]?.id
      : locations.places.find((place) => place.id === "place-taj-mahal")?.id;
    const defaultDestination = mode === "city_to_city"
      ? "Agra"
      : locations.places.find((place) => place.id === "place-agra-fort")?.id;
    setForm((f) => ({
      ...f,
      itinerary_mode: mode,
      origin: defaultOrigin || "",
      destination: defaultDestination || "",
    }));
    setFieldErrors({});
  }

  function toggleInterest(name) {
    setForm((f) => ({
      ...f,
      interests: f.interests.includes(name) ? f.interests.filter((x) => x !== name) : [...f.interests, name],
    }));
  }

  function validate() {
    const errs = {};
    if (form.itinerary_mode === "city_to_city") {
      if (!originCities.some((city) => city.id === form.origin)) errs.origin = "Select an origin city.";
    } else {
      if (!selectablePlaces.some((place) => place.id === form.origin)) errs.origin = "Select a starting place.";
      if (!selectablePlaces.some((place) => place.id === form.destination)) errs.destination = "Select a destination place.";
      if (form.origin && form.origin === form.destination) errs.destination = "Starting and destination places must differ.";
    }
    const b = Number(form.budget);
    if (!(b > 0)) errs.budget = "Budget must be greater than 0.";
    const d = Number(form.days);
    if (!(d >= 1 && d <= 30)) errs.days = "Days must be between 1 and 30.";
    const t = Number(form.travelers);
    if (!(t >= 1 && t <= 100)) errs.travelers = "Travelers must be between 1 and 100.";
    if (form.include_parking && !form.parking_vehicle_type) {
      errs.parking_vehicle_type = "Select a vehicle type for parking costs.";
    }
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function submit(e) {
    e.preventDefault();
    if (!validate()) return;
    setError(null);
    setLoading(true);
    try {
      const originCity = originCities.find((city) => city.id === form.origin);
      const startPlace = selectablePlaces.find((place) => place.id === form.origin);
      const destinationPlace = selectablePlaces.find(
        (place) => place.id === form.destination,
      );
      const locationFields = form.itinerary_mode === "city_to_city"
        ? {
          itinerary_mode: "city_to_city",
          origin: originCity.name,
          origin_id: originCity.id,
          destination: "Agra",
          destination_id: "city-agra",
        }
        : {
          itinerary_mode: "place_to_place",
          origin: startPlace.name,
          origin_id: startPlace.id,
          destination: destinationPlace.name,
          destination_id: destinationPlace.id,
        };
      const body = {
        ...locationFields,
        budget: Number(form.budget),
        days: Number(form.days),
        travelers: Number(form.travelers),
        travel_style: form.travel_style,
        interests: form.interests,
        include_food: !!form.include_food,
        include_transport: !!form.include_transport,
        include_guides: !!form.include_guides,
        include_parking: !!form.include_parking,
        parking_vehicle_type: form.include_parking
          ? form.parking_vehicle_type
          : null,
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
                <h2 className="font-heading text-xl font-bold">Choose your itinerary mode</h2>
              </div>
              <div className="grid sm:grid-cols-2 gap-3 mb-5">
                <ModeButton
                  active={form.itinerary_mode === "city_to_city"}
                  onClick={() => setMode("city_to_city")}
                  title="City-to-City"
                  description="Choose an origin city. Destination is fixed to Agra."
                />
                <ModeButton
                  active={form.itinerary_mode === "place_to_place"}
                  onClick={() => setMode("place_to_place")}
                  title="Place-to-Place"
                  description="Choose both the starting and destination heritage places."
                />
              </div>
              {locations.loading && (
                <p className="mb-4 text-sm text-ink-500">Loading cities and places...</p>
              )}
              {locations.error && (
                <div className="mb-4">
                  <ErrorBanner
                    title="We could not load the location catalog"
                    message={locations.error.message}
                    onRetry={() => setLocationRetry((attempt) => attempt + 1)}
                  />
                </div>
              )}
              {form.itinerary_mode === "city_to_city" ? (
                <div className="grid sm:grid-cols-2 gap-4">
                  <SelectField
                    label="Origin city"
                    required
                    value={form.origin}
                    onChange={(value) => set("origin", value)}
                    options={originCities.map((city) => ({ value: city.id, label: city.name }))}
                    error={fieldErrors.origin}
                  />
                  <div>
                    <label className="block mb-1.5 text-xs font-semibold tracking-wide text-ink-500 uppercase">Destination</label>
                    <div className="rounded-field border border-cream-300 bg-cream-100 px-3.5 py-3 text-ink-700">Agra (fixed)</div>
                  </div>
                </div>
              ) : (
                <div className="grid sm:grid-cols-2 gap-4">
                  <SelectField
                    label="Starting place"
                    required
                    value={form.origin}
                    onChange={(value) => set("origin", value)}
                    options={selectablePlaces.map((place) => ({ value: place.id, label: `${place.name} · ${place.city}` }))}
                    error={fieldErrors.origin}
                  />
                  <SelectField
                    label="Destination place"
                    required
                    value={form.destination}
                    onChange={(value) => set("destination", value)}
                    options={selectablePlaces.map((place) => ({ value: place.id, label: `${place.name} · ${place.city}` }))}
                    error={fieldErrors.destination}
                  />
                </div>
              )}

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
                <Toggle label="Include guide costs" value={form.include_guides} onChange={(v) => set("include_guides", v)} />
                <Toggle
                  label="Include parking costs"
                  value={form.include_parking}
                  onChange={(v) => setForm((current) => ({
                    ...current,
                    include_parking: v,
                    parking_vehicle_type: v ? current.parking_vehicle_type : "",
                  }))}
                />
              </div>
              {form.include_parking && (
                <label className="block max-w-sm mb-6 text-sm font-medium text-ink-700">
                  Parking vehicle type
                  <select
                    value={form.parking_vehicle_type}
                    onChange={(event) => set("parking_vehicle_type", event.target.value)}
                    className="mt-1 block w-full rounded-xl border border-cream-300 bg-white px-3 py-2"
                  >
                    <option value="">Select a vehicle type</option>
                    <option value="two_wheeler">Two-wheeler</option>
                    <option value="car_taxi">Car or taxi</option>
                    <option value="tempo_traveller">Tempo traveller</option>
                    <option value="bus">Bus</option>
                  </select>
                  {fieldErrors.parking_vehicle_type && (
                    <span className="mt-1 block text-xs text-rose-600">{fieldErrors.parking_vehicle_type}</span>
                  )}
                </label>
              )}

              {error && (
                <div className="mb-4"><ErrorBanner title="We could not reach the planning service" message={error.message} onRetry={() => submit({ preventDefault: () => {} })} /></div>
              )}

              <Button
                type="submit"
                size="lg"
                className="w-full"
                disabled={loading || locations.loading || Boolean(locations.error)}
              >
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

function ModeButton({ active, onClick, title, description }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`text-left p-4 rounded-2xl border transition ${active ? "border-teal-700 bg-teal-50" : "border-cream-300 bg-white hover:border-teal-600"}`}
    >
      <div className="font-semibold">{title}</div>
      <div className="text-xs text-ink-500 mt-1">{description}</div>
    </button>
  );
}

function SelectField({ label, required, value, onChange, options, error }) {
  return (
    <div>
      <label className="block mb-1.5 text-xs font-semibold tracking-wide text-ink-500 uppercase">
        {label} {required && <span className="text-saffron-600">*</span>}
      </label>
      <select
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-invalid={Boolean(error)}
        className={`w-full rounded-field border bg-white px-3.5 py-3 text-ink-900 outline-none transition focus:border-saffron-500 focus:shadow-[0_0_0_4px_rgba(227,123,64,0.12)] ${error ? "border-rose-600" : "border-cream-300"}`}
      >
        {options.map((option) => {
          const item = typeof option === "string"
            ? { value: option, label: option }
            : option;
          return <option key={item.value} value={item.value}>{item.label}</option>;
        })}
      </select>
      {error && <p className="mt-1 text-xs text-rose-600">{error}</p>}
    </div>
  );
}
