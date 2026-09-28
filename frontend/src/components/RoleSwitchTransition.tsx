import { useEffect, useRef, useState } from "react";
import type { UserRole } from "../auth/types";

/* =============================================================
   ROLE-SPECIFIC CONTENT
   All strings defined here in one place — no logic change elsewhere.
============================================================= */

type RoleContent = {
  label: string;
  primaryMessage: string;
  description: string;
  statusLine: string;
};

const ROLE_CONTENT: Record<UserRole, RoleContent> = {
  FIELD_INSPECTOR: {
    label: "FIELD INSPECTOR",
    primaryMessage: "Field Operations Active",
    description:
      "Accessing assigned inspections, field measurements, safety checklists, evidence capture, and inspection history.",
    statusLine: "Preparing your field inspection workspace...",
  },
  MINE_SUPERVISOR: {
    label: "MINE SUPERVISOR",
    primaryMessage: "Operational Oversight Active",
    description:
      "Accessing workforce attendance, safety observations, team activity, and operational controls.",
    statusLine: "Preparing your operational oversight workspace...",
  },
  MINE_MANAGER: {
    label: "MINE MANAGER",
    primaryMessage: "Mine Command Active",
    description:
      "Accessing mine compliance, inspection status, verification, corrective actions, reporting, and management controls.",
    statusLine: "Preparing your mine command environment...",
  },
  CORPORATE_MANAGEMENT: {
    label: "CORPORATE MANAGEMENT",
    primaryMessage: "Enterprise Intelligence Active",
    description:
      "Accessing subsidiary performance, mine-wide risk trends, predictive alerts, resource allocation, and corporate reporting.",
    statusLine: "Preparing your enterprise intelligence workspace...",
  },
};


/* =============================================================
   PHASE TIMING (ms)
   These constants define the cascade of CSS animation delays
   and the JS timer that fires onComplete.
============================================================= */

const PHASE_BRAND       = 80;   // brand block appears
const PHASE_ROLE        = 280;  // role label appears
const PHASE_MESSAGE     = 450;  // primary message appears
const PHASE_DESCRIPTION = 580;  // description appears
const PHASE_STATUS      = 710;  // status line appears
const PHASE_SCAN        = 200;  // scanning line starts
const PHASE_COMPLETE    = 1050; // triggers exit animation
const PHASE_NAVIGATE    = 1320; // fires onComplete → navigate


/* =============================================================
   PROPS
============================================================= */

type Props = {
  role: UserRole;
  onComplete: () => void;
};


/* =============================================================
   COMPONENT
============================================================= */

export default function RoleSwitchTransition({ role, onComplete }: Props) {

  const content = ROLE_CONTENT[role];

  /* Track whether the exit animation is active */
  const [exiting, setExiting] = useState(false);

  /*
   * Stable ref for the onComplete callback — prevents stale
   * closures if the parent happens to re-render during the
   * transition without remounting the overlay.
   */
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    const exitTimer = window.setTimeout(() => {
      setExiting(true);
    }, PHASE_COMPLETE);

    const navigateTimer = window.setTimeout(() => {
      onCompleteRef.current();
    }, PHASE_NAVIGATE);

    return () => {
      window.clearTimeout(exitTimer);
      window.clearTimeout(navigateTimer);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  // Intentionally empty deps — fires exactly once per mount.
  // role/onComplete captured via ref above.


  return (
    <div
      className={`rst-overlay${exiting ? " rst-overlay--exiting" : ""}`}
      aria-live="assertive"
      aria-label={`Switching to ${content.label} operational context`}
      role="status"
    >

      {/* ── Subtle background grid ─────────────────────── */}
      <div className="rst-grid" aria-hidden="true" />

      {/* ── Architectural scanning line ────────────────── */}
      <div
        className="rst-scan-line"
        aria-hidden="true"
        style={{ animationDelay: `${PHASE_SCAN}ms` }}
      />

      {/* ── Content centred block ─────────────────────── */}
      <div className="rst-content">

        {/* ── Brand block ─────────────────────────────── */}
        <div
          className="rst-brand rst-reveal"
          style={{ animationDelay: `${PHASE_BRAND}ms` }}
        >
          <span className="rst-brand-name">PRITHVI</span>
          <span className="rst-brand-sub">COMPLIANCE INTELLIGENCE PLATFORM</span>
        </div>

        {/* ── Thin architectural rule ──────────────────── */}
        <div
          className="rst-rule rst-rule-anim"
          style={{ animationDelay: `${PHASE_BRAND + 60}ms` }}
          aria-hidden="true"
        />

        {/* ── Role context marker ──────────────────────── */}
        <div
          className="rst-context-marker rst-reveal"
          style={{ animationDelay: `${PHASE_ROLE - 50}ms` }}
          aria-hidden="true"
        >
          ROLE CONTEXT
        </div>

        {/* ── Role label — strongest visual element ───── */}
        <h1
          className="rst-role-label rst-reveal"
          style={{ animationDelay: `${PHASE_ROLE}ms` }}
        >
          {content.label}
        </h1>

        {/* ── Primary message ─────────────────────────── */}
        <p
          className="rst-primary-message rst-reveal"
          style={{ animationDelay: `${PHASE_MESSAGE}ms` }}
        >
          {content.primaryMessage}
        </p>

        {/* ── Description ─────────────────────────────── */}
        <p
          className="rst-description rst-reveal"
          style={{ animationDelay: `${PHASE_DESCRIPTION}ms` }}
        >
          {content.description}
        </p>

        {/* ── Transition progress line ─────────────────── */}
        <div
          className="rst-progress rst-reveal"
          aria-hidden="true"
          style={{ animationDelay: `${PHASE_STATUS - 70}ms` }}
        >
          <div className="rst-progress-fill" />
        </div>

        {/* ── Status line ─────────────────────────────── */}
        <p
          className="rst-status-line rst-reveal"
          style={{ animationDelay: `${PHASE_STATUS}ms` }}
        >
          {content.statusLine}
        </p>

      </div>

    </div>
  );
}
