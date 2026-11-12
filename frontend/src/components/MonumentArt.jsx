// Inline SVG monument illustrations in the Option B template style:
// warm glowing sun, silhouette monument, soft hill ground, cypress trees.
// No external images required — scales to any container via viewBox.

const PALETTES = {
  dusk:  { sky1:"#1b3a4d", sky2:"#2b3f49", sun:"#f0c689", moNT:"#ead9b7", ground:"#0f3b3c", tree:"#0b2a2a" },
  rust:  { sky1:"#5e1b1f", sky2:"#3a2730", sun:"#f0a860", moNT:"#c84a2a", ground:"#2a1017", tree:"#140507" },
  sage:  { sky1:"#304a3b", sky2:"#243a30", sun:"#f0c680", moNT:"#d8b36b", ground:"#1a2f24", tree:"#0b1d14" },
  sand:  { sky1:"#413323", sky2:"#2f2419", sun:"#f0bb55", moNT:"#e3c38b", ground:"#1f1812", tree:"#0b0806" },
  night: { sky1:"#0b1a2e", sky2:"#081225", sun:"#f0d088", moNT:"#9bb0bd", ground:"#060c17", tree:"#030711" },
  mint:  { sky1:"#174647", sky2:"#0f3335", sun:"#f0bb66", moNT:"#eadfc2", ground:"#0a2324", tree:"#061617" },
};

function Trees({ color }) {
  return (
    <g fill={color}>
      <ellipse cx="60"  cy="330" rx="14" ry="38" />
      <ellipse cx="86"  cy="334" rx="12" ry="34" />
      <ellipse cx="540" cy="330" rx="14" ry="38" />
      <ellipse cx="566" cy="336" rx="11" ry="30" />
    </g>
  );
}

function Sun({ color, cx = 300, cy = 160 }) {
  return (
    <g>
      <circle cx={cx} cy={cy} r="140" fill={color} opacity="0.06" />
      <circle cx={cx} cy={cy} r="100" fill={color} opacity="0.10" />
      <circle cx={cx} cy={cy} r="70"  fill={color} opacity="0.18" />
      <circle cx={cx} cy={cy} r="42"  fill={color} opacity="0.85" />
    </g>
  );
}

function Taj({ p }) {
  return (
    <g>
      <Sun color={p.sun} cx={260} cy={170} />
      {/* minarets */}
      <rect x="310" y="150" width="8" height="180" fill={p.moNT} />
      <circle cx="314" cy="148" r="8" fill={p.moNT} />
      <rect x="520" y="150" width="8" height="180" fill={p.moNT} />
      <circle cx="524" cy="148" r="8" fill={p.moNT} />
      {/* platform */}
      <rect x="330" y="280" width="190" height="55" fill={p.moNT} />
      {/* main building */}
      <rect x="360" y="215" width="130" height="80" fill={p.moNT} />
      <path d="M360 215 h130 l-10 -18 h-110 Z" fill={p.moNT} />
      {/* dome */}
      <path d="M365 195 Q425 110 485 195 Z" fill={p.moNT} />
      <rect x="422" y="110" width="6" height="18" fill={p.moNT} />
      {/* arched door */}
      <path d="M408 260 q17 -24 34 0 v24 h-34 Z" fill={p.sky2} />
    </g>
  );
}

function Fort({ p }) {
  return (
    <g>
      <Sun color={p.sun} cx={460} cy={170} />
      <rect x="110" y="235" width="420" height="100" fill={p.moNT} />
      {/* battlements */}
      {Array.from({ length: 14 }).map((_, i) => (
        <rect key={i} x={110 + i * 30} y={222} width="18" height="18" fill={p.moNT} />
      ))}
      {/* domes */}
      <circle cx="200" cy="215" r="18" fill={p.moNT} />
      <circle cx="260" cy="210" r="22" fill={p.moNT} />
      <circle cx="320" cy="215" r="18" fill={p.moNT} />
      {/* big arched gate */}
      <path d="M300 335 v-55 q20 -40 40 0 v55 Z" fill={p.sky2} />
      {/* side arches */}
      <path d="M150 335 v-30 q10 -20 20 0 v30 Z" fill={p.sky2} />
      <path d="M470 335 v-30 q10 -20 20 0 v30 Z" fill={p.sky2} />
    </g>
  );
}

function Shikhara({ p }) {
  return (
    <g>
      <Sun color={p.sun} cx={460} cy={170} />
      {/* base */}
      <rect x="220" y="275" width="200" height="60" fill={p.moNT} />
      {/* tiered spire */}
      <path d="M260 275 l60 -140 l60 140 Z" fill={p.moNT} />
      <path d="M280 275 l40 -90 l40 90 Z" fill={p.moNT} opacity="0.9" />
      {/* small side spires */}
      <path d="M220 275 l20 -50 l20 50 Z" fill={p.moNT} />
      <path d="M380 275 l20 -50 l20 50 Z" fill={p.moNT} />
      {/* door */}
      <rect x="310" y="295" width="20" height="40" fill={p.sky2} />
    </g>
  );
}

function Ruins({ p }) {
  return (
    <g>
      <Sun color={p.sun} cx={460} cy={170} />
      {/* back temple */}
      <path d="M320 280 l60 -120 l60 120 Z" fill={p.moNT} opacity="0.85" />
      {/* front pillared hall */}
      <rect x="150" y="260" width="320" height="75" fill={p.moNT} />
      {/* columns */}
      {Array.from({ length: 7 }).map((_, i) => (
        <rect key={i} x={170 + i * 46} y={200} width="12" height="60" fill={p.moNT} />
      ))}
      {/* capital line */}
      <rect x="160" y="195" width="300" height="10" fill={p.moNT} />
      {/* small shikhara on top */}
      <path d="M305 165 l15 -30 l15 30 Z" fill={p.moNT} />
    </g>
  );
}

function Minar({ p }) {
  return (
    <g>
      <Sun color={p.sun} cx={240} cy={180} />
      <rect x="150" y="300" width="400" height="35" fill={p.moNT} />
      {/* tower */}
      <path d="M400 335 l-18 -210 l36 0 Z" fill={p.moNT} />
      {/* bands */}
      <rect x="378" y="195" width="44" height="6" fill={p.sky2} />
      <rect x="380" y="235" width="40" height="6" fill={p.sky2} />
      <rect x="382" y="275" width="36" height="6" fill={p.sky2} />
      {/* small companion */}
      <path d="M480 335 l-8 -80 l16 0 Z" fill={p.moNT} />
    </g>
  );
}

const DRAWERS = {
  taj: Taj,
  fort: Fort,
  shikhara: Shikhara,
  ruins: Ruins,
  minar: Minar,
};

export default function MonumentArt({
  art = "taj",
  palette = "dusk",
  className = "",
  rounded = "rounded-2xl",
  withTrees = true,
  withHill = true,
  withStars = false,
  overlay = null,
}) {
  const p = PALETTES[palette] || PALETTES.dusk;
  const Draw = DRAWERS[art] || DRAWERS.taj;
  return (
    <div className={`relative overflow-hidden ${rounded} ${className}`}>
      <svg viewBox="0 0 600 350" preserveAspectRatio="xMidYMid slice" className="w-full h-full block">
        <defs>
          <linearGradient id={`sky-${palette}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={p.sky1} />
            <stop offset="1" stopColor={p.sky2} />
          </linearGradient>
          <radialGradient id={`floor-${palette}`} cx="50%" cy="100%" r="80%">
            <stop offset="0" stopColor={p.ground} stopOpacity="0" />
            <stop offset="1" stopColor={p.ground} />
          </radialGradient>
        </defs>
        <rect width="600" height="350" fill={`url(#sky-${palette})`} />
        {withStars && (
          <g fill="#f5efe3" opacity="0.7">
            {[[80,60],[150,40],[220,70],[460,50],[520,90],[560,40]].map(([x,y],i) => (
              <circle key={i} cx={x} cy={y} r="1.2" />
            ))}
          </g>
        )}
        {withHill && (
          <path d="M0 290 Q160 240 300 275 T 600 285 V350 H0 Z" fill={p.ground} opacity="0.85" />
        )}
        <Draw p={p} />
        {withTrees && <Trees color={p.tree} />}
        <rect y="200" width="600" height="150" fill={`url(#floor-${palette})`} opacity="0.4" />
      </svg>
      {overlay && <div className="absolute inset-0">{overlay}</div>}
    </div>
  );
}
