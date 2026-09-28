import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
    fetchLatestMineTelemetry,
    fetchMineTelemetryHistory,
    fetchMineSafetySignals,
    fetchTelemetryHealth,
    postTelemetryBatch,
    type TelemetryReading,
    type SafetySignal,
    type TelemetryHealth,
} from "../api/telemetry";
import {
    Activity,
    ShieldAlert,
    CheckCircle2,
    Clock,
    Flame,
    Wind,
    Fan,
    CloudRain,
    Mountain,
    Gauge,
    Sparkles,
    RefreshCw,
    ExternalLink,
    Radio,
    Play,
    Layers,
    Cpu,
} from "lucide-react";

interface MineOption {
    id: string;
    name: string;
    type: string;
}

const MINES: MineOption[] = [
    { id: "MINE-BCCL-JHARIA-01", name: "Jharia Underground Demonstration Mine", type: "Underground Coal (Degree II Gassy)" },
    { id: "MINE-ECL-RANIGANJ-01", name: "Raniganj Underground Demonstration Mine", type: "Underground Mechanised (Degree I)" },
    { id: "MINE-MCL-TALCHER-01", name: "Talcher Opencast Demonstration Mine", type: "Opencast Mechanised Coal" },
];

// Presets for rapid evaluator demonstration
const SIMULATION_SCENARIOS = [
    {
        id: "normal",
        name: "Normal Baseline",
        desc: "All sensors within CMR 2017 safe operating limits",
        color: "bg-emerald-900/40 text-emerald-300 border-emerald-700/50 hover:bg-emerald-800/50",
        readings: [
            { sensor_type: "METHANE", value: 0.32, unit: "%" },
            { sensor_type: "AIRFLOW", value: 32.5, unit: "m³/s" },
            { sensor_type: "VENTILATION_FAN", value: 1450.0, unit: "RPM" },
            { sensor_type: "DUST", value: 1.4, unit: "mg/m³" },
            { sensor_type: "SLOPE_DISPLACEMENT", value: 4.5, unit: "mm" },
            { sensor_type: "PORE_PRESSURE", value: 110.0, unit: "kPa" },
            { sensor_type: "RAINFALL", value: 2.0, unit: "mm/hr" },
        ],
    },
    {
        id: "warning",
        name: "Advisory Warning",
        desc: "Methane elevation and reduced airflow approaching statutory limits",
        color: "bg-amber-900/40 text-amber-300 border-amber-700/50 hover:bg-amber-800/50",
        readings: [
            { sensor_type: "METHANE", value: 0.88, unit: "%" },
            { sensor_type: "AIRFLOW", value: 17.5, unit: "m³/s" },
            { sensor_type: "VENTILATION_FAN", value: 1100.0, unit: "RPM" },
            { sensor_type: "DUST", value: 2.4, unit: "mg/m³" },
            { sensor_type: "SLOPE_DISPLACEMENT", value: 28.0, unit: "mm" },
            { sensor_type: "PORE_PRESSURE", value: 280.0, unit: "kPa" },
            { sensor_type: "RAINFALL", value: 18.0, unit: "mm/hr" },
        ],
    },
    {
        id: "critical_methane",
        name: "CMR Reg 153 Methane Breach",
        desc: "Methane reaches 1.68% (> 1.25% withdrawal limit) — Triggers Incident & Case",
        color: "bg-rose-900/40 text-rose-300 border-rose-700/50 hover:bg-rose-800/50",
        readings: [
            { sensor_type: "METHANE", value: 1.68, unit: "%" },
            { sensor_type: "AIRFLOW", value: 16.0, unit: "m³/s" },
            { sensor_type: "VENTILATION_FAN", value: 1250.0, unit: "RPM" },
            { sensor_type: "DUST", value: 1.8, unit: "mg/m³" },
            { sensor_type: "SLOPE_DISPLACEMENT", value: 5.0, unit: "mm" },
            { sensor_type: "PORE_PRESSURE", value: 120.0, unit: "kPa" },
            { sensor_type: "RAINFALL", value: 3.0, unit: "mm/hr" },
        ],
    },
    {
        id: "critical_ventilation",
        name: "CMR Reg 154 Fan Failure",
        desc: "Ventilation fan drops to 520 RPM & airflow to 9.2 m³/s (< 15 m³/s statutory minimum)",
        color: "bg-rose-900/40 text-rose-300 border-rose-700/50 hover:bg-rose-800/50",
        readings: [
            { sensor_type: "METHANE", value: 0.95, unit: "%" },
            { sensor_type: "AIRFLOW", value: 9.2, unit: "m³/s" },
            { sensor_type: "VENTILATION_FAN", value: 520.0, unit: "RPM" },
            { sensor_type: "DUST", value: 2.7, unit: "mg/m³" },
            { sensor_type: "SLOPE_DISPLACEMENT", value: 5.0, unit: "mm" },
            { sensor_type: "PORE_PRESSURE", value: 110.0, unit: "kPa" },
            { sensor_type: "RAINFALL", value: 1.0, unit: "mm/hr" },
        ],
    },
    {
        id: "critical_slope",
        name: "Highwall Slope Slip",
        desc: "Highwall slope displacement exceeds 50 mm bench failure limit",
        color: "bg-rose-900/40 text-rose-300 border-rose-700/50 hover:bg-rose-800/50",
        readings: [
            { sensor_type: "METHANE", value: 0.20, unit: "%" },
            { sensor_type: "AIRFLOW", value: 32.0, unit: "m³/s" },
            { sensor_type: "VENTILATION_FAN", value: 1450.0, unit: "RPM" },
            { sensor_type: "DUST", value: 1.5, unit: "mg/m³" },
            { sensor_type: "SLOPE_DISPLACEMENT", value: 62.5, unit: "mm" },
            { sensor_type: "PORE_PRESSURE", value: 430.0, unit: "kPa" },
            { sensor_type: "RAINFALL", value: 46.0, unit: "mm/hr" },
        ],
    },
    {
        id: "recovery",
        name: "Restoration & Recovery",
        desc: "Sensors normalize — active signals mark recovered, cases remain open for human review",
        color: "bg-blue-900/40 text-blue-300 border-blue-700/50 hover:bg-blue-800/50",
        readings: [
            { sensor_type: "METHANE", value: 0.35, unit: "%" },
            { sensor_type: "AIRFLOW", value: 34.0, unit: "m³/s" },
            { sensor_type: "VENTILATION_FAN", value: 1470.0, unit: "RPM" },
            { sensor_type: "DUST", value: 1.2, unit: "mg/m³" },
            { sensor_type: "SLOPE_DISPLACEMENT", value: 6.0, unit: "mm" },
            { sensor_type: "PORE_PRESSURE", value: 125.0, unit: "kPa" },
            { sensor_type: "RAINFALL", value: 1.5, unit: "mm/hr" },
        ],
    },
];

const SENSOR_META: Record<string, { label: string; icon: any; statutoryRef: string; limits: string }> = {
    METHANE: {
        label: "Methane Concentration",
        icon: Flame,
        statutoryRef: "CMR 2017 Reg 119 & 156",
        limits: "Safe < 0.8% | Warn 0.8–1.25% | Crit ≥ 1.25%",
    },
    AIRFLOW: {
        label: "Airflow Velocity",
        icon: Wind,
        statutoryRef: "CMR 2017 Reg 119 Dilution",
        limits: "Safe ≥ 15 m³/s | Warn 8–15 | Crit < 8 m³/s",
    },
    VENTILATION_FAN: {
        label: "Ventilation Fan",
        icon: Fan,
        statutoryRef: "CMR 2017 Reg 154 Exhaust",
        limits: "Safe ≥ 1200 RPM | Warn 800–1200 | Crit < 800 RPM",
    },
    DUST: {
        label: "Respirable Dust",
        icon: Activity,
        statutoryRef: "CMR 2017 Reg 124 Airway Quality",
        limits: "Safe < 2.0 mg/m³ | Warn 2.0–3.0 | Crit ≥ 3.0 mg/m³",
    },
    SLOPE_DISPLACEMENT: {
        label: "Slope Displacement",
        icon: Mountain,
        statutoryRef: "Highwall Stability Directive",
        limits: "Safe < 25 mm | Warn 25–50 mm | Crit ≥ 50 mm",
    },
    PORE_PRESSURE: {
        label: "Pore Pressure",
        icon: Gauge,
        statutoryRef: "Hydrostatic Barrier Safety",
        limits: "Safe < 250 kPa | Warn 250–400 kPa | Crit ≥ 400 kPa",
    },
    RAINFALL: {
        label: "Rainfall Rate",
        icon: CloudRain,
        statutoryRef: "Pit Inundation Protection",
        limits: "Safe < 15 mm/hr | Warn 15–40 | Crit ≥ 40 mm/hr",
    },
};

export default function SafetyIntelligence() {
    const [selectedMine, setSelectedMine] = useState<string>("MINE-BCCL-JHARIA-01");
    const [latestReadings, setLatestReadings] = useState<TelemetryReading[]>([]);
    const [safetySignals, setSafetySignals] = useState<SafetySignal[]>([]);
    const [telemetryHistory, setTelemetryHistory] = useState<TelemetryReading[]>([]);
    const [health, setHealth] = useState<TelemetryHealth | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [simulating, setSimulating] = useState<boolean>(false);
    const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
    const [simResultMsg, setSimResultMsg] = useState<string | null>(null);

    const loadData = useCallback(async () => {
        try {
            const [readings, signals, hist, h] = await Promise.all([
                fetchLatestMineTelemetry(selectedMine),
                fetchMineSafetySignals(selectedMine, false),
                fetchMineTelemetryHistory(selectedMine, 20),
                fetchTelemetryHealth(),
            ]);
            setLatestReadings(readings || []);
            setSafetySignals(signals || []);
            setTelemetryHistory(hist || []);
            setHealth(h || null);
        } catch (err) {
            console.error("Failed to load telemetry intelligence:", err);
        } finally {
            setLoading(false);
        }
    }, [selectedMine]);

    useEffect(() => {
        setLoading(true);
        loadData();
    }, [loadData]);

    useEffect(() => {
        if (!autoRefresh) return;
        const timer = setInterval(() => {
            loadData();
        }, 4000);
        return () => clearInterval(timer);
    }, [autoRefresh, loadData]);

    const handleInjectScenario = async (scenario: (typeof SIMULATION_SCENARIOS)[0]) => {
        setSimulating(true);
        setSimResultMsg(null);
        try {
            const batch = scenario.readings.map((r) => ({
                mine_id: selectedMine,
                sensor_type: r.sensor_type,
                value: r.value,
                unit: r.unit,
                quality: "GOOD",
                simulated: true,
            }));
            const res = await postTelemetryBatch(batch);
            setSimResultMsg(
                `✓ Ingested ${res.ingested_count} readings. Critical Signals: ${res.critical_signals_count}, Cases Created: ${res.new_cases_created}`
            );
            await loadData();
        } catch (err: any) {
            setSimResultMsg(`✗ Injection error: ${err.message}`);
        } finally {
            setSimulating(false);
        }
    };

    const activeSignals = safetySignals.filter((s) => s.status === "ACTIVE");
    const recoveredSignals = safetySignals.filter((s) => s.status === "RECOVERED");

    return (
        <div className="gov-container scada-intel-page">
            {/* TOP NOTICE: EXPLICIT SIMULATION DISCLAIMER */}
            <div className="scada-sim-banner">
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{ padding: "8px", borderRadius: "6px", backgroundColor: "#FEF3C7", color: "#D97706" }}>
                        <Radio size={20} className="gov-pulse-dot" />
                    </div>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span className="scada-sim-badge">
                                SIMULATED SCADA TELEMETRY
                            </span>
                            <span style={{ fontSize: "11px", color: "#92400E", fontFamily: "monospace" }}>
                                [Explicitly Simulated IoT Layer]
                            </span>
                        </div>
                        <p className="scada-sim-desc">
                            All sensor signals and threshold evaluations originate from the independent PRITHVI SCADA Telemetry Simulator.
                            Demonstrates real-time statutory compliance surveillance under Coal Mines Regulations, 2017 without physical underground PLC connection.
                        </p>
                    </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <label style={{ fontSize: "12px", color: "#6B7280", display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                        />
                        <span>Auto-poll (4s)</span>
                    </label>
                    <button
                        type="button"
                        onClick={() => loadData()}
                        disabled={loading}
                        className="gov-btn-secondary"
                        style={{ padding: "6px 12px", fontSize: "12px" }}
                    >
                        <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
                        <span>Refresh</span>
                    </button>
                </div>
            </div>

            {/* HEADER & MINE SELECTOR */}
            <div className="scada-header-row">
                <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: "700", color: "var(--gov-red)", textTransform: "uppercase" }}>
                        <Cpu size={14} />
                        <span>Industrial IoT Surveillance — Task 9</span>
                    </div>
                    <h1 className="scada-header-title">
                        SCADA Telemetry &amp; Mine Safety Intelligence
                    </h1>
                    <p className="scada-header-sub">
                        Statutory threshold surveillance, multi-hazard telemetry detection, and autonomous incident case synthesis.
                    </p>
                </div>

                <div className="scada-mine-selector">
                    <span style={{ fontSize: "12px", fontWeight: "700", color: "#4B5563" }}>Mine:</span>
                    <select
                        value={selectedMine}
                        onChange={(e) => setSelectedMine(e.target.value)}
                    >
                        {MINES.map((m) => (
                            <option key={m.id} value={m.id}>
                                {m.name} ({m.id})
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* SYSTEM STATUS & HEALTH STRIP */}
            <div className="scada-kpi-grid">
                <div className="scada-kpi-card">
                    <div className="scada-kpi-label">
                        <span>Telemetry Stream</span>
                        <span style={{ color: "var(--status-success)", fontWeight: "800", display: "flex", alignItems: "center", gap: "4px" }}>
                            <Activity size={12} className="gov-pulse-dot" /> ACTIVE
                        </span>
                    </div>
                    <div className="scada-kpi-val">
                        {health?.sensors_reporting_live ?? latestReadings.length}
                    </div>
                    <div className="scada-kpi-sub">
                        Protocol: REST Telemetry Stream / SCADA Sim
                    </div>
                </div>

                <div className="scada-kpi-card">
                    <div className="scada-kpi-label">
                        <span>Active Safety Signals</span>
                        <ShieldAlert size={14} style={{ color: activeSignals.length > 0 ? "var(--status-critical)" : "#9CA3AF" }} />
                    </div>
                    <div className="scada-kpi-val" style={{ color: activeSignals.length > 0 ? "var(--status-critical)" : "var(--status-success)" }}>
                        {activeSignals.length}
                    </div>
                    <div className="scada-kpi-sub">
                        {recoveredSignals.length} signals normalized historically
                    </div>
                </div>

                <div className="scada-kpi-card">
                    <div className="scada-kpi-label">
                        <span>Total Stored Readings</span>
                    </div>
                    <div className="scada-kpi-val">
                        {health?.total_readings_stored ?? "—"}
                    </div>
                    <div className="scada-kpi-sub">
                        Persisted in SQLite database
                    </div>
                </div>

                <div className="scada-kpi-card">
                    <div className="scada-kpi-label">
                        <span>Last Signal Ingestion</span>
                    </div>
                    <div className="scada-kpi-val" style={{ fontSize: "16px", marginTop: "12px", fontFamily: "monospace" }}>
                        {health?.last_telemetry_timestamp
                            ? new Date(health.last_telemetry_timestamp).toLocaleTimeString()
                            : "Awaiting pulses"}
                    </div>
                    <div className="scada-kpi-sub">
                        {health?.last_telemetry_timestamp
                            ? new Date(health.last_telemetry_timestamp).toLocaleDateString()
                            : "No recent packets"}
                    </div>
                </div>
            </div>

            {/* INTERACTIVE SCADA SIMULATOR CONSOLE */}
            <div className="scada-console-box">
                <div className="scada-console-header">
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <div style={{ padding: "6px", borderRadius: "4px", backgroundColor: "#EFF6FF", color: "var(--status-info)" }}>
                            <Sparkles size={18} />
                        </div>
                        <div>
                            <h2 style={{ fontSize: "13px", fontWeight: "800", textTransform: "uppercase", margin: 0, color: "#1F2937" }}>
                                Interactive SCADA Simulator Console
                            </h2>
                            <p style={{ fontSize: "11px", color: "#6B7280", margin: "2px 0 0 0" }}>
                                Single-click telemetry injection to evaluate PRITHVI's autonomous statutory alert &amp; case synthesis workflow.
                            </p>
                        </div>
                    </div>
                    {simResultMsg && (
                        <div style={{ fontSize: "11px", padding: "4px 8px", borderRadius: "4px", backgroundColor: "#F3F4F6", color: "#1F2937", border: "1px solid #E5E7EB" }}>
                            {simResultMsg}
                        </div>
                    )}
                </div>

                <div className="scada-scenario-grid">
                    {SIMULATION_SCENARIOS.map((sc) => (
                        <button
                            key={sc.id}
                            type="button"
                            onClick={() => handleInjectScenario(sc)}
                            disabled={simulating}
                            className={`scada-scenario-btn ${
                                sc.id.includes("methane") || sc.id.includes("airflow") ? "active-critical" : sc.id.includes("warning") ? "active-warning" : ""
                            }`}
                        >
                            <div className="scada-scenario-name">
                                <span>{sc.name}</span>
                                <Play size={11} style={{ opacity: 0.7 }} />
                            </div>
                            <p className="scada-scenario-desc">
                                {sc.desc}
                            </p>
                        </button>
                    ))}
                </div>
            </div>

            {/* 7 INDUSTRIAL TELEMETRY SENSOR CARDS */}
            <div style={{ marginBottom: "28px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
                    <div>
                        <h2 style={{ fontSize: "16px", fontWeight: "800", color: "#111827", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                            <Layers size={16} style={{ color: "var(--gov-red)" }} />
                            <span>Live Industrial Safety Telemetry</span>
                        </h2>
                        <p style={{ fontSize: "12px", color: "#6B7280", margin: "2px 0 0 0" }}>
                            Evaluated continuously against statutory Coal Mines Regulations (2017) and geotechnical thresholds.
                        </p>
                    </div>
                    <span style={{ fontSize: "11px", fontFamily: "monospace", color: "#6B7280" }}>
                        {latestReadings.length} sensors active for this mine
                    </span>
                </div>

                <div className="scada-sensor-grid">
                    {latestReadings.map((reading) => {
                        const meta = SENSOR_META[reading.sensor_type] || {
                            label: reading.sensor_type,
                            icon: Activity,
                            statutoryRef: "Safety Regulation",
                            limits: "Statutory threshold",
                        };
                        const Icon = meta.icon;

                        const isCritical = reading.threshold_status === "CRITICAL";
                        const isWarning = reading.threshold_status === "WARNING";

                        let cardClass = "scada-sensor-card";
                        if (isCritical) {
                            cardClass += " is-critical";
                        } else if (isWarning) {
                            cardClass += " is-warning";
                        }

                        return (
                            <div
                                key={reading.reading_id}
                                className={cardClass}
                            >
                                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "8px" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                        <div style={{ padding: "6px", borderRadius: "6px", backgroundColor: isCritical ? "#FEE2E2" : isWarning ? "#FEF3C7" : "#DCFCE7", color: isCritical ? "#B91C1C" : isWarning ? "#B45309" : "#15803D" }}>
                                            <Icon size={18} />
                                        </div>
                                        <div>
                                            <div style={{ fontSize: "12px", fontWeight: "800", color: "#1F2937" }}>
                                                {meta.label}
                                            </div>
                                            <div style={{ fontSize: "10px", fontFamily: "monospace", color: "#6B7280" }}>
                                                {reading.sensor_code || reading.sensor_id}
                                            </div>
                                        </div>
                                    </div>
                                    <span
                                        style={{
                                            fontSize: "9px",
                                            fontWeight: "800",
                                            textTransform: "uppercase",
                                            padding: "2px 6px",
                                            borderRadius: "4px",
                                            backgroundColor: isCritical ? "#FEE2E2" : isWarning ? "#FEF3C7" : "#DCFCE7",
                                            color: isCritical ? "#B91C1C" : isWarning ? "#B45309" : "#15803D",
                                            border: `1px solid ${isCritical ? "#FCA5A5" : isWarning ? "#FDE68A" : "#86EFAC"}`
                                        }}
                                    >
                                        {reading.threshold_status}
                                    </span>
                                </div>

                                <div style={{ marginTop: "14px", display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
                                    <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                                        <span style={{ fontSize: "28px", fontWeight: "800", fontFamily: "monospace", color: isCritical ? "#B91C1C" : isWarning ? "#B45309" : "#111827" }}>
                                            {typeof reading.value === "number"
                                                ? reading.value % 1 !== 0
                                                    ? reading.value.toFixed(2)
                                                    : reading.value
                                                : reading.value}
                                        </span>
                                        <span style={{ fontSize: "12px", fontWeight: "700", color: "#6B7280" }}>
                                            {reading.unit}
                                        </span>
                                    </div>
                                    <div style={{ fontSize: "10px", fontFamily: "monospace", color: "#6B7280" }}>
                                        {reading.zone_id || "Mine General"}
                                    </div>
                                </div>

                                <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid #F1F5F9", fontSize: "11px" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", color: "#475569" }}>
                                        <span style={{ fontWeight: "700", textTransform: "uppercase", fontSize: "9px", color: "#64748B" }}>Basis:</span>
                                        <span style={{ fontWeight: "600" }}>{meta.statutoryRef}</span>
                                    </div>
                                    <div style={{ fontSize: "10px", color: "#6B7280", marginTop: "2px" }}>
                                        {meta.limits}
                                    </div>
                                    <div style={{ fontSize: "10px", color: "#94A3B8", marginTop: "4px", display: "flex", justifyContent: "space-between", fontFamily: "monospace" }}>
                                        <span>Recorded:</span>
                                        <span>{new Date(reading.recorded_at).toLocaleTimeString()}</span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* ACTIVE & RECENT SAFETY SIGNALS */}
            <div className="scada-table-card">
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", paddingBottom: "10px", borderBottom: "1px solid #F1F5F9" }}>
                    <div>
                        <h2 style={{ fontSize: "15px", fontWeight: "800", color: "#111827", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                            <ShieldAlert size={16} style={{ color: "var(--gov-red)" }} />
                            <span>Safety Signals &amp; Autonomous Compliance Cases</span>
                        </h2>
                        <p style={{ fontSize: "11px", color: "#6B7280", margin: "2px 0 0 0" }}>
                            Explainable safety triggers generated from telemetry. Critical events synthesize formal Compliance Cases.
                        </p>
                    </div>
                    <span style={{ fontSize: "11px", fontWeight: "700", padding: "3px 8px", borderRadius: "4px", backgroundColor: "#F3F4F6", color: "#374151" }}>
                        Total Signals: {safetySignals.length}
                    </span>
                </div>

                {safetySignals.length === 0 ? (
                    <div style={{ padding: "36px 0", textAlign: "center", color: "#6B7280" }}>
                        <CheckCircle2 size={32} style={{ color: "#10B981", margin: "0 auto 8px auto" }} />
                        <p style={{ fontSize: "13px", fontWeight: "700", color: "#1F2937", margin: 0 }}>No Safety Signals Detected</p>
                        <p style={{ fontSize: "11px", color: "#6B7280", marginTop: "4px" }}>
                            All sensors reporting safe operational parameters. Use the Simulator Console above to test anomaly detection.
                        </p>
                    </div>
                ) : (
                    <div style={{ overflowX: "auto" }}>
                        <table className="scada-data-table">
                            <thead>
                                <tr>
                                    <th>Signal / Sensor</th>
                                    <th>Severity</th>
                                    <th>Status</th>
                                    <th>Observed Value</th>
                                    <th>Statutory Explanation</th>
                                    <th>First / Last Detected</th>
                                    <th style={{ textAlign: "right" }}>Compliance Case</th>
                                </tr>
                            </thead>
                            <tbody>
                                {safetySignals.map((sig) => {
                                    const isCrit = sig.severity === "CRITICAL";
                                    const isActive = sig.status === "ACTIVE";

                                    return (
                                        <tr key={sig.signal_id}>
                                            <td>
                                                <div style={{ fontFamily: "monospace", fontWeight: "800", color: "#111827" }}>{sig.signal_id}</div>
                                                <div style={{ fontSize: "10px", color: "#6B7280" }}>{sig.sensor_code || sig.sensor_id} ({sig.sensor_type})</div>
                                            </td>
                                            <td>
                                                <span
                                                    style={{
                                                        padding: "2px 6px",
                                                        borderRadius: "4px",
                                                        fontSize: "9px",
                                                        fontWeight: "800",
                                                        textTransform: "uppercase",
                                                        backgroundColor: isCrit ? "#FEE2E2" : "#FEF3C7",
                                                        color: isCrit ? "#B91C1C" : "#B45309",
                                                        border: `1px solid ${isCrit ? "#FCA5A5" : "#FDE68A"}`
                                                    }}
                                                >
                                                    {sig.severity}
                                                </span>
                                            </td>
                                            <td>
                                                <span
                                                    style={{
                                                        padding: "2px 6px",
                                                        borderRadius: "4px",
                                                        fontSize: "9px",
                                                        fontWeight: "800",
                                                        textTransform: "uppercase",
                                                        backgroundColor: isActive ? "#FEE2E2" : "#DBEAFE",
                                                        color: isActive ? "#B91C1C" : "#1D4ED8",
                                                        border: `1px solid ${isActive ? "#FCA5A5" : "#BFDBFE"}`
                                                    }}
                                                >
                                                    {isActive ? "ACTIVE" : "RECOVERED"}
                                                </span>
                                            </td>
                                            <td style={{ fontFamily: "monospace", fontWeight: "700" }}>
                                                {sig.observed_value} {sig.unit}
                                            </td>
                                            <td style={{ maxWidth: "340px", lineHeight: "1.4" }}>
                                                <div style={{ fontWeight: "600", color: "#1F2937" }}>{sig.explanation}</div>
                                                <div style={{ fontSize: "10px", color: "#64748B", marginTop: "2px" }}>Rule: {sig.threshold_definition}</div>
                                            </td>
                                            <td style={{ fontFamily: "monospace", fontSize: "11px", color: "#64748B" }}>
                                                <div>{new Date(sig.first_detected_at).toLocaleTimeString()}</div>
                                            </td>
                                            <td style={{ textAlign: "right" }}>
                                                {sig.linked_case_id ? (
                                                    <Link
                                                        to="/cases"
                                                        style={{ fontSize: "11px", fontWeight: "700", color: "var(--gov-red)", display: "inline-flex", alignItems: "center", gap: "4px" }}
                                                    >
                                                        <span>{sig.linked_case_id}</span>
                                                        <ExternalLink size={11} />
                                                    </Link>
                                                ) : (
                                                    <span style={{ fontSize: "11px", color: "#9CA3AF" }}>Advisory Only</span>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* RAW TELEMETRY TIMELINE LOG */}
            <div className="scada-table-card">
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px", paddingBottom: "8px", borderBottom: "1px solid #F1F5F9" }}>
                    <h2 style={{ fontSize: "14px", fontWeight: "800", color: "#111827", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                        <Clock size={15} style={{ color: "var(--gov-red)" }} />
                        <span>Recent Telemetry Log Stream (Audit Trail)</span>
                    </h2>
                    <span style={{ fontSize: "11px", color: "#6B7280", fontFamily: "monospace" }}>
                        Showing last {telemetryHistory.length} readings
                    </span>
                </div>

                <div style={{ overflowX: "auto", maxHeight: "240px", overflowY: "auto" }}>
                    <table className="scada-data-table" style={{ fontFamily: "monospace" }}>
                        <thead>
                            <tr>
                                <th>Reading ID</th>
                                <th>Sensor Type</th>
                                <th>Value</th>
                                <th>Status</th>
                                <th>Quality</th>
                                <th>Source</th>
                                <th style={{ textAlign: "right" }}>Recorded Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {telemetryHistory.map((item) => (
                                <tr key={item.reading_id}>
                                    <td style={{ fontWeight: "700" }}>{item.reading_id}</td>
                                    <td>{item.sensor_type}</td>
                                    <td style={{ fontWeight: "800" }}>{item.value} {item.unit}</td>
                                    <td>
                                        <span
                                            style={{
                                                padding: "1px 5px",
                                                borderRadius: "3px",
                                                fontSize: "9px",
                                                fontWeight: "800",
                                                backgroundColor: item.threshold_status === "CRITICAL" ? "#FEE2E2" : item.threshold_status === "WARNING" ? "#FEF3C7" : "#DCFCE7",
                                                color: item.threshold_status === "CRITICAL" ? "#B91C1C" : item.threshold_status === "WARNING" ? "#B45309" : "#15803D"
                                            }}
                                        >
                                            {item.threshold_status}
                                        </span>
                                    </td>
                                    <td style={{ color: "#15803D" }}>{item.quality_status}</td>
                                    <td style={{ color: "#6B7280" }}>{item.source}</td>
                                    <td style={{ textAlign: "right", color: "#6B7280" }}>
                                        {new Date(item.recorded_at).toLocaleTimeString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
