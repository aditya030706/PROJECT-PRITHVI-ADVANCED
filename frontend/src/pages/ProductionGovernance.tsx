import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Truck,
  ShieldAlert,
  FileText,
  Layers,
  Building2,
  MapPin,
  RefreshCw,
  Plus,
  Edit3,
  BarChart3,
  Lock,
  Printer,
  FileCheck,
} from "lucide-react";
import {
  getMineProductionSummary,
  getAreaProductionSummary,
  getSubsidiaryProductionSummary,
  getCorporateProductionSummary,
  getDailyProductionReport,
  createProductionRecord,
  correctProductionRecord,
  type MineProductionSummary,
  type AreaProductionSummary,
  type SubsidiaryProductionSummary,
  type CorporateProductionSummary,
  type DailyProductionReport,
} from "../api/production";
import { useAuth } from "../auth/AuthContext";

interface MineSelectorOption {
  id: string;
  name: string;
  type: "underground_coal" | "opencast_coal";
  subsidiary: string;
  areaId: string;
  areaName: string;
}

const DEMO_MINES: MineSelectorOption[] = [
  {
    id: "MINE-BCCL-JHARIA-01",
    name: "Jharia Underground Demonstration Mine",
    type: "underground_coal",
    subsidiary: "BCCL",
    areaId: "AREA-BCCL-JHARIA",
    areaName: "Jharia Coalfield Area",
  },
  {
    id: "MINE-MCL-TALCHER-01",
    name: "Talcher Opencast Demonstration Mine",
    type: "opencast_coal",
    subsidiary: "MCL",
    areaId: "AREA-MCL-TALCHER",
    areaName: "Talcher Coalfield Area",
  },
  {
    id: "MINE-ECL-RANIGANJ-01",
    name: "Raniganj Deep Underground Coal Mine",
    type: "underground_coal",
    subsidiary: "ECL",
    areaId: "AREA-ECL-RANIGANJ",
    areaName: "Raniganj Coalfield Area",
  },
];

type ViewTab = "mine" | "area" | "subsidiary" | "corporate" | "report";

export default function ProductionGovernance() {
  const { session } = useAuth();
  const userRole = session?.role || "MINE_MANAGER";

  // Navigation / Selection State
  const [activeTab, setActiveTab] = useState<ViewTab>("mine");
  const [selectedMineId, setSelectedMineId] = useState<string>("MINE-BCCL-JHARIA-01");
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Data States
  const [mineSummary, setMineSummary] = useState<MineProductionSummary | null>(null);
  const [areaSummary, setAreaSummary] = useState<AreaProductionSummary | null>(null);
  const [subsidiarySummary, setSubsidiarySummary] = useState<SubsidiaryProductionSummary | null>(null);
  const [corporateSummary, setCorporateSummary] = useState<CorporateProductionSummary | null>(null);
  const [dailyReport, setDailyReport] = useState<DailyProductionReport | null>(null);

  // Modals
  const [showLogModal, setShowLogModal] = useState<boolean>(false);
  const [showCorrectModal, setShowCorrectModal] = useState<boolean>(false);

  // Log Form State
  const currentMineConfig = DEMO_MINES.find((m) => m.id === selectedMineId) || DEMO_MINES[0];
  const [logShift, setLogShift] = useState<string>("Shift A");
  const [logQuantity, setLogQuantity] = useState<string>("");
  const [logDispatch, setLogDispatch] = useState<string>("");
  const [logSource, setLogSource] = useState<string>("WEIGHBRIDGE");
  const [logOverburden, setLogOverburden] = useState<string>("");
  const [logDistrict, setLogDistrict] = useState<string>("");
  const [logFacePanel, setLogFacePanel] = useState<string>("");
  const [logContractorType, setLogContractorType] = useState<string>("DEPARTMENTAL");
  const [logContractorName, setLogContractorName] = useState<string>("");
  const [logDowntime, setLogDowntime] = useState<string>("0");
  const [logDelayReason, setLogDelayReason] = useState<string>("");
  const [logHemmContext, setLogHemmContext] = useState<string>("");
  const [submittingLog, setSubmittingLog] = useState<boolean>(false);

  // Correction Form State
  const [correctRecordId, setCorrectRecordId] = useState<string>("");
  const [correctQty, setCorrectQty] = useState<string>("");
  const [correctDispatch, setCorrectDispatch] = useState<string>("");
  const [correctReason, setCorrectReason] = useState<string>("");
  const [submittingCorrection, setSubmittingCorrection] = useState<boolean>(false);

  // Auto-clear messages
  useEffect(() => {
    if (successMsg) {
      const timer = setTimeout(() => setSuccessMsg(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [successMsg]);

  // Data Fetching
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === "mine") {
        const data = await getMineProductionSummary(selectedMineId, selectedDate);
        setMineSummary(data);
      } else if (activeTab === "area") {
        const data = await getAreaProductionSummary(currentMineConfig.areaId, selectedDate);
        setAreaSummary(data);
      } else if (activeTab === "subsidiary") {
        const data = await getSubsidiaryProductionSummary(currentMineConfig.subsidiary, selectedDate);
        setSubsidiarySummary(data);
      } else if (activeTab === "corporate") {
        const data = await getCorporateProductionSummary(selectedDate);
        setCorporateSummary(data);
      } else if (activeTab === "report") {
        const data = await getDailyProductionReport(selectedMineId, selectedDate);
        setDailyReport(data);
      }
    } catch (err: any) {
      setError(err.message || "Failed to retrieve production data.");
    } finally {
      setLoading(false);
    }
  }, [activeTab, selectedMineId, selectedDate, currentMineConfig]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handler: Submit New Production Record
  const handleCreateRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    const qty = parseFloat(logQuantity);
    if (isNaN(qty) || qty <= 0) {
      setError("Please enter a valid positive production quantity.");
      return;
    }

    setSubmittingLog(true);
    setError(null);
    try {
      await createProductionRecord(
        {
          mine_id: selectedMineId,
          shift_name: logShift,
          production_date: selectedDate,
          production_quantity: qty,
          dispatch_quantity: logDispatch ? parseFloat(logDispatch) : undefined,
          production_source: logSource,
          operation_type:
            currentMineConfig.type === "opencast_coal"
              ? "OPENCAST_MINING"
              : "UNDERGROUND_EXTRACTION",
          overburden_quantity: logOverburden ? parseFloat(logOverburden) : undefined,
          overburden_unit: logOverburden ? "BCM" : undefined,
          district_section: logDistrict || undefined,
          face_panel: logFacePanel || undefined,
          contract_type: logContractorType,
          contractor_name: logContractorName || undefined,
          downtime_minutes: parseInt(logDowntime, 10) || 0,
          delay_reason: logDelayReason || undefined,
          hemm_context: logHemmContext || undefined,
          entered_by: session?.name || session?.role || "OPERATOR",
          simulated: true,
        },
        userRole
      );

      setSuccessMsg(`Production record for ${logShift} successfully registered with cryptographic verification hash.`);
      setShowLogModal(false);
      setLogQuantity("");
      setLogDispatch("");
      setLogOverburden("");
      setLogDelayReason("");
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create production record.");
    } finally {
      setSubmittingLog(false);
    }
  };

  // Handler: Submit Record Correction
  const handleCorrectRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    const qty = parseFloat(correctQty);
    if (isNaN(qty) || qty <= 0) {
      setError("Please enter a valid corrected quantity.");
      return;
    }
    if (!correctReason.trim()) {
      setError("A statutory explanation and audit reason is mandatory for historical corrections.");
      return;
    }

    setSubmittingCorrection(true);
    setError(null);
    try {
      await correctProductionRecord(
        correctRecordId,
        {
          corrected_quantity: qty,
          corrected_dispatch: correctDispatch ? parseFloat(correctDispatch) : undefined,
          reason: correctReason,
          corrected_by: session?.name || session?.role || "OPERATOR",
        },
        userRole
      );

      setSuccessMsg(`Record ${correctRecordId} superseded. Corrected version created with immutable audit trail.`);
      setShowCorrectModal(false);
      setCorrectRecordId("");
      setCorrectQty("");
      setCorrectDispatch("");
      setCorrectReason("");
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to submit correction.");
    } finally {
      setSubmittingCorrection(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#0F172A] font-sans pb-16">
      {/* =========================================================
          TOP INSTITUTIONAL HEADER
      ========================================================= */}
      <div className="bg-white border-b border-[#E2E8F0] shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-semibold bg-[#FDEEE9] text-[#D62F26] border border-[#F8C8BE]">
                  MINISTRY OF COAL · CIL GOVERNANCE
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-[#E0F2FE] text-[#0369A1] border border-[#BAE6FD]">
                  PHASE 2 TASK 10
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-amber-50 text-amber-800 border border-amber-200">
                  DEMO / SIMULATED DATA
                </span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] flex items-center gap-2">
                <BarChart3 className="w-7 h-7 text-[#D62F26]" />
                Production & Operational Governance Intelligence
              </h1>
              <p className="text-sm text-[#475569] mt-0.5">
                Statutory reconciliation, source-to-report hierarchy rollups, HEMM context, and SCADA safety correlation.
              </p>
            </div>

            {/* Top Right Controls: Mine Selector & Date */}
            <div className="flex flex-wrap items-center gap-2.5">
              <div className="flex items-center bg-[#F1F5F9] px-3 py-1.5 rounded-md border border-[#CBD5E1]">
                <MapPin className="w-4 h-4 text-[#64748B] mr-2" />
                <select
                  aria-label="Select Coal Mine"
                  value={selectedMineId}
                  onChange={(e) => setSelectedMineId(e.target.value)}
                  className="bg-transparent text-xs font-semibold text-[#0F172A] focus:outline-none cursor-pointer"
                >
                  {DEMO_MINES.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.subsidiary})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center bg-[#F1F5F9] px-3 py-1.5 rounded-md border border-[#CBD5E1]">
                <Clock className="w-4 h-4 text-[#64748B] mr-2" />
                <input
                  aria-label="Select Operational Date"
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="bg-transparent text-xs font-semibold text-[#0F172A] focus:outline-none cursor-pointer"
                />
              </div>

              <button
                onClick={loadData}
                disabled={loading}
                className="p-2 text-[#475569] hover:text-[#0F172A] hover:bg-[#E2E8F0] rounded-md transition-colors border border-[#CBD5E1]"
                title="Refresh Operational Data"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#D62F26]" : ""}`} />
              </button>

              {/* Action Buttons: Log Production & Correction */}
              {(userRole === "MINE_MANAGER" || userRole === "MINE_SUPERVISOR") && (
                <button
                  onClick={() => setShowLogModal(true)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#D62F26] text-white text-xs font-semibold rounded-md shadow-sm hover:bg-[#B91C1C] transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Log Production
                </button>
              )}

              {userRole === "MINE_MANAGER" && (
                <button
                  onClick={() => {
                    if (mineSummary && mineSummary.shifts.length > 0) {
                      setShowCorrectModal(true);
                    } else {
                      setError("No production records logged for this date to correct.");
                    }
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white text-[#334155] border border-[#CBD5E1] text-xs font-semibold rounded-md hover:bg-[#F8FAFC] transition-colors"
                >
                  <Edit3 className="w-3.5 h-3.5 text-[#64748B]" />
                  Correction Audit
                </button>
              )}
            </div>
          </div>

          {/* =========================================================
              NAVIGATION TABS
          ========================================================= */}
          <div className="flex border-b border-[#E2E8F0] mt-6 gap-1 sm:gap-2">
            {[
              { id: "mine", label: "Mine Operational View", icon: Layers },
              { id: "area", label: "Area Overview", icon: Building2 },
              { id: "subsidiary", label: "Subsidiary Rollup", icon: Building2 },
              { id: "corporate", label: "CIL Corporate Command", icon: TrendingUp },
              { id: "report", label: "Statutory Daily Report", icon: FileText },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as ViewTab)}
                  className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                    isActive
                      ? "border-[#D62F26] text-[#D62F26] bg-[#FFF5F5]"
                      : "border-transparent text-[#64748B] hover:text-[#0F172A] hover:border-[#CBD5E1]"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* =========================================================
          NOTIFICATIONS / MESSAGES
      ========================================================= */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-800 text-xs rounded-md p-3.5 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <span className="font-semibold">Operational Exception:</span> {error}
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-900 text-xs font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs rounded-md p-3.5 flex items-start gap-2.5">
            <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1 font-medium">{successMsg}</div>
          </div>
        )}
      </div>

      {/* =========================================================
          MAIN VIEW AREA
      ========================================================= */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        {/* TAB 1: MINE OPERATIONAL VIEW */}
        {activeTab === "mine" && mineSummary && (
          <div className="space-y-6">
            {/* Critical Operational / Safety Banner if active */}
            {mineSummary.active_safety_stoppage && (
              <div className="bg-red-50 border-l-4 border-red-600 p-4 rounded-r-md shadow-sm">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h2 className="text-xs font-bold text-red-900 uppercase tracking-wider">
                      Critical Safety Stoppage Active
                    </h2>
                    <p className="text-xs text-red-700 mt-0.5">
                      {mineSummary.safety_stoppage_notes ||
                        "Production recorded concurrently with active statutory SCADA alarms. Extraction in affected districts must undergo operational review."}
                    </p>
                    <div className="mt-2">
                      <Link
                        to="/safety"
                        className="text-xs font-semibold text-red-800 underline hover:text-red-900"
                      >
                        Inspect SCADA Telemetry Console & Cases →
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TOP METRIC CARDS (TARGET VS ACTUAL) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Production Card */}
              <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm">
                <div className="flex items-center justify-between text-xs text-[#64748B] font-medium">
                  <span>TODAY'S PRODUCTION</span>
                  <span className="font-mono text-[11px] bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">
                    TONNES
                  </span>
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-[#0F172A]">
                    {mineSummary.production_actual_tonnes.toLocaleString()} T
                  </span>
                  {mineSummary.achievement_percentage !== null &&
                  mineSummary.achievement_percentage !== undefined ? (
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        mineSummary.achievement_percentage >= 100
                          ? "bg-emerald-100 text-emerald-800"
                          : mineSummary.achievement_percentage >= 80
                          ? "bg-amber-100 text-amber-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {mineSummary.achievement_percentage}%
                    </span>
                  ) : (
                    <span className="text-xs text-[#64748B] italic">Target not configured</span>
                  )}
                </div>
                <div className="mt-2.5 pt-2.5 border-t border-[#F1F5F9] text-xs flex justify-between text-[#64748B]">
                  <span>
                    Target:{" "}
                    <strong className="text-[#334155]">
                      {mineSummary.production_target_tonnes
                        ? `${mineSummary.production_target_tonnes.toLocaleString()} T`
                        : "Target not configured"}
                    </strong>
                  </span>
                  <span>
                    Variance:{" "}
                    <strong
                      className={
                        (mineSummary.variance_tonnes || 0) >= 0
                          ? "text-emerald-600"
                          : "text-red-600"
                      }
                    >
                      {mineSummary.variance_tonnes !== null &&
                      mineSummary.variance_tonnes !== undefined
                        ? `${mineSummary.variance_tonnes > 0 ? "+" : ""}${mineSummary.variance_tonnes} T`
                        : "N/A"}
                    </strong>
                  </span>
                </div>
              </div>

              {/* Dispatch Card */}
              <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm">
                <div className="flex items-center justify-between text-xs text-[#64748B] font-medium">
                  <span>DISPATCH RECONCILIATION</span>
                  <Truck className="w-4 h-4 text-[#64748B]" />
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-[#0F172A]">
                    {mineSummary.dispatch_actual_tonnes.toLocaleString()} T
                  </span>
                  <span className="text-xs text-[#64748B]">
                    {mineSummary.dispatch_variance_tonnes !== null &&
                    mineSummary.dispatch_variance_tonnes !== undefined
                      ? `${mineSummary.dispatch_variance_tonnes > 0 ? "+" : ""}${mineSummary.dispatch_variance_tonnes} T delta`
                      : "Balanced"}
                  </span>
                </div>
                <div className="mt-2.5 pt-2.5 border-t border-[#F1F5F9] text-xs flex justify-between text-[#64748B]">
                  <span>Source Verification:</span>
                  <strong className="text-[#334155]">
                    {mineSummary.sources_used.join(", ") || "Weighbridge"}
                  </strong>
                </div>
              </div>

              {/* Overburden or Face Panel Card (Mine-type aware) */}
              <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm">
                <div className="flex items-center justify-between text-xs text-[#64748B] font-medium">
                  <span>
                    {mineSummary.mine_type === "opencast_coal"
                      ? "OVERBURDEN REMOVAL"
                      : "UNDERGROUND WORKINGS"}
                  </span>
                  <span className="font-mono text-[11px] bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">
                    {mineSummary.mine_type === "opencast_coal" ? "BCM" : "DISTRICT"}
                  </span>
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-[#0F172A]">
                    {mineSummary.mine_type === "opencast_coal"
                      ? mineSummary.overburden_actual_bcm
                        ? `${mineSummary.overburden_actual_bcm.toLocaleString()} BCM`
                        : "0 BCM"
                      : "Seam VII Panel A"}
                  </span>
                  <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded">
                    {mineSummary.mine_type === "opencast_coal" ? "Stripping Active" : "Continuous Miner"}
                  </span>
                </div>
                <div className="mt-2.5 pt-2.5 border-t border-[#F1F5F9] text-xs text-[#64748B]">
                  HEMM / Machinery:{" "}
                  <strong className="text-[#334155]">
                    {mineSummary.hemm_context_summary || "HEMM data unavailable"}
                  </strong>
                </div>
              </div>

              {/* Downtime & Delays Card */}
              <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm">
                <div className="flex items-center justify-between text-xs text-[#64748B] font-medium">
                  <span>OPERATIONAL DELAYS</span>
                  <Clock className="w-4 h-4 text-[#64748B]" />
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-[#0F172A]">
                    {mineSummary.total_downtime_minutes} min
                  </span>
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      mineSummary.total_downtime_minutes === 0
                        ? "bg-emerald-100 text-emerald-800"
                        : mineSummary.total_downtime_minutes < 60
                        ? "bg-amber-100 text-amber-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {mineSummary.total_downtime_minutes === 0
                      ? "Zero Delays"
                      : `${mineSummary.total_downtime_minutes}m stoppage`}
                  </span>
                </div>
                <div className="mt-2.5 pt-2.5 border-t border-[#F1F5F9] text-xs text-[#64748B] truncate">
                  Primary Cause:{" "}
                  <strong className="text-[#334155]">
                    {mineSummary.delay_reasons[0] || "No recorded operational delay"}
                  </strong>
                </div>
              </div>
            </div>

            {/* SHIFT-LEVEL REPORTING MATRIX */}
            <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-[#E2E8F0] flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-[#0F172A]">Shift Performance Ledger</h3>
                  <p className="text-xs text-[#64748B]">
                    Granular shift-by-shift coal production, dispatch reconciliation, downtime, and source traceability.
                  </p>
                </div>
                <span className="text-xs font-mono text-[#64748B] bg-slate-50 px-2 py-1 rounded border border-[#E2E8F0]">
                  3 Configured Shifts
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[#E2E8F0]">
                {mineSummary.shifts.map((s) => (
                  <div key={s.shift_name} className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-bold text-[#0F172A]">{s.shift_name}</span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                        {s.sources.join(", ") || "Shift Report"}
                      </span>
                    </div>

                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between py-1 border-b border-[#F1F5F9]">
                        <span className="text-[#64748B]">Coal Extracted:</span>
                        <span className="font-bold text-[#0F172A]">
                          {s.production_tonnes.toLocaleString()} T
                        </span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-[#F1F5F9]">
                        <span className="text-[#64748B]">Dispatched:</span>
                        <span className="font-semibold text-[#334155]">
                          {s.dispatch_tonnes.toLocaleString()} T
                        </span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-[#F1F5F9]">
                        <span className="text-[#64748B]">Downtime Duration:</span>
                        <span
                          className={`font-semibold ${
                            s.downtime_minutes > 0 ? "text-amber-700" : "text-emerald-700"
                          }`}
                        >
                          {s.downtime_minutes} min
                        </span>
                      </div>
                      <div className="pt-2">
                        <span className="text-[11px] text-[#64748B] block mb-1">Delays & Operational Notes:</span>
                        <div className="text-[11px] text-[#334155] italic bg-[#F8FAFC] p-2 rounded border border-[#F1F5F9] min-h-[38px]">
                          {s.delays.length > 0 ? s.delays.join("; ") : "Continuous smooth operations"}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* CONTRACTOR / MDO CONTRIBUTION & DELAYS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Contractor / MDO Link */}
              <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-[#0F172A]">Production by Contractor & MDO</h3>
                    <p className="text-xs text-[#64748B]">
                      Departmental workforce vs Work-order outsourcing vs MDO contribution.
                    </p>
                  </div>
                  <span className="text-[11px] font-semibold text-[#D62F26] bg-[#FDEEE9] px-2 py-0.5 rounded">
                    Statutory Linkage
                  </span>
                </div>

                {mineSummary.contractor_contributions.length === 0 ? (
                  <div className="text-xs text-[#64748B] italic py-6 text-center">
                    No contractor production registered for this date.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {mineSummary.contractor_contributions.map((c, idx) => (
                      <div key={idx} className="p-3 rounded-md bg-[#F8FAFC] border border-[#E2E8F0]">
                        <div className="flex items-center justify-between text-xs mb-1.5">
                          <span className="font-bold text-[#0F172A]">{c.contractor_name}</span>
                          <span className="font-mono text-xs font-semibold text-[#0F172A]">
                            {c.production_tonnes.toLocaleString()} T ({c.percentage_share}%)
                          </span>
                        </div>
                        <div className="w-full bg-[#E2E8F0] h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              c.contract_type === "DEPARTMENTAL"
                                ? "bg-slate-700"
                                : c.contract_type === "MDO"
                                ? "bg-[#D62F26]"
                                : "bg-blue-600"
                            }`}
                            style={{ width: `${Math.min(c.percentage_share, 100)}%` }}
                          />
                        </div>
                        <div className="mt-1.5 flex items-center justify-between text-[11px] text-[#64748B]">
                          <span>Contract Category: {c.contract_type}</span>
                          <span>ID: {c.contractor_id || "DEPT"}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Explainable Anomalies Section */}
              <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-[#0F172A]">Operational Review Required</h3>
                    <p className="text-xs text-[#64748B]">
                      Explainable governance anomaly detection (no black-box scoring).
                    </p>
                  </div>
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      mineSummary.anomalies.length > 0
                        ? "bg-red-100 text-red-800"
                        : "bg-emerald-100 text-emerald-800"
                    }`}
                  >
                    {mineSummary.anomalies.length} Signals
                  </span>
                </div>

                {mineSummary.anomalies.length === 0 ? (
                  <div className="text-center py-8 bg-[#F8FAFC] rounded border border-dashed border-[#CBD5E1]">
                    <CheckCircle className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                    <span className="text-xs font-semibold text-[#334155] block">
                      Reconciliation Consistent
                    </span>
                    <span className="text-[11px] text-[#64748B]">
                      No dispatch mismatches, safety stoppages, or report deviations detected.
                    </span>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[340px] overflow-y-auto pr-1">
                    {mineSummary.anomalies.map((anom) => (
                      <div
                        key={anom.anomaly_id}
                        className={`p-3.5 rounded-md border text-xs ${
                          anom.severity === "CRITICAL"
                            ? "bg-red-50/70 border-red-200 text-red-900"
                            : "bg-amber-50/70 border-amber-200 text-amber-900"
                        }`}
                      >
                        <div className="flex items-center justify-between font-bold mb-1">
                          <span className="flex items-center gap-1.5">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            {anom.what}
                          </span>
                          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 bg-white/70 rounded">
                            {anom.severity}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#475569] mb-1.5">
                          <strong>Why:</strong> {anom.why}
                        </p>
                        <div className="text-[11px] bg-white/90 p-2 rounded border border-black/5">
                          <strong>Recommended Action:</strong> {anom.recommended_review}
                        </div>
                        <div className="mt-2 flex items-center justify-between text-[10px] text-[#64748B]">
                          <span>Source: {anom.source}</span>
                          <span>Signal ID: {anom.anomaly_id}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: AREA AGGREGATION VIEW */}
        {activeTab === "area" && areaSummary && (
          <div className="space-y-6">
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <div className="text-xs text-[#64748B] uppercase tracking-wider font-semibold">
                    {areaSummary.subsidiary} · AREA OPERATIONAL OVERVIEW
                  </div>
                  <h2 className="text-xl font-bold text-[#0F172A]">{areaSummary.area_name}</h2>
                </div>
                <div className="flex items-center gap-4 text-xs font-medium text-[#475569]">
                  <div>
                    Mines Reporting:{" "}
                    <strong className="text-[#0F172A]">
                      {areaSummary.mines_reporting} / {areaSummary.total_mines}
                    </strong>
                  </div>
                  <div>
                    Unresolved Anomalies:{" "}
                    <strong
                      className={
                        areaSummary.unresolved_anomalies_count > 0 ? "text-red-600" : "text-emerald-600"
                      }
                    >
                      {areaSummary.unresolved_anomalies_count}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Area Rollup KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-[#F1F5F9]">
                <div>
                  <span className="text-xs text-[#64748B]">Total Area Production</span>
                  <div className="text-xl font-bold text-[#0F172A] mt-0.5">
                    {areaSummary.total_production_tonnes.toLocaleString()} T
                  </div>
                </div>
                <div>
                  <span className="text-xs text-[#64748B]">Target & Achievement</span>
                  <div className="text-xl font-bold text-[#0F172A] mt-0.5">
                    {areaSummary.total_target_tonnes
                      ? `${areaSummary.total_target_tonnes.toLocaleString()} T (${areaSummary.overall_achievement_percentage}%)`
                      : "Target not configured"}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-[#64748B]">Total Dispatch</span>
                  <div className="text-xl font-bold text-[#0F172A] mt-0.5">
                    {areaSummary.total_dispatch_tonnes.toLocaleString()} T
                  </div>
                </div>
              </div>
            </div>

            {/* Mines in this Area Matrix */}
            <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-[#E2E8F0]">
                <h3 className="text-sm font-bold text-[#0F172A]">Constituent Mines Performance Matrix</h3>
                <p className="text-xs text-[#64748B]">
                  Single source records rolled up automatically from pithead weighbridges and shift logs.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0] text-[#64748B] font-semibold">
                    <tr>
                      <th className="py-3 px-4">Mine Name</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Production (T)</th>
                      <th className="py-3 px-4">Target (T)</th>
                      <th className="py-3 px-4">Achievement</th>
                      <th className="py-3 px-4">Safety Stoppage</th>
                      <th className="py-3 px-4">Compliance Status</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {areaSummary.mines.map((m) => (
                      <tr key={m.mine_id} className="hover:bg-[#F8FAFC] transition-colors">
                        <td className="py-3 px-4 font-bold text-[#0F172A]">{m.mine_name}</td>
                        <td className="py-3 px-4 text-[#64748B]">
                          {m.mine_type === "opencast_coal" ? "Opencast" : "Underground"}
                        </td>
                        <td className="py-3 px-4 font-mono font-semibold">
                          {m.production_tonnes.toLocaleString()} T
                        </td>
                        <td className="py-3 px-4 font-mono text-[#64748B]">
                          {m.target_tonnes ? `${m.target_tonnes.toLocaleString()} T` : "Not set"}
                        </td>
                        <td className="py-3 px-4">
                          {m.achievement_percentage !== null && m.achievement_percentage !== undefined ? (
                            <span
                              className={`px-2 py-0.5 rounded font-semibold text-[11px] ${
                                m.achievement_percentage >= 100
                                  ? "bg-emerald-100 text-emerald-800"
                                  : m.achievement_percentage >= 80
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-red-100 text-red-800"
                              }`}
                            >
                              {m.achievement_percentage}%
                            </span>
                          ) : (
                            <span className="text-[#94A3B8] italic">—</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          {m.active_safety_stoppage ? (
                            <span className="inline-flex items-center gap-1 text-red-700 font-semibold">
                              <AlertTriangle className="w-3.5 h-3.5" /> Active Stoppage
                            </span>
                          ) : (
                            <span className="text-emerald-700 font-medium">Clear</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              m.compliance_status === "COMPLIANT"
                                ? "bg-emerald-50 text-emerald-700"
                                : "bg-red-50 text-red-700"
                            }`}
                          >
                            {m.compliance_status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => {
                              setSelectedMineId(m.mine_id);
                              setActiveTab("mine");
                            }}
                            className="text-[#D62F26] font-semibold hover:underline"
                          >
                            Drill Down →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: SUBSIDIARY ROLLUP VIEW */}
        {activeTab === "subsidiary" && subsidiarySummary && (
          <div className="space-y-6">
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <div className="text-xs text-[#64748B] uppercase tracking-wider font-semibold">
                    CIL HOLDING COMPANY · SUBSIDIARY OVERVIEW
                  </div>
                  <h2 className="text-xl font-bold text-[#0F172A]">{subsidiarySummary.subsidiary_name}</h2>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs bg-[#F1F5F9] px-2.5 py-1 rounded border border-[#CBD5E1] text-[#334155]">
                    Mines Reporting:{" "}
                    <strong>
                      {subsidiarySummary.mines_reporting_count} / {subsidiarySummary.total_mines_count}
                    </strong>
                  </span>
                  <span className="text-xs bg-red-50 px-2.5 py-1 rounded border border-red-200 text-red-700">
                    Critical Alarms: <strong>{subsidiarySummary.critical_safety_signals_count}</strong>
                  </span>
                </div>
              </div>

              {/* Subsidiary KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-3 border-t border-[#F1F5F9] text-xs">
                <div>
                  <span className="text-[#64748B]">Total Production</span>
                  <div className="text-xl font-bold text-[#0F172A] mt-0.5">
                    {subsidiarySummary.total_production_tonnes.toLocaleString()} T
                  </div>
                </div>
                <div>
                  <span className="text-[#64748B]">Target</span>
                  <div className="text-xl font-bold text-[#0F172A] mt-0.5">
                    {subsidiarySummary.total_target_tonnes
                      ? `${subsidiarySummary.total_target_tonnes.toLocaleString()} T`
                      : "Not configured"}
                  </div>
                </div>
                <div>
                  <span className="text-[#64748B]">Total Dispatch</span>
                  <div className="text-xl font-bold text-[#0F172A] mt-0.5">
                    {subsidiarySummary.total_dispatch_tonnes.toLocaleString()} T
                  </div>
                </div>
                <div>
                  <span className="text-[#64748B]">Achievement</span>
                  <div className="text-xl font-bold text-emerald-700 mt-0.5">
                    {subsidiarySummary.overall_achievement_percentage !== null &&
                    subsidiarySummary.overall_achievement_percentage !== undefined
                      ? `${subsidiarySummary.overall_achievement_percentage}%`
                      : "N/A"}
                  </div>
                </div>
              </div>
            </div>

            {/* Areas Table */}
            <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-[#E2E8F0]">
                <h3 className="text-sm font-bold text-[#0F172A]">Operating Areas Rollup</h3>
                <p className="text-xs text-[#64748B]">
                  Aggregated directly from operational source records without duplicate manual entry.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0] text-[#64748B] font-semibold">
                    <tr>
                      <th className="py-3 px-4">Area Name</th>
                      <th className="py-3 px-4">Mines Active</th>
                      <th className="py-3 px-4">Production (T)</th>
                      <th className="py-3 px-4">Target (T)</th>
                      <th className="py-3 px-4">Achievement</th>
                      <th className="py-3 px-4">Open Anomalies</th>
                      <th className="py-3 px-4">Critical Safety</th>
                      <th className="py-3 px-4 text-right">Drill Down</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {subsidiarySummary.areas.map((a) => (
                      <tr key={a.area_id} className="hover:bg-[#F8FAFC] transition-colors">
                        <td className="py-3 px-4 font-bold text-[#0F172A]">{a.area_name}</td>
                        <td className="py-3 px-4 text-[#64748B]">
                          {a.mines_reporting} / {a.total_mines}
                        </td>
                        <td className="py-3 px-4 font-mono font-semibold">
                          {a.total_production_tonnes.toLocaleString()} T
                        </td>
                        <td className="py-3 px-4 font-mono text-[#64748B]">
                          {a.total_target_tonnes ? `${a.total_target_tonnes.toLocaleString()} T` : "—"}
                        </td>
                        <td className="py-3 px-4 font-semibold text-emerald-700">
                          {a.achievement_percentage ? `${a.achievement_percentage}%` : "—"}
                        </td>
                        <td className="py-3 px-4 font-semibold text-amber-700">
                          {a.unresolved_anomalies_count}
                        </td>
                        <td className="py-3 px-4 font-semibold text-red-700">
                          {a.critical_safety_signals}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setActiveTab("area")}
                            className="text-[#D62F26] font-semibold hover:underline"
                          >
                            View Area →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: CIL CORPORATE COMMAND */}
        {activeTab === "corporate" && corporateSummary && (
          <div className="space-y-6">
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <div className="text-xs text-[#64748B] uppercase tracking-wider font-semibold">
                    PAN-INDIA HOLDING COMPANY
                  </div>
                  <h2 className="text-xl font-bold text-[#0F172A]">{corporateSummary.organization}</h2>
                </div>
                <div className="flex items-center gap-3 text-xs font-medium">
                  <span className="bg-[#F1F5F9] px-2.5 py-1 rounded border border-[#CBD5E1]">
                    Subsidiaries Active: <strong>{corporateSummary.total_subsidiaries}</strong>
                  </span>
                  <span className="bg-[#F1F5F9] px-2.5 py-1 rounded border border-[#CBD5E1]">
                    Mines Reporting:{" "}
                    <strong>
                      {corporateSummary.total_mines_reporting} / {corporateSummary.total_mines_operating}
                    </strong>
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-3 border-t border-[#F1F5F9] text-xs">
                <div>
                  <span className="text-[#64748B]">Pan-India Production</span>
                  <div className="text-2xl font-bold text-[#0F172A] mt-0.5">
                    {corporateSummary.pan_india_production_tonnes.toLocaleString()} T
                  </div>
                </div>
                <div>
                  <span className="text-[#64748B]">Pan-India Target</span>
                  <div className="text-2xl font-bold text-[#0F172A] mt-0.5">
                    {corporateSummary.pan_india_target_tonnes
                      ? `${corporateSummary.pan_india_target_tonnes.toLocaleString()} T`
                      : "Configured Mines Only"}
                  </div>
                </div>
                <div>
                  <span className="text-[#64748B]">Overall Dispatch</span>
                  <div className="text-2xl font-bold text-[#0F172A] mt-0.5">
                    {corporateSummary.pan_india_dispatch_tonnes.toLocaleString()} T
                  </div>
                </div>
                <div>
                  <span className="text-[#64748B]">Critical Operational Conflicts</span>
                  <div className="text-2xl font-bold text-red-600 mt-0.5">
                    {corporateSummary.critical_operational_signals_count}
                  </div>
                </div>
              </div>
            </div>

            {/* Subsidiaries Table */}
            <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-[#E2E8F0]">
                <h3 className="text-sm font-bold text-[#0F172A]">Subsidiary Operational Comparison</h3>
                <p className="text-xs text-[#64748B]">
                  Real-time rollup connecting Ministry & Corporate governance directly to pithead extraction data.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0] text-[#64748B] font-semibold">
                    <tr>
                      <th className="py-3 px-4">Subsidiary</th>
                      <th className="py-3 px-4">Mines Active</th>
                      <th className="py-3 px-4">Production (T)</th>
                      <th className="py-3 px-4">Target (T)</th>
                      <th className="py-3 px-4">Achievement</th>
                      <th className="py-3 px-4">Critical Safety Signals</th>
                      <th className="py-3 px-4">Operational Anomalies</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {corporateSummary.subsidiaries.map((s) => (
                      <tr key={s.subsidiary_id} className="hover:bg-[#F8FAFC] transition-colors">
                        <td className="py-3 px-4 font-bold text-[#0F172A]">{s.subsidiary_name}</td>
                        <td className="py-3 px-4 text-[#64748B]">
                          {s.mines_reporting} / {s.total_mines}
                        </td>
                        <td className="py-3 px-4 font-mono font-semibold">
                          {s.production_tonnes.toLocaleString()} T
                        </td>
                        <td className="py-3 px-4 font-mono text-[#64748B]">
                          {s.target_tonnes ? `${s.target_tonnes.toLocaleString()} T` : "—"}
                        </td>
                        <td className="py-3 px-4 font-semibold text-emerald-700">
                          {s.achievement_percentage ? `${s.achievement_percentage}%` : "—"}
                        </td>
                        <td className="py-3 px-4 font-semibold text-red-600">
                          {s.critical_signals_count}
                        </td>
                        <td className="py-3 px-4 font-semibold text-amber-700">
                          {s.anomalies_count}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setActiveTab("subsidiary")}
                            className="text-[#D62F26] font-semibold hover:underline"
                          >
                            Explore Subsidiary →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: STATUTORY DAILY REPORT */}
        {activeTab === "report" && dailyReport && (
          <div className="space-y-6">
            <div className="bg-white border border-[#CBD5E1] rounded-lg p-6 shadow-sm max-w-4xl mx-auto print:shadow-none print:border-none print:p-0">
              {/* Report Header */}
              <div className="border-b-2 border-[#0F172A] pb-4 mb-6">
                <div className="flex items-center justify-between text-xs text-[#64748B] mb-2">
                  <span>COAL INDIA LIMITED · STATUTORY MINING RECORD</span>
                  <span className="font-mono">FORM IV-B RECONCILIATION</span>
                </div>
                <h2 className="text-xl font-bold text-[#0F172A] uppercase tracking-wide">
                  {dailyReport.report_title}
                </h2>
                <div className="mt-2 text-xs grid grid-cols-2 sm:grid-cols-4 gap-2 text-[#475569]">
                  <div>
                    Mine: <strong className="text-[#0F172A]">{dailyReport.mine_name}</strong>
                  </div>
                  <div>
                    Subsidiary: <strong className="text-[#0F172A]">{dailyReport.subsidiary}</strong>
                  </div>
                  <div>
                    Date: <strong className="text-[#0F172A]">{dailyReport.date}</strong>
                  </div>
                  <div>
                    Generated: <strong className="text-[#0F172A]">{dailyReport.generated_at.split("T")[0]}</strong>
                  </div>
                </div>
              </div>

              {/* Report Tonnage Summary Table */}
              <div className="mb-6">
                <h3 className="text-xs font-bold text-[#0F172A] uppercase tracking-wider mb-2">
                  I. Operational Production Summary
                </h3>
                <table className="w-full text-xs border border-[#CBD5E1]">
                  <thead className="bg-[#F1F5F9] border-b border-[#CBD5E1]">
                    <tr>
                      <th className="p-2.5 border-r border-[#CBD5E1]">Actual Coal (T)</th>
                      <th className="p-2.5 border-r border-[#CBD5E1]">Target Coal (T)</th>
                      <th className="p-2.5 border-r border-[#CBD5E1]">Variance (T)</th>
                      <th className="p-2.5 border-r border-[#CBD5E1]">Achievement %</th>
                      <th className="p-2.5 border-r border-[#CBD5E1]">Dispatched (T)</th>
                      <th className="p-2.5">Total Downtime</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="text-center font-mono">
                      <td className="p-2.5 border-r border-[#CBD5E1] font-bold">
                        {dailyReport.production_actual_tonnes.toLocaleString()} T
                      </td>
                      <td className="p-2.5 border-r border-[#CBD5E1]">
                        {dailyReport.production_target_tonnes
                          ? `${dailyReport.production_target_tonnes.toLocaleString()} T`
                          : "Not Configured"}
                      </td>
                      <td className="p-2.5 border-r border-[#CBD5E1] font-semibold text-emerald-700">
                        {dailyReport.variance_tonnes !== null && dailyReport.variance_tonnes !== undefined
                          ? `${dailyReport.variance_tonnes > 0 ? "+" : ""}${dailyReport.variance_tonnes} T`
                          : "N/A"}
                      </td>
                      <td className="p-2.5 border-r border-[#CBD5E1] font-bold">
                        {dailyReport.achievement_percentage !== null && dailyReport.achievement_percentage !== undefined
                          ? `${dailyReport.achievement_percentage}%`
                          : "N/A"}
                      </td>
                      <td className="p-2.5 border-r border-[#CBD5E1]">
                        {dailyReport.dispatch_actual_tonnes.toLocaleString()} T
                      </td>
                      <td className="p-2.5 text-amber-800">
                        {dailyReport.total_downtime_minutes} min
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Shift Breakdown Section */}
              <div className="mb-6">
                <h3 className="text-xs font-bold text-[#0F172A] uppercase tracking-wider mb-2">
                  II. Shift-wise Output & Delays
                </h3>
                <table className="w-full text-xs border border-[#CBD5E1]">
                  <thead className="bg-[#F1F5F9] border-b border-[#CBD5E1]">
                    <tr>
                      <th className="p-2 border-r border-[#CBD5E1]">Shift</th>
                      <th className="p-2 border-r border-[#CBD5E1]">Extraction (T)</th>
                      <th className="p-2 border-r border-[#CBD5E1]">Dispatch (T)</th>
                      <th className="p-2 border-r border-[#CBD5E1]">Downtime</th>
                      <th className="p-2 border-r border-[#CBD5E1]">Primary Data Source</th>
                      <th className="p-2">Reported Operational Delay</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#CBD5E1]">
                    {dailyReport.shifts_reported.map((s) => (
                      <tr key={s.shift_name} className="text-left font-mono">
                        <td className="p-2 border-r border-[#CBD5E1] font-bold text-[#0F172A]">
                          {s.shift_name}
                        </td>
                        <td className="p-2 border-r border-[#CBD5E1]">
                          {s.production_tonnes.toLocaleString()} T
                        </td>
                        <td className="p-2 border-r border-[#CBD5E1]">
                          {s.dispatch_tonnes.toLocaleString()} T
                        </td>
                        <td className="p-2 border-r border-[#CBD5E1] text-amber-800">
                          {s.downtime_minutes}m
                        </td>
                        <td className="p-2 border-r border-[#CBD5E1] text-[11px] font-sans">
                          {s.sources.join(", ") || "Weighbridge"}
                        </td>
                        <td className="p-2 font-sans text-[11px] text-[#475569]">
                          {s.delays.join("; ") || "Smooth continuous operations"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Cryptographic Traceability & Audit Section */}
              <div className="bg-[#F8FAFC] border border-[#E2E8F0] p-4 rounded-md text-xs mb-6 space-y-2">
                <div className="flex items-center justify-between font-bold text-[#0F172A]">
                  <span className="flex items-center gap-1.5">
                    <FileCheck className="w-4 h-4 text-[#D62F26]" />
                    Cryptographic Integrity & Data Origin Proof
                  </span>
                  <span className="font-mono text-[11px] bg-slate-200 px-2 py-0.5 rounded">
                    {dailyReport.integrity_mode}
                  </span>
                </div>
                <div className="text-[#475569] text-[11px]">
                  Records Synthesized: <strong>{dailyReport.records_included_count}</strong> · Source Types:{" "}
                  <strong>{dailyReport.source_types.join(", ") || "Weighbridge, Shift Report"}</strong>
                </div>
                <div className="font-mono text-[11px] bg-white p-2 rounded border border-[#CBD5E1] break-all text-[#334155]">
                  SHA-256: {dailyReport.integrity_verification_hash}
                </div>
              </div>

              {/* Print / Export Button */}
              <div className="flex justify-end gap-3 print:hidden">
                <button
                  onClick={() => window.print()}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-[#0F172A] text-white text-xs font-semibold rounded hover:bg-[#1E293B] transition-colors"
                >
                  <Printer className="w-4 h-4" />
                  Print Official Statutory Report
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* =========================================================
          MODAL: LOG PRODUCTION EVENT
      ========================================================= */}
      {showLogModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl border border-[#CBD5E1] text-xs max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0] mb-4">
              <div>
                <h3 className="text-base font-bold text-[#0F172A]">Log Operational Production Event</h3>
                <p className="text-[11px] text-[#64748B]">
                  Register shift extraction data with deterministic SHA-256 content verification.
                </p>
              </div>
              <button
                onClick={() => setShowLogModal(false)}
                className="text-[#64748B] hover:text-[#0F172A] font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRecord} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">Mine ID</label>
                  <input
                    type="text"
                    disabled
                    value={selectedMineId}
                    className="w-full p-2 bg-[#F1F5F9] border border-[#CBD5E1] rounded text-[#64748B] font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">Shift</label>
                  <select
                    value={logShift}
                    onChange={(e) => setLogShift(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded focus:outline-none focus:border-[#D62F26]"
                  >
                    <option value="Shift A">Shift A (06:00 - 14:00)</option>
                    <option value="Shift B">Shift B (14:00 - 22:00)</option>
                    <option value="Shift C">Shift C (22:00 - 06:00)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">
                    Coal Extracted (Tonnes) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    placeholder="e.g. 1250"
                    value={logQuantity}
                    onChange={(e) => setLogQuantity(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded focus:outline-none focus:border-[#D62F26]"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">
                    Dispatched Quantity (Tonnes)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="e.g. 1200"
                    value={logDispatch}
                    onChange={(e) => setLogDispatch(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded focus:outline-none focus:border-[#D62F26]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">Data Source</label>
                  <select
                    value={logSource}
                    onChange={(e) => setLogSource(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded focus:outline-none focus:border-[#D62F26]"
                  >
                    <option value="WEIGHBRIDGE">Weighbridge</option>
                    <option value="SHIFT_REPORT">Shift Report</option>
                    <option value="SURVEYOR">Surveyor Log</option>
                    <option value="CHP">CHP / Counter</option>
                    <option value="MANUAL_ENTRY">Manual Entry</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-[#334155] mb-1">Contractor / MDO</label>
                  <select
                    value={logContractorType}
                    onChange={(e) => setLogContractorType(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded focus:outline-none focus:border-[#D62F26]"
                  >
                    <option value="DEPARTMENTAL">Departmental Workforce</option>
                    <option value="WORK_ORDER">Work-Order Outsourcing</option>
                    <option value="MDO">Mine Developer & Operator (MDO)</option>
                  </select>
                </div>
              </div>

              {logContractorType !== "DEPARTMENTAL" && (
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">
                    Contractor / Agency Legal Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Talcher Mining Logistics Ltd."
                    value={logContractorName}
                    onChange={(e) => setLogContractorName(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded focus:outline-none focus:border-[#D62F26]"
                  />
                </div>
              )}

              {/* Conditional Opencast vs Underground Fields */}
              {currentMineConfig.type === "opencast_coal" ? (
                <div className="p-3 bg-[#FFF8F0] border border-[#FEE6D0] rounded space-y-3">
                  <span className="text-[11px] font-bold text-amber-900 block">
                    OPENCAST OPERATIONAL PARAMETERS
                  </span>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        Overburden Removed (BCM)
                      </label>
                      <input
                        type="number"
                        step="1"
                        placeholder="e.g. 10500"
                        value={logOverburden}
                        onChange={(e) => setLogOverburden(e.target.value)}
                        className="w-full p-2 border border-[#CBD5E1] rounded bg-white"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        HEMM Deployment Context
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. 6 Dumpers · 1 Excavator"
                        value={logHemmContext}
                        onChange={(e) => setLogHemmContext(e.target.value)}
                        className="w-full p-2 border border-[#CBD5E1] rounded bg-white"
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-[#F0FDF4] border border-[#DCFCE7] rounded space-y-3">
                  <span className="text-[11px] font-bold text-emerald-900 block">
                    UNDERGROUND WORKINGS PARAMETERS
                  </span>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        District / Section
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. 14 Seam District 3"
                        value={logDistrict}
                        onChange={(e) => setLogDistrict(e.target.value)}
                        className="w-full p-2 border border-[#CBD5E1] rounded bg-white"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-[#334155] mb-1">
                        Working Face / Panel
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Panel 7 East Face"
                        value={logFacePanel}
                        onChange={(e) => setLogFacePanel(e.target.value)}
                        className="w-full p-2 border border-[#CBD5E1] rounded bg-white"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Downtime & Delays */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">
                    Downtime Duration (Minutes)
                  </label>
                  <input
                    type="number"
                    min="0"
                    placeholder="0"
                    value={logDowntime}
                    onChange={(e) => setLogDowntime(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">Delay Reason</label>
                  <input
                    type="text"
                    placeholder="e.g. Belt conveyor chute jamming"
                    value={logDelayReason}
                    onChange={(e) => setLogDelayReason(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[#E2E8F0]">
                <button
                  type="button"
                  onClick={() => setShowLogModal(false)}
                  className="px-4 py-2 border border-[#CBD5E1] rounded text-[#475569] font-semibold hover:bg-[#F1F5F9]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingLog}
                  className="px-4 py-2 bg-[#D62F26] text-white rounded font-semibold hover:bg-[#B91C1C] disabled:opacity-50"
                >
                  {submittingLog ? "Verifying & Saving..." : "Commit Production Record"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =========================================================
          MODAL: HISTORICAL CORRECTION WORKFLOW
      ========================================================= */}
      {showCorrectModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl border border-[#CBD5E1] text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0] mb-4">
              <div>
                <h3 className="text-base font-bold text-[#0F172A]">Historical Record Correction</h3>
                <p className="text-[11px] text-[#64748B]">
                  Original record is preserved immutably. A linked superseded version is generated.
                </p>
              </div>
              <button
                onClick={() => setShowCorrectModal(false)}
                className="text-[#64748B] hover:text-[#0F172A] font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCorrectRecord} className="space-y-4">
              <div className="bg-amber-50 border border-amber-200 p-3 rounded text-[11px] text-amber-900">
                <Lock className="w-3.5 h-3.5 inline mr-1 text-amber-700" />
                <strong>Statutory Immutability Rule:</strong> PRITHVI does not allow silent editing.
                Every correction is recorded as an auditable version with timestamp and user attribution.
              </div>

              <div>
                <label className="block font-semibold text-[#334155] mb-1">
                  Target Production Record ID *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. PROD-ABC1234567"
                  value={correctRecordId}
                  onChange={(e) => setCorrectRecordId(e.target.value)}
                  className="w-full p-2 border border-[#CBD5E1] rounded font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">
                    Corrected Quantity (T) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    placeholder="e.g. 1280.0"
                    value={correctQty}
                    onChange={(e) => setCorrectQty(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#334155] mb-1">
                    Corrected Dispatch (T)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="e.g. 1250.0"
                    value={correctDispatch}
                    onChange={(e) => setCorrectDispatch(e.target.value)}
                    className="w-full p-2 border border-[#CBD5E1] rounded"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#334155] mb-1">
                  Statutory Reason for Correction *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Detailed justification (e.g. Weighbridge bridge 2 zero tare calibration drift confirmed by surveyor certificate)"
                  value={correctReason}
                  onChange={(e) => setCorrectReason(e.target.value)}
                  className="w-full p-2 border border-[#CBD5E1] rounded"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-[#E2E8F0]">
                <button
                  type="button"
                  onClick={() => setShowCorrectModal(false)}
                  className="px-4 py-2 border border-[#CBD5E1] rounded text-[#475569] font-semibold hover:bg-[#F1F5F9]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCorrection}
                  className="px-4 py-2 bg-[#D62F26] text-white rounded font-semibold hover:bg-[#B91C1C] disabled:opacity-50"
                >
                  {submittingCorrection ? "Submitting..." : "Apply Immutable Correction"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
