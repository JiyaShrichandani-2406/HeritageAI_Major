import Badge from "./ui/Badge.jsx";

export default function CostBadge({ status }) {
  const normalized = (status || "unknown").toLowerCase();
  const label =
    normalized === "verified" ? "Verified" :
    normalized === "estimated" ? "Estimated" :
    "Unknown";
  return <Badge variant={normalized} size="sm">{label}</Badge>;
}
