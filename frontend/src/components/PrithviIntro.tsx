import { useEffect, useState } from "react";
import PrithviLogo from "./PrithviLogo";

/* =============================================================
   PRITHVI SYSTEM INTRO
   Cinematic initialization sequence.
   Duration ≈ 2.7 s.  Click to skip.
============================================================= */

type Phase =
  | "init"      // 0 ms      dark screen, init bar draws
  | "logo"      // 300 ms    logo appears
  | "identity"  // 850 ms    PROJECT PRITHVI text
  | "context"   // 1 250 ms  SIH / Ministry context
  | "scan"      // 1 700 ms  scan line + SYSTEM ONLINE
  | "exit";     // 2 250 ms  fade-out

export default function PrithviIntro({
  onComplete,
}: {
  onComplete: () => void;
}) {
  const [phase, setPhase] = useState<Phase>("init");

  useEffect(() => {
    const schedule: [Phase, number][] = [
      ["logo",     300],
      ["identity", 850],
      ["context",  1250],
      ["scan",     1700],
      ["exit",     2250],
    ];

    const timers = schedule.map(([p, delay]) =>
      window.setTimeout(() => setPhase(p), delay)
    );
    const done = window.setTimeout(onComplete, 2700);

    return () => {
      timers.forEach(clearTimeout);
      clearTimeout(done);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function skip() {
    setPhase("exit");
    window.setTimeout(onComplete, 380);
  }

  /* Derived visibility flags */
  const logoV    = phase !== "init";
  const identV   = phase === "identity" || phase === "context" || phase === "scan";
  const contextV = phase === "context"  || phase === "scan";
  const scanV    = phase === "scan";
  const isExit   = phase === "exit";

  return (
    <div
      className="pi-root"
      style={{
        opacity: isExit ? 0 : 1,
        pointerEvents: isExit ? "none" : "auto",
        transition: isExit ? "opacity 420ms ease" : "none",
      }}
      onClick={skip}
      aria-live="assertive"
      role="status"
      aria-label="PRITHVI system initializing"
    >
      <style>{PI_STYLES}</style>

      {/* Subtle grid */}
      <div className="pi-grid" aria-hidden="true" />

      {/* Corner bracket marks */}
      <div className="pi-corners" aria-hidden="true">
        <span className="pi-c pi-c-tl" />
        <span className="pi-c pi-c-tr" />
        <span className="pi-c pi-c-bl" />
        <span className="pi-c pi-c-br" />
      </div>

      {/* Phase-01: init bar */}
      <div
        className={`pi-init-bar${phase === "init" ? " pi-bar-grow" : " pi-bar-done"}`}
        aria-hidden="true"
      />

      {/* Phase-01: INITIALIZING label */}
      <div
        className="pi-init-label"
        style={{ opacity: phase === "init" ? 1 : 0, transition: "opacity 300ms ease" }}
        aria-hidden="true"
      >
        <span className="pi-init-dot" />
        INITIALIZING
      </div>

      {/* ── CENTRAL CONTENT ───────────────────────────── */}
      <div
        className="pi-center"
        style={
          isExit
            ? { opacity: 0, transform: "translateY(-14px)", transition: "opacity 350ms ease, transform 350ms ease" }
            : {}
        }
      >

        {/* Phase-02: Logo mark */}
        <div
          className="pi-logo-mark"
          style={{
            opacity:   logoV ? 1 : 0,
            transform: logoV ? "scale(1)" : "scale(0.84)",
            transition: "opacity 520ms ease, transform 520ms cubic-bezier(0.22, 0.61, 0.36, 1)",
          }}
          aria-hidden="true"
        >
          <PrithviLogo size={68} color="#f3efe6" accentColor="#b86f3c" />
        </div>

        {/* Phase-03: Identity text */}
        <div
          className="pi-identity"
          style={{
            opacity:   identV ? 1 : 0,
            transform: identV ? "translateY(0)" : "translateY(10px)",
            transition: "opacity 420ms 60ms ease, transform 420ms 60ms cubic-bezier(0.22, 0.61, 0.36, 1)",
          }}
        >
          <div className="pi-ident-rule" aria-hidden="true" />
          <div className="pi-project-label">PROJECT</div>
          <div className="pi-brand-name">PRITHVI</div>
          <div className="pi-brand-subtitle">MINE COMPLIANCE INTELLIGENCE</div>
        </div>

        {/* Phase-04: SIH context */}
        <div
          className="pi-context"
          style={{
            opacity:   contextV ? 1 : 0,
            transform: contextV ? "translateY(0)" : "translateY(8px)",
            transition: "opacity 380ms ease, transform 380ms cubic-bezier(0.22, 0.61, 0.36, 1)",
          }}
        >
          <div className="pi-ctx-rule" aria-hidden="true" />
          <div className="pi-ctx-row">
            <span>SMART INDIA HACKATHON 2026</span>
            <span className="pi-ctx-sep" aria-hidden="true">·</span>
            <span>SIH26024</span>
            <span className="pi-ctx-sep" aria-hidden="true">·</span>
            <span>MINISTRY OF COAL</span>
          </div>
          <div className="pi-ctx-sub">
            AI-BASED SMART GOVERNANCE AND COMPLIANCE MONITORING SYSTEM FOR COAL MINES
          </div>
        </div>

      </div>

      {/* Phase-05: Horizontal scan line */}
      {scanV && (
        <div className="pi-scan-line" aria-hidden="true" />
      )}

      {/* Phase-05: SYSTEM ONLINE badge */}
      <div
        className="pi-online"
        style={{ opacity: scanV ? 1 : 0, transition: "opacity 400ms 200ms ease" }}
        aria-hidden="true"
      >
        <span className="pi-online-dot" />
        SYSTEM ONLINE
      </div>

      {/* Skip hint */}
      <div className="pi-skip-hint" aria-hidden="true">
        CLICK ANYWHERE TO SKIP
      </div>
    </div>
  );
}


/* =============================================================
   INTRO STYLES
   All scoped under .pi- prefix.  Inline to avoid any
   CSS architecture collision.
============================================================= */

const PI_STYLES = `

.pi-root {
  position: fixed;
  inset: 0;
  background: #0b0e10;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  cursor: pointer;
  user-select: none;
}

/* Subtle background grid */
.pi-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.016) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.016) 1px, transparent 1px);
  background-size: 56px 56px;
  pointer-events: none;
}

/* Corner L-bracket marks */
.pi-corners { position: absolute; inset: 0; pointer-events: none; }
.pi-c {
  position: absolute;
  width: 18px;
  height: 18px;
  border-color: rgba(184, 111, 60, 0.35);
  border-style: solid;
}
.pi-c-tl { top: 28px;    left: 28px;  border-width: 1.5px 0 0 1.5px; }
.pi-c-tr { top: 28px;    right: 28px; border-width: 1.5px 1.5px 0 0; }
.pi-c-bl { bottom: 28px; left: 28px;  border-width: 0 0 1.5px 1.5px; }
.pi-c-br { bottom: 28px; right: 28px; border-width: 0 1.5px 1.5px 0; }

/* Phase-01: growing horizontal init bar */
.pi-init-bar {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, 90px);
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(184, 111, 60, 0.5),
    transparent
  );
  width: 0;
  transition: width 680ms cubic-bezier(0.4, 0, 0.2, 1);
}
.pi-init-bar.pi-bar-grow { width: 200px; }
.pi-init-bar.pi-bar-done {
  width: 300px;
  opacity: 0;
  transition: width 200ms ease, opacity 250ms ease;
}

/* Phase-01: INITIALIZING label */
.pi-init-label {
  position: absolute;
  bottom: 96px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 9px;
  font-family: "DM Mono", "Courier New", monospace;
  font-size: 9px;
  font-weight: 400;
  letter-spacing: 0.22em;
  color: rgba(243, 239, 230, 0.28);
  white-space: nowrap;
  pointer-events: none;
}
.pi-init-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(184, 111, 60, 0.55);
  animation: pi-pulse 1100ms ease-in-out infinite;
}

@keyframes pi-pulse {
  0%, 100% { opacity: 0.3; }
  50%       { opacity: 1;   }
}

/* Central content stack */
.pi-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  text-align: center;
}

/* Logo mark */
.pi-logo-mark {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Identity block */
.pi-identity {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.pi-ident-rule {
  width: 42px;
  height: 1px;
  background: rgba(184, 111, 60, 0.45);
  margin-bottom: 8px;
}

.pi-project-label {
  font-family: "DM Mono", "Courier New", monospace;
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 0.26em;
  color: rgba(184, 111, 60, 0.65);
}

.pi-brand-name {
  font-family: "DM Sans", Arial, sans-serif;
  font-size: 46px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #f3efe6;
  line-height: 1;
}

.pi-brand-subtitle {
  font-family: "DM Mono", "Courier New", monospace;
  font-size: 9px;
  font-weight: 400;
  letter-spacing: 0.2em;
  color: rgba(243, 239, 230, 0.38);
}

/* SIH context block */
.pi-context {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.pi-ctx-rule {
  width: 260px;
  height: 1px;
  background: rgba(255, 255, 255, 0.07);
  margin-bottom: 4px;
}

.pi-ctx-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
  font-family: "DM Mono", "Courier New", monospace;
  font-size: 8.5px;
  font-weight: 400;
  letter-spacing: 0.18em;
  color: rgba(243, 239, 230, 0.32);
}

.pi-ctx-sep {
  color: rgba(184, 111, 60, 0.35);
}

.pi-ctx-sub {
  font-family: "DM Mono", "Courier New", monospace;
  font-size: 7.5px;
  font-weight: 400;
  letter-spacing: 0.12em;
  color: rgba(243, 239, 230, 0.17);
  max-width: 380px;
  line-height: 1.6;
}

/* Phase-05: Horizontal scan line */
@keyframes pi-scan {
  from { left: -4px;  opacity: 0;   }
  8%   {               opacity: 0.7; }
  85%  {               opacity: 0.4; }
  to   { left: 100%;  opacity: 0;   }
}

.pi-scan-line {
  position: absolute;
  top: 0;
  left: -4px;
  width: 3px;
  height: 100%;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(184, 111, 60, 0.55) 50%,
    transparent 100%
  );
  animation: pi-scan 780ms cubic-bezier(0.42, 0, 0.58, 1) both;
  pointer-events: none;
}

/* SYSTEM ONLINE badge */
.pi-online {
  position: absolute;
  bottom: 64px;
  right: 52px;
  display: flex;
  align-items: center;
  gap: 7px;
  font-family: "DM Mono", "Courier New", monospace;
  font-size: 9px;
  font-weight: 400;
  letter-spacing: 0.14em;
  color: rgba(95, 138, 112, 0.85);
  pointer-events: none;
}

.pi-online-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #5f8a70;
  flex-shrink: 0;
}

/* Skip hint */
.pi-skip-hint {
  position: absolute;
  bottom: 28px;
  right: 52px;
  font-family: "DM Mono", "Courier New", monospace;
  font-size: 7.5px;
  letter-spacing: 0.1em;
  color: rgba(243, 239, 230, 0.12);
  pointer-events: none;
}


/* ── REDUCED MOTION ──────────────────────────────────────── */

@media (prefers-reduced-motion: reduce) {
  .pi-init-dot  { animation: none !important; opacity: 0.55; }
  .pi-scan-line { display: none; }
  .pi-logo-mark,
  .pi-identity,
  .pi-context {
    opacity: 1   !important;
    transform: none !important;
    transition: none !important;
  }
}

`;
