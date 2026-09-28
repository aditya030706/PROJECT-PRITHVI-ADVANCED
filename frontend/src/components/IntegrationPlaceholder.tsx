import React from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ShieldCheck,
  CheckCircle2,
  Clock,
  FileCode,
  Layers,
  Database,
  Lock,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { ROLE_HOME_ROUTES } from "../auth/navigation";

interface IntegrationPlaceholderProps {
  moduleTitle: string;
  moduleCode: string;
  regulationRef: string;
  description: string;
  plannedCapabilities: string[];
  departmentBadge?: string;
}

export const IntegrationPlaceholder: React.FC<IntegrationPlaceholderProps> = ({
  moduleTitle,
  moduleCode,
  regulationRef,
  description,
  plannedCapabilities,
  departmentBadge = "MINISTRY OF COAL · STATUTORY SPECIFICATION",
}) => {
  const navigate = useNavigate();
  const { session } = useAuth();
  const homePath = session?.role ? ROLE_HOME_ROUTES[session.role] : "/";

  return (
    <main className="integration-module-page" role="main">
      <div className="integration-module-inner">
        { /* Navigation Breadcrumb & Back */ }
        <div className="module-top-actions">
          <button
            type="button"
            className="module-back-btn"
            onClick={() => navigate(homePath)}
          >
            <ArrowLeft size={14} />
            RETURN TO OPERATIONAL COMMAND
          </button>
          <div className="module-badge-tag">{departmentBadge}</div>
        </div>

        { /* Header Hero */ }
        <header className="module-hero-card">
          <div className="module-meta-row">
            <span className="module-code-pill">{moduleCode}</span>
            <span className="module-status-pill">
              <Clock size={12} />
              COMING SOON — INTEGRATION READY
            </span>
          </div>

          <h1 className="module-title">{moduleTitle}</h1>
          <p className="module-description">{description}</p>

          <div className="module-regulatory-banner">
            <div className="reg-icon-wrapper">
              <ShieldCheck size={18} />
            </div>
            <div className="reg-text">
              <strong>STATUTORY REGULATORY BASIS</strong>
              <span>{regulationRef}</span>
            </div>
          </div>
        </header>

        { /* Capabilities & Readiness Grid */ }
        <section className="module-specs-grid" aria-label="System Integration Specifications">
          { /* Planned Capabilities */ }
          <div className="spec-card">
            <div className="spec-card-header">
              <Layers size={16} />
              <h3>PLANNED CAPABILITIES</h3>
            </div>
            <ul className="spec-capabilities-list">
              {plannedCapabilities.map((cap, idx) => (
                <li key={idx}>
                  <CheckCircle2 size={14} className="cap-check" />
                  <span>{cap}</span>
                </li>
              ))}
            </ul>
          </div>


          { /* Architecture Readiness */ }
          <div className="spec-card">
            <div className="spec-card-header">
              <Database size={16} />
              <h3>INTEGRATION STATUS</h3>
            </div>
            <div className="readiness-items">
              <div className="readiness-row">
                <span className="readiness-label">Role-Based Authorization</span>
                <span className="readiness-value ready">
                  <Lock size={12} /> ENFORCED ({session?.role?.replaceAll("_", " ")})
                </span>
              </div>
              <div className="readiness-row">
                <span className="readiness-label">Database Schema</span>
                <span className="readiness-value ready">
                  <FileCode size={12} /> V2 COMPLIANT
                </span>
              </div>
              <div className="readiness-row">
                <span className="readiness-label">Telemetry Pipeline</span>
                <span className="readiness-value pending">
                  <Clock size={12} /> QUEUED FOR DEPLOYMENT
                </span>
              </div>
              <div className="readiness-row">
                <span className="readiness-label">Verification Integrity</span>
                <span className="readiness-value ready">
                  <ShieldCheck size={12} /> SHA-256 COMPLIANT
                </span>
              </div>
            </div>
          </div>
        </section>

        { /* Notice Footer */ }
        <footer className="module-notice-footer">
          <p>
            This module is pre-configured and schema-validated for the Smart India Hackhathon 2026
            demonstration. All active operational modules (Field Inspection Dossier, Mine Portfolio
            Registry, AI Document Intelligence, and DGMS Regulatory Command) are fully interactive.
          </p>
          <button
            type="button"
            className="module-action-primary"
            onClick={() => navigate(homePath)}
          >
            PROCEED TO ACTIVE WORKSPACE
          </button>
        </footer>
      </div>
    </main>
  );
};

export default IntegrationPlaceholder;
