import { Link } from "react-router-dom";
import MonumentArt from "./MonumentArt.jsx";

export default function MonumentPhoto({
  image,
  art = "taj",
  palette = "dusk",
  linkTo,
  linkLabel = "Explore monument details",
  className = "",
  rounded = "rounded-2xl",
  overlay = null,
  withTrees = true,
  withHill = true,
}) {
  const positionClass = className.split(/\s+/).includes("absolute") ? "" : "relative";

  if (!image?.url) {
    return (
      <div className={`${positionClass} overflow-hidden ${rounded} ${className}`}>
        <MonumentArt
          art={art}
          palette={palette}
          rounded="rounded-none"
          className="absolute inset-0 w-full h-full"
          withTrees={withTrees}
          withHill={withHill}
          overlay={overlay}
        />
        <div className="absolute bottom-2 right-2 rounded-full bg-black/55 px-2 py-1 text-[10px] font-medium text-white">
          Photo pending
        </div>
      </div>
    );
  }

  const attribution = [image.credit, image.license].filter(Boolean).join(" · ");

  return (
    <div className={`${positionClass} overflow-hidden ${rounded} ${className}`}>
      <img
        src={image.url}
        alt={image.caption}
        loading="lazy"
        decoding="async"
        className="absolute inset-0 h-full w-full object-cover"
      />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
      {linkTo && <Link to={linkTo} aria-label={linkLabel} className="absolute inset-0 z-10" />}
      {overlay && <div className="absolute inset-0 z-20">{overlay}</div>}
      {image.source_url ? (
        <a
          href={image.source_url}
          target="_blank"
          rel="noreferrer"
          title={attribution}
          aria-label={`Photo source and license: ${attribution}`}
          className="absolute bottom-2 right-2 z-30 max-w-[85%] truncate rounded bg-black/60 px-2 py-1 text-[10px] text-white/95 backdrop-blur-sm hover:bg-black/80"
        >
          Photo: {attribution}
        </a>
      ) : (
        <span
          title={attribution}
          className="absolute bottom-2 right-2 z-30 max-w-[85%] truncate rounded bg-black/60 px-2 py-1 text-[10px] text-white/95 backdrop-blur-sm"
        >
          Photo: {attribution}
        </span>
      )}
    </div>
  );
}
