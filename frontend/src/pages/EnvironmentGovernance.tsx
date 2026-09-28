import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Leaf,
  CheckCircle,
  FileText,
  Building2,
  RefreshCw,
  Plus,
  BarChart3,
  ShieldCheck,
  ShieldAlert,
  Sliders,
  ExternalLink,
  Lock,
  Calendar,
  Compass,
  FileCheck,
  AlertCircle,
  Wind,
  Droplets,
  Volume2,
  Activity,
  Mountain,
  Trees,
  Trash2,
} from "lucide-react";
import {
  getEnvironmentOverview,
  listEnvironmentalParameters,
  listEnvironmentalThresholds,
  listEnvironmentalMeasurements,
  recordEnvironmentalMeasurement,
  listEnvironmentalObligations,
  listEnvironmentalSchedules,
  listEnvironmentalViolations,
  getEnvironmentalRisk,
  listEnvironmentalCases,
  listEnvironmentalReports,
  generateEnvironmentalReport,
  finalizeEnvironmentalReport,
  type EnvironmentalDomain,
  type EnvironmentalParameter,
  type EnvironmentalMeasurement,
  type EnvironmentalThreshold,
  type EnvironmentalObligation,
  type EnvironmentalSchedule,
  type EnvironmentalReport,
  type EnvironmentalRisk,
  type EnvironmentalOverview,
  type EnvironmentalMeasurementCreate,
  type EnvironmentalReportGenerateRequest,
} from "../api/environment";
import { HierarchyBreadcrumb } from "../components/HierarchyBreadcrumb";

interface MineOption {
  id: string;
  name: string;
  type: "underground_coal" | "opencast_coal";
  subsidiary: string;
}

const DEMO_MINES: MineOption[] = [
  {
    id: "MINE-MCL-TALCHER-01",
    name: "Talcher Opencast Demonstration Mine",
    type: "opencast_coal",
    subsidiary: "MCL",
  },
  {
    id: "MINE-BCCL-JHARIA-01",
    name: "Jharia Underground Demonstration Mine",
    type: "underground_coal",
    subsidiary: "BCCL",
  },
  {
    id: "MINE-ECL-RANIGANJ-01",
    name: "Raniganj Deep Underground Coal Mine",
    type: "underground_coal",
    subsidiary: "ECL",
  },
  {
    id: "MINE-SECL-GEVRA-01",
    name: "Gevra Mega Opencast Coal Mine",
    type: "opencast_coal",
    subsidiary: "SECL",
  },
];

const DOMAINS: { key: EnvironmentalDomain | "ALL"; label: string; icon: any }[] = [
  { key: "ALL", label: "All Domains", icon: Sliders },
  { key: "AIR", label: "Air Quality", icon: Wind },
  { key: "WATER", label: "Mine Water", icon: Droplets },
  { key: "NOISE", label: "Noise & Acoustics", icon: Volume2 },
  { key: "VIBRATION", label: "Ground Vibration", icon: Activity },
  { key: "LAND", label: "Dump & Slope Stability", icon: Mountain },
  { key: "RECLAMATION", label: "Bio-Reclamation", icon: Trees },
  { key: "WASTE", label: "Waste Management", icon: Trash2 },
];

export const EnvironmentGovernance: React.FC = () => {
  // State
  const [selectedMineId, setSelectedMineId] = useState<string>("MINE-MCL-TALCHER-01");
  const [selectedDomain, setSelectedDomain] = useState<EnvironmentalDomain | "ALL">("ALL");
  const [activeTab, setActiveTab] = useState<
    "overview" | "measurements" | "violations" | "obligations" | "reports"
  >("overview");

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Data
  const [overview, setOverview] = useState<EnvironmentalOverview | null>(null);
  const [parameters, setParameters] = useState<EnvironmentalParameter[]>([]);
  const [measurements, setMeasurements] = useState<EnvironmentalMeasurement[]>([]);
  const [thresholds, setThresholds] = useState<EnvironmentalThreshold[]>([]);
  const [obligations, setObligations] = useState<EnvironmentalObligation[]>([]);
  const [schedules, setSchedules] = useState<EnvironmentalSchedule[]>([]);
  const [violations, setViolations] = useState<any[]>([]);
  const [risk, setRisk] = useState<EnvironmentalRisk | null>(null);
  const [cases, setCases] = useState<any[]>([]);
  const [reports, setReports] = useState<EnvironmentalReport[]>([]);

  // Modals
  const [showRecordModal, setShowRecordModal] = useState<boolean>(false);
  const [showReportModal, setShowReportModal] = useState<boolean>(false);
  const [viewReport, setViewReport] = useState<EnvironmentalReport | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Form states
  const [newMeasurement, setNewMeasurement] = useState<Partial<EnvironmentalMeasurementCreate>>({
    mine_id: selectedMineId,
    parameter_id: "",
    value: 0,
    unit: "",
    source_type: "FIELD_OBSERVATION",
    source_reference: "Field Portable Sampler",
    simulated: true,
  });

  const [newReport, setNewReport] = useState<Partial<EnvironmentalReportGenerateRequest>>({
    mine_id: selectedMineId,
    reporting_period_start: "2026-09-01",
    reporting_period_end: "2026-09-15",
    title: "Statutory Environmental Compliance & Monitoring Dossier",
    report_type: "STATUTORY_HALF_YEARLY",
  });

  const selectedMine = DEMO_MINES.find((m) => m.id === selectedMineId) || DEMO_MINES[0];

  // Fetch all data
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        overviewRes,
        paramsRes,
        measRes,
        threshRes,
        obRes,
        schedRes,
        violRes,
        riskRes,
        casesRes,
        repRes,
      ] = await Promise.all([
        getEnvironmentOverview(selectedMineId),
        listEnvironmentalParameters(selectedDomain === "ALL" ? undefined : selectedDomain),
        listEnvironmentalMeasurements({
          mine_id: selectedMineId,
          domain: selectedDomain === "ALL" ? undefined : selectedDomain,
          limit: 50,
        }),
        listEnvironmentalThresholds(),
        listEnvironmentalObligations(selectedMineId, selectedDomain === "ALL" ? undefined : selectedDomain),
        listEnvironmentalSchedules({
          mine_id: selectedMineId,
          domain: selectedDomain === "ALL" ? undefined : selectedDomain,
        }),
        listEnvironmentalViolations(selectedMineId, selectedDomain === "ALL" ? undefined : selectedDomain),
        getEnvironmentalRisk(selectedMineId),
        listEnvironmentalCases(selectedMineId, selectedDomain === "ALL" ? undefined : selectedDomain),
        listEnvironmentalReports(selectedMineId, 20),
      ]);

      setOverview(overviewRes);
      setParameters(paramsRes);
      setMeasurements(measRes);
      setThresholds(threshRes);
      setObligations(obRes);
      setSchedules(schedRes);
      setViolations(violRes);
      setRisk(riskRes);
      setCases(casesRes);
      setReports(repRes);
    } catch (err: any) {
      console.error("Failed to load environmental governance data:", err);
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedMineId, selectedDomain]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleMineChange = (mineId: string) => {
    setSelectedMineId(mineId);
    setNewMeasurement((prev) => ({ ...prev, mine_id: mineId }));
    setNewReport((prev) => ({ ...prev, mine_id: mineId }));
  };

  const handleRecordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMeasurement.parameter_id || newMeasurement.value === undefined) {
      alert("Please select a parameter and enter a numeric value.");
      return;
    }

    try {
      const payload: EnvironmentalMeasurementCreate = {
        mine_id: selectedMineId,
        parameter_id: newMeasurement.parameter_id,
        value: Number(newMeasurement.value),
        unit: newMeasurement.unit || "unit",
        measured_at: new Date().toISOString(),
        source_type: newMeasurement.source_type || "FIELD_OBSERVATION",
        source_reference: newMeasurement.source_reference || "Field Observation Desk",
        operational_unit_id: newMeasurement.operational_unit_id || null,
        simulated: Boolean(newMeasurement.simulated),
      };

      const res = await recordEnvironmentalMeasurement(payload);
      setShowRecordModal(false);

      if (res.threshold_breach) {
        setActionSuccess(
          `Measurement recorded. EXCEEDANCE FLAGGED: Observed ${payload.value} ${payload.unit} breached statutory threshold! Case created.`
        );
      } else {
        setActionSuccess(`Measurement of ${payload.value} ${payload.unit} successfully verified against threshold rules.`);
      }
      loadData();
    } catch (err: any) {
      alert(`Error recording measurement: ${err.message}`);
    }
  };

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: EnvironmentalReportGenerateRequest = {
        mine_id: selectedMineId,
        reporting_period_start: newReport.reporting_period_start || "2026-09-01",
        reporting_period_end: newReport.reporting_period_end || "2026-09-15",
        title: newReport.title || "Statutory Environmental Compliance Dossier",
        report_type: newReport.report_type || "MONITORING_SUMMARY",
      };

      const res = await generateEnvironmentalReport(payload);
      setShowReportModal(false);
      setActionSuccess(`Statutory Regulatory Report ${res.report_id} generated. Ready for cryptographic sealing.`);
      loadData();
    } catch (err: any) {
      alert(`Error generating report: ${err.message}`);
    }
  };

  const handleFinalizeReport = async (reportId: string) => {
    try {
      const finalized = await finalizeEnvironmentalReport(reportId);
      setActionSuccess(
        `Report ${finalized.report_id} Finalized & Signed! SHA-256 Digest: ${finalized.content_hash?.substring(
          0,
          16
        )}... | IPFS CID: ${finalized.ipfs_cid?.substring(0, 18)}...`
      );
      loadData();
      if (viewReport && viewReport.report_id === reportId) {
        setViewReport(finalized);
      }
    } catch (err: any) {
      alert(`Error finalizing report: ${err.message}`);
    }
  };

  const getRiskColor = (level?: string) => {
    switch (level) {
      case "CRITICAL":
        return "bg-rose-100 text-rose-800 border-rose-300";
      case "HIGH":
        return "bg-red-100 text-red-800 border-red-300";
      case "MEDIUM":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "LOW":
      default:
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900 pb-16">
      {/* 1. Header & Institutional Banner */}
      <header className="bg-white border-b border-stone-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="p-1.5 bg-emerald-800 text-white rounded shadow-xs">
                  <Leaf className="w-5 h-5" />
                </span>
                <span className="text-[11px] font-bold tracking-wider text-emerald-900 uppercase bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  STATUTORY COMPLIANCE MONITORING · PHASE 2 TASK 13
                </span>
              </div>
              <h1 className="text-xl font-bold text-stone-900 mt-1 flex items-center gap-2 tracking-tight">
                Environmental Governance & Regulatory Reporting
              </h1>
              <p className="text-xs text-stone-500">
                Authoritative Traceability: Obligation → Measurement → Threshold Check → Evidence → Violation → Risk → Corrective Action → Regulatory Dossier
              </p>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* Mine Selector */}
              <div className="flex items-center bg-stone-100 border border-stone-300 rounded px-2.5 py-1 text-xs">
                <Building2 className="w-3.5 h-3.5 text-stone-500 mr-1.5" />
                <span className="font-semibold text-stone-600 mr-2">MINE:</span>
                <select
                  value={selectedMineId}
                  onChange={(e) => handleMineChange(e.target.value)}
                  className="bg-transparent font-medium text-stone-900 focus:outline-none cursor-pointer"
                >
                  {DEMO_MINES.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.subsidiary})
                    </option>
                  ))}
                </select>
              </div>

              {/* Action Buttons */}
              <button
                onClick={() => setShowRecordModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Record Measurement</span>
              </button>

              <button
                onClick={() => setShowReportModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-stone-800 hover:bg-stone-900 text-white text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Generate Report</span>
              </button>

              <button
                onClick={handleRefresh}
                disabled={refreshing}
                title="Refresh environmental data"
                className="p-1.5 text-stone-500 hover:text-stone-800 border border-stone-300 rounded bg-white hover:bg-stone-100 transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-emerald-800" : ""}`} />
              </button>
            </div>
          </div>

          {/* Canonical Breadcrumb */}
          <div className="mt-2.5 pt-2 border-t border-stone-100">
            <HierarchyBreadcrumb unitId={selectedMineId} />
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        {/* Success Alert */}
        {actionSuccess && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-300 rounded text-xs text-emerald-900 flex items-center justify-between shadow-xs">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-700 shrink-0" />
              <span className="font-medium">{actionSuccess}</span>
            </div>
            <button
              onClick={() => setActionSuccess(null)}
              className="text-emerald-700 hover:text-emerald-900 text-xs font-bold ml-4 cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-300 rounded text-xs text-rose-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-700 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="mb-4 p-3 bg-stone-100 border border-stone-200 rounded text-xs text-stone-700 flex items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-emerald-800 shrink-0" />
            <span>Loading authoritative environmental governance records for {selectedMine.name}... ({thresholds.length} statutory/configured threshold rules loaded)</span>
          </div>
        )}

        {/* 2. Mining Method Segregation Callout (UG vs OC) */}
        <div className="mb-6 p-3.5 bg-white border border-stone-200 rounded shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
          <div className="flex items-start gap-2.5">
            <div
              className={`p-2 rounded shrink-0 ${
                selectedMine.type === "underground_coal"
                  ? "bg-purple-100 text-purple-900"
                  : "bg-amber-100 text-amber-900"
              }`}
            >
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-stone-900 text-sm">
                  {selectedMine.type === "underground_coal"
                    ? "UNDERGROUND MINING METHOD GOVERNANCE"
                    : "OPENCAST MINING METHOD GOVERNANCE"}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-stone-100 text-stone-700 border border-stone-300">
                  {selectedMine.type === "underground_coal" ? "CMR 2017 Ch. X / XII" : "CMR 2017 Ch. IX & DGMS Circ. 7"}
                </span>
              </div>
              <p className="text-stone-600 mt-0.5">
                {selectedMine.type === "underground_coal"
                  ? "Statutory monitoring mandates: Main exhaust shaft ventilation air quality, treated sump mine water discharge, and surface subsidence / strata monitoring."
                  : "Statutory monitoring mandates: Haul-road respirable dust (PM10/PM2.5) with water tanker suppression, blast-induced ground vibration (PPV) at lease boundary, and external OB dump slope stability."}
              </p>
            </div>
          </div>
          <div className="shrink-0 flex items-center gap-2 bg-stone-50 px-3 py-1.5 rounded border border-stone-200">
            <span className="text-[10px] font-semibold text-stone-500 uppercase">RULE APPLICABILITY:</span>
            <span className="text-xs font-bold text-stone-800">
              {selectedMine.type === "underground_coal" ? "Underground Only + All" : "Opencast Only + All"}
            </span>
          </div>
        </div>

        {/* 3. KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
          <div className="bg-white border border-stone-200 rounded p-3 shadow-xs">
            <div className="text-[10px] font-bold text-stone-500 uppercase tracking-wider">OBLIGATIONS</div>
            <div className="text-2xl font-bold text-stone-900 mt-1">{obligations.length}</div>
            <div className="text-[10px] text-stone-400 mt-0.5">CTO & EC Mandates</div>
          </div>

          <div className="bg-white border border-stone-200 rounded p-3 shadow-xs">
            <div className="text-[10px] font-bold text-stone-500 uppercase tracking-wider">PARAMETERS</div>
            <div className="text-2xl font-bold text-stone-900 mt-1">{overview?.total_parameters || parameters.length}</div>
            <div className="text-[10px] text-stone-400 mt-0.5">Air, Water, Land, Noise...</div>
          </div>

          <div className="bg-white border border-stone-200 rounded p-3 shadow-xs">
            <div className="text-[10px] font-bold text-stone-500 uppercase tracking-wider">MEASUREMENTS</div>
            <div className="text-2xl font-bold text-stone-900 mt-1">{overview?.total_measurements || measurements.length}</div>
            <div className="text-[10px] text-stone-400 mt-0.5">Recorded & Verified</div>
          </div>

          <div className="bg-white border border-stone-200 rounded p-3 shadow-xs">
            <div className="text-[10px] font-bold text-stone-500 uppercase tracking-wider">VIOLATIONS</div>
            <div className="text-2xl font-bold text-red-700 mt-1">
              {overview?.total_violations || violations.length}
            </div>
            <div className="text-[10px] text-stone-400 mt-0.5">Breaches Flagged</div>
          </div>

          <div className="bg-white border border-stone-200 rounded p-3 shadow-xs">
            <div className="text-[10px] font-bold text-stone-500 uppercase tracking-wider">OVERDUE SCHED.</div>
            <div className="text-2xl font-bold text-amber-700 mt-1">
              {overview?.overdue_schedules_count || 0}
            </div>
            <div className="text-[10px] text-stone-400 mt-0.5">Monitoring Due</div>
          </div>

          <div className="bg-white border border-stone-200 rounded p-3 shadow-xs">
            <div className="text-[10px] font-bold text-stone-500 uppercase tracking-wider">RISK TIER</div>
            <div className="mt-1 flex items-center gap-1.5">
              <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getRiskColor(risk?.risk_level)}`}>
                {risk?.risk_level || "LOW"}
              </span>
              <span className="text-xs font-mono font-bold text-stone-600">({risk?.risk_score || 0}/100)</span>
            </div>
            <div className="text-[10px] text-stone-400 mt-0.5">Deterministic Index</div>
          </div>
        </div>

        {/* 4. Domain Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-4 scrollbar-none">
          {DOMAINS.map((dom) => {
            const Icon = dom.icon;
            const isSelected = selectedDomain === dom.key;
            return (
              <button
                key={dom.key}
                onClick={() => setSelectedDomain(dom.key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all shrink-0 cursor-pointer border ${
                  isSelected
                    ? "bg-emerald-900 text-white border-emerald-900 shadow-xs"
                    : "bg-white text-stone-600 border-stone-300 hover:border-stone-400 hover:bg-stone-50"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{dom.label}</span>
              </button>
            );
          })}
        </div>

        {/* 5. Navigation Tabs */}
        <div className="border-b border-stone-200 mb-6 bg-white rounded-t px-2 shadow-xs">
          <nav className="flex space-x-6">
            {[
              { id: "overview", label: "Overview & Risk Intelligence", icon: BarChart3 },
              { id: "measurements", label: "Measurements Ledger", icon: Sliders },
              { id: "violations", label: "Violations & Cases", icon: ShieldAlert, badge: violations.length },
              { id: "obligations", label: "Obligations & Schedules", icon: Calendar },
              { id: "reports", label: "Regulatory Reports & Audit Seal", icon: FileCheck, badge: reports.length },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-xs transition-colors cursor-pointer ${
                    isActive
                      ? "border-emerald-800 text-emerald-900 font-bold"
                      : "border-transparent text-stone-500 hover:text-stone-700 hover:border-stone-300"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                  {tab.badge !== undefined && tab.badge > 0 && (
                    <span
                      className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                        isActive ? "bg-emerald-100 text-emerald-800" : "bg-stone-100 text-stone-600"
                      }`}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab 1: Overview & Risk Dashboard */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Risk Explanation & Domain Risk Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Overall Risk Score Card */}
              <div className="bg-white border border-stone-200 rounded p-5 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-stone-500 uppercase tracking-wider">
                      STATUTORY RISK ASSESSMENT
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getRiskColor(risk?.risk_level)}`}>
                      {risk?.risk_level || "LOW"} TIER
                    </span>
                  </div>
                  <div className="mt-4 flex items-baseline gap-2">
                    <span className="text-4xl font-extrabold text-stone-900">{risk?.risk_score || 0}</span>
                    <span className="text-sm font-semibold text-stone-400">/ 100</span>
                  </div>
                  <div className="w-full bg-stone-100 h-2 rounded-full mt-3 overflow-hidden border border-stone-200">
                    <div
                      className={`h-full ${
                        (risk?.risk_score || 0) > 75
                          ? "bg-rose-600"
                          : (risk?.risk_score || 0) > 50
                          ? "bg-red-600"
                          : (risk?.risk_score || 0) > 25
                          ? "bg-amber-500"
                          : "bg-emerald-600"
                      }`}
                      style={{ width: `${Math.min(100, risk?.risk_score || 0)}%` }}
                    />
                  </div>
                  <p className="text-xs text-stone-600 mt-4 leading-relaxed bg-stone-50 p-2.5 rounded border border-stone-200">
                    {risk?.explanation || "All monitored parameters are currently within statutory clearance limits."}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-stone-100 text-[11px] text-stone-500 flex items-center justify-between">
                  <span>Recurring Breaches: <b>{risk?.recurring_violations_count || 0}</b></span>
                  <span>Active Breaches: <b>{risk?.active_breaches_count || 0}</b></span>
                </div>
              </div>

              {/* Domain Specific Breakdown */}
              <div className="md:col-span-2 bg-white border border-stone-200 rounded p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                    DOMAIN HAZARD & COMPLIANCE BREAKDOWN
                  </h3>
                  <span className="text-[10px] text-stone-400 font-mono">Weighted Risk Engine</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {risk?.domain_risks &&
                    Object.entries(risk.domain_risks).map(([dom, detail]) => (
                      <div key={dom} className="p-3 bg-stone-50 border border-stone-200 rounded">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold text-stone-700">{dom}</span>
                          <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold border ${getRiskColor(detail.level)}`}>
                            {detail.level}
                          </span>
                        </div>
                        <div className="text-lg font-bold text-stone-900 mt-1.5">{detail.score}/100</div>
                        <div className="text-[10px] text-stone-500 mt-0.5">
                          {detail.breaches > 0 ? (
                            <span className="text-red-700 font-semibold">{detail.breaches} breach(es)</span>
                          ) : (
                            <span className="text-emerald-700 font-semibold">Compliant</span>
                          )}
                        </div>
                      </div>
                    ))}
                </div>

                {/* Contractor & Operational Context Correlation */}
                <div className="mt-4 p-3 bg-blue-50/60 border border-blue-200 rounded text-xs text-blue-900 flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-blue-700 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Contractor & Production Cross-Correlation: </span>
                    <span>
                      Environmental monitoring events automatically correlate with Task 12 active contracts (e.g. haul road watering under contract <b>CONT-TML</b> at Talcher) and Task 10 shift extraction volume to isolate compliance anomalies caused by operational spikes.
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Violations & Active Enforcement */}
            <div className="bg-white border border-stone-200 rounded p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-stone-900 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-red-700" />
                  <span>ACTIVE ENVIRONMENTAL EXCEEDANCES & ENFORCEMENT CASES</span>
                </h3>
                <Link
                  to="/governance"
                  className="text-xs font-semibold text-emerald-800 hover:text-emerald-900 flex items-center gap-1"
                >
                  <span>View Full Governance Master</span>
                  <ExternalLink className="w-3 h-3" />
                </Link>
              </div>

              {violations.length === 0 ? (
                <div className="py-8 text-center text-xs text-stone-500 bg-stone-50 rounded border border-dashed border-stone-200">
                  <CheckCircle className="w-8 h-8 text-emerald-600 mx-auto mb-2 opacity-80" />
                  No open threshold violations recorded for this mine property. All domains operating within permitted limits.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-stone-100 text-stone-600 uppercase text-[10px] tracking-wider border-b border-stone-200">
                      <tr>
                        <th className="py-2.5 px-3">Violation ID / Time</th>
                        <th className="py-2.5 px-3">Domain</th>
                        <th className="py-2.5 px-3">Parameter</th>
                        <th className="py-2.5 px-3">Observed Value</th>
                        <th className="py-2.5 px-3">Configured Limit</th>
                        <th className="py-2.5 px-3">Rule Reference</th>
                        <th className="py-2.5 px-3">Severity</th>
                        <th className="py-2.5 px-3">Case Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 font-sans">
                      {violations.map((v) => (
                        <tr key={v.measurement_id} className="hover:bg-red-50/30 transition-colors">
                          <td className="py-2.5 px-3 font-mono">
                            <span className="font-bold text-stone-900">{v.measurement_id}</span>
                            <div className="text-[10px] text-stone-400">
                              {new Date(v.measured_at).toLocaleString()}
                            </div>
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-stone-100 text-stone-700 border border-stone-300">
                              {v.domain}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 font-medium text-stone-900">{v.parameter_name}</td>
                          <td className="py-2.5 px-3 font-mono font-bold text-red-700">
                            {v.observed_value} {v.unit}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-stone-600">
                            Limit: {v.upper_limit !== null ? v.upper_limit : v.lower_limit} {v.unit}
                          </td>
                          <td className="py-2.5 px-3 text-stone-600">
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-50 text-amber-900 border border-amber-300">
                              {v.source_reference}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-900 border border-rose-300">
                              {v.severity}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-stone-100 text-stone-800 border border-stone-300">
                              ACTION_REQUIRED
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Measurements Ledger */}
        {activeTab === "measurements" && (
          <div className="bg-white border border-stone-200 rounded p-5 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                  ENVIRONMENTAL MEASUREMENTS & OBSERVATION LEDGER
                </h3>
                <p className="text-[11px] text-stone-500">
                  Immutable audit records captured from field sensors, manual instruments, and lab assays.
                </p>
              </div>

              <button
                onClick={() => setShowRecordModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer self-start sm:self-auto"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Measurement</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-stone-100 text-stone-600 uppercase text-[10px] tracking-wider border-b border-stone-200">
                  <tr>
                    <th className="py-2.5 px-3">Measurement ID / Time</th>
                    <th className="py-2.5 px-3">Domain</th>
                    <th className="py-2.5 px-3">Parameter</th>
                    <th className="py-2.5 px-3">Operational Unit</th>
                    <th className="py-2.5 px-3">Observed Value</th>
                    <th className="py-2.5 px-3">Source Type</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Quality</th>
                    <th className="py-2.5 px-3">Source Ref</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-200 font-sans">
                  {measurements.map((m) => (
                    <tr
                      key={m.id}
                      className={`hover:bg-stone-50 transition-colors ${
                        m.status === "FLAGGED_ANOMALY" ? "bg-red-50/20" : ""
                      }`}
                    >
                      <td className="py-2.5 px-3 font-mono">
                        <span className="font-bold text-stone-900">{m.id}</span>
                        <div className="text-[10px] text-stone-400">
                          {new Date(m.measured_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-stone-100 text-stone-700 border border-stone-300">
                          {m.domain || "AIR"}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-medium text-stone-900">
                        {m.parameter_name || m.parameter_id}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-stone-600">
                        {m.operational_unit_id || "Mine Surface"}
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-stone-900">
                        {m.value} {m.unit}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="text-[10px] text-stone-600 bg-stone-100 px-1.5 py-0.5 rounded border border-stone-200">
                          {m.source_type}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        {m.status === "FLAGGED_ANOMALY" ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">
                            ANOMALY
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                            RECORDED
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="text-[10px] font-semibold text-stone-600">
                          {m.data_quality_status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-stone-500 text-[11px]">
                        {m.source_reference || "Direct Entry"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Violations & Cases */}
        {activeTab === "violations" && (
          <div className="bg-white border border-stone-200 rounded p-5 shadow-xs space-y-4">
            <div>
              <h3 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                TRACEABLE COMPLIANCE CASES & CORRECTIVE ACTION CHAINS
              </h3>
              <p className="text-[11px] text-stone-500">
                Every threshold breach automatically creates a statutory ComplianceCase, links evidence, and issues a time-bound Corrective Action.
              </p>
            </div>

            <div className="space-y-3">
              {cases.length === 0 ? (
                <div className="p-8 text-center text-xs text-stone-500 bg-stone-50 rounded border border-dashed border-stone-200">
                  <CheckCircle className="w-8 h-8 text-emerald-600 mx-auto mb-2 opacity-80" />
                  Zero open environmental cases for this property.
                </div>
              ) : (
                cases.map((c) => (
                  <div key={c.case_id} className="p-4 bg-stone-50 border border-stone-300 rounded shadow-xs">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xs text-stone-900">{c.case_id}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 border border-red-300">
                          {c.severity} SEVERITY
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-stone-200 text-stone-800">
                          {c.category}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 self-start sm:self-auto">
                        {c.status}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-stone-900 mt-2">{c.title}</h4>
                    <p className="text-xs text-stone-600 mt-1">{c.description}</p>

                    <div className="mt-3 pt-2.5 border-t border-stone-200 flex flex-wrap items-center justify-between gap-2 text-[11px] text-stone-500">
                      <div>
                        Statutory Reference: <b>{c.regulation_reference || "DEMO / CONFIGURED RULE"}</b>
                      </div>
                      <div>
                        Source Measurement: <span className="font-mono text-stone-800">{c.source_id}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Tab 4: Obligations & Schedules */}
        {activeTab === "obligations" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Statutory Obligations Card */}
            <div className="bg-white border border-stone-200 rounded p-5 shadow-xs space-y-4">
              <h3 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                STATUTORY ENVIRONMENTAL OBLIGATIONS (CTO / EC CLEARANCES)
              </h3>

              <div className="space-y-3">
                {obligations.map((ob) => (
                  <div key={ob.obligation_id} className="p-3 bg-stone-50 border border-stone-200 rounded">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-xs text-stone-900">{ob.code}</span>
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
                        {ob.frequency}
                      </span>
                    </div>
                    <div className="font-bold text-xs text-stone-900 mt-1">{ob.title}</div>
                    <div className="text-[11px] text-stone-600 mt-0.5">{ob.description}</div>
                    <div className="mt-2 pt-1.5 border-t border-stone-200 text-[10px] text-stone-500 flex justify-between">
                      <span>Source: <b>{ob.regulatory_source}</b></span>
                      <span>Role: <b>{ob.responsible_role}</b></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Monitoring Schedules */}
            <div className="bg-white border border-stone-200 rounded p-5 shadow-xs space-y-4">
              <h3 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                MONITORING CALENDAR & ACTIVE SCHEDULES
              </h3>

              <div className="space-y-2">
                {schedules.map((sc) => (
                  <div key={sc.schedule_id} className="p-2.5 bg-stone-50 border border-stone-200 rounded flex items-center justify-between">
                    <div>
                      <div className="font-mono text-xs font-bold text-stone-900">{sc.schedule_id}</div>
                      <div className="text-[11px] text-stone-600 mt-0.5">
                        Due: <b>{sc.due_date}</b> · Role: {sc.responsible_role}
                      </div>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        sc.status === "VERIFIED"
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : sc.status === "NON_COMPLIANT"
                          ? "bg-rose-100 text-rose-800 border border-rose-300"
                          : "bg-amber-100 text-amber-800 border border-amber-300"
                      }`}
                    >
                      {sc.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Traceable Regulatory Reports */}
        {activeTab === "reports" && (
          <div className="bg-white border border-stone-200 rounded p-5 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                  STATUTORY REGULATORY DOSSIERS & CRYPTOGRAPHIC LEDGER
                </h3>
                <p className="text-[11px] text-stone-500">
                  Every finalized dossier incorporates SHA-256 cryptographic digest, IPFS content identifier, and complete organizational lineage to Ministry of Coal.
                </p>
              </div>

              <button
                onClick={() => setShowReportModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-stone-800 hover:bg-stone-900 text-white text-xs font-semibold rounded shadow-xs transition-colors cursor-pointer self-start sm:self-auto"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Generate Dossier</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-stone-100 text-stone-600 uppercase text-[10px] tracking-wider border-b border-stone-200">
                  <tr>
                    <th className="py-2.5 px-3">Report ID</th>
                    <th className="py-2.5 px-3">Reporting Period</th>
                    <th className="py-2.5 px-3">Title</th>
                    <th className="py-2.5 px-3">Measurements</th>
                    <th className="py-2.5 px-3">Violations</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Cryptographic Seal</th>
                    <th className="py-2.5 px-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-200 font-sans">
                  {reports.map((r) => (
                    <tr key={r.report_id} className="hover:bg-stone-50 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-stone-900">{r.report_id}</td>
                      <td className="py-2.5 px-3 text-stone-600">
                        {r.reporting_period_start} to {r.reporting_period_end}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-stone-900">{r.title}</td>
                      <td className="py-2.5 px-3 font-mono">{r.measurements_count}</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-red-700">{r.violations_count}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            r.status === "FINALIZED"
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                              : "bg-stone-100 text-stone-800 border border-stone-300"
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[10px]">
                        {r.content_hash ? (
                          <div className="flex items-center gap-1 text-emerald-700">
                            <Lock className="w-3 h-3" />
                            <span>{r.content_hash.substring(0, 10)}...</span>
                          </div>
                        ) : (
                          <span className="text-stone-400">Pending finalization</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setViewReport(r)}
                            className="text-xs font-semibold text-emerald-800 hover:text-emerald-900 cursor-pointer"
                          >
                            Inspect
                          </button>
                          {r.status !== "FINALIZED" && (
                            <button
                              onClick={() => handleFinalizeReport(r.report_id)}
                              className="px-2 py-0.5 bg-red-800 hover:bg-red-900 text-white rounded text-[10px] font-semibold cursor-pointer"
                            >
                              Finalize & Sign
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* MODAL 1: Record Measurement */}
      {showRecordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg shadow-xl border border-stone-300 max-w-lg w-full p-6 text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200">
              <h3 className="text-sm font-bold text-stone-900 uppercase tracking-wider flex items-center gap-2">
                <Plus className="w-4 h-4 text-emerald-800" />
                Record Environmental Field Measurement
              </h3>
              <button
                onClick={() => setShowRecordModal(false)}
                className="text-stone-400 hover:text-stone-700 text-lg font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleRecordSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block font-bold text-stone-700 mb-1">Environmental Parameter</label>
                <select
                  value={newMeasurement.parameter_id}
                  onChange={(e) => {
                    const pid = e.target.value;
                    const p = parameters.find((x) => x.id === pid);
                    setNewMeasurement((prev) => ({
                      ...prev,
                      parameter_id: pid,
                      unit: p ? p.unit : prev.unit,
                    }));
                  }}
                  required
                  className="w-full bg-stone-50 border border-stone-300 rounded p-2 text-xs focus:ring-1 focus:ring-emerald-700"
                >
                  <option value="">-- Select Monitored Parameter --</option>
                  {parameters.map((p) => (
                    <option key={p.id} value={p.id}>
                      [{p.domain}] {p.name} ({p.unit}) — {p.mine_type_applicability}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Observed Value</label>
                  <input
                    type="number"
                    step="any"
                    value={newMeasurement.value}
                    onChange={(e) => setNewMeasurement((prev) => ({ ...prev, value: parseFloat(e.target.value) }))}
                    required
                    className="w-full bg-stone-50 border border-stone-300 rounded p-2 text-xs font-mono font-bold"
                  />
                </div>
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Unit of Measurement</label>
                  <input
                    type="text"
                    value={newMeasurement.unit}
                    onChange={(e) => setNewMeasurement((prev) => ({ ...prev, unit: e.target.value }))}
                    required
                    className="w-full bg-stone-50 border border-stone-300 rounded p-2 text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-stone-700 mb-1">Operational Unit / Work Zone</label>
                <input
                  type="text"
                  placeholder="e.g. OP-ROAD-TALCHER-01 or Pit Head"
                  value={newMeasurement.operational_unit_id || ""}
                  onChange={(e) => setNewMeasurement((prev) => ({ ...prev, operational_unit_id: e.target.value }))}
                  className="w-full bg-stone-50 border border-stone-300 rounded p-2 text-xs"
                />
              </div>

              <div>
                <label className="block font-bold text-stone-700 mb-1">Instrument / Source Reference</label>
                <input
                  type="text"
                  value={newMeasurement.source_reference || ""}
                  onChange={(e) => setNewMeasurement((prev) => ({ ...prev, source_reference: e.target.value }))}
                  className="w-full bg-stone-50 border border-stone-300 rounded p-2 text-xs"
                />
              </div>

              <div className="flex items-center gap-2 p-2 bg-stone-100 rounded border border-stone-200">
                <input
                  type="checkbox"
                  id="simCheck"
                  checked={newMeasurement.simulated}
                  onChange={(e) => setNewMeasurement((prev) => ({ ...prev, simulated: e.target.checked }))}
                  className="cursor-pointer"
                />
                <label htmlFor="simCheck" className="text-[11px] text-stone-700 cursor-pointer font-medium">
                  Mark as DEMO / SIMULATED Record (Statutory Transparency)
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-stone-200">
                <button
                  type="button"
                  onClick={() => setShowRecordModal(false)}
                  className="px-4 py-2 border border-stone-300 rounded text-stone-600 hover:bg-stone-100 cursor-pointer font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white rounded font-bold shadow-xs cursor-pointer"
                >
                  Verify & Record Measurement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Generate Statutory Report */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg shadow-xl border border-stone-300 max-w-lg w-full p-6 text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200">
              <h3 className="text-sm font-bold text-stone-900 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-stone-800" />
                Generate Statutory Environmental Dossier
              </h3>
              <button
                onClick={() => setShowReportModal(false)}
                className="text-stone-400 hover:text-stone-700 text-lg font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleGenerateReport} className="mt-4 space-y-4">
              <div>
                <label className="block font-bold text-stone-700 mb-1">Dossier Title</label>
                <input
                  type="text"
                  value={newReport.title}
                  onChange={(e) => setNewReport((prev) => ({ ...prev, title: e.target.value }))}
                  required
                  className="w-full bg-stone-50 border border-stone-300 rounded p-2 text-xs font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Period Start Date</label>
                  <input
                    type="date"
                    value={newReport.reporting_period_start}
                    onChange={(e) => setNewReport((prev) => ({ ...prev, reporting_period_start: e.target.value }))}
                    required
                    className="w-full bg-stone-50 border border-stone-300 rounded p-2 text-xs"
                  />
                </div>
                <div>
                  <label className="block font-bold text-stone-700 mb-1">Period End Date</label>
                  <input
                    type="date"
                    value={newReport.reporting_period_end}
                    onChange={(e) => setNewReport((prev) => ({ ...prev, reporting_period_end: e.target.value }))}
                    required
                    className="w-full bg-stone-50 border border-stone-300 rounded p-2 text-xs"
                  />
                </div>
              </div>

              <div className="p-3 bg-stone-50 border border-stone-200 rounded text-[11px] text-stone-600">
                <b>Automatic Lineage Inclusion:</b> The generated dossier will bundle all authoritative records in the selected window, freeze an upward organizational lineage snapshot (to Ministry of Coal), and compute source hashes for audit integrity.
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-stone-200">
                <button
                  type="button"
                  onClick={() => setShowReportModal(false)}
                  className="px-4 py-2 border border-stone-300 rounded text-stone-600 hover:bg-stone-100 cursor-pointer font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-stone-800 hover:bg-stone-900 text-white rounded font-bold shadow-xs cursor-pointer"
                >
                  Generate Statutory Report
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Inspect Report with Cryptographic Lineage */}
      {viewReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-lg shadow-xl border border-stone-300 max-w-2xl w-full p-6 text-xs max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200">
              <div>
                <span className="font-mono text-[10px] text-stone-500 uppercase">{viewReport.report_id}</span>
                <h3 className="text-sm font-bold text-stone-900 mt-0.5">{viewReport.title}</h3>
              </div>
              <button
                onClick={() => setViewReport(null)}
                className="text-stone-400 hover:text-stone-700 text-lg font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="mt-4 space-y-4">
              {/* Status & Counts */}
              <div className="grid grid-cols-4 gap-2 text-center">
                <div className="p-2 bg-stone-50 border border-stone-200 rounded">
                  <div className="text-[10px] text-stone-500">PERIOD</div>
                  <div className="font-bold text-stone-900 mt-0.5">{viewReport.reporting_period_start}</div>
                </div>
                <div className="p-2 bg-stone-50 border border-stone-200 rounded">
                  <div className="text-[10px] text-stone-500">MEASUREMENTS</div>
                  <div className="font-bold text-stone-900 mt-0.5">{viewReport.measurements_count}</div>
                </div>
                <div className="p-2 bg-stone-50 border border-stone-200 rounded">
                  <div className="text-[10px] text-stone-500">VIOLATIONS</div>
                  <div className="font-bold text-red-700 mt-0.5">{viewReport.violations_count}</div>
                </div>
                <div className="p-2 bg-stone-50 border border-stone-200 rounded">
                  <div className="text-[10px] text-stone-500">SEAL STATUS</div>
                  <div className="font-bold text-emerald-800 mt-0.5">{viewReport.status}</div>
                </div>
              </div>

              {/* Cryptographic Ledger Verification Box */}
              <div className="p-3 bg-stone-900 text-white rounded font-mono text-[11px] space-y-2">
                <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5" />
                  <span>CRYPTOGRAPHIC VERIFICATION SEAL</span>
                </div>
                <div>
                  <span className="text-stone-400">SHA-256 Digest: </span>
                  <span className="text-amber-300 break-all">{viewReport.content_hash || "Unsealed"}</span>
                </div>
                <div>
                  <span className="text-stone-400">IPFS Immutable CID: </span>
                  <span className="text-emerald-300 break-all">{viewReport.ipfs_cid || "Unsealed"}</span>
                </div>
                <div>
                  <span className="text-stone-400">Signatory: </span>
                  <span>{viewReport.finalized_by || viewReport.generated_by}</span>
                </div>
              </div>

              {/* Canonical Lineage Snapshot */}
              <div>
                <h4 className="font-bold text-stone-800 mb-1 uppercase text-[11px] tracking-wider">
                  CANONICAL ORGANIZATIONAL LINEAGE SNAPSHOT
                </h4>
                <div className="bg-stone-50 p-3 rounded border border-stone-200 text-stone-700 font-mono text-[11px] space-y-1">
                  {viewReport.lineage_snapshot ? (
                    (() => {
                      try {
                        const lin = JSON.parse(viewReport.lineage_snapshot);
                        return (
                          <div>
                            <div>MINISTRY: {lin.ministry?.name} ({lin.ministry?.id})</div>
                            <div>HOLDING: {lin.holding_company?.name} ({lin.holding_company?.id})</div>
                            <div>SUBSIDIARY: {lin.subsidiary?.name} ({lin.subsidiary?.id})</div>
                            <div>AREA: {lin.area?.name} ({lin.area?.id})</div>
                            <div>MINE: {lin.mine?.name} ({lin.mine?.id})</div>
                          </div>
                        );
                      } catch {
                        return <div>{viewReport.lineage_snapshot}</div>;
                      }
                    })()
                  ) : (
                    <div>Lineage snapshot recorded at finalization.</div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-2 pt-3 border-t border-stone-200">
                {viewReport.status !== "FINALIZED" && (
                  <button
                    onClick={() => handleFinalizeReport(viewReport.report_id)}
                    className="px-4 py-2 bg-red-800 hover:bg-red-900 text-white rounded font-bold shadow-xs cursor-pointer"
                  >
                    Finalize & Cryptographically Sign
                  </button>
                )}
                <button
                  onClick={() => setViewReport(null)}
                  className="px-4 py-2 border border-stone-300 rounded text-stone-600 hover:bg-stone-100 cursor-pointer font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnvironmentGovernance;
