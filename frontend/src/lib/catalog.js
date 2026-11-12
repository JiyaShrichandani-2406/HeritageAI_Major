// Curated monument catalog for the Explorer page.
// The backend does not expose a "list all monuments" endpoint, so the UI
// renders a card for each entry here and fetches details on demand from
// GET /api/v1/monuments/{id}. IDs MUST match the backend dataset in
// data/processed/heritage.json. Only monuments that exist there are listed.
//
// Fields outside the backend contract (unesco, tags, art, palette) are
// UI-only annotations used for the illustration and category filters.

export const CATEGORIES = ["All", "Historical", "Religious", "Architectural", "UNESCO"];

export const MONUMENT_CATALOG = [
  {
    id: "taj-mahal",
    name: "Taj Mahal",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: true,
    tags: ["UNESCO", "Architectural", "Historical"],
    art: "taj",
    palette: "dusk",
  },
  {
    id: "agra-fort",
    name: "Agra Fort",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: true,
    tags: ["UNESCO", "Historical", "Architectural"],
    art: "fort",
    palette: "rust",
  },
  {
    id: "fatehpur-sikri",
    name: "Fatehpur Sikri",
    city: "Fatehpur Sikri",
    state: "Uttar Pradesh",
    unesco: true,
    tags: ["UNESCO", "Historical", "Architectural"],
    art: "fort",
    palette: "sand",
  },
  {
    id: "akbar-tomb-sikandra",
    name: "Akbar's Tomb (Sikandra)",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Historical", "Architectural"],
    art: "shikhara",
    palette: "sand",
  },
  {
    id: "mehtab-bagh",
    name: "Mehtab Bagh",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Historical"],
    art: "ruins",
    palette: "sage",
  },
  {
    id: "ram-bagh",
    name: "Ram Bagh (Aram Bagh)",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Historical"],
    art: "ruins",
    palette: "mint",
  },
  {
    id: "itimad-ud-daulah",
    name: "Tomb of Itimad-ud-Daulah",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Historical", "Architectural"],
    art: "shikhara",
    palette: "dusk",
  },
  {
    id: "chini-ka-rauza",
    name: "Chini ka Rauza",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Historical", "Architectural"],
    art: "shikhara",
    palette: "sage",
  },
  {
    id: "tomb-mariam-uz-zamani",
    name: "Tomb of Mariam-uz-Zamani",
    city: "Sikandra, Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Historical", "Architectural"],
    art: "shikhara",
    palette: "sand",
  },
  {
    id: "jama-masjid-agra",
    name: "Jama Masjid, Agra",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Religious", "Architectural"],
    art: "fort",
    palette: "rust",
  },
  {
    id: "guru-ka-taal",
    name: "Guru ka Taal",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Religious"],
    art: "shikhara",
    palette: "mint",
  },
  {
    id: "soami-bagh-samadhi",
    name: "Soami Bagh Samadhi",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Religious", "Architectural"],
    art: "taj",
    palette: "dusk",
  },
  {
    id: "mankameshwar-temple-agra",
    name: "Mankameshwar Temple",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Religious"],
    art: "shikhara",
    palette: "night",
  },
  {
    id: "balkeshwar-temple-agra",
    name: "Balkeshwar Temple",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Religious"],
    art: "shikhara",
    palette: "sage",
  },
  {
    id: "roman-catholic-cemetery-agra",
    name: "Roman Catholic Cemetery, Agra",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Religious", "Historical"],
    art: "ruins",
    palette: "night",
  },
  {
    id: "delhi-gate-agra",
    name: "Delhi Gate, Agra",
    city: "Agra",
    state: "Uttar Pradesh",
    unesco: false,
    tags: ["Historical", "Architectural"],
    art: "fort",
    palette: "rust",
  },
];

// Homepage "Popular destinations" — must only link to places we can serve.
// Agra opens the Taj Mahal detail; Fatehpur Sikri opens its own detail.
export const DESTINATION_HINTS = [
  { name: "Agra",           summary: "Taj Mahal and Agra Fort",      art: "taj",      palette: "dusk", monumentId: "taj-mahal" },
  { name: "Agra Fort",      summary: "Mughal citadel on the Yamuna", art: "fort",     palette: "rust", monumentId: "agra-fort" },
  { name: "Fatehpur Sikri", summary: "Akbar's ceremonial capital",   art: "fort",     palette: "sand", monumentId: "fatehpur-sikri" },
  { name: "Sikandra",       summary: "Akbar's tomb complex",         art: "shikhara", palette: "sand", monumentId: "akbar-tomb-sikandra" },
];

// Chips under the home search bar.
export const POPULAR_SEARCHES = ["Taj Mahal", "Agra Fort", "Fatehpur Sikri", "Itimad-ud-Daulah"];

export function findMonument(id) {
  return MONUMENT_CATALOG.find((m) => m.id === id);
}
