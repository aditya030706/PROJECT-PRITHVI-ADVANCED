/* =============================================================
   PRITHVI LOGO MARK
   Geometric "P" with copper accent lines suggesting geological
   strata / data layers. Reusable across all PRITHVI surfaces.
============================================================= */

type PrithviLogoProps = {
  /** Rendered size in px (applied to both width and height). */
  size?: number;
  /** Fill colour for the letterform. Defaults to currentColor. */
  color?: string;
  /** Colour of the geological accent lines. */
  accentColor?: string;
  className?: string;
};

export default function PrithviLogo({
  size = 36,
  color = "currentColor",
  accentColor = "#b86f3c",
  className,
}: PrithviLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="PRITHVI"
      role="img"
      className={className}
    >
      {/* ── Letterform ─────────────────────────────────── */}

      {/* Stem — full-height vertical bar */}
      <rect x="6" y="4" width="5" height="28" fill={color} />

      {/* Bowl — top horizontal bar */}
      <rect x="6" y="4" width="20" height="4" fill={color} />

      {/* Bowl — right vertical side */}
      <rect x="22" y="4" width="4" height="16.5" fill={color} />

      {/* Bowl — bottom horizontal bar */}
      <rect x="6" y="16.5" width="20" height="4" fill={color} />

      {/* ── Geological layer accents (inside bowl) ─────── */}
      {/* These thin lines suggest geological strata / data layers */}

      <rect x="11" y="9.5"  width="11" height="1.5"  fill={accentColor} opacity="0.88" />
      <rect x="11" y="12.5" width="11" height="1"    fill={accentColor} opacity="0.58" />
      <rect x="11" y="15"   width="8"  height="0.75" fill={accentColor} opacity="0.38" />

      {/* ── Bottom detail marks ────────────────────────── */}
      {/* Trailing strata marks below the bowl */}
      <rect x="6" y="33"   width="9" height="1.5"  fill={color} opacity="0.22" />
      <rect x="6" y="34.5" width="6" height="0.75" fill={color} opacity="0.10" />
    </svg>
  );
}
