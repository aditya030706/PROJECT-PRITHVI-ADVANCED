import {
  useState,
  useRef,
} from "react";

import {
  BrowserRouter,
  Routes,
  Route,
  useNavigate,
} from "react-router-dom";

import Mines from "./pages/Mines";
import ManagerReports from "./pages/ManagerReports";
import StartInspection from "./pages/StartInspection";
import InspectionPreparation from "./pages/InspectionPreparation";
import Dashboard from "./pages/Dashboard";
import FieldInspectorHome from "./pages/FieldInspectorHome";
import InspectionPlan from "./pages/InspectionPlan";
import InspectionWorkspace from "./pages/InspectionWorkspace";
import MineDetails from "./pages/MineDetails";
import VerificationQueue from "./pages/VerificationQueue";
import VerificationReview from "./pages/VerificationReview";
import PrithviLanding from "./pages/PrithviLanding";
import EvidenceAuditChain from "./pages/EvidenceAuditChain";
import FieldAttendance from "./pages/FieldAttendance";
import AttendanceTeam from "./pages/AttendanceTeam";
import SafetyIntelligence from "./pages/SafetyIntelligence";
import ProductionGovernance from "./pages/ProductionGovernance";
import GovernanceMaster from "./pages/GovernanceMaster";
import MasterDataAdmin from "./pages/MasterDataAdmin";
import EnvironmentGovernance from "./pages/EnvironmentGovernance";
import WorkspaceSelection from "./pages/WorkspaceSelection";
import PrithviIntro from "./components/PrithviIntro";
import IntegrationPlaceholder from "./components/IntegrationPlaceholder";
import {
  RoleSwitchContext,
} from "./context/RoleSwitchContext";

import {
  AuthProvider,
  useAuth,
} from "./auth/AuthContext";

import type { UserRole } from "./auth/types";

import RoleGuard from "./auth/RoleGuard";
import RoleSwitchTransition from "./components/RoleSwitchTransition";

import InstitutionalShell from "./components/layout/InstitutionalShell";
import { LanguageProvider } from "./i18n/LanguageContext";
import "./App.css";


/* =============================================================
   ROLE → LANDING ROUTE
============================================================= */

const ROLE_HOME_ROUTES: Record<UserRole, string> = {
  FIELD_INSPECTOR: "/inspections",
  MINE_SUPERVISOR: "/supervisor",
  MINE_MANAGER: "/manager",
  CORPORATE_MANAGEMENT: "/corporate",
};




/* =============================================================
   MAIN APPLICATION LAYOUT
============================================================= */

function Layout() {
  const navigate = useNavigate();

  const {
    role: activeRole,
    setRole,
  } = useAuth();

  const role = activeRole ?? undefined;

  /*
   * Intro animation display state on initial application load.
   * Plays once per session; skips or completes cleanly to show public homepage.
   */
  const [showIntro, setShowIntro] = useState<boolean>(() => {
    try {
      return sessionStorage.getItem("prithvi_intro_seen") !== "true";
    } catch {
      return false;
    }
  });

  function handleIntroComplete() {
    try {
      sessionStorage.setItem("prithvi_intro_seen", "true");
    } catch {
      // ignore
    }
    setShowIntro(false);
  }

  /* =========================================================
     ROLE SWITCH TRANSITION STATE
  ========================================================= */

  /*
   * transitionRole: when non-null, the overlay is active for
   * this role. Cleared after navigation fires.
   */
  const [transitionRole, setTransitionRole] =
    useState<UserRole | null>(null);

  /*
   * Pending role ref: guards against rapid switching.
   * Only the last-selected role is ever navigated to.
   */
  const pendingRoleRef = useRef<UserRole | null>(null);


  /* =========================================================
     ROLE SWITCH — shared activation function
     Used by both the header dropdown and PrithviLanding.
  ========================================================= */
  function activateRoleSwitch(nextRole: UserRole) {
    // Record the pending role. If the user switches again
    // before the overlay fires, this ref wins.
    pendingRoleRef.current = nextRole;

    // Update auth context immediately so nav labels update
    // as soon as the overlay clears — no change to logic.
    setRole(nextRole);

    // Mount the overlay; it will call handleTransitionComplete
    // when done.
    setTransitionRole(nextRole);
  }


  /* =========================================================
     TRANSITION COMPLETE CALLBACK
     Called by the overlay component after its exit animation.
  ========================================================= */
  function handleTransitionComplete() {
    const nextRole = pendingRoleRef.current;
    pendingRoleRef.current = null;
    setTransitionRole(null);

    if (nextRole) {
      navigate(
        ROLE_HOME_ROUTES[nextRole],
        { replace: true }
      );
    }
  }


  return (
    <RoleSwitchContext.Provider value={{ triggerRoleSwitch: activateRoleSwitch }}>
    <>
    {showIntro && <PrithviIntro onComplete={handleIntroComplete} />}
    <div className={`app${transitionRole ? " app--role-switching" : ""}`}>


      {/* =================================================
          GOVERNMENT INSTITUTIONAL SHELL (3-Tier Header + Nav + Footer)
      ================================================= */}
      <InstitutionalShell>

      {/* =================================================
          APPLICATION ROUTES
      ================================================= */}

      <Routes>



        {/* =================================================
            SYSTEM OVERVIEW / LANDING
            Neutral entry point — no RoleGuard required.
        ================================================= */}

        <Route
          path="/"
          element={<PrithviLanding />}
        />

        <Route
          path="/landing"
          element={<PrithviLanding />}
        />

        <Route
          path="/overview"
          element={<PrithviLanding />}
        />

        <Route
          path="/workspace"
          element={<WorkspaceSelection />}
        />


        {/* =================================================
            MINE MANAGER — COMMAND CENTRE
            Dedicated home route /manager for Mine Manager.
        ================================================= */}

        <Route
          path="/manager"
          element={
            <RoleGuard
              role={role}
              permission="mine.view"
            >
              <Dashboard />
            </RoleGuard>
          }
        />

        <Route
          path="/compliance"
          element={
            <RoleGuard
              role={role}
              permission="mine.view"
            >
              <Dashboard />
            </RoleGuard>
          }
        />



        {/* =================================================
            FIELD INSPECTOR
        ================================================= */}

        <Route
          path="/inspections"
          element={
            <RoleGuard
              role={role}
              permission="inspection.view_assigned"
            >
              <FieldInspectorHome />
            </RoleGuard>
          }
        />


        <Route
          path="/inspections/plan"
          element={
            <RoleGuard
              role={role}
              permission="inspection.view_assigned"
            >
              <InspectionPlan />
            </RoleGuard>
          }
        />


        <Route
          path="/inspections/prepare/:scheduleInstanceId"
          element={
            <RoleGuard
              role={role}
              permission="inspection.create"
            >
              <InspectionPreparation />
            </RoleGuard>
          }
        />


        <Route
          path="/inspections/start/:scheduleInstanceId"
          element={
            <RoleGuard
              role={role}
              permission="inspection.create"
            >
              <StartInspection />
            </RoleGuard>
          }
        />


        <Route
          path="/inspections/:inspectionId"
          element={
            <RoleGuard
              role={role}
              permission="inspection.view_assigned"
            >
              <InspectionWorkspace />
            </RoleGuard>
          }
        />


        {/* =================================================
            MINE MANAGER
        ================================================= */}

        <Route
          path="/mines/:mineId"
          element={
            <RoleGuard
              role={role}
              permission="mine.view"
            >
              <MineDetails />
            </RoleGuard>
          }
        />


        {/* =================================================
            VERIFICATION
        ================================================= */}

        <Route
          path="/verification"
          element={
            <RoleGuard
              role={role}
              permission="verification.view"
            >
              <VerificationQueue />
            </RoleGuard>
          }
        />
        <Route
          path="/verification/:inspectionId"
          element={
            <RoleGuard
              role={role}
              permission="verification.view"
            >
              <VerificationReview />
            </RoleGuard>
          }
        />
        <Route
          path="/mines"
          element={
            <RoleGuard
              role={role}
              permission="mine.view"
            >
              <Mines />
            </RoleGuard>
          }
        />
        <Route
          path="/manager/reports"
          element={
            <RoleGuard
              role={role}
              permission="report.approve"
            >
              <ManagerReports />
            </RoleGuard>
          }
        />

        {/* =================================================
            PRODUCTION & OPERATIONAL GOVERNANCE (TASK 10)
        ================================================= */}

        <Route
          path="/production"
          element={
            <RoleGuard
              role={role}
              permission="production.view"
            >
              <ProductionGovernance />
            </RoleGuard>
          }
        />

        {/* =================================================
            FIELD INSPECTOR — STATUTORY HISTORY
        ================================================= */}

        <Route
          path="/inspections/history"
          element={
            <RoleGuard
              role={role}
              permission="inspection.history_own"
            >
              <IntegrationPlaceholder
                moduleTitle="Inspector Historical Audit Dossier"
                moduleCode="INSP-HIST-01"
                regulationRef="Coal Mines Regulations 2017 Rule 27 & Schedule V (Statutory Record Preservation)"
                description="Historical repository of all past field inspection submissions, cryptographically signed audit logs, and longitudinal defect rectification histories across allocated mining properties."
                plannedCapabilities={[
                  "Historical Dossier Search & Full-text Inspection Retrieval",
                  "Cryptographic SHA-256 Chain Verification on Historical Records",
                  "Longitudinal Non-compliance & Defect Recurrence Analytics",
                  "DGMS Audit Reference Cross-linking & Export"
                ]}
              />
            </RoleGuard>
          }
        />


        {/* =================================================
            MINE SUPERVISOR WORKSPACE ROUTES
        ================================================= */}

        <Route
          path="/supervisor"
          element={
            <RoleGuard
              role={role}
              permission="attendance.view_team"
            >
              <IntegrationPlaceholder
                moduleTitle="Mine Supervisor Shift Command"
                moduleCode="SUP-CMD-01"
                regulationRef="Mines Act 1952 Section 37 / CMR 2017 Rule 39 (Supervision & Safety Management)"
                description="Operational command centre for shift supervisors to orchestrate underground shift allocations, pre-shift gas clearing exams, and safety equipment verification."
                plannedCapabilities={[
                  "Real-time Underground Shift Muster Roll Tracking",
                  "Statutory Pre-Shift Examination (Ventilation & Methane Check)",
                  "HEMM & Face Equipment Deployment Validation",
                  "Digital Safety Handover Between Consecutive Shifts"
                ]}
              />
            </RoleGuard>
          }
        />

        <Route
          path="/supervisor/attendance"
          element={
            <RoleGuard
              role={role}
              permission="attendance.create"
            >
              <IntegrationPlaceholder
                moduleTitle="Biometric & Shift Attendance Registry"
                moduleCode="SUP-ATT-01"
                regulationRef="Mines Rules 1955 Rule 48 (Register of Persons Employed in Mine)"
                description="Statutory shift attendance ledger with automated underground muster roll generation and cap-lamp battery checkout tracking."
                plannedCapabilities={[
                  "Digital Shift Muster Roll & Underground Entry Logging",
                  "Cap-Lamp & Self-Rescuer Battery Assignment Verification",
                  "Statutory Rest Interval & Overtime Compliance Enforcer",
                  "Emergency Evacuation Rollcall Real-time Cross-check"
                ]}
              />
            </RoleGuard>
          }
        />

        <Route
          path="/supervisor/safety"
          element={
            <RoleGuard
              role={role}
              permission="safety.create"
            >
              <IntegrationPlaceholder
                moduleTitle="Shift Safety & Gas Examination Log"
                moduleCode="SUP-SAF-01"
                regulationRef="CMR 2017 Rule 113 & 129 (Pre-shift Examination of Workings)"
                description="Digital gas-clearing report and dangerous occurrence journal for statutory mining sirdars, overmen, and ventilation officers."
                plannedCapabilities={[
                  "Pre-shift Working Face Gas Clearance Logging (CH4 / CO / O2)",
                  "Roof Bolting & Support System Physical Inspection Attestation",
                  "Dangerous Occurrence & Near-miss Immediate Dispatch",
                  "Air Quantity Verification at Tailgate & Intake Splittings"
                ]}
              />
            </RoleGuard>
          }
        />

        <Route
          path="/supervisor/team"
          element={
            <RoleGuard
              role={role}
              permission="attendance.view_team"
            >
              <IntegrationPlaceholder
                moduleTitle="Workforce Competency & Machinery Allocation"
                moduleCode="SUP-TEAM-01"
                regulationRef="Mines Vocational Training Rules 1966 / CMR 2017 Chapter IV"
                description="Crew deployment matrix tracking statutory certifications, gas-testing competencies, and machinery operator licencing."
                plannedCapabilities={[
                  "Statutory Gas Testing & Sirdar Licence Validity Verification",
                  "HEMM Operator Active Duty Licencing & Medical Fitness Tracking",
                  "Contractor Workforce Induction & Mandatory Training Registry",
                  "Shift-wise Station & Working Face Allocation Engine"
                ]}
              />
            </RoleGuard>
          }
        />


        {/* =================================================
            CORPORATE MANAGEMENT ROUTES
        ================================================= */}

        <Route
          path="/corporate"
          element={
            <RoleGuard
              role={role}
              permission="corporate.view"
            >
              <IntegrationPlaceholder
                moduleTitle="Corporate Executive Command Centre"
                moduleCode="CORP-HQ-01"
                regulationRef="Ministry of Coal Strategic Governance & CIL Operational Directive"
                description="High-level holding company executive intelligence dashboard synthesizing real-time statutory compliance, production safety balance, and critical safety escalations across all 8 Coal India subsidiaries."
                plannedCapabilities={[
                  "Pan-India Multi-Subsidiary Compliance Real-time Dashboard",
                  "Production-versus-Safety Statutory Index Balance Matrix",
                  "Critical Unresolved Violation Escalation & Executive Action Tracker",
                  "Automated Weekly Executive Briefing & Cabinet Note Digest"
                ]}
                departmentBadge="MINISTRY OF COAL · CORPORATE GOVERNANCE"
              />
            </RoleGuard>
          }
        />

        <Route
          path="/corporate/subsidiaries"
          element={
            <RoleGuard
              role={role}
              permission="subsidiary.view"
            >
              <IntegrationPlaceholder
                moduleTitle="Subsidiary Performance & Governance Matrix"
                moduleCode="CORP-SUB-01"
                regulationRef="Coal India Holding Company Statutory Oversight Framework"
                description="Comparative governance matrix across BCCL, ECL, MCL, SECL, WCL, NCL, CCL, and CMPDI monitoring subsidiary board safety performance."
                plannedCapabilities={[
                  "Subsidiary-by-Subsidiary Composite Compliance Scores",
                  "Safety Capital Expenditure & Equipment Modernization Tracking",
                  "Subsidiary Managing Director Quarterly Safety Scorecard",
                  "Inter-Subsidiary Best Practice & Incident Transfer Ledger"
                ]}
                departmentBadge="MINISTRY OF COAL · CORPORATE GOVERNANCE"
              />
            </RoleGuard>
          }
        />

        <Route
          path="/corporate/mines"
          element={
            <RoleGuard
              role={role}
              permission="mine.view"
            >
              <Mines />
            </RoleGuard>
          }
        />

        <Route
          path="/corporate/risk"
          element={
            <RoleGuard
              role={role}
              permission="risk.trends"
            >
              <IntegrationPlaceholder
                moduleTitle="Enterprise Environmental & Operational Risk Monitor"
                moduleCode="CORP-RISK-01"
                regulationRef="Ministry of Environment, Forest & Climate Change / DGMS Directives"
                description="Holding company panoramic risk monitor tracking catastrophic hazard exposures, coal seam spontaneous combustion risks, and environmental clearance compliance."
                plannedCapabilities={[
                  "Enterprise Risk Heatmap across 300+ Operational Mining Leases",
                  "Continuous Environmental Clearance & Forest Land Status Monitoring",
                  "Mine Fire & Subsidence Hazard Early-Warning Radar",
                  "Loss-of-Production Business Continuity Risk Forecasting"
                ]}
                departmentBadge="MINISTRY OF COAL · CORPORATE GOVERNANCE"
              />
            </RoleGuard>
          }
        />

        <Route
          path="/corporate/trends"
          element={
            <RoleGuard
              role={role}
              permission="risk.trends"
            >
              <IntegrationPlaceholder
                moduleTitle="Strategic Longitudinal Compliance Analytics"
                moduleCode="CORP-TRND-01"
                regulationRef="NITI Aayog & Ministry of Coal National Governance Indicators"
                description="Long-term historical trend engine analyzing multi-year compliance trajectories, equipment lifecycle safety degradation, and regulatory policy shifts."
                plannedCapabilities={[
                  "5-Year Multi-Basin Statutory Violation Trend Analysis",
                  "Predictive AI Verification Confidence & Model Drift Analysis",
                  "Regulatory Rule Modification Impact Simulator",
                  "Zero-Harm National Safety Roadmap Milestone Progress Tracker"
                ]}
                departmentBadge="MINISTRY OF COAL · CORPORATE GOVERNANCE"
              />
            </RoleGuard>
          }
        />

        <Route
          path="/corporate/reports"
          element={
            <RoleGuard
              role={role}
              permission="corporate_reports.view"
            >
              <IntegrationPlaceholder
                moduleTitle="Corporate Board & Ministry Statutory Intelligence"
                moduleCode="CORP-REP-01"
                regulationRef="Companies Act 2013 / SEBI BRSR ESG Reporting Mandate"
                description="Statutory disclosure generator compiling Board Safety Committee reports, SEBI Business Responsibility & Sustainability Reporting (BRSR) metrics, and Parliamentary Standing Committee dossiers."
                plannedCapabilities={[
                  "Automated SEBI BRSR Core Mining Safety & Health Disclosures",
                  "Quarterly CIL Board of Directors Safety Performance Package",
                  "Ministry of Coal KPI & Cabinet Committee on Economic Affairs Briefings",
                  "Immutable Public Regulatory Verification Report Verification Exports"
                ]}
                departmentBadge="MINISTRY OF COAL · CORPORATE GOVERNANCE"
              />
            </RoleGuard>
          }
        />


        {/* EVIDENCE AUDIT CHAIN (Phase 2 Task 7) */}
        <Route
          path="/audit-chain/:type/:id"
          element={<EvidenceAuditChain />}
        />

        {/* GIS ATTENDANCE & FIELD OPERATIONS (Phase 2 Task 8) */}
        <Route
          path="/field"
          element={<FieldAttendance />}
        />
        <Route
          path="/attendance/team"
          element={<AttendanceTeam />}
        />
        <Route
          path="/supervisor/attendance"
          element={<AttendanceTeam />}
        />

        {/* SCADA TELEMETRY & SAFETY INTELLIGENCE (Phase 2 Task 9) */}
        <Route
          path="/safety"
          element={<SafetyIntelligence />}
        />
        <Route
          path="/supervisor/safety"
          element={<SafetyIntelligence />}
        />

        {/* PRODUCTION & OPERATIONAL GOVERNANCE (Phase 2 Task 10) */}
        <Route
          path="/production"
          element={
            <RoleGuard
              role={role}
              permission="production.view"
            >
              <ProductionGovernance />
            </RoleGuard>
          }
        />

        {/* CANONICAL GOVERNANCE MASTER & SCOPE ENGINE (Phase 2 Task 11) */}
        <Route
          path="/governance"
          element={
            <RoleGuard
              role={role}
              permission="hierarchy.view"
            >
              <GovernanceMaster />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/master-data"
          element={
            <RoleGuard
              role={role}
              permission="hierarchy.admin"
            >
              <MasterDataAdmin />
            </RoleGuard>
          }
        />

        {/* ENVIRONMENTAL GOVERNANCE & REGULATORY MONITORING (Phase 2 Task 13) */}
        <Route
          path="/environment"
          element={
            <RoleGuard
              role={role}
              permission="environment.view"
            >
              <EnvironmentGovernance />
            </RoleGuard>
          }
        />
      </Routes>
      </InstitutionalShell>

    </div>


    {/* =================================================
        ROLE SWITCH TRANSITION OVERLAY
        Mounted only while a role switch is in progress.
        Rendered outside the .app wrapper so the freeze
        class does not apply to it.
    ================================================= */}

    {transitionRole && (
      <RoleSwitchTransition
        key={transitionRole}
        role={transitionRole}
        onComplete={handleTransitionComplete}
      />
    )}

    </>
    </RoleSwitchContext.Provider>
  );
}


/* =============================================================
   APP ROOT
============================================================= */

function App() {

  return (

    <BrowserRouter>

      <AuthProvider>
        <LanguageProvider>
          <Layout />
        </LanguageProvider>
      </AuthProvider>

    </BrowserRouter>

  );

}


export default App;