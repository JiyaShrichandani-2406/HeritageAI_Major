export default function Input({
  label,
  hint,
  error,
  required,
  prefix,
  suffix,
  className = "",
  containerClassName = "",
  ...props
}) {
  return (
    <div className={`w-full ${containerClassName}`}>
      {label && (
        <label className="block mb-1.5 text-xs font-semibold tracking-wide text-ink-500 uppercase">
          {label} {required && <span className="text-saffron-600">*</span>}
        </label>
      )}
      <div
        className={`flex items-center gap-2 rounded-field border border-cream-300 bg-white px-3.5 py-2.5 focus-within:border-saffron-500 focus-within:shadow-[0_0_0_4px_rgba(227,123,64,0.12)] transition ${
          error ? "border-rose-600" : ""
        }`}
      >
        {prefix && <span className="text-ink-400">{prefix}</span>}
        <input
          {...props}
          className={`flex-1 bg-transparent outline-none placeholder:text-ink-400 text-ink-900 ${className}`}
        />
        {suffix && <span className="text-ink-400 text-sm">{suffix}</span>}
      </div>
      {error ? (
        <p className="mt-1 text-xs text-rose-600">{error}</p>
      ) : hint ? (
        <p className="mt-1 text-xs text-ink-400">{hint}</p>
      ) : null}
    </div>
  );
}
