const base =
  "inline-flex items-center justify-center gap-2 font-semibold rounded-button transition-all duration-150 " +
  "disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer select-none " +
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-saffron-500 focus-visible:ring-offset-2 focus-visible:ring-offset-cream-100";

const variants = {
  primary: "bg-saffron-500 text-white hover:bg-saffron-600 shadow-[0_6px_18px_rgba(227,123,64,0.35)]",
  teal: "bg-teal-800 text-white hover:bg-teal-700",
  outline: "bg-transparent border border-teal-800 text-teal-900 hover:bg-teal-50",
  ghost: "bg-white/60 border border-cream-300 text-teal-900 hover:bg-white",
  darkGhost: "bg-white/5 border border-white/15 text-white hover:bg-white/10",
  link: "text-saffron-600 hover:text-saffron-700 underline-offset-4 hover:underline",
};

const sizes = {
  sm: "px-3.5 py-1.5 text-sm",
  md: "px-5 py-2.5 text-sm",
  lg: "px-6 py-3 text-base",
};

export default function Button({
  as: As = "button",
  variant = "primary",
  size = "md",
  className = "",
  type,
  children,
  ...props
}) {
  const v = variants[variant] || variants.primary;
  const s = sizes[size] || sizes.md;
  const extra = As === "button" ? { type: type || "button" } : {};
  return (
    <As {...extra} {...props} className={`${base} ${v} ${s} ${className}`.trim()}>
      {children}
    </As>
  );
}
