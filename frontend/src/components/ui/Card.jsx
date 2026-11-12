export default function Card({
  as: As = "div",
  className = "",
  padding = "p-6",
  children,
  ...props
}) {
  return (
    <As
      {...props}
      className={`bg-white rounded-card border border-cream-300/70 shadow-[0_1px_2px_rgba(15,59,60,0.04),0_8px_24px_rgba(15,59,60,0.05)] ${padding} ${className}`}
    >
      {children}
    </As>
  );
}
