import { useEffect, useState, useMemo } from "react";
import {
    AlertOctagon,
    AlertTriangle,
    ArrowRight,
    CheckCircle2,
    ClipboardCheck,
    Flame,
    Layers,
    RefreshCw,
    Search,
    ShieldAlert,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import {
    getMineVerificationQueue,
    type VerificationQueueResponse,
} from "../api/verification";

const MINE_ID = "MINE-BCCL-JHARIA-01";

function formatTimestamp(value?: string | null): string {
    if (!value) return "Pending Submission";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    });
}

function getPriorityBadge(priority: "CRITICAL" | "HIGH" | "NORMAL") {
    switch (priority) {
        case "CRITICAL":
            return {
                label: "CRITICAL PRIORITY",
                bg: "rgba(239, 68, 68, 0.15)",
                border: "#ef4444",
                color: "#fca5a5",
                icon: <Flame size={13} className="animate-pulse" />,
            };
        case "HIGH":
            return {
                label: "HIGH PRIORITY",
                bg: "rgba(245, 158, 11, 0.15)",
                border: "#f59e0b",
                color: "#fcd34d",
                icon: <AlertTriangle size={13} />,
            };
        case "NORMAL":
        default:
            return {
                label: "NORMAL PRIORITY",
                bg: "rgba(100, 116, 139, 0.15)",
                border: "#475569",
                color: "#cbd5e1",
                icon: <CheckCircle2 size={13} />,
            };
    }
}

export default function VerificationQueue() {
    const navigate = useNavigate();

    const [queueData, setQueueData] = useState<VerificationQueueResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [activeTab, setActiveTab] = useState<"ALL" | "CRITICAL" | "HIGH" | "VIOLATIONS" | "INCOMPLETE">("ALL");
    const [searchQuery, setSearchQuery] = useState("");

    async function loadQueue() {
        try {
            setLoading(true);
            setError(null);
            const data = await getMineVerificationQueue(MINE_ID);
            setQueueData(data);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Unable to connect to the Verification Center."
            );
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        void loadQueue();
    }, []);

    const counts = queueData?.counts || {
        submitted: 0,
        review_required: 0,
        verified: 0,
        rejected: 0,
        high_risk_review: 0,
    };

    const items = queueData?.items || [];

    // Filtered items
    const filteredItems = useMemo(() => {
        return items.filter((it) => {
            // Tab filter
            if (activeTab === "CRITICAL" && it.priority !== "CRITICAL") return false;
            if (activeTab === "HIGH" && it.risk_level !== "HIGH" && it.priority !== "HIGH") return false;
            if (activeTab === "VIOLATIONS" && !it.has_violations) return false;
            if (activeTab === "INCOMPLETE" && it.evidence_compliant) return false;

            // Search query
            if (searchQuery.trim()) {
                const q = searchQuery.toLowerCase();
                const matchId = it.inspection_id.toLowerCase().includes(q);
                const matchTemplate = it.template_name.toLowerCase().includes(q);
                const matchCategory = it.category.toLowerCase().includes(q);
                const matchInspector = it.inspector_id.toLowerCase().includes(q);
                return matchId || matchTemplate || matchCategory || matchInspector;
            }

            return true;
        });
    }, [items, activeTab, searchQuery]);

    return (
        <section className="vcenter-root">
            {/* INLINE INDUSTRIAL STYLES */}
            <style>{`
                .vcenter-root {
                    min-height: 100vh;
                    background-color: #060608;
                    color: #ededed;
                    padding: 32px 36px 80px 36px;
                    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                }
                .vcenter-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    border-bottom: 1px solid #1f1f26;
                    padding-bottom: 24px;
                    margin-bottom: 28px;
                    gap: 24px;
                }
                .vcenter-title-area h1 {
                    font-size: 26px;
                    font-weight: 700;
                    letter-spacing: -0.02em;
                    color: #ffffff;
                    margin: 4px 0 6px 0;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .vcenter-eyebrow {
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.12em;
                    color: #f97316;
                    text-transform: uppercase;
                }
                .vcenter-subtitle {
                    font-size: 14px;
                    color: #94a3b8;
                    margin: 0;
                }
                /* COUNTERS BAR */
                .vcenter-kpis {
                    display: grid;
                    grid-template-columns: repeat(5, minmax(130px, 1fr));
                    gap: 14px;
                    margin-bottom: 30px;
                }
                .vcenter-kpi-box {
                    background: #0d0d12;
                    border: 1px solid #202028;
                    border-radius: 8px;
                    padding: 16px 18px;
                    position: relative;
                    transition: border-color 0.2s;
                }
                .vcenter-kpi-box:hover {
                    border-color: #333340;
                }
                .vcenter-kpi-box.active-urgent {
                    border-color: rgba(239, 68, 68, 0.4);
                    background: linear-gradient(180deg, rgba(239, 68, 68, 0.08) 0%, #0d0d12 100%);
                }
                .vcenter-kpi-box.active-warn {
                    border-color: rgba(245, 158, 11, 0.4);
                    background: linear-gradient(180deg, rgba(245, 158, 11, 0.06) 0%, #0d0d12 100%);
                }
                .vcenter-kpi-box.active-success {
                    border-color: rgba(34, 197, 94, 0.3);
                }
                .vcenter-kpi-label {
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.08em;
                    color: #94a3b8;
                    text-transform: uppercase;
                    margin-bottom: 8px;
                    display: block;
                }
                .vcenter-kpi-value {
                    font-size: 28px;
                    font-weight: 800;
                    font-family: 'DM Mono', monospace;
                    line-height: 1;
                    color: #ffffff;
                }
                .vcenter-kpi-sub {
                    font-size: 11px;
                    color: #64748b;
                    margin-top: 6px;
                }
                /* COMMAND / FILTER BAR */
                .vcenter-filter-bar {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: #0d0d12;
                    border: 1px solid #202028;
                    border-radius: 8px;
                    padding: 10px 16px;
                    margin-bottom: 24px;
                    flex-wrap: wrap;
                    gap: 12px;
                }
                .vcenter-tabs {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    flex-wrap: wrap;
                }
                .vcenter-tab-btn {
                    background: transparent;
                    border: 1px solid transparent;
                    color: #94a3b8;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                    letter-spacing: 0.03em;
                    cursor: pointer;
                    transition: all 0.15s;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .vcenter-tab-btn:hover {
                    color: #ffffff;
                    background: #171720;
                }
                .vcenter-tab-btn.active {
                    background: #f97316;
                    color: #ffffff;
                    font-weight: 700;
                }
                .vcenter-search-box {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    background: #060608;
                    border: 1px solid #262632;
                    border-radius: 6px;
                    padding: 6px 12px;
                    min-width: 240px;
                }
                .vcenter-search-input {
                    background: transparent;
                    border: none;
                    color: #ededed;
                    font-size: 12px;
                    width: 100%;
                    outline: none;
                }
                .vcenter-refresh-btn {
                    background: #171720;
                    border: 1px solid #262632;
                    color: #cbd5e1;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    transition: background 0.15s;
                }
                .vcenter-refresh-btn:hover {
                    background: #20202c;
                    color: #ffffff;
                }
                /* CARDS LIST */
                .vcenter-cards-grid {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                .vcenter-card {
                    background: #0d0d12;
                    border: 1px solid #202028;
                    border-radius: 8px;
                    padding: 20px 24px;
                    display: grid;
                    grid-template-columns: 2fr 1.6fr 1fr;
                    gap: 20px;
                    align-items: center;
                    transition: transform 0.15s, border-color 0.15s;
                    position: relative;
                }
                .vcenter-card:hover {
                    border-color: #383848;
                    transform: translateY(-1px);
                }
                .vcenter-card.priority-critical {
                    border-left: 4px solid #ef4444;
                }
                .vcenter-card.priority-high {
                    border-left: 4px solid #f59e0b;
                }
                .vcenter-card.priority-normal {
                    border-left: 4px solid #475569;
                }
                .vcenter-card-main {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                }
                .vcenter-tag-row {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex-wrap: wrap;
                }
                .vcenter-category-tag {
                    font-size: 10px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.07em;
                    color: #f97316;
                    background: rgba(249, 115, 22, 0.12);
                    padding: 2px 8px;
                    border-radius: 4px;
                    border: 1px solid rgba(249, 115, 22, 0.25);
                }
                .vcenter-priority-badge {
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 0.05em;
                    padding: 2px 8px;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }
                .vcenter-card-title {
                    font-size: 17px;
                    font-weight: 700;
                    color: #ffffff;
                    margin: 2px 0 0 0;
                    line-height: 1.3;
                }
                .vcenter-card-meta {
                    font-size: 12px;
                    color: #94a3b8;
                    display: flex;
                    align-items: center;
                    gap: 14px;
                    flex-wrap: wrap;
                    margin-top: 4px;
                }
                .vcenter-card-meta span {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
                /* INTEL PILLS */
                .vcenter-card-intel {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    padding-left: 10px;
                    border-left: 1px solid #1c1c24;
                }
                .vcenter-intel-row {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-size: 12px;
                }
                .vcenter-intel-label {
                    color: #64748b;
                    font-weight: 600;
                    min-width: 70px;
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }
                .vcenter-intel-val {
                    font-family: 'DM Mono', monospace;
                    font-weight: 600;
                    font-size: 12px;
                }
                .vcenter-chip-compliant {
                    color: #22c55e;
                    background: rgba(34, 197, 94, 0.1);
                    padding: 2px 6px;
                    border-radius: 4px;
                    border: 1px solid rgba(34, 197, 94, 0.25);
                }
                .vcenter-chip-incomplete {
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.12);
                    padding: 2px 6px;
                    border-radius: 4px;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                }
                .vcenter-reasons-list {
                    font-size: 11px;
                    color: #cbd5e1;
                    display: flex;
                    flex-direction: column;
                    gap: 3px;
                    margin-top: 2px;
                }
                .vcenter-reason-bullet {
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    color: #fca5a5;
                }
                /* ACTION AREA */
                .vcenter-card-action {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    justify-content: center;
                    gap: 12px;
                }
                .vcenter-status-indicator {
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.06em;
                    text-transform: uppercase;
                    padding: 4px 10px;
                    border-radius: 4px;
                    background: rgba(245, 158, 11, 0.12);
                    color: #f59e0b;
                    border: 1px solid rgba(245, 158, 11, 0.3);
                }
                .vcenter-review-btn {
                    background: #f97316;
                    color: #ffffff;
                    border: none;
                    padding: 10px 18px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 0.03em;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transition: background 0.15s, transform 0.1s;
                }
                .vcenter-review-btn:hover {
                    background: #ea580c;
                    transform: translateX(2px);
                }
                /* SKELETON / EMPTY */
                .vcenter-skeleton {
                    background: #0d0d12;
                    border: 1px solid #1f1f26;
                    border-radius: 8px;
                    padding: 24px;
                    height: 110px;
                    animation: pulse 1.5s infinite;
                }
                .vcenter-empty {
                    background: #0d0d12;
                    border: 1px dashed #262632;
                    border-radius: 8px;
                    padding: 60px 24px;
                    text-align: center;
                    color: #94a3b8;
                }
                .vcenter-empty h3 {
                    color: #ffffff;
                    font-size: 18px;
                    margin: 12px 0 6px 0;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 0.6; }
                    50% { opacity: 0.3; }
                }
                @media (max-width: 1024px) {
                    .vcenter-card {
                        grid-template-columns: 1fr;
                        gap: 16px;
                    }
                    .vcenter-card-intel {
                        border-left: none;
                        border-top: 1px solid #1c1c24;
                        padding-left: 0;
                        padding-top: 12px;
                    }
                    .vcenter-card-action {
                        flex-direction: row;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .vcenter-kpis {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
            `}</style>

            {/* HEADER */}
            <header className="vcenter-header">
                <div className="vcenter-title-area">
                    <span className="vcenter-eyebrow">
                        PRITHVI COMPLIANCE INTELLIGENCE · REGULATORY AUDIT
                    </span>
                    <h1>
                        <ClipboardCheck size={26} color="#f97316" />
                        VERIFICATION CENTER
                    </h1>
                    <p className="vcenter-subtitle">
                        {queueData?.mine_name || "Jharia Underground Demonstration Mine"} · Statutory Review Workspace
                    </p>
                </div>

                <button
                    type="button"
                    className="vcenter-refresh-btn"
                    onClick={() => void loadQueue()}
                    disabled={loading}
                >
                    <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                    {loading ? "SYNCING..." : "REFRESH QUEUE"}
                </button>
            </header>

            {/* REAL DATABASE COUNTERS */}
            <section className="vcenter-kpis">
                <div className="vcenter-kpi-box">
                    <span className="vcenter-kpi-label">SUBMITTED</span>
                    <div className="vcenter-kpi-value">{loading ? "--" : counts.submitted}</div>
                    <div className="vcenter-kpi-sub">Total field submissions</div>
                </div>

                <div className={`vcenter-kpi-box ${counts.review_required > 0 ? "active-warn" : ""}`}>
                    <span className="vcenter-kpi-label">REVIEW REQUIRED</span>
                    <div className="vcenter-kpi-value" style={{ color: counts.review_required > 0 ? "#f59e0b" : "#ffffff" }}>
                        {loading ? "--" : counts.review_required}
                    </div>
                    <div className="vcenter-kpi-sub">Pending manager verification</div>
                </div>

                <div className="vcenter-kpi-box active-success">
                    <span className="vcenter-kpi-label">VERIFIED</span>
                    <div className="vcenter-kpi-value" style={{ color: "#22c55e" }}>
                        {loading ? "--" : counts.verified}
                    </div>
                    <div className="vcenter-kpi-sub">Legally confirmed & closed</div>
                </div>

                <div className="vcenter-kpi-box">
                    <span className="vcenter-kpi-label">REJECTED</span>
                    <div className="vcenter-kpi-value" style={{ color: counts.rejected > 0 ? "#f87171" : "#ffffff" }}>
                        {loading ? "--" : counts.rejected}
                    </div>
                    <div className="vcenter-kpi-sub">Returned for correction</div>
                </div>

                <div className={`vcenter-kpi-box ${counts.high_risk_review > 0 ? "active-urgent" : ""}`}>
                    <span className="vcenter-kpi-label">HIGH-RISK REVIEW</span>
                    <div className="vcenter-kpi-value" style={{ color: counts.high_risk_review > 0 ? "#ef4444" : "#ffffff" }}>
                        {loading ? "--" : counts.high_risk_review}
                    </div>
                    <div className="vcenter-kpi-sub">Violations / Incomplete evidence</div>
                </div>
            </section>

            {/* ERROR BANNER */}
            {error && (
                <div style={{
                    background: "rgba(239, 68, 68, 0.12)",
                    border: "1px solid #ef4444",
                    borderRadius: "8px",
                    padding: "16px 20px",
                    marginBottom: "24px",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                }}>
                    <ShieldAlert size={20} color="#ef4444" />
                    <div>
                        <strong style={{ color: "#ef4444", display: "block" }}>API Connection Error</strong>
                        <span style={{ fontSize: "13px", color: "#fca5a5" }}>{error}</span>
                    </div>
                </div>
            )}

            {/* FILTER COMMAND BAR */}
            <div className="vcenter-filter-bar">
                <div className="vcenter-tabs">
                    <button
                        type="button"
                        className={`vcenter-tab-btn ${activeTab === "ALL" ? "active" : ""}`}
                        onClick={() => setActiveTab("ALL")}
                    >
                        <Layers size={13} />
                        ALL PENDING ({items.length})
                    </button>

                    <button
                        type="button"
                        className={`vcenter-tab-btn ${activeTab === "CRITICAL" ? "active" : ""}`}
                        onClick={() => setActiveTab("CRITICAL")}
                    >
                        <Flame size={13} />
                        CRITICAL PRIORITY ({items.filter(i => i.priority === "CRITICAL").length})
                    </button>

                    <button
                        type="button"
                        className={`vcenter-tab-btn ${activeTab === "HIGH" ? "active" : ""}`}
                        onClick={() => setActiveTab("HIGH")}
                    >
                        <AlertTriangle size={13} />
                        HIGH RISK ({items.filter(i => i.priority === "HIGH" || i.risk_level === "HIGH").length})
                    </button>

                    <button
                        type="button"
                        className={`vcenter-tab-btn ${activeTab === "VIOLATIONS" ? "active" : ""}`}
                        onClick={() => setActiveTab("VIOLATIONS")}
                    >
                        <AlertOctagon size={13} />
                        VIOLATIONS ({items.filter(i => i.has_violations).length})
                    </button>

                    <button
                        type="button"
                        className={`vcenter-tab-btn ${activeTab === "INCOMPLETE" ? "active" : ""}`}
                        onClick={() => setActiveTab("INCOMPLETE")}
                    >
                        <ShieldAlert size={13} />
                        INCOMPLETE EVIDENCE ({items.filter(i => !i.evidence_compliant).length})
                    </button>
                </div>

                <div className="vcenter-search-box">
                    <Search size={14} color="#64748b" />
                    <input
                        type="text"
                        placeholder="Filter by ID, template, inspector..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="vcenter-search-input"
                    />
                </div>
            </div>

            {/* INSPECTION QUEUE CARDS */}
            <div className="vcenter-cards-grid">
                {loading && (
                    <>
                        <div className="vcenter-skeleton" />
                        <div className="vcenter-skeleton" />
                        <div className="vcenter-skeleton" />
                    </>
                )}

                {!loading && filteredItems.length === 0 && (
                    <div className="vcenter-empty">
                        <CheckCircle2 size={42} color="#22c55e" style={{ margin: "0 auto" }} />
                        <h3>Regulatory Review Queue Clear</h3>
                        <p>No inspections matching the active filter currently require verification.</p>
                    </div>
                )}

                {!loading && filteredItems.map((item) => {
                    const prio = getPriorityBadge(item.priority);
                    return (
                        <article
                            key={item.inspection_id}
                            className={`vcenter-card priority-${item.priority.toLowerCase()}`}
                        >
                            {/* MAIN IDENTITY */}
                            <div className="vcenter-card-main">
                                <div className="vcenter-tag-row">
                                    <span className="vcenter-category-tag">
                                        {item.category}
                                    </span>
                                    <span
                                        className="vcenter-priority-badge"
                                        style={{
                                            background: prio.bg,
                                            border: `1px solid ${prio.border}`,
                                            color: prio.color,
                                        }}
                                    >
                                        {prio.icon}
                                        {prio.label}
                                    </span>
                                    <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "'DM Mono', monospace" }}>
                                        {item.inspection_id}
                                    </span>
                                </div>

                                <h2 className="vcenter-card-title">{item.template_name}</h2>

                                <div className="vcenter-card-meta">
                                    <span>
                                        <strong>Submitted by:</strong> {item.inspector_name}
                                    </span>
                                    <span>•</span>
                                    <span>
                                        <strong>Submitted:</strong> {formatTimestamp(item.submitted_at)}
                                    </span>
                                    {item.regulation_reference && (
                                        <>
                                            <span>•</span>
                                            <span style={{ color: "#f97316" }}>{item.regulation_reference}</span>
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* COMPLIANCE INTELLIGENCE */}
                            <div className="vcenter-card-intel">
                                <div className="vcenter-intel-row">
                                    <span className="vcenter-intel-label">RISK:</span>
                                    <span
                                        className="vcenter-intel-val"
                                        style={{
                                            color:
                                                item.risk_level === "CRITICAL"
                                                    ? "#ef4444"
                                                    : item.risk_level === "HIGH"
                                                    ? "#f59e0b"
                                                    : "#cbd5e1",
                                        }}
                                    >
                                        {item.risk_level}
                                    </span>
                                </div>

                                <div className="vcenter-intel-row">
                                    <span className="vcenter-intel-label">EVIDENCE:</span>
                                    <span className="vcenter-intel-val">
                                        {item.evidence_count} / {item.required_evidence_count}
                                    </span>
                                    <span className={item.evidence_compliant ? "vcenter-chip-compliant" : "vcenter-chip-incomplete"}>
                                        {item.evidence_compliant ? "COMPLIANT" : "INCOMPLETE"}
                                    </span>
                                </div>

                                <div className="vcenter-intel-row">
                                    <span className="vcenter-intel-label">FINDINGS:</span>
                                    <span
                                        className="vcenter-intel-val"
                                        style={{ color: item.findings_count > 0 ? "#f59e0b" : "#94a3b8" }}
                                    >
                                        {item.findings_count} {item.findings_count === 1 ? "finding" : "findings"}
                                    </span>
                                </div>

                                {item.priority_reasons.length > 0 && (
                                    <div className="vcenter-reasons-list">
                                        {item.priority_reasons.map((reason, idx) => (
                                            <div key={idx} className="vcenter-reason-bullet">
                                                <span>•</span>
                                                <span>{reason}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* DECISION ACTION */}
                            <div className="vcenter-card-action">
                                <span className="vcenter-status-indicator">
                                    {item.inspection_status.replaceAll("_", " ").toUpperCase()}
                                </span>

                                <button
                                    type="button"
                                    className="vcenter-review-btn"
                                    onClick={() => navigate(`/verification/${item.inspection_id}`)}
                                >
                                    REVIEW CASE
                                    <ArrowRight size={15} />
                                </button>
                            </div>
                        </article>
                    );
                })}
            </div>
        </section>
    );
}