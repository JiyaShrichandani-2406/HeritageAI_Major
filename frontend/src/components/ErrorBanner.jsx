import Button from "./ui/button.jsx";

export default function ErrorBanner({ title = "Something went wrong", message, onRetry }) {
  return (
    <div className="rounded-2xl border border-rose-100 bg-rose-100/60 p-4 text-rose-600">
      <div className="text-sm font-semibold uppercase tracking-wide">{title}</div>
      {message && <p className="mt-1 text-sm text-rose-600/90">{message}</p>}
      {onRetry && (
        <div className="mt-3">
          <Button variant="outline" size="sm" onClick={onRetry}>Retry</Button>
        </div>
      )}
    </div>
  );
}
