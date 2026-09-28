import React from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ClipboardList,
  Users,
  Building2,
  Briefcase,
  Shield,
  Layers,
  Home,
  CheckCircle2,
  Lock,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useRoleSwitch } from "../context/RoleSwitchContext";
import { useLanguage } from "../i18n/LanguageContext";
import type { UserRole } from "../auth/types";

interface RoleCardConfig {
  role: UserRole;
  titleKey: string;
  defaultTitle: string;
  badge: string;
  badgeColor: string;
  icon: React.ReactNode;
  summary: string;
  scope: string;
  responsibilities: string[];
}

export default function WorkspaceSelection() {
  const { session } = useAuth();
  const { triggerRoleSwitch } = useRoleSwitch();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const roleConfigs: RoleCardConfig[] = [
    {
      role: "FIELD_INSPECTOR",
      titleKey: "roles.field_inspector",
      defaultTitle: "FIELD INSPECTOR",
      badge: "ON-SITE INSPECTION",
      badgeColor: "#92400e",
      icon: <ClipboardList size={28} className="text-amber-700" />,
      summary: "Conduct on-site inspections, capture physical measurements, record findings, and verify safety evidence.",
      scope: "Assigned Mine Districts, Shafts, Working Faces",
      responsibilities: [
        "GPS-verified biometric field attendance",
        "Statutory checklist inspection execution",
        "SHA-256 tamper-evident evidence capture",
        "Direct observation and finding logging",
      ],
    },
    {
      role: "MINE_SUPERVISOR",
      titleKey: "roles.mine_supervisor",
      defaultTitle: "MINE SUPERVISOR",
      badge: "SHIFT OPERATIONS",
      badgeColor: "#0369a1",
      icon: <Users size={28} className="text-sky-700" />,
      summary: "Direct shift supervision, workforce attendance roster, HEMM operations, and frontline safety protocols.",
      scope: "Operational Units, Pits, Haul Roads, Ventilation Districts",
      responsibilities: [
        "Shift workforce and roster monitoring",
        "Active HEMM equipment & park tracking",
        "Frontline safety hazard observations",
        "Daily shift operational logs",
      ],
    },
    {
      role: "MINE_MANAGER",
      titleKey: "roles.mine_manager",
      defaultTitle: "MINE MANAGER",
      badge: "MINE COMMAND",
      badgeColor: "#15803d",
      icon: <Building2 size={28} className="text-emerald-700" />,
      summary: "Overall statutory command, compliance monitoring, verification review, environmental oversight, and management reporting.",
      scope: "Single Mine Entity (e.g., Jharia Underground / Talcher Opencast)",
      responsibilities: [
        "Mine-wide compliance score & live posture",
        "Two-person integrity verification queue",
        "Environmental limits & air/water monitoring",
        "Corrective action verification & sign-off",
      ],
    },
    {
      role: "CORPORATE_MANAGEMENT",
      titleKey: "roles.corporate_management",
      defaultTitle: "CORPORATE MANAGEMENT",
      badge: "ENTERPRISE INTELLIGENCE",
      badgeColor: "#4338ca",
      icon: <Briefcase size={28} className="text-indigo-700" />,
      summary: "CIL & Subsidiary executive oversight, enterprise ESG metrics, master data governance, and strategic resource allocation.",
      scope: "Enterprise-wide (Coal India & Subsidiaries: BCCL, ECL, SECL, MCL)",
      responsibilities: [
        "Multi-subsidiary comparative compliance index",
        "Canonical organizational hierarchy administration",
        "Enterprise ESG & contractor governance",
        "Corporate executive compliance reporting",
      ],
    },
  ];

  const handleSelectRole = (role: UserRole) => {
    triggerRoleSwitch(role);
  };

  return (
    <div className="gov-workspace-page" style={{ minHeight: "85vh", backgroundColor: "#fbfaf8", padding: "40px 20px" }}>
      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        
        {/* Top Breadcrumb / Return Link */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "28px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", color: "#64748b" }}>
            <Link to="/" style={{ color: "#8B1E0F", textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: "4px" }}>
              <Home size={14} /> Public Portal
            </Link>
            <span>/</span>
            <span style={{ color: "#334155", fontWeight: 500 }}>Workspace Gate</span>
          </div>

          <Link
            to="/governance"
            style={{
              fontSize: "12px",
              fontFamily: "DM Mono, monospace",
              color: "#8B1E0F",
              textDecoration: "none",
              border: "1px solid #fed7aa",
              padding: "6px 14px",
              borderRadius: "4px",
              backgroundColor: "#fff7ed",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontWeight: 600,
            }}
          >
            <Layers size={13} />
            Explore Governance Hierarchy →
          </Link>
        </div>

        {/* Header Block */}
        <div
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderLeft: "6px solid #8B1E0F",
            borderRadius: "6px",
            padding: "28px 32px",
            marginBottom: "32px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <Shield size={16} style={{ color: "#8B1E0F" }} />
            <span
              style={{
                fontFamily: "DM Mono, monospace",
                fontSize: "12px",
                letterSpacing: "0.1em",
                color: "#8B1E0F",
                fontWeight: 700,
                textTransform: "uppercase",
              }}
            >
              Role Authorization Gate
            </span>
          </div>

          <h1
            style={{
              fontSize: "28px",
              fontWeight: 800,
              color: "#0f172a",
              letterSpacing: "-0.02em",
              margin: "0 0 10px 0",
            }}
          >
            CHOOSE YOUR PRITHVI WORKSPACE
          </h1>

          <p
            style={{
              fontSize: "15px",
              color: "#475569",
              maxWidth: "840px",
              margin: 0,
              lineHeight: 1.6,
            }}
          >
            Select the authorized role through which you will access the PRITHVI compliance intelligence platform.
            Navigation capabilities, operational oversight tools, and verification controls are strictly scoped to your authorized role and organizational unit.
          </p>
        </div>

        {/* Current Role Banner (if any) */}
        {session && session.role && (
          <div
            style={{
              background: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: "6px",
              padding: "14px 20px",
              marginBottom: "28px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <CheckCircle2 size={18} style={{ color: "#16a34a" }} />
              <span style={{ fontSize: "14px", color: "#166534" }}>
                Active Session: <strong>{session.role.replace(/_/g, " ")}</strong> ({session.name})
              </span>
            </div>
            <button
              onClick={() => {
                const home = session.role === "FIELD_INSPECTOR" ? "/inspections" :
                             session.role === "MINE_SUPERVISOR" ? "/supervisor" :
                             session.role === "MINE_MANAGER" ? "/manager" : "/corporate";
                navigate(home);
              }}
              style={{
                fontSize: "13px",
                background: "#16a34a",
                color: "#ffffff",
                border: "none",
                borderRadius: "4px",
                padding: "6px 14px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Continue to Active Workspace →
            </button>
          </div>
        )}

        {/* 5-Column Role Selection Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "24px",
          }}
        >
          {roleConfigs.map((cfg) => {
            const isCurrent = session?.role === cfg.role;
            return (
              <div
                key={cfg.role}
                style={{
                  background: "#ffffff",
                  border: isCurrent ? "2px solid #8B1E0F" : "1px solid #e2e8f0",
                  borderRadius: "8px",
                  padding: "24px",
                  display: "flex",
                  flexDirection: "column",
                  boxShadow: isCurrent ? "0 4px 12px rgba(139, 30, 15, 0.1)" : "0 1px 3px rgba(0,0,0,0.05)",
                  transition: "transform 0.15s ease, box-shadow 0.15s ease",
                  position: "relative",
                }}
              >
                {/* Badge Row */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                  <div
                    style={{
                      width: "48px",
                      height: "48px",
                      borderRadius: "8px",
                      background: "#f8fafc",
                      border: "1px solid #e2e8f0",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {cfg.icon}
                  </div>

                  <span
                    style={{
                      fontFamily: "DM Mono, monospace",
                      fontSize: "11px",
                      fontWeight: 700,
                      letterSpacing: "0.08em",
                      color: cfg.badgeColor,
                      background: `${cfg.badgeColor}12`,
                      padding: "4px 10px",
                      borderRadius: "4px",
                      border: `1px solid ${cfg.badgeColor}25`,
                    }}
                  >
                    {cfg.badge}
                  </span>
                </div>

                {/* Role Title */}
                <h2
                  style={{
                    fontSize: "18px",
                    fontWeight: 700,
                    color: "#0f172a",
                    letterSpacing: "0.02em",
                    margin: "0 0 8px 0",
                  }}
                >
                  {t(cfg.titleKey, cfg.defaultTitle)}
                </h2>

                {/* Summary */}
                <p
                  style={{
                    fontSize: "13px",
                    color: "#475569",
                    lineHeight: 1.5,
                    margin: "0 0 16px 0",
                    flexGrow: 1,
                  }}
                >
                  {cfg.summary}
                </p>

                {/* Scope pill */}
                <div
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #f1f5f9",
                    borderRadius: "4px",
                    padding: "8px 12px",
                    marginBottom: "16px",
                  }}
                >
                  <span style={{ fontSize: "11px", fontFamily: "DM Mono, monospace", color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: "2px" }}>
                    Operational Scope:
                  </span>
                  <span style={{ fontSize: "12px", color: "#1e293b", fontWeight: 600 }}>
                    {cfg.scope}
                  </span>
                </div>

                {/* Core Responsibilities */}
                <div style={{ marginBottom: "20px" }}>
                  <span style={{ fontSize: "11px", fontFamily: "DM Mono, monospace", color: "#64748b", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>
                    Authorized Capabilities:
                  </span>
                  <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "12px", color: "#334155", lineHeight: 1.6 }}>
                    {cfg.responsibilities.map((r, idx) => (
                      <li key={idx} style={{ marginBottom: "4px" }}>{r}</li>
                    ))}
                  </ul>
                </div>

                {/* Enter Action Button */}
                <button
                  type="button"
                  onClick={() => handleSelectRole(cfg.role)}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                    padding: "12px 16px",
                    background: isCurrent ? "#8B1E0F" : "#0f172a",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    fontWeight: 700,
                    fontSize: "13px",
                    letterSpacing: "0.04em",
                    cursor: "pointer",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    transition: "background 0.15s ease",
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.background = "#8B1E0F";
                  }}
                  onMouseOut={(e) => {
                    if (!isCurrent) e.currentTarget.style.background = "#0f172a";
                  }}
                >
                  <span>{isCurrent ? "ACTIVE WORKSPACE →" : "ENTER WORKSPACE →"}</span>
                </button>
              </div>
            );
          })}
        </div>

        {/* Security / Notice Footer */}
        <div
          style={{
            marginTop: "36px",
            padding: "16px 20px",
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "6px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontSize: "13px",
            color: "#64748b",
          }}
        >
          <Lock size={16} style={{ color: "#8B1E0F", flexShrink: 0 }} />
          <span>
            <strong>Statutory Notice:</strong> PRITHVI role workspaces enforce strict server-side RBAC and organizational unit hierarchy checks. Unverified actions and cross-mine inspections are logged to the immutable audit ledger.
          </span>
        </div>
      </div>
    </div>
  );
}
