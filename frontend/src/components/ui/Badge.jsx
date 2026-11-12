const variants = {
  default:   "bg-cream-200 text-ink-700",
  muted:     "bg-cream-100 text-ink-500 border border-cream-300",
  teal:      "bg-teal-100 text-teal-800",
  tealSolid: "bg-teal-800 text-white",
  saffron:   "bg-saffron-100 text-saffron-700",
  gold:      "bg-gold-500 text-teal-900",
  unesco:    "bg-gold-500 text-teal-900",
  verified:  "bg-leaf-100 text-leaf-600",
  estimated: "bg-sand-100 text-sand-600",
  unknown:   "bg-cream-200 text-ink-500",
  danger:    "bg-rose-100 text-rose-600",
  demo:      "bg-gold-100 text-sand-600",
  dot:       "bg-teal-100 text-teal-800",
};

const sizes = {
  sm: "px-2.5 py-0.5 text-[10px]",
  md: "px-3 py-1 text-xs",
  lg: "px-3.5 py-1.5 text-sm",
};

export default function Badge({
  children,
  variant = "default",
  size = "md",
  className = "",
  dot = false,
  ...props
}) {
  const v = variants[variant] || variants.default;
  const s = sizes[size] || sizes.md;
  return (
    <span
      {...props}
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold tracking-wide uppercase ${v} ${s} ${className}`}
    >
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
