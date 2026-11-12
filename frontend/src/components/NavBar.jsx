import { useEffect, useState } from "react";
import { NavLink, Link, useLocation } from "react-router-dom";
import Logo from "./Logo.jsx";
import Button from "./ui/button.jsx";
import Badge from "./ui/Badge.jsx";
import { api } from "../lib/api.js";

const LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/monuments", label: "Monuments" },
  { to: "/chat", label: "AI Chat" },
  { to: "/plan", label: "Plan Trip" },
  { to: "/nearby", label: "Nearby Places" },
];

function HealthPill() {
  const [state, setState] = useState("checking"); // checking | ok | down
  useEffect(() => {
    let cancelled = false;
    api.health()
      .then(() => { if (!cancelled) setState("ok"); })
      .catch(() => { if (!cancelled) setState("down"); });
    return () => { cancelled = true; };
  }, []);
  if (state === "checking") {
    return <Badge variant="muted" size="sm" dot>Checking API</Badge>;
  }
  if (state === "down") {
    return <Badge variant="danger" size="sm" dot>API offline</Badge>;
  }
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-leaf-100 text-leaf-600 text-[11px] font-semibold tracking-wide uppercase">
      <span className="w-1.5 h-1.5 rounded-full bg-leaf-600" />
      API connected
    </span>
  );
}

export default function NavBar({ variant = "cream" }) {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  useEffect(() => { setOpen(false); }, [location.pathname]);

  const dark = variant === "dark";
  const wrap = dark
    ? "bg-transparent text-white"
    : "bg-white/90 backdrop-blur border-b border-cream-300";
  const linkBase = dark
    ? "text-white/85 hover:text-white"
    : "text-ink-700 hover:text-ink-900";
  const activeCls = dark
    ? "text-white after:bg-saffron-500"
    : "text-ink-900 after:bg-saffron-500";

  return (
    <header className={`sticky top-0 z-40 ${wrap}`}>
      <div className="container-page flex items-center justify-between h-16">
        <Link to="/" className="shrink-0">
          <Logo inverted={dark} />
        </Link>

        <nav className="hidden md:flex items-center gap-7">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                `relative text-sm font-medium transition pb-1 after:content-[''] after:absolute after:left-0 after:right-0 after:-bottom-0.5 after:h-[2px] after:rounded-full ${linkBase} ${isActive ? activeCls : "after:bg-transparent"}`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <HealthPill />
          {location.pathname === "/" ? (
            <Button as={Link} to="/dashboard">Start Exploring</Button>
          ) : (
            <div className="w-9 h-9 rounded-full bg-teal-800 text-white font-semibold grid place-items-center">G</div>
          )}
        </div>

        <button
          type="button"
          className={`md:hidden inline-flex items-center justify-center w-10 h-10 rounded-full border ${dark ? "border-white/20 text-white" : "border-cream-300 text-ink-700 bg-white"}`}
          aria-label="Open navigation"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {open ? (
              <>
                <path d="M6 6l12 12" />
                <path d="M18 6L6 18" />
              </>
            ) : (
              <>
                <path d="M4 7h16" />
                <path d="M4 12h16" />
                <path d="M4 17h16" />
              </>
            )}
          </svg>
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-cream-300 bg-white">
          <div className="container-page py-3 flex flex-col gap-1">
            {LINKS.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  `block rounded-xl px-3 py-2.5 text-sm font-medium ${isActive ? "bg-cream-100 text-ink-900" : "text-ink-700 hover:bg-cream-100"}`
                }
              >
                {l.label}
              </NavLink>
            ))}
            <div className="flex items-center justify-between pt-2 border-t border-cream-300 mt-2">
              <HealthPill />
              <Button as={Link} to="/dashboard" size="sm">Start Exploring</Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
