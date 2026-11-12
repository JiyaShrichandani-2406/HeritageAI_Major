export default function Logo({ compact = false, inverted = false, className = "" }) {
  const label = inverted ? "text-white" : "text-ink-900";
  return (
    <div className={`inline-flex items-center gap-2.5 ${className}`}>
      <span className="relative inline-flex items-center justify-center w-9 h-9 rounded-full bg-saffron-500 text-white shadow-[0_4px_12px_rgba(227,123,64,0.35)]">
        {/* small monument glyph */}
        <svg viewBox="0 0 32 32" className="w-5 h-5" fill="currentColor">
          <path d="M4 26h24v3H4z" />
          <rect x="10" y="12" width="12" height="14" rx="1" />
          <path d="M10 12 Q16 4 22 12 Z" />
          <rect x="15" y="5" width="2" height="4" />
          <rect x="6" y="14" width="2" height="12" />
          <rect x="24" y="14" width="2" height="12" />
        </svg>
      </span>
      {!compact && (
        <span className={`font-heading font-bold text-xl ${label}`}>
          Heritage<span className="text-saffron-500">AI</span>
        </span>
      )}
    </div>
  );
}
