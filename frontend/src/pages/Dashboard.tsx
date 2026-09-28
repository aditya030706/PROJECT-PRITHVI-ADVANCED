import { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
    ShieldCheck,
    Clock3,
    AlertTriangle,
    FileCheck2,
    AlertOctagon,
    RefreshCw,
    ArrowRight,
    CheckCircle2,
    Activity,
    Wind,
    Cable,
    Zap,
    Truck,
    Flame,
    Shield,
    Droplets,
    ExternalLink,
    Filter,
    Repeat,
} from "lucide-react";
import {
    getMineComplianceSummary,
    getMineRisk,
    getMineRecurringCompliance,
    type MineComplianceSummary,
    type CategoryComplianceSummary,
    type AttentionItem,
    type MineRiskResponse,
    type CategoryRiskSummary,
    type RecurringComplianceIssue,
} from "../api/compliance";
import MineComplianceCrossSection from "../components/MineComplianceCrossSection";
import CompliancePipelineDiagram from "../components/CompliancePipelineDiagram";
import { fetchMineSafetySignals, type SafetySignal } from "../api/telemetry";

const JHARIA_MINE_ID = "MINE-BCCL-JHARIA-01";

function fmt(n?: number | null): string {
    if (n === undefined || n === null) return "--";
    return String(n).padStart(2, "0");
}

function formatDate(isoString?: string | null): string {
    if (!isoString) return "Not available";
    try {
        const d = new Date(isoString);
        return d.toLocaleString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: true,
        }).toUpperCase();
    } catch {
        return isoString;
    }
}

const CATEGORY_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
    "Ventilation & Gas": Wind,
    "Shaft & Winding": Cable,
    "Electrical": Zap,
    "HEMM": Truck,
    "Blasting": Flame,
    "Roof / Strata": Shield,
    "Water / Drainage": Droplets,
};

const CATEGORY_REGULATIONS: Record<string, string> = {
    "Ventilation & Gas": "CMR 2017, Reg 119, 156 (Ventilation & Gases)",
    "Shaft & Winding": "CMR 2017, Reg 75–80 (Shafts, Outlets & Winding)",
    "Electrical": "CMR 2017, Reg 160–170 (Flameproof Apparatus & Earthing)",
    "HEMM": "CMR 2017, Reg 135 (Heavy Earthmoving Machinery)",
    "Blasting": "CMR 2017, Reg 155–158 (Shotfiring & Danger Zones)",
    "Roof / Strata": "CMR 2017, Reg 85–95 (SCAMP & Support Plan)",
    "Water / Drainage": "CMR 2017, Reg 145 (Inundation & Pumping Stations)",
};

export default function Dashboard() {
    const navigate = useNavigate();
    const [summary, setSummary] = useState<MineComplianceSummary | null>(null);
    const [riskData, setRiskData] = useState<MineRiskResponse | null>(null);
    const [recurringIssues, setRecurringIssues] = useState<RecurringComplianceIssue[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [safetySignals, setSafetySignals] = useState<SafetySignal[]>([]);

    async function loadData(isRefresh = false) {
        if (isRefresh) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }
        setError(null);

        try {
            const [summaryRes, riskRes, recurringRes, signalsRes] = await Promise.all([
                getMineComplianceSummary(JHARIA_MINE_ID),
                getMineRisk(JHARIA_MINE_ID),
                getMineRecurringCompliance(JHARIA_MINE_ID),
                fetchMineSafetySignals(JHARIA_MINE_ID, true).catch(() => []),
            ]);
            setSummary(summaryRes);
            setRiskData(riskRes);
            setRecurringIssues(recurringRes);
            setSafetySignals(signalsRes || []);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to load mine compliance intelligence from server."
            );
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }

    useEffect(() => {
        void loadData();
    }, []);

    // Filtered categories if user selected a sector from the cross-section
    const displayCategories = useMemo(() => {
        if (!summary?.category_compliance) return [];
        if (!selectedCategory) return summary.category_compliance;
        return summary.category_compliance.filter(
            (c) => c.category.toLowerCase().trim() === selectedCategory.toLowerCase().trim()
        );
    }, [summary, selectedCategory]);

    // Risk badge helper for deterministic risk states
    function getRiskBadge(level?: string | null) {
        const l = (level || "LOW").toUpperCase();
        if (l === "CRITICAL") {
            return {
                label: "CRITICAL RISK",
                bg: "rgba(239, 68, 68, 0.15)",
                color: "#ef4444",
                border: "rgba(239, 68, 68, 0.4)",
                barColor: "#ef4444",
            };
        }
        if (l === "HIGH") {
            return {
                label: "HIGH RISK",
                bg: "rgba(248, 113, 113, 0.15)",
                color: "#f87171",
                border: "rgba(248, 113, 113, 0.4)",
                barColor: "#f87171",
            };
        }
        if (l === "MEDIUM") {
            return {
                label: "MEDIUM RISK",
                bg: "rgba(245, 158, 11, 0.15)",
                color: "#f59e0b",
                border: "rgba(245, 158, 11, 0.4)",
                barColor: "#f59e0b",
            };
        }
        if (l === "INSUFFICIENT_DATA") {
            return {
                label: "INSUFFICIENT DATA",
                bg: "#18181c",
                color: "#a1a1aa",
                border: "#27272e",
                barColor: "#3f3f46",
            };
        }
        return {
            label: "COMPLIANT / LOW",
            bg: "rgba(16, 185, 129, 0.12)",
            color: "#10b981",
            border: "rgba(16, 185, 129, 0.3)",
            barColor: "#10b981",
        };
    }

    // Priority badge helpers
    function getPriorityBadge(severity?: string | null) {
        const s = (severity || "LOW").toUpperCase();
        if (s === "CRITICAL") {
            return {
                label: "CRITICAL SEVERITY",
                bg: "rgba(239, 68, 68, 0.2)",
                color: "#ef4444",
                border: "rgba(239, 68, 68, 0.5)",
            };
        }
        if (s === "HIGH") {
            return {
                label: "HIGH SEVERITY",
                bg: "rgba(239, 68, 68, 0.15)",
                color: "#f87171",
                border: "rgba(239, 68, 68, 0.4)",
            };
        }
        if (s === "MEDIUM") {
            return {
                label: "MEDIUM SEVERITY",
                bg: "rgba(245, 158, 11, 0.15)",
                color: "#f59e0b",
                border: "rgba(245, 158, 11, 0.4)",
            };
        }
        return {
            label: "LOW SEVERITY",
            bg: "#18181c",
            color: "#a1a1aa",
            border: "#27272e",
        };
    }

    function getCategoryStatusBadge(status?: string | null) {
        const s = (status || "").toUpperCase();
        if (s === "CRITICAL_NON_COMPLIANCE") {
            return {
                label: "CRITICAL NON-COMPLIANCE",
                tone: "critical",
                dotColor: "#ef4444",
                color: "#fca5a5",
                bg: "rgba(239, 68, 68, 0.12)",
                border: "rgba(239, 68, 68, 0.3)",
            };
        }
        if (s === "ACTION_REQUIRED") {
            return {
                label: "ACTION REQUIRED",
                tone: "attention",
                dotColor: "#f59e0b",
                color: "#fde68a",
                bg: "rgba(245, 158, 11, 0.12)",
                border: "rgba(245, 158, 11, 0.3)",
            };
        }
        return {
            label: "COMPLIANT",
            tone: "compliant",
            dotColor: "#10b981",
            color: "#6ee7b7",
            bg: "rgba(16, 185, 129, 0.12)",
            border: "rgba(16, 185, 129, 0.3)",
        };
    }

    return (
        <div className="compliance-command-center">
            <style>{`
                .compliance-command-center {
                    background: #060608;
                    color: #ededed;
                    min-height: calc(100vh - 64px);
                    padding: 24px 32px 64px;
                    font-family: "DM Sans", -apple-system, sans-serif;
                }

                /* Top Hero Toolbar */
                .ccc-toolbar {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: 24px;
                    margin-bottom: 24px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #1c1c22;
                }

                .ccc-eyebrow {
                    font-family: "DM Mono", monospace;
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 0.14em;
                    color: #d0915f;
                    margin: 0 0 4px 0;
                    text-transform: uppercase;
                }

                .ccc-title-cluster h1 {
                    font-size: 26px;
                    font-weight: 800;
                    letter-spacing: -0.02em;
                    margin: 0;
                    color: #ffffff;
                    line-height: 1.2;
                }

                .ccc-mine-name {
                    font-size: 14px;
                    font-weight: 700;
                    color: #d4d4d8;
                    margin-top: 4px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .ccc-mine-tags {
                    display: flex;
                    gap: 6px;
                    margin-top: 10px;
                    flex-wrap: wrap;
                }

                .ccc-tag {
                    font-family: "DM Mono", monospace;
                    font-size: 9px;
                    font-weight: 600;
                    padding: 3px 8px;
                    background: #0e0e11;
                    border: 1px solid #222226;
                    border-radius: 2px;
                    color: #8c8c96;
                    letter-spacing: 0.04em;
                }

                .ccc-controls {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    gap: 10px;
                }

                .ccc-asof {
                    font-family: "DM Mono", monospace;
                    font-size: 10px;
                    color: #71717a;
                    letter-spacing: 0.05em;
                }

                .ccc-refresh-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    background: #0f0f12;
                    border: 1px solid #25252b;
                    color: #ededed;
                    padding: 8px 16px;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.06em;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .ccc-refresh-btn:hover:not(:disabled) {
                    background: #17171c;
                    border-color: #d0915f;
                    color: #ffffff;
                }

                .ccc-refresh-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                /* Error Card */
                .ccc-error-banner {
                    background: rgba(239, 68, 68, 0.08);
                    border: 1px solid rgba(239, 68, 68, 0.25);
                    border-radius: 4px;
                    padding: 16px 20px;
                    margin-bottom: 24px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    color: #fca5a5;
                }

                /* KPI Strip (Top Real Metrics) */
                .ccc-kpis {
                    display: grid;
                    grid-template-columns: repeat(5, 1fr);
                    gap: 14px;
                    margin-bottom: 24px;
                }

                .ccc-kpi-card {
                    background: #0d0d10;
                    border: 1px solid #202026;
                    border-radius: 4px;
                    padding: 18px 20px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    min-height: 125px;
                    transition: all 0.2s ease;
                    position: relative;
                    overflow: hidden;
                }

                .ccc-kpi-card:hover {
                    border-color: #2e2e36;
                    background: #111115;
                }

                .ccc-kpi-card.warn {
                    border-top: 2px solid #f59e0b;
                }

                .ccc-kpi-card.danger {
                    border-top: 2px solid #ef4444;
                }

                .ccc-kpi-card.success {
                    border-top: 2px solid #10b981;
                }

                .ccc-kpi-card.primary {
                    border-top: 2px solid #d0915f;
                }

                .ccc-kpi-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .ccc-kpi-label {
                    font-size: 10px;
                    font-weight: 800;
                    letter-spacing: 0.1em;
                    color: #8c8c96;
                    text-transform: uppercase;
                }

                .ccc-kpi-icon {
                    color: #71717a;
                }

                .ccc-kpi-card.warn .ccc-kpi-icon { color: #f59e0b; }
                .ccc-kpi-card.danger .ccc-kpi-icon { color: #ef4444; }
                .ccc-kpi-card.primary .ccc-kpi-icon { color: #d0915f; }

                .ccc-kpi-val {
                    font-size: 36px;
                    font-weight: 800;
                    letter-spacing: -0.03em;
                    color: #ffffff;
                    margin: 8px 0 4px;
                    line-height: 1;
                    font-family: "DM Sans", sans-serif;
                }

                .ccc-kpi-card.warn .ccc-kpi-val { color: #fde68a; }
                .ccc-kpi-card.danger .ccc-kpi-val { color: #fca5a5; }

                .ccc-kpi-sub {
                    font-size: 11px;
                    color: #71717a;
                    line-height: 1.35;
                }

                /* Secondary Operation Strip */
                .ccc-sec-strip {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 14px;
                    background: #0a0a0d;
                    border: 1px solid #1c1c22;
                    border-radius: 4px;
                    padding: 12px 20px;
                    margin-bottom: 24px;
                }

                .ccc-sec-item {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 4px 12px;
                    border-right: 1px solid #1c1c22;
                }

                .ccc-sec-item:last-child {
                    border-right: none;
                }

                .ccc-sec-title {
                    font-size: 11px;
                    font-weight: 700;
                    color: #8c8c96;
                    letter-spacing: 0.05em;
                }

                .ccc-sec-num {
                    font-family: "DM Mono", monospace;
                    font-size: 16px;
                    font-weight: 800;
                    color: #ededed;
                }

                /* Layout Grid for Attention & Mine Vis */
                .ccc-main-grid {
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 24px;
                    margin-bottom: 28px;
                }

                /* Section Heading */
                .ccc-section-head {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                    margin-bottom: 16px;
                    border-bottom: 1px solid #1c1c22;
                    padding-bottom: 10px;
                }

                .ccc-section-head h2 {
                    font-size: 16px;
                    font-weight: 800;
                    letter-spacing: 0.04em;
                    color: #ffffff;
                    margin: 0;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .ccc-section-head p {
                    font-size: 11px;
                    color: #71717a;
                    margin: 4px 0 0 0;
                }

                /* Attention Items List */
                .ccc-attention-feed {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    margin-bottom: 28px;
                }

                .ccc-attention-card {
                    background: #0d0d10;
                    border: 1px solid #202026;
                    border-left: 4px solid #f59e0b;
                    border-radius: 4px;
                    padding: 16px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 20px;
                    transition: all 0.2s ease;
                }

                .ccc-attention-card.critical {
                    border-left-color: #ef4444;
                    background: #0f0a0b;
                }

                .ccc-attention-card.high {
                    border-left-color: #f87171;
                    background: #0e0b0c;
                }

                .ccc-attention-card.medium {
                    border-left-color: #f59e0b;
                    background: #0d0d10;
                }

                .ccc-attention-card.low {
                    border-left-color: #71717a;
                    background: #0d0d10;
                }

                .ccc-attention-card:hover {
                    background: #111115;
                    border-color: #2c2c34;
                }

                .ccc-attention-meta {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 6px;
                }

                .ccc-badge-priority {
                    font-family: "DM Mono", monospace;
                    font-size: 9px;
                    font-weight: 700;
                    padding: 2px 7px;
                    border-radius: 2px;
                    letter-spacing: 0.05em;
                }

                .ccc-badge-category {
                    font-family: "DM Mono", monospace;
                    font-size: 9px;
                    font-weight: 600;
                    padding: 2px 7px;
                    background: #131317;
                    border: 1px solid #24242c;
                    border-radius: 2px;
                    color: #8c8c96;
                    letter-spacing: 0.05em;
                }

                .ccc-attention-title {
                    font-size: 14px;
                    font-weight: 700;
                    color: #f4f4f5;
                    margin: 0 0 4px 0;
                }

                .ccc-attention-desc {
                    font-size: 12px;
                    color: #a1a1aa;
                    margin: 0;
                    line-height: 1.45;
                }

                .ccc-attention-action-btn {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    background: #121216;
                    border: 1px solid #26262e;
                    color: #ededed;
                    padding: 8px 14px;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.05em;
                    cursor: pointer;
                    white-space: nowrap;
                    transition: all 0.2s ease;
                }

                .ccc-attention-action-btn:hover {
                    background: #d0915f;
                    border-color: #d0915f;
                    color: #000000;
                }

                /* Seven Compliance Categories Grid */
                .ccc-categories-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                    gap: 16px;
                    margin-bottom: 32px;
                }

                .ccc-category-card {
                    background: #0d0d10;
                    border: 1px solid #202026;
                    border-radius: 4px;
                    padding: 18px 20px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    transition: all 0.2s ease;
                }

                .ccc-category-card:hover {
                    border-color: #2c2c34;
                    background: #111115;
                }

                .ccc-category-top {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 12px;
                }

                .ccc-cat-icon-cluster {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .ccc-cat-icon {
                    width: 32px;
                    height: 32px;
                    border-radius: 4px;
                    background: #131317;
                    border: 1px solid #24242c;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #d0915f;
                }

                .ccc-cat-name {
                    font-size: 14px;
                    font-weight: 800;
                    color: #ffffff;
                    margin: 0;
                }

                .ccc-cat-regulation {
                    font-size: 10px;
                    color: #71717a;
                    margin-top: 2px;
                }

                .ccc-cat-status-badge {
                    font-family: "DM Mono", monospace;
                    font-size: 9px;
                    font-weight: 700;
                    padding: 3px 8px;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    letter-spacing: 0.04em;
                    white-space: nowrap;
                }

                .ccc-cat-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                }

                .ccc-cat-metrics {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 8px;
                    margin-top: 14px;
                    padding-top: 14px;
                    border-top: 1px solid #1c1c22;
                }

                .ccc-cat-metric-box {
                    display: flex;
                    flex-direction: column;
                }

                .ccc-cat-metric-label {
                    font-family: "DM Mono", monospace;
                    font-size: 9px;
                    color: #71717a;
                    letter-spacing: 0.05em;
                }

                .ccc-cat-metric-val {
                    font-size: 16px;
                    font-weight: 700;
                    color: #ededed;
                    margin-top: 2px;
                }

                /* ── Compliance Risk Intelligence Styles ───────────────── */
                .ccc-risk-overall-banner {
                    background: #0d0d10;
                    border: 1px solid #202026;
                    border-radius: 4px;
                    padding: 16px 20px;
                    margin-bottom: 18px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }

                .ccc-risk-overall-top {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 12px;
                }

                .ccc-overall-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 5px 12px;
                    border-radius: 3px;
                    font-family: "DM Mono", monospace;
                    font-size: 11px;
                    font-weight: 800;
                    letter-spacing: 0.08em;
                }

                .ccc-drivers-list {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    padding: 12px 14px;
                    background: #08080a;
                    border: 1px solid #1c1c22;
                    border-radius: 3px;
                }

                .ccc-driver-item {
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    font-size: 12px;
                    color: #d4d4d8;
                    line-height: 1.45;
                }

                .ccc-driver-dot {
                    color: #d0915f;
                    font-size: 14px;
                    line-height: 1;
                    flex-shrink: 0;
                    margin-top: 1px;
                }

                .ccc-risk-domains-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
                    gap: 14px;
                    margin-bottom: 32px;
                }

                .ccc-risk-domain-card {
                    background: #0d0d10;
                    border: 1px solid #202026;
                    border-radius: 4px;
                    padding: 14px 16px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .ccc-risk-domain-card:hover {
                    background: #111115;
                    border-color: #2c2c34;
                    transform: translateY(-1px);
                }

                .ccc-risk-domain-card.active-sector {
                    border-color: #d0915f;
                    background: #111115;
                }

                .ccc-risk-bar-track {
                    width: 100%;
                    height: 6px;
                    background: #141418;
                    border: 1px solid #202026;
                    border-radius: 3px;
                    overflow: hidden;
                    margin: 8px 0;
                }

                .ccc-risk-bar-fill {
                    height: 100%;
                    border-radius: 2px;
                    transition: width 0.3s ease;
                }

                .ccc-risk-stat-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-family: "DM Mono", monospace;
                    font-size: 10px;
                    color: #8c8c96;
                    margin-top: 6px;
                    padding-top: 6px;
                    border-top: 1px solid #191920;
                }

                /* ── Recurring Compliance Feed Styles ─────────────────── */
                .ccc-recurring-card {
                    background: #0d0d10;
                    border: 1px solid #202026;
                    border-left-width: 4px;
                    border-radius: 4px;
                    padding: 18px 20px;
                    margin-bottom: 14px;
                    transition: all 0.2s ease;
                }

                .ccc-recurring-card.critical {
                    border-left-color: #ef4444;
                    background: #0f0a0b;
                }

                .ccc-recurring-card.high {
                    border-left-color: #f87171;
                    background: #0e0b0c;
                }

                .ccc-recurring-card.medium {
                    border-left-color: #f59e0b;
                    background: #0d0d10;
                }

                .ccc-recurring-card:hover {
                    background: #121217;
                    border-color: #2c2c34;
                }

                .ccc-badge-occ {
                    font-family: "DM Mono", monospace;
                    font-size: 9px;
                    font-weight: 700;
                    padding: 2px 8px;
                    background: rgba(208, 145, 95, 0.15);
                    color: #d0915f;
                    border: 1px solid rgba(208, 145, 95, 0.35);
                    border-radius: 2px;
                    letter-spacing: 0.05em;
                }

                .ccc-chips-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                    margin-top: 8px;
                }

                .ccc-case-chip {
                    font-family: "DM Mono", monospace;
                    font-size: 10px;
                    background: #141418;
                    border: 1px solid #24242c;
                    color: #d4d4d8;
                    padding: 3px 8px;
                    border-radius: 2px;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    transition: all 0.15s ease;
                }

                .ccc-case-chip:hover {
                    background: #1f1f26;
                    border-color: #d0915f;
                    color: #ffffff;
                }

                .ccc-empty-notice {
                    padding: 32px 20px;
                    background: #0d0d10;
                    border: 1px solid #202026;
                    border-radius: 4px;
                    text-align: center;
                    color: #71717a;
                    font-size: 13px;
                }

                @media (max-width: 1200px) {
                    .ccc-kpis { grid-template-columns: repeat(3, 1fr); }
                }

                @media (max-width: 800px) {
                    .compliance-command-center { padding: 16px; }
                    .ccc-toolbar { flex-direction: column; }
                    .ccc-controls { align-items: flex-start; }
                    .ccc-kpis { grid-template-columns: 1fr; }
                    .ccc-sec-strip { grid-template-columns: 1fr; }
                    .ccc-sec-item { border-right: none; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
                    .ccc-attention-card { flex-direction: column; align-items: flex-start; }
                }
            `}</style>

            {/* ═══ COMMAND CENTER HEADER ═══════════════════════ */}
            <section className="ccc-toolbar">
                <div className="ccc-title-cluster">
                    <p className="ccc-eyebrow">
                        PROJECT PRITHVI / MINE COMPLIANCE INTELLIGENCE
                    </p>
                    <h1>Compliance Command Center</h1>
                    <div className="ccc-mine-name">
                        <Activity size={16} color="#10b981" />
                        <span>
                            {summary?.mine_name || "Jharia Underground Demonstration Mine"}
                        </span>
                        <span style={{ color: "#64748b", fontFamily: "DM Mono, monospace", fontSize: "12px" }}>
                            ({summary?.mine_id || JHARIA_MINE_ID})
                        </span>
                    </div>
                    <div className="ccc-mine-tags">
                        <span className="ccc-tag">SUBSIDIARY: {summary?.subsidiary || "BCCL"}</span>
                        <span className="ccc-tag">TYPE: UNDERGROUND COAL</span>
                        <span className="ccc-tag">GASSINESS: DEGREE II GASSY</span>
                        <span className="ccc-tag">DEPTH: 300m – 600m</span>
                        <span className="ccc-tag">REGULATION: CMR 2017</span>
                    </div>
                </div>

                <div className="ccc-controls">
                    <button
                        className="ccc-refresh-btn"
                        onClick={() => void loadData(true)}
                        disabled={loading || refreshing}
                        title="Fetch latest compliance telemetry"
                    >
                        <RefreshCw size={14} className={refreshing ? "spin" : ""} />
                        <span>{refreshing ? "REFRESHING..." : "REFRESH DATA"}</span>
                    </button>
                    <span className="ccc-asof">
                        AS OF: {formatDate(summary?.as_of)}
                    </span>
                </div>
            </section>

            {/* ═══ ERROR DISPLAY ═══════════════════════════════ */}
            {error && (
                <div className="ccc-error-banner">
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <AlertOctagon size={18} />
                        <div>
                            <strong>FAILED TO RETRIEVE MINE COMPLIANCE INTELLIGENCE</strong>
                            <div style={{ fontSize: "12px", marginTop: "2px" }}>{error}</div>
                        </div>
                    </div>
                    <button
                        className="ccc-refresh-btn"
                        onClick={() => void loadData()}
                    >
                        RETRY
                    </button>
                </div>
            )}

            {/* ═══ SCADA TELEMETRY SAFETY SIGNAL STRIP (Phase 2 Task 9) ════════ */}
            <div
                onClick={() => navigate("/safety")}
                style={{
                    cursor: "pointer",
                    padding: "12px 18px",
                    marginBottom: "20px",
                    borderRadius: "4px",
                    border: safetySignals.some((s) => s.severity === "CRITICAL")
                        ? "1px solid rgba(244, 63, 94, 0.6)"
                        : safetySignals.length > 0
                        ? "1px solid rgba(245, 158, 11, 0.6)"
                        : "1px solid #1c1c22",
                    background: safetySignals.some((s) => s.severity === "CRITICAL")
                        ? "rgba(136, 19, 55, 0.25)"
                        : safetySignals.length > 0
                        ? "rgba(120, 53, 15, 0.2)"
                        : "#0a0a0d",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "12px",
                }}
            >
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div
                        style={{
                            padding: "8px",
                            borderRadius: "4px",
                            background: safetySignals.some((s) => s.severity === "CRITICAL")
                                ? "rgba(244, 63, 94, 0.2)"
                                : safetySignals.length > 0
                                ? "rgba(245, 158, 11, 0.2)"
                                : "rgba(16, 185, 129, 0.15)",
                            color: safetySignals.some((s) => s.severity === "CRITICAL")
                                ? "#fda4af"
                                : safetySignals.length > 0
                                ? "#fcd34d"
                                : "#6ee7b7",
                        }}
                    >
                        <Activity size={18} />
                    </div>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.06em", color: "#ededed" }}>
                                LIVE SAFETY SIGNALS (SIMULATED SCADA)
                            </span>
                            <span
                                style={{
                                    fontSize: "9px",
                                    padding: "2px 6px",
                                    borderRadius: "3px",
                                    background: "#18181b",
                                    color: "#a1a1aa",
                                    fontFamily: "monospace",
                                    fontWeight: 700,
                                }}
                            >
                                TASK 9 IOT SURVEILLANCE
                            </span>
                        </div>
                        <div style={{ fontSize: "12px", marginTop: "3px" }}>
                            {safetySignals.length === 0 ? (
                                <span style={{ color: "#6ee7b7", fontWeight: 500 }}>
                                    All 7 industrial telemetry feeds reporting normal statutory baseline (CMR 2017 compliant).
                                </span>
                            ) : (
                                <span style={{ color: "#fda4af", fontWeight: 700 }}>
                                    {safetySignals.length} Active Statutory Safety Breach{safetySignals.length > 1 ? "es" : ""}:{" "}
                                    {safetySignals.map((s) => `${s.sensor_code} (${s.observed_value} ${s.unit})`).join(", ")}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 700, color: "#60a5fa" }}>
                    <span>VIEW SAFETY INTELLIGENCE</span>
                    <ArrowRight size={13} />
                </div>
            </div>

            {/* ═══ FIRST VIEW: TOP REAL METRICS ════════════════ */}
            <section className="ccc-kpis">
                {/* 1. Total Applicable */}
                <article className="ccc-kpi-card primary">
                    <div className="ccc-kpi-header">
                        <span className="ccc-kpi-label">TOTAL APPLICABLE</span>
                        <ShieldCheck size={16} className="ccc-kpi-icon" />
                    </div>
                    <div className="ccc-kpi-val">
                        {loading ? "--" : fmt(summary?.total_applicable_inspections)}
                    </div>
                    <div className="ccc-kpi-sub">
                        13 statutory CMR inspection templates active for Jharia
                    </div>
                </article>

                {/* 2. Due Today */}
                <article className={`ccc-kpi-card ${summary && summary.due_today > 0 ? "warn" : "success"}`}>
                    <div className="ccc-kpi-header">
                        <span className="ccc-kpi-label">DUE TODAY</span>
                        <Clock3 size={16} className="ccc-kpi-icon" />
                    </div>
                    <div className="ccc-kpi-val">
                        {loading ? "--" : fmt(summary?.due_today)}
                    </div>
                    <div className="ccc-kpi-sub">
                        Mandatory statutory shifts due for execution today
                    </div>
                </article>

                {/* 3. Overdue */}
                <article className={`ccc-kpi-card ${summary && summary.overdue > 0 ? "danger" : "success"}`}>
                    <div className="ccc-kpi-header">
                        <span className="ccc-kpi-label">OVERDUE</span>
                        <AlertOctagon size={16} className="ccc-kpi-icon" />
                    </div>
                    <div className="ccc-kpi-val">
                        {loading ? "--" : fmt(summary?.overdue)}
                    </div>
                    <div className="ccc-kpi-sub">
                        Statutory inspection deadlines breached
                    </div>
                </article>

                {/* 4. Review Required */}
                <article
                    className={`ccc-kpi-card ${summary && summary.review_required > 0 ? "warn" : "success"}`}
                    onClick={() => navigate("/verification")}
                    style={{ cursor: "pointer" }}
                    title="Click to open Verification Center"
                >
                    <div className="ccc-kpi-header">
                        <span className="ccc-kpi-label">REVIEW REQUIRED</span>
                        <FileCheck2 size={16} className="ccc-kpi-icon" />
                    </div>
                    <div className="ccc-kpi-val">
                        {loading ? "--" : fmt(summary?.review_required)}
                    </div>
                    <div className="ccc-kpi-sub">
                        Statutory compliance cases awaiting manager verification →
                    </div>
                </article>

                {/* 5. Open Findings */}
                <article className={`ccc-kpi-card ${summary && summary.open_findings > 0 ? "danger" : "success"}`}>
                    <div className="ccc-kpi-header">
                        <span className="ccc-kpi-label">OPEN FINDINGS</span>
                        <AlertTriangle size={16} className="ccc-kpi-icon" />
                    </div>
                    <div className="ccc-kpi-val">
                        {loading ? "--" : fmt(summary?.open_findings)}
                    </div>
                    <div className="ccc-kpi-sub">
                        Active statutory defect notices requiring remediation
                    </div>
                </article>
            </section>

            {/* ═══ SECONDARY METRIC COUNTERS ═══════════════════ */}
            <section className="ccc-sec-strip">
                <div className="ccc-sec-item">
                    <span className="ccc-sec-title">SUBMITTED INSPECTIONS:</span>
                    <span className="ccc-sec-num">{loading ? "--" : fmt(summary?.submitted)}</span>
                </div>
                <div className="ccc-sec-item">
                    <span className="ccc-sec-title">VERIFIED COMPLIANT:</span>
                    <span className="ccc-sec-num" style={{ color: "#10b981" }}>
                        {loading ? "--" : fmt(summary?.verified)}
                    </span>
                </div>
                <div className="ccc-sec-item">
                    <span className="ccc-sec-title">THRESHOLD VIOLATIONS:</span>
                    <span
                        className="ccc-sec-num"
                        style={{ color: summary && summary.threshold_violations > 0 ? "#ef4444" : "#10b981" }}
                    >
                        {loading ? "--" : fmt(summary?.threshold_violations)}
                    </span>
                </div>
            </section>

            {/* ═══ COMPLIANCE PIPELINE ARCHITECTURE ════════════ */}
            <CompliancePipelineDiagram />

            {/* ═══ MAIN LAYOUT: MINE STRATIGRAPHIC VISUALIZATION */}
            <div className="ccc-main-grid">
                <section>
                    <MineComplianceCrossSection
                        categories={summary?.category_compliance || []}
                        selectedCategory={selectedCategory}
                        onSelectCategory={(cat) => setSelectedCategory(cat)}
                    />
                </section>
            </div>

            {/* ═══ COMPLIANCE RISK INTELLIGENCE ══════════════════ */}
            <section style={{ marginBottom: "32px" }}>
                <div className="ccc-section-head">
                    <div>
                        <h2>
                            <Activity size={17} color="#ef4444" />
                            <span>COMPLIANCE RISK INTELLIGENCE</span>
                        </h2>
                        <p>
                            Deterministic statutory risk evaluation derived from real inspection cycles, threshold breaches & recurring signals
                        </p>
                    </div>
                    {riskData && (
                        <div
                            className="ccc-overall-badge"
                            style={{
                                background: getRiskBadge(riskData.overall_risk_level).bg,
                                color: getRiskBadge(riskData.overall_risk_level).color,
                                border: `1px solid ${getRiskBadge(riskData.overall_risk_level).border}`,
                            }}
                        >
                            <span>OVERALL MINE RISK: {riskData.overall_risk_level}</span>
                            <span style={{ opacity: 0.8 }}>({riskData.overall_risk_score} / 100)</span>
                        </div>
                    )}
                </div>

                {loading ? (
                    <div className="ccc-empty-notice">Calculating deterministic statutory compliance risk...</div>
                ) : !riskData ? (
                    <div className="ccc-empty-notice">No risk intelligence available for this mine.</div>
                ) : (
                    <>
                        {/* Overall Mine Risk Summary Banner */}
                        <div className="ccc-risk-overall-banner">
                            <div className="ccc-risk-overall-top">
                                <div>
                                    <div style={{ fontSize: "11px", fontFamily: "DM Mono, monospace", color: "#8c8c96", fontWeight: 700, letterSpacing: "0.1em" }}>
                                        PRIMARY RISK DRIVERS & EXPLAINABILITY
                                    </div>
                                    <div style={{ fontSize: "13px", color: "#ededed", marginTop: "2px", fontWeight: 600 }}>
                                        Statutory compliance risk profile derived from real database signals:
                                    </div>
                                </div>
                                <div style={{ fontSize: "10px", fontFamily: "DM Mono, monospace", color: "#71717a" }}>
                                    DERIVED FROM OBSERVABLE COMPLIANCE SIGNALS
                                </div>
                            </div>

                            <div className="ccc-drivers-list">
                                {riskData.top_risk_drivers.map((driver: string, idx: number) => (
                                    <div key={idx} className="ccc-driver-item">
                                        <span className="ccc-driver-dot">●</span>
                                        <span>{driver}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Seven Compliance Domains Risk Matrix */}
                        <div className="ccc-risk-domains-grid">
                            {riskData.categories.map((catRisk: CategoryRiskSummary) => {
                                const IconComponent = CATEGORY_ICONS[catRisk.category] || ShieldCheck;
                                const rBadge = getRiskBadge(catRisk.risk_level);
                                const isSelected = selectedCategory?.toLowerCase().trim() === catRisk.category.toLowerCase().trim();

                                return (
                                    <article
                                        key={catRisk.category}
                                        className={`ccc-risk-domain-card ${isSelected ? "active-sector" : ""}`}
                                        onClick={() => setSelectedCategory(isSelected ? null : catRisk.category)}
                                        title={`Filter command center by ${catRisk.category}`}
                                    >
                                        <div>
                                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                                                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                                    <div className="ccc-cat-icon" style={{ width: "26px", height: "26px" }}>
                                                        <IconComponent size={14} />
                                                    </div>
                                                    <div>
                                                        <div style={{ fontSize: "12px", fontWeight: 800, color: "#ffffff" }}>
                                                            {catRisk.category}
                                                        </div>
                                                        <div style={{ fontSize: "9px", color: "#71717a", fontFamily: "DM Mono, monospace" }}>
                                                            {CATEGORY_REGULATIONS[catRisk.category] || "CMR 2017"}
                                                        </div>
                                                    </div>
                                                </div>

                                                <span
                                                    className="ccc-badge-priority"
                                                    style={{
                                                        background: rBadge.bg,
                                                        color: rBadge.color,
                                                        border: `1px solid ${rBadge.border}`,
                                                    }}
                                                >
                                                    {rBadge.label}
                                                </span>
                                            </div>

                                            {/* Horizontal Risk Bar */}
                                            <div className="ccc-risk-bar-track">
                                                <div
                                                    className="ccc-risk-bar-fill"
                                                    style={{
                                                        width: `${Math.max(5, catRisk.risk_score)}%`,
                                                        background: rBadge.barColor,
                                                    }}
                                                />
                                            </div>

                                            {/* Driver Summary */}
                                            <div style={{ fontSize: "11px", color: "#a1a1aa", minHeight: "30px", lineHeight: 1.4 }}>
                                                {catRisk.drivers[0] || "All statutory parameters compliant."}
                                            </div>
                                        </div>

                                        {/* Metrics Row */}
                                        <div className="ccc-risk-stat-row">
                                            <span>SIGNALS: <strong style={{ color: catRisk.active_signals > 0 ? "#f59e0b" : "#ededed" }}>{catRisk.active_signals}</strong></span>
                                            <span>RECURRING: <strong style={{ color: catRisk.recurring_issues > 0 ? "#ef4444" : "#ededed" }}>{catRisk.recurring_issues}</strong></span>
                                            <span>OVERDUE: <strong style={{ color: catRisk.overdue_inspections > 0 ? "#ef4444" : "#ededed" }}>{catRisk.overdue_inspections}</strong></span>
                                            <span>SCORE: <strong style={{ color: rBadge.color }}>{catRisk.risk_score}/100</strong></span>
                                        </div>
                                    </article>
                                );
                            })}
                        </div>
                    </>
                )}
            </section>

            {/* ═══ RECURRING COMPLIANCE ISSUES ══════════════════ */}
            <section style={{ marginBottom: "32px" }}>
                <div className="ccc-section-head">
                    <div>
                        <h2>
                            <Repeat size={17} color="#d0915f" />
                            <span>RECURRING COMPLIANCE ISSUES</span>
                        </h2>
                        <p>
                            Pattern intelligence isolating repeated threshold breaches, recurrent findings, and persistent non-compliance
                        </p>
                    </div>
                    <span style={{ fontFamily: "DM Mono, monospace", fontSize: "11px", color: "#8c8c96" }}>
                        {recurringIssues.length} RECURRING PATTERN{recurringIssues.length === 1 ? "" : "S"}
                    </span>
                </div>

                {loading ? (
                    <div className="ccc-empty-notice">Scanning historical inspection cycles for recurring non-compliance...</div>
                ) : recurringIssues.length === 0 ? (
                    <div className="ccc-empty-notice" style={{ color: "#10b981" }}>
                        <CheckCircle2 size={24} style={{ margin: "0 auto 8px", display: "block" }} />
                        No recurring compliance failures detected. All historical non-compliance events remain isolated.
                    </div>
                ) : (
                    <div>
                        {recurringIssues.map((issue: RecurringComplianceIssue) => {
                            const sevClass = (issue.severity || "HIGH").toLowerCase();
                            const pBadge = getPriorityBadge(issue.severity);
                            const latestInspId = issue.related_inspection_ids?.[0];

                            return (
                                <article key={issue.issue_id} className={`ccc-recurring-card ${sevClass}`}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px", flexWrap: "wrap" }}>
                                        <div style={{ flex: 1, minWidth: "280px" }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "8px" }}>
                                                <span
                                                    className="ccc-badge-priority"
                                                    style={{
                                                        background: pBadge.bg,
                                                        color: pBadge.color,
                                                        border: `1px solid ${pBadge.border}`,
                                                    }}
                                                >
                                                    {pBadge.label}
                                                </span>
                                                <span className="ccc-badge-category">
                                                    {issue.category.toUpperCase()}
                                                </span>
                                                <span className="ccc-badge-occ">
                                                    {issue.occurrences} OCCURRENCES
                                                </span>
                                                <span
                                                    style={{
                                                        fontFamily: "DM Mono, monospace",
                                                        fontSize: "9px",
                                                        padding: "2px 6px",
                                                        borderRadius: "2px",
                                                        background: issue.status === "OPEN" ? "rgba(239, 68, 68, 0.12)" : "rgba(16, 185, 129, 0.12)",
                                                        color: issue.status === "OPEN" ? "#ef4444" : "#10b981",
                                                        border: `1px solid ${issue.status === "OPEN" ? "rgba(239, 68, 68, 0.3)" : "rgba(16, 185, 129, 0.3)"}`,
                                                    }}
                                                >
                                                    STATUS: {issue.status}
                                                </span>
                                            </div>

                                            <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#ffffff", margin: "0 0 4px 0" }}>
                                                {issue.title}
                                            </h3>

                                            <div style={{ fontSize: "10px", fontFamily: "DM Mono, monospace", color: "#71717a", marginBottom: "8px" }}>
                                                FIRST DETECTED: {formatDate(issue.first_detected_at)} &nbsp;|&nbsp; LAST DETECTED: {formatDate(issue.last_detected_at)}
                                            </div>

                                            <div style={{ fontSize: "12px", color: "#d4d4d8", lineHeight: 1.45, marginBottom: "8px" }}>
                                                <strong style={{ color: "#8c8c96" }}>Primary Statutory Driver: </strong>
                                                {issue.description}
                                            </div>

                                            <div style={{ fontSize: "11px", color: "#d0915f", fontWeight: 600, marginBottom: "10px", lineHeight: 1.4 }}>
                                                <strong>Recommended Statutory Action: </strong>
                                                {issue.recommended_action}
                                            </div>

                                            {/* Contributing Inspections */}
                                            {issue.related_inspection_ids?.length > 0 && (
                                                <div style={{ marginTop: "10px" }}>
                                                    <span style={{ fontSize: "10px", fontFamily: "DM Mono, monospace", color: "#8c8c96" }}>
                                                        CONTRIBUTING INSPECTION RECORDS ({issue.related_inspection_ids.length}):
                                                    </span>
                                                    <div className="ccc-chips-container">
                                                        {issue.related_inspection_ids.map((inspId: string) => (
                                                            <button
                                                                key={inspId}
                                                                type="button"
                                                                className="ccc-case-chip"
                                                                onClick={() => navigate(`/inspections/${inspId}`)}
                                                                title={`Inspect case record ${inspId}`}
                                                            >
                                                                <span>{inspId}</span>
                                                                <ArrowRight size={10} color="#d0915f" />
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {latestInspId && (
                                            <div style={{ alignSelf: "flex-start", marginTop: "4px" }}>
                                                <button
                                                    className="ccc-attention-action-btn"
                                                    onClick={() => navigate(`/inspections/${latestInspId}`)}
                                                >
                                                    <span>VIEW CASE</span>
                                                    <ArrowRight size={13} />
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </article>
                            );
                        })}
                    </div>
                )}
            </section>

            {/* ═══ REQUIRES ATTENTION SECTION ══════════════════ */}
            <section style={{ marginBottom: "32px" }}>
                <div className="ccc-section-head">
                    <div>
                        <h2>
                            <AlertTriangle size={17} color="#f59e0b" />
                            <span>REQUIRES ATTENTION</span>
                        </h2>
                        <p>
                            Prioritized statutory breaches, threshold violations, and pending verifications
                        </p>
                    </div>
                    <span style={{ fontFamily: "DM Mono, monospace", fontSize: "11px", color: "#8c8c96" }}>
                        {summary?.attention_items?.length ?? 0} ACTIVE SIGNALS
                    </span>
                </div>

                {loading ? (
                    <div className="ccc-empty-notice">Scanning compliance database for attention items...</div>
                ) : !summary?.attention_items || summary.attention_items.length === 0 ? (
                    <div className="ccc-empty-notice" style={{ color: "#10b981" }}>
                        <CheckCircle2 size={24} style={{ margin: "0 auto 8px", display: "block" }} />
                        All measurements are within statutory thresholds. No overdue inspections or open compliance findings.
                    </div>
                ) : (
                    <div className="ccc-attention-feed">
                        {summary.attention_items.map((item: AttentionItem, idx: number) => {
                            const severitySafe = (item.severity || "HIGH").toUpperCase();
                            const badge = getPriorityBadge(severitySafe);
                            const cardClass = severitySafe.toLowerCase();
                            const categorySafe = (item.category || "General Safety").replaceAll("_", " ").toUpperCase();
                            const actionText = item.action || "Conduct statutory check and report status.";

                            return (
                                <article
                                    key={`${item.reference_id || idx}-${item.category || idx}`}
                                    className={`ccc-attention-card ${cardClass}`}
                                >
                                    <div style={{ flex: 1 }}>
                                        <div className="ccc-attention-meta">
                                            <span
                                                className="ccc-badge-priority"
                                                style={{
                                                    background: badge.bg,
                                                    color: badge.color,
                                                    border: `1px solid ${badge.border}`,
                                                }}
                                            >
                                                {badge.label}
                                            </span>
                                            <span className="ccc-badge-category">
                                                {categorySafe}
                                            </span>
                                            {item.item_type && (
                                                <span className="ccc-badge-category" style={{ color: "#a1a1aa" }}>
                                                    {item.item_type.replaceAll("_", " ")}
                                                </span>
                                            )}
                                            {item.reference_id && (
                                                <span
                                                    style={{
                                                        fontFamily: "DM Mono, monospace",
                                                        fontSize: "10px",
                                                        color: "#71717a",
                                                    }}
                                                >
                                                    REF: {item.reference_id}
                                                </span>
                                            )}
                                        </div>
                                        <h3 className="ccc-attention-title">{item.title}</h3>
                                        <p className="ccc-attention-desc">{item.description}</p>
                                        <div style={{ marginTop: "6px", fontSize: "11px", color: "#d0915f", fontWeight: 600 }}>
                                            Mandated Statutory Action: {actionText}
                                        </div>
                                    </div>

                                    {item.reference_id && (
                                        <button
                                            className="ccc-attention-action-btn"
                                            onClick={() => {
                                                if (item.item_type === "VERIFICATION_REVIEW" || item.category === "review_required") {
                                                    navigate(`/verification/${item.reference_id}`);
                                                } else {
                                                    navigate(`/inspections/${item.reference_id}`);
                                                }
                                            }}
                                        >
                                            <span>VIEW CASE</span>
                                            <ArrowRight size={13} />
                                        </button>
                                    )}
                                </article>
                            );
                        })}
                    </div>
                )}
            </section>

            {/* ═══ SEVEN COMPLIANCE DOMAINS OVERVIEW ═══════════ */}
            <section>
                <div className="ccc-section-head">
                    <div>
                        <h2>
                            <Shield size={17} color="#d0915f" />
                            <span>SEVEN STATUTORY COMPLIANCE DOMAINS</span>
                        </h2>
                        <p>
                            Coal Mines Regulations 2017 category posture derived from field execution records
                        </p>
                    </div>
                    {selectedCategory && (
                        <button
                            className="ccc-refresh-btn"
                            style={{ padding: "4px 10px", fontSize: "10px" }}
                            onClick={() => setSelectedCategory(null)}
                        >
                            <Filter size={11} />
                            <span>CLEAR SECTOR FILTER ({selectedCategory.toUpperCase()})</span>
                        </button>
                    )}
                </div>

                {loading ? (
                    <div className="ccc-empty-notice">Aggregating category compliance records...</div>
                ) : (
                    <div className="ccc-categories-grid">
                        {displayCategories.map((cat: CategoryComplianceSummary) => {
                            const IconComponent = CATEGORY_ICONS[cat.category] || ShieldCheck;
                            const statusMeta = getCategoryStatusBadge(cat.compliance_status);
                            const regRef = CATEGORY_REGULATIONS[cat.category] || "CMR 2017 Statutory Mandate";

                            return (
                                <article key={cat.category} className="ccc-category-card">
                                    <div>
                                        <div className="ccc-category-top">
                                            <div className="ccc-cat-icon-cluster">
                                                <div className="ccc-cat-icon">
                                                    <IconComponent size={16} />
                                                </div>
                                                <div>
                                                    <h3 className="ccc-cat-name">{cat.category}</h3>
                                                    <div className="ccc-cat-regulation">{regRef}</div>
                                                </div>
                                            </div>
                                            <span
                                                className="ccc-cat-status-badge"
                                                style={{
                                                    color: statusMeta.color,
                                                    background: statusMeta.bg,
                                                    border: `1px solid ${statusMeta.border}`,
                                                }}
                                            >
                                                <span
                                                    className="ccc-cat-dot"
                                                    style={{ background: statusMeta.dotColor }}
                                                />
                                                {statusMeta.label}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="ccc-cat-metrics">
                                        <div className="ccc-cat-metric-box">
                                            <span className="ccc-cat-metric-label">SCHEDULES</span>
                                            <span className="ccc-cat-metric-val">{fmt(cat.total_schedules)}</span>
                                        </div>
                                        <div className="ccc-cat-metric-box">
                                            <span className="ccc-cat-metric-label">SUBMITTED</span>
                                            <span className="ccc-cat-metric-val">{fmt(cat.submitted_count)}</span>
                                        </div>
                                        <div className="ccc-cat-metric-box">
                                            <span className="ccc-cat-metric-label">REVIEW REQ</span>
                                            <span
                                                className="ccc-cat-metric-val"
                                                style={{ color: cat.review_required_count > 0 ? "#f59e0b" : "#ededed" }}
                                            >
                                                {fmt(cat.review_required_count)}
                                            </span>
                                        </div>
                                        <div className="ccc-cat-metric-box">
                                            <span className="ccc-cat-metric-label">VIOLATIONS</span>
                                            <span
                                                className="ccc-cat-metric-val"
                                                style={{ color: cat.threshold_violations_count > 0 ? "#ef4444" : "#10b981" }}
                                            >
                                                {fmt(cat.threshold_violations_count)}
                                            </span>
                                        </div>
                                    </div>

                                    <div style={{ marginTop: "14px", display: "flex", justifyContent: "flex-end" }}>
                                        <button
                                            style={{
                                                background: "transparent",
                                                border: "none",
                                                color: "#d0915f",
                                                fontSize: "10px",
                                                fontFamily: "DM Mono, monospace",
                                                fontWeight: 700,
                                                cursor: "pointer",
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "4px",
                                                padding: 0,
                                            }}
                                            onClick={() => navigate("/inspections/plan")}
                                        >
                                            <span>VIEW STATUTORY PLAN</span>
                                            <ExternalLink size={10} />
                                        </button>
                                    </div>
                                </article>
                            );
                        })}
                    </div>
                )}
            </section>
        </div>
    );
}
