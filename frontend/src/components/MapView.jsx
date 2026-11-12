import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";

// Re-create Leaflet's default marker icon without the broken image URLs that
// ship with the npm package. We draw a saffron teardrop inline instead.
function makeIcon(color = "#E37B40", label = "") {
  const svg = `
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 42'>
      <path d='M16 1 C7 1 1 8 1 16 c0 12 15 25 15 25 s15 -13 15 -25 C31 8 25 1 16 1 Z' fill='${color}' stroke='#ffffff' stroke-width='2'/>
      <circle cx='16' cy='16' r='7' fill='#ffffff'/>
      ${label ? `<text x='16' y='19.5' text-anchor='middle' font-family='DM Sans, sans-serif' font-size='10' font-weight='700' fill='${color}'>${label}</text>` : ""}
    </svg>`;
  return L.divIcon({
    html: svg,
    className: "heritage-marker",
    iconSize: [32, 42],
    iconAnchor: [16, 40],
    popupAnchor: [0, -34],
  });
}

function Recentre({ center, zoom }) {
  const map = useMap();
  useEffect(() => { if (center) map.setView(center, zoom ?? map.getZoom()); }, [center, zoom, map]);
  return null;
}

export default function MapView({
  center,
  zoom = 13,
  markers = [],
  height = 260,
  className = "",
}) {
  const safeCenter = useMemo(() => {
    if (center && Number.isFinite(center[0]) && Number.isFinite(center[1])) return center;
    if (markers[0]?.position) return markers[0].position;
    return null;
  }, [center, markers]);

  if (!safeCenter) {
    return (
      <div className={`rounded-2xl bg-cream-100 border border-cream-300 text-ink-500 text-sm grid place-items-center ${className}`} style={{ height }}>
        Map shown only when valid coordinates are available
      </div>
    );
  }

  return (
    <div className={`rounded-2xl overflow-hidden border border-cream-300 ${className}`} style={{ height }}>
      <MapContainer center={safeCenter} zoom={zoom} scrollWheelZoom={false} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Recentre center={safeCenter} zoom={zoom} />
        {markers.map((m, i) => (
          <Marker
            key={m.id || i}
            position={m.position}
            icon={makeIcon(m.color || "#E37B40", m.label || String(i + 1))}
          >
            {(m.title || m.subtitle) && (
              <Popup>
                <div className="text-xs">
                  {m.title && <div className="font-semibold text-ink-900">{m.title}</div>}
                  {m.subtitle && <div className="text-ink-500">{m.subtitle}</div>}
                </div>
              </Popup>
            )}
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
