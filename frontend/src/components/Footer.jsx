import { Link } from "react-router-dom";
import Logo from "./Logo.jsx";

const LINKS = [
  { to: "/monuments", label: "Monuments" },
  { to: "/chat", label: "AI Chat" },
  { to: "/plan", label: "Plan Trip" },
  { to: "/nearby", label: "Nearby Places" },
  { to: "/dashboard", label: "Dashboard" },
];

export default function Footer() {
  return (
    <footer className="mt-16 bg-teal-900 text-white">
      <div className="container-page py-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <Logo inverted />
          <p className="mt-2 text-sm text-white/70 max-w-sm">
            Explore India's heritage with context — grounded answers and honest trip costs.
          </p>
        </div>
        <nav className="flex flex-wrap gap-5">
          {LINKS.map((l) => (
            <Link key={l.to} to={l.to} className="text-sm text-white/80 hover:text-white">
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="border-t border-white/10">
        <div className="container-page py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-white/50">
          <span>© {new Date().getFullYear()} HeritageAI · Built for learning India's heritage.</span>
          <span>Interface based on Option B template.</span>
        </div>
      </div>
    </footer>
  );
}
