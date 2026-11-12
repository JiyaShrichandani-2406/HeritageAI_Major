export default function Thinking({ label = "Thinking..." }) {
  return (
    <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-white border border-cream-300 text-ink-500 text-sm">
      <span className="dot-pulse"><span /><span /><span /></span>
      {label}
    </div>
  );
}
