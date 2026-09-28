import { useEffect, useState } from "react";
import {
    AlertTriangle,
    ArrowLeft,
    CheckCircle2,
    FileCheck2,
    FileText,
    History,
    Layers,
    RefreshCw,
    ShieldAlert,
    ShieldCheck,
    X,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import {
    getInspectionVerificationDetail,
    verifyInspectionOperational,
    returnInspectionOperational,
    type InspectionVerificationDetailResponse,
} from "../api/verification";

function formatTimestamp(value?: string | null): string {
    if (!value) return "—";
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

export default function VerificationReview() {
    const { inspectionId } = useParams<{ inspectionId: string }>();
    const navigate = useNavigate();

    const [dossier, setDossier] = useState<InspectionVerificationDetailResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Decision state
    const [verifying, setVerifying] = useState(false);
    const [verifyNotes, setVerifyNotes] = useState("");
    const [showVerifyModal, setShowVerifyModal] = useState(false);

    // Return for correction modal state
    const [showReturnModal, setShowReturnModal] = useState(false);
    const [returnReason, setReturnReason] = useState("");
    const [returning, setReturning] = useState(false);
    const [actionFeedback, setActionFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

    async function loadDossier() {
        if (!inspectionId) {
            setError("Inspection ID is missing.");
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            setError(null);
            const data = await getInspectionVerificationDetail(inspectionId);
            setDossier(data);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Unable to load inspection verification dossier."
            );
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        void loadDossier();
    }, [inspectionId]);

    async function handleVerify() {
        if (!inspectionId) return;
        try {
            setVerifying(true);
            setActionFeedback(null);
            const res = await verifyInspectionOperational(inspectionId, {
                reviewer_id: "MGR-JHARIA-01",
                notes: verifyNotes.trim() || undefined,
            });
            setActionFeedback({ type: "success", message: res.message });
            setShowVerifyModal(false);
            // Reload updated dossier
            await loadDossier();
        } catch (err) {
            setActionFeedback({
                type: "error",
                message: err instanceof Error ? err.message : "Failed to verify inspection.",
            });
        } finally {
            setVerifying(false);
        }
    }

    async function handleReturn() {
        if (!inspectionId) return;
        if (!returnReason.trim() || returnReason.trim().length < 5) {
            setActionFeedback({
                type: "error",
                message: "A valid, substantive reason (at least 5 characters) is required to return this inspection.",
            });
            return;
        }

        try {
            setReturning(true);
            setActionFeedback(null);
            const res = await returnInspectionOperational(inspectionId, {
                reviewer_id: "MGR-JHARIA-01",
                reason: returnReason.trim(),
            });
            setActionFeedback({ type: "success", message: res.message });
            setShowReturnModal(false);
            setReturnReason("");
            // Reload updated dossier
            await loadDossier();
        } catch (err) {
            setActionFeedback({
                type: "error",
                message: err instanceof Error ? err.message : "Failed to return inspection for correction.",
            });
        } finally {
            setReturning(false);
        }
    }

    if (loading) {
        return (
            <div style={{ padding: "60px 40px", backgroundColor: "#060608", minHeight: "100vh", color: "#ededed" }}>
                <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
                    <p style={{ color: "#94a3b8", fontSize: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <RefreshCw size={16} className="animate-spin" /> Loading compliance dossier for {inspectionId}...
                    </p>
                </div>
            </div>
        );
    }

    if (error || !dossier) {
        return (
            <div style={{ padding: "60px 40px", backgroundColor: "#060608", minHeight: "100vh", color: "#ededed" }}>
                <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
                    <div style={{ background: "#0d0d12", border: "1px solid #ef4444", padding: "24px", borderRadius: "8px" }}>
                        <ShieldAlert size={24} color="#ef4444" style={{ marginBottom: "12px" }} />
                        <h2 style={{ color: "#ffffff", margin: "0 0 8px 0" }}>Inspection Review Dossier Unavailable</h2>
                        <p style={{ color: "#fca5a5" }}>{error || "Inspection record not found."}</p>
                        <button
                            type="button"
                            onClick={() => navigate("/verification")}
                            style={{ background: "#202028", color: "#ffffff", border: "none", padding: "8px 16px", borderRadius: "4px", marginTop: "16px", cursor: "pointer" }}
                        >
                            Return to Verification Center
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    const {
        template_name,
        category,
        regulation_reference,
        frequency,
        mine_name,
        inspector_name,
        submitted_at,
        inspection_status,
        measurements,
        checklist,
        evidence,
        evidence_completeness,
        findings,
        review_summary,
        risk_level,
        audit_history,
        can_verify,
        validation_errors,
    } = dossier;

    return (
        <section className="vreview-root">
            {/* INLINE INDUSTRIAL STYLES */}
            <style>{`
                .vreview-root {
                    min-height: 100vh;
                    background-color: #060608;
                    color: #ededed;
                    padding: 28px 36px 80px 36px;
                    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                }
                .vreview-container {
                    max-width: 1240px;
                    margin: 0 auto;
                }
                .vreview-back-btn {
                    background: transparent;
                    border: none;
                    color: #94a3b8;
                    font-size: 13px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    cursor: pointer;
                    margin-bottom: 20px;
                    padding: 0;
                    transition: color 0.15s;
                }
                .vreview-back-btn:hover {
                    color: #f97316;
                }
                /* SECTION CARDS */
                .vreview-section {
                    background: #0d0d12;
                    border: 1px solid #202028;
                    border-radius: 8px;
                    padding: 24px 28px;
                    margin-bottom: 22px;
                }
                .vreview-section-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid #1f1f28;
                    padding-bottom: 14px;
                    margin-bottom: 18px;
                }
                .vreview-section-title {
                    font-size: 14px;
                    font-weight: 700;
                    letter-spacing: 0.08em;
                    color: #f97316;
                    text-transform: uppercase;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin: 0;
                }
                /* IDENTITY GRID */
                .vreview-identity-grid {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 18px;
                }
                .vreview-identity-item {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                .vreview-identity-label {
                    font-size: 11px;
                    color: #64748b;
                    font-weight: 700;
                    letter-spacing: 0.06em;
                    text-transform: uppercase;
                }
                .vreview-identity-value {
                    font-size: 14px;
                    font-weight: 600;
                    color: #ffffff;
                }
                /* TABLES */
                .vreview-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 13px;
                }
                .vreview-table th {
                    text-align: left;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.06em;
                    color: #64748b;
                    text-transform: uppercase;
                    padding: 10px 14px;
                    border-bottom: 1px solid #202028;
                    background: #09090d;
                }
                .vreview-table td {
                    padding: 12px 14px;
                    border-bottom: 1px solid #1a1a22;
                    color: #cbd5e1;
                }
                .vreview-table tr.violation-row {
                    background: rgba(239, 68, 68, 0.08);
                }
                .vreview-table tr.violation-row td {
                    color: #ffffff;
                }
                /* STATUS BADGES */
                .badge-pass {
                    font-size: 11px;
                    font-weight: 700;
                    color: #22c55e;
                    background: rgba(34, 197, 94, 0.12);
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    padding: 3px 8px;
                    border-radius: 4px;
                    display: inline-block;
                }
                .badge-violation {
                    font-size: 11px;
                    font-weight: 700;
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.15);
                    border: 1px solid rgba(239, 68, 68, 0.4);
                    padding: 3px 8px;
                    border-radius: 4px;
                    display: inline-block;
                    animation: pulse 2s infinite;
                }
                .badge-fail {
                    font-size: 11px;
                    font-weight: 700;
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.15);
                    border: 1px solid rgba(239, 68, 68, 0.4);
                    padding: 3px 8px;
                    border-radius: 4px;
                    display: inline-block;
                }
                .badge-na {
                    font-size: 11px;
                    font-weight: 600;
                    color: #94a3b8;
                    background: #171720;
                    border: 1px solid #282834;
                    padding: 3px 8px;
                    border-radius: 4px;
                    display: inline-block;
                }
                /* SUMMARY BANNER */
                .vreview-summary-banner {
                    background: #111118;
                    border: 1px solid #282834;
                    border-radius: 8px;
                    padding: 18px 22px;
                    margin-bottom: 22px;
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 16px;
                }
                .vreview-summary-item strong {
                    font-size: 11px;
                    color: #64748b;
                    text-transform: uppercase;
                    display: block;
                    margin-bottom: 4px;
                }
                .vreview-summary-item span {
                    font-size: 13px;
                    font-weight: 600;
                    color: #ffffff;
                }
                /* ACTION BUTTONS */
                .vreview-actions-bar {
                    display: flex;
                    align-items: center;
                    justify-content: flex-end;
                    gap: 14px;
                    background: #0d0d12;
                    border: 1px solid #202028;
                    border-radius: 8px;
                    padding: 18px 24px;
                }
                .btn-verify {
                    background: #22c55e;
                    color: #060608;
                    border: none;
                    padding: 11px 24px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 800;
                    letter-spacing: 0.04em;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transition: background 0.15s;
                }
                .btn-verify:hover:not(:disabled) {
                    background: #16a34a;
                    color: #ffffff;
                }
                .btn-verify:disabled {
                    background: #1f2937;
                    color: #6b7280;
                    cursor: not-allowed;
                }
                .btn-return {
                    background: rgba(239, 68, 68, 0.15);
                    color: #ef4444;
                    border: 1px solid #ef4444;
                    padding: 11px 22px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 0.04em;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transition: all 0.15s;
                }
                .btn-return:hover {
                    background: #ef4444;
                    color: #ffffff;
                }
                /* MODAL */
                .vreview-modal-backdrop {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: rgba(0, 0, 0, 0.85);
                    backdrop-filter: blur(4px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    padding: 20px;
                }
                .vreview-modal {
                    background: #0e0e14;
                    border: 1px solid #282834;
                    border-radius: 10px;
                    max-width: 540px;
                    width: 100%;
                    padding: 24px 28px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.8);
                }
                .vreview-textarea {
                    width: 100%;
                    min-height: 110px;
                    background: #060608;
                    border: 1px solid #2a2a38;
                    border-radius: 6px;
                    color: #ededed;
                    padding: 12px;
                    font-family: inherit;
                    font-size: 13px;
                    margin: 14px 0 18px 0;
                    resize: vertical;
                    outline: none;
                }
                .vreview-textarea:focus {
                    border-color: #f97316;
                }
                @media (max-width: 900px) {
                    .vreview-identity-grid {
                        grid-template-columns: repeat(2, 1fr);
                    }
                    .vreview-summary-banner {
                        grid-template-columns: 1fr;
                    }
                }
            `}</style>

            <div className="vreview-container">
                {/* TOP BREADCRUMB */}
                <button
                    type="button"
                    className="vreview-back-btn"
                    onClick={() => navigate("/verification")}
                >
                    <ArrowLeft size={16} />
                    BACK TO VERIFICATION QUEUE
                </button>

                {/* FEEDBACK BANNER */}
                {actionFeedback && (
                    <div
                        style={{
                            background:
                                actionFeedback.type === "success"
                                    ? "rgba(34, 197, 94, 0.12)"
                                    : "rgba(239, 68, 68, 0.12)",
                            border: `1px solid ${actionFeedback.type === "success" ? "#22c55e" : "#ef4444"}`,
                            color: actionFeedback.type === "success" ? "#86efac" : "#fca5a5",
                            borderRadius: "8px",
                            padding: "14px 18px",
                            marginBottom: "20px",
                            display: "flex",
                            alignItems: "center",
                            gap: "10px",
                        }}
                    >
                        {actionFeedback.type === "success" ? <CheckCircle2 size={18} /> : <ShieldAlert size={18} />}
                        <span style={{ fontSize: "13px", fontWeight: 600 }}>{actionFeedback.message}</span>
                    </div>
                )}

                {/* A. INSPECTION IDENTITY */}
                <section className="vreview-section">
                    <div className="vreview-section-header">
                        <h2 className="vreview-section-title">
                            <Layers size={16} />
                            A. INSPECTION IDENTITY
                        </h2>
                        <span
                            style={{
                                fontSize: "11px",
                                fontWeight: 700,
                                textTransform: "uppercase",
                                padding: "4px 10px",
                                borderRadius: "4px",
                                background:
                                    inspection_status === "verified"
                                        ? "rgba(34, 197, 94, 0.15)"
                                        : inspection_status === "rejected"
                                        ? "rgba(239, 68, 68, 0.15)"
                                        : "rgba(245, 158, 11, 0.15)",
                                color:
                                    inspection_status === "verified"
                                        ? "#22c55e"
                                        : inspection_status === "rejected"
                                        ? "#ef4444"
                                        : "#f59e0b",
                                border: `1px solid ${
                                    inspection_status === "verified"
                                        ? "#22c55e"
                                        : inspection_status === "rejected"
                                        ? "#ef4444"
                                        : "#f59e0b"
                                }`,
                            }}
                        >
                            STATUS: {inspection_status.replaceAll("_", " ").toUpperCase()}
                        </span>
                    </div>

                    <div className="vreview-identity-grid">
                        <div className="vreview-identity-item">
                            <span className="vreview-identity-label">INSPECTION TYPE</span>
                            <span className="vreview-identity-value">{template_name}</span>
                        </div>

                        <div className="vreview-identity-item">
                            <span className="vreview-identity-label">COMPLIANCE DOMAIN</span>
                            <span className="vreview-identity-value" style={{ color: "#f97316" }}>
                                {category}
                            </span>
                        </div>

                        <div className="vreview-identity-item">
                            <span className="vreview-identity-label">REGULATION REFERENCE</span>
                            <span className="vreview-identity-value">{regulation_reference || "Mines Act / CMR 2017"}</span>
                        </div>

                        <div className="vreview-identity-item">
                            <span className="vreview-identity-label">STATUTORY FREQUENCY</span>
                            <span className="vreview-identity-value">{frequency || "Periodic"}</span>
                        </div>

                        <div className="vreview-identity-item">
                            <span className="vreview-identity-label">ALLOCATED MINE</span>
                            <span className="vreview-identity-value">{mine_name}</span>
                        </div>

                        <div className="vreview-identity-item">
                            <span className="vreview-identity-label">SUBMITTING INSPECTOR</span>
                            <span className="vreview-identity-value">{inspector_name}</span>
                        </div>

                        <div className="vreview-identity-item">
                            <span className="vreview-identity-label">SUBMISSION TIMESTAMP</span>
                            <span className="vreview-identity-value">{formatTimestamp(submitted_at)}</span>
                        </div>

                        <div className="vreview-identity-item">
                            <span className="vreview-identity-label">INSPECTION ID</span>
                            <span className="vreview-identity-value" style={{ fontFamily: "'DM Mono', monospace" }}>
                                {inspectionId}
                            </span>
                        </div>
                    </div>
                </section>

                {/* B. MEASUREMENTS */}
                <section className="vreview-section">
                    <div className="vreview-section-header">
                        <h2 className="vreview-section-title">
                            <FileCheck2 size={16} />
                            B. SUBMITTED MEASUREMENTS & STATUTORY THRESHOLDS
                        </h2>
                        <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                            {measurements.length} parameter{measurements.length === 1 ? "" : "s"} recorded
                        </span>
                    </div>

                    {measurements.length === 0 ? (
                        <p style={{ color: "#94a3b8", fontSize: "13px" }}>No measurements submitted for this inspection.</p>
                    ) : (
                        <table className="vreview-table">
                            <thead>
                                <tr>
                                    <th>Parameter</th>
                                    <th>Recorded Value</th>
                                    <th>Statutory Threshold</th>
                                    <th>Threshold Metadata</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {measurements.map((m) => {
                                    const isViol = m.status === "VIOLATION";
                                    return (
                                        <tr key={m.measurement_id} className={isViol ? "violation-row" : ""}>
                                            <td>
                                                <strong style={{ color: isViol ? "#fca5a5" : "#ffffff" }}>
                                                    {m.parameter}
                                                </strong>
                                            </td>
                                            <td style={{ fontFamily: "'DM Mono', monospace", fontWeight: 700 }}>
                                                {m.value} {m.unit || ""}
                                            </td>
                                            <td style={{ fontFamily: "'DM Mono', monospace", color: isViol ? "#ef4444" : "#94a3b8" }}>
                                                {m.threshold || "Standard"}
                                            </td>
                                            <td style={{ fontSize: "12px", color: "#64748b" }}>
                                                {m.threshold_label || "Statutory compliance limit"}
                                            </td>
                                            <td>
                                                <span className={isViol ? "badge-violation" : "badge-pass"}>
                                                    {m.status}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </section>

                {/* C. CHECKLIST */}
                <section className="vreview-section">
                    <div className="vreview-section-header">
                        <h2 className="vreview-section-title">
                            <CheckCircle2 size={16} />
                            C. STATUTORY CHECKLIST VERIFICATION
                        </h2>
                        <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                            {checklist.length} checklist item{checklist.length === 1 ? "" : "s"}
                        </span>
                    </div>

                    {checklist.length === 0 ? (
                        <p style={{ color: "#94a3b8", fontSize: "13px" }}>No checklist items defined for this inspection.</p>
                    ) : (
                        <table className="vreview-table">
                            <thead>
                                <tr>
                                    <th>Item ID</th>
                                    <th>Checklist Requirement</th>
                                    <th>Mandatory</th>
                                    <th>Field Observation</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {checklist.map((chk) => (
                                    <tr key={chk.item_id}>
                                        <td style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", color: "#94a3b8" }}>
                                            {chk.item_id}
                                        </td>
                                        <td style={{ color: chk.status === "FAIL" ? "#fca5a5" : "#ffffff" }}>
                                            {chk.question}
                                        </td>
                                        <td style={{ fontSize: "11px", color: chk.required ? "#f97316" : "#64748b" }}>
                                            {chk.required ? "MANDATORY" : "OPTIONAL"}
                                        </td>
                                        <td style={{ fontSize: "12px", color: "#94a3b8" }}>
                                            {chk.observation || "—"}
                                        </td>
                                        <td>
                                            <span
                                                className={
                                                    chk.status === "PASS"
                                                        ? "badge-pass"
                                                        : chk.status === "FAIL"
                                                        ? "badge-fail"
                                                        : "badge-na"
                                                }
                                            >
                                                {chk.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </section>

                {/* D. EVIDENCE & COMPLETENESS */}
                <section className="vreview-section">
                    <div className="vreview-section-header">
                        <h2 className="vreview-section-title">
                            <FileText size={16} />
                            D. FIELD EVIDENCE & REGULATORY COMPLETENESS
                        </h2>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ fontSize: "12px", color: "#94a3b8", fontFamily: "'DM Mono', monospace" }}>
                                {evidence_completeness.actual_count} / {evidence_completeness.required_count} REQUIRED
                            </span>
                            <span
                                style={{
                                    fontSize: "11px",
                                    fontWeight: 700,
                                    padding: "3px 8px",
                                    borderRadius: "4px",
                                    background: evidence_completeness.is_compliant ? "rgba(34, 197, 94, 0.15)" : "rgba(239, 68, 68, 0.15)",
                                    color: evidence_completeness.is_compliant ? "#22c55e" : "#ef4444",
                                    border: `1px solid ${evidence_completeness.is_compliant ? "#22c55e" : "#ef4444"}`,
                                }}
                            >
                                {evidence_completeness.is_compliant ? "COMPLIANT" : "INCOMPLETE"}
                            </span>
                        </div>
                    </div>

                    {!evidence_completeness.is_compliant && evidence_completeness.missing_requirements.length > 0 && (
                        <div
                            style={{
                                background: "rgba(239, 68, 68, 0.1)",
                                border: "1px solid #ef4444",
                                borderRadius: "6px",
                                padding: "12px 16px",
                                marginBottom: "16px",
                                color: "#fca5a5",
                                fontSize: "13px",
                            }}
                        >
                            <strong>Missing Required Evidence Items:</strong>
                            <ul style={{ margin: "6px 0 0 16px", padding: 0 }}>
                                {evidence_completeness.missing_requirements.map((req, idx) => (
                                    <li key={idx}>{req}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {evidence.length === 0 ? (
                        <p style={{ color: "#94a3b8", fontSize: "13px" }}>No evidence files attached to this inspection.</p>
                    ) : (
                        <table className="vreview-table">
                            <thead>
                                <tr>
                                    <th>Evidence ID</th>
                                    <th>Type</th>
                                    <th>Reference / Filename</th>
                                    <th>Captured Timestamp</th>
                                    <th>SHA-256 Hash</th>
                                </tr>
                            </thead>
                            <tbody>
                                {evidence.map((ev) => (
                                    <tr key={ev.evidence_id}>
                                        <td style={{ fontFamily: "'DM Mono', monospace", color: "#f97316" }}>
                                            {ev.evidence_id}
                                        </td>
                                        <td style={{ textTransform: "uppercase", fontSize: "11px", fontWeight: 700 }}>
                                            {ev.evidence_type}
                                        </td>
                                        <td style={{ fontSize: "12px", color: "#ffffff" }}>
                                            {ev.name || ev.file_path || "evidence_attachment"}
                                        </td>
                                        <td style={{ fontSize: "12px", color: "#94a3b8" }}>
                                            {formatTimestamp(ev.captured_at)}
                                        </td>
                                        <td style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "#64748b" }}>
                                            {ev.sha256_hash ? ev.sha256_hash.slice(0, 16) + "..." : "Recorded"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </section>

                {/* D2. EVIDENCE INTEGRITY AUDIT CHAIN (Phase 2 Task 7) */}
                <section className="vreview-section">
                    <div className="vreview-section-header">
                        <h2 className="vreview-section-title">
                            <span style={{ fontSize: 16 }}>⛓️</span>
                            D2. EVIDENCE INTEGRITY &amp; BLOCKCHAIN AUDIT CHAIN
                        </h2>
                        <button
                            onClick={() => navigate(`/audit-chain/inspection/${inspectionId}`)}
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: 6,
                                padding: "6px 16px",
                                borderRadius: 7,
                                border: "1px solid #f97316",
                                background: "transparent",
                                color: "#f97316",
                                fontSize: 12,
                                fontWeight: 700,
                                cursor: "pointer",
                                letterSpacing: "0.02em",
                                transition: "background 0.15s",
                            }}
                            onMouseEnter={e => (e.currentTarget.style.background = "#f9731622")}
                            onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
                        >
                            🔗 View Full Audit Chain
                        </button>
                    </div>
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(4, 1fr)",
                            gap: 8,
                            padding: "12px 0 4px",
                        }}
                    >
                        {[
                            { icon: "📎", label: "Evidence Captured", desc: `${evidence.length} items` },
                            { icon: "🔢", label: "SHA-256 Hashed", desc: "Deterministic fingerprint" },
                            { icon: "📦", label: "IPFS CID Computed", desc: "Dev: local hash mode" },
                            { icon: "⛓️", label: "Blockchain Anchor", desc: "Demo audit mode" },
                        ].map((step) => (
                            <div
                                key={step.label}
                                style={{
                                    background: "#060608",
                                    border: "1px solid #1f2937",
                                    borderRadius: 8,
                                    padding: "10px 12px",
                                    textAlign: "center",
                                }}
                            >
                                <div style={{ fontSize: 20, marginBottom: 4 }}>{step.icon}</div>
                                <div style={{ fontSize: 11, fontWeight: 700, color: "#e5e7eb", marginBottom: 2 }}>{step.label}</div>
                                <div style={{ fontSize: 10, color: "#6b7280" }}>{step.desc}</div>
                            </div>
                        ))}
                    </div>
                    <p style={{ fontSize: 12, color: "#6b7280", margin: "8px 0 0", lineHeight: 1.6 }}>
                        Each evidence item is cryptographically fingerprinted (SHA-256), assigned an IPFS content address,
                        and anchored to a tamper-evident blockchain reference.
                        Click <strong style={{ color: "#f97316" }}>View Full Audit Chain</strong> to inspect individual evidence records,
                        verify integrity, and view anchor proofs.
                    </p>
                </section>

                {/* E. FINDINGS */}
                <section className="vreview-section">
                    <div className="vreview-section-header">
                        <h2 className="vreview-section-title">
                            <AlertTriangle size={16} />
                            E. STATUTORY FINDINGS & SAFETY OBSERVATIONS
                        </h2>
                        <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                            {findings.length} finding{findings.length === 1 ? "" : "s"}
                        </span>
                    </div>

                    {findings.length === 0 ? (
                        <p style={{ color: "#94a3b8", fontSize: "13px" }}>No formal findings recorded for this inspection.</p>
                    ) : (
                        <table className="vreview-table">
                            <thead>
                                <tr>
                                    <th>Finding ID</th>
                                    <th>Severity</th>
                                    <th>Description</th>
                                    <th>Linked Evidence</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {findings.map((f) => (
                                    <tr key={f.finding_id}>
                                        <td style={{ fontFamily: "'DM Mono', monospace", color: "#f97316" }}>
                                            {f.finding_id}
                                        </td>
                                        <td>
                                            <span
                                                style={{
                                                    fontSize: "11px",
                                                    fontWeight: 700,
                                                    padding: "2px 6px",
                                                    borderRadius: "4px",
                                                    color: f.severity === "critical" ? "#ef4444" : "#f59e0b",
                                                    background: f.severity === "critical" ? "rgba(239, 68, 68, 0.15)" : "rgba(245, 158, 11, 0.15)",
                                                }}
                                            >
                                                {f.severity.toUpperCase()}
                                            </span>
                                        </td>
                                        <td style={{ color: "#ffffff" }}>{f.description}</td>
                                        <td style={{ fontSize: "12px", color: "#94a3b8" }}>
                                            {f.evidence_linked.length > 0 ? f.evidence_linked.join(", ") : "None linked"}
                                        </td>
                                        <td style={{ fontSize: "11px", fontWeight: 700, color: "#64748b" }}>
                                            {f.status.toUpperCase()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </section>

                {/* REVIEW SUMMARY & RISK */}
                <div className="vreview-summary-banner">
                    <div className="vreview-summary-item">
                        <strong>EVIDENCE COMPLETENESS</strong>
                        <span>{review_summary.evidence_completeness}</span>
                    </div>

                    <div className="vreview-summary-item">
                        <strong>MEASUREMENT COMPLIANCE</strong>
                        <span style={{ color: review_summary.has_violations ? "#ef4444" : "#22c55e" }}>
                            {review_summary.measurement_compliance}
                        </span>
                    </div>

                    <div className="vreview-summary-item">
                        <strong>RISK LEVEL (TASK 3 ENGINE)</strong>
                        <span
                            style={{
                                color:
                                    risk_level === "CRITICAL"
                                        ? "#ef4444"
                                        : risk_level === "HIGH"
                                        ? "#f59e0b"
                                        : "#22c55e",
                            }}
                        >
                            {risk_level}
                        </span>
                    </div>

                    <div className="vreview-summary-item" style={{ gridColumn: "span 3" }}>
                        <strong>RECURRING COMPLIANCE PATTERN</strong>
                        <span style={{ color: "#cbd5e1" }}>{review_summary.recurring_issue_status}</span>
                    </div>
                </div>

                {/* VALIDATION WARNING IF VERIFY BLOCKED */}
                {!can_verify && validation_errors.length > 0 && (
                    <div
                        style={{
                            background: "rgba(245, 158, 11, 0.12)",
                            border: "1px solid #f59e0b",
                            borderRadius: "8px",
                            padding: "16px 20px",
                            marginBottom: "20px",
                        }}
                    >
                        <strong style={{ color: "#f59e0b", display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                            <AlertTriangle size={18} />
                            Cannot Complete Verification (Server-Side Rules)
                        </strong>
                        <ul style={{ margin: "4px 0 0 20px", padding: 0, color: "#fcd34d", fontSize: "13px" }}>
                            {validation_errors.map((err, idx) => (
                                <li key={idx}>{err}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* VERIFICATION ACTIONS BAR */}
                <div className="vreview-actions-bar">
                    <button
                        type="button"
                        className="btn-return"
                        onClick={() => setShowReturnModal(true)}
                    >
                        <ShieldAlert size={16} />
                        REJECT / RETURN FOR CORRECTION
                    </button>

                    <button
                        type="button"
                        className="btn-verify"
                        disabled={!can_verify || verifying}
                        onClick={() => setShowVerifyModal(true)}
                    >
                        <ShieldCheck size={17} />
                        VERIFY INSPECTION
                    </button>
                </div>

                {/* VERIFICATION AUDIT TRAIL */}
                <section className="vreview-section" style={{ marginTop: "24px" }}>
                    <div className="vreview-section-header">
                        <h2 className="vreview-section-title">
                            <History size={16} />
                            VERIFICATION HISTORY & AUDIT TRAIL
                        </h2>
                        <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                            {audit_history.length} decision record{audit_history.length === 1 ? "" : "s"}
                        </span>
                    </div>

                    {audit_history.length === 0 ? (
                        <p style={{ color: "#94a3b8", fontSize: "13px" }}>No verification reviews recorded yet.</p>
                    ) : (
                        <table className="vreview-table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Reviewer</th>
                                    <th>Decision</th>
                                    <th>Status Transition</th>
                                    <th>Persisted Reason / Explanation</th>
                                </tr>
                            </thead>
                            <tbody>
                                {audit_history.map((audit) => (
                                    <tr key={audit.review_id}>
                                        <td style={{ fontSize: "12px", color: "#cbd5e1" }}>
                                            {formatTimestamp(audit.timestamp)}
                                        </td>
                                        <td style={{ fontWeight: 600, color: "#ffffff" }}>
                                            {audit.reviewer_name || audit.reviewer_id}
                                        </td>
                                        <td>
                                            <span
                                                style={{
                                                    fontSize: "11px",
                                                    fontWeight: 700,
                                                    padding: "3px 8px",
                                                    borderRadius: "4px",
                                                    color:
                                                        audit.decision.includes("return") || audit.decision.includes("reject")
                                                            ? "#ef4444"
                                                            : "#22c55e",
                                                    background:
                                                        audit.decision.includes("return") || audit.decision.includes("reject")
                                                            ? "rgba(239, 68, 68, 0.12)"
                                                            : "rgba(34, 197, 94, 0.12)",
                                                }}
                                            >
                                                {audit.decision.toUpperCase()}
                                            </span>
                                        </td>
                                        <td style={{ fontSize: "12px", fontFamily: "'DM Mono', monospace", color: "#94a3b8" }}>
                                            {audit.previous_status || "—"} → {audit.new_status || "—"}
                                        </td>
                                        <td style={{ color: "#ffffff" }}>{audit.reason}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </section>
            </div>

            {/* CONFIRM VERIFY MODAL */}
            {showVerifyModal && (
                <div className="vreview-modal-backdrop">
                    <div className="vreview-modal">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                            <h3 style={{ margin: 0, color: "#ffffff", fontSize: "18px", display: "flex", alignItems: "center", gap: "8px" }}>
                                <ShieldCheck size={20} color="#22c55e" />
                                Confirm Statutory Verification
                            </h3>
                            <button
                                type="button"
                                onClick={() => setShowVerifyModal(false)}
                                style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer" }}
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <p style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: 1.5 }}>
                            You are certifying that all field measurements, checklist items, and photographic evidence for <strong>{template_name}</strong> have been reviewed and satisfy regulatory statutory compliance under CMR 2017.
                        </p>

                        <label style={{ fontSize: "12px", color: "#94a3b8", fontWeight: 600 }}>
                            Manager Sign-off Notes (Optional):
                        </label>
                        <textarea
                            className="vreview-textarea"
                            placeholder="Enter any statutory observations or confirmation notes..."
                            value={verifyNotes}
                            onChange={(e) => setVerifyNotes(e.target.value)}
                        />

                        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                            <button
                                type="button"
                                onClick={() => setShowVerifyModal(false)}
                                style={{ background: "#1f1f28", color: "#cbd5e1", border: "none", padding: "10px 18px", borderRadius: "6px", cursor: "pointer", fontWeight: 600 }}
                            >
                                CANCEL
                            </button>
                            <button
                                type="button"
                                className="btn-verify"
                                onClick={() => void handleVerify()}
                                disabled={verifying}
                            >
                                {verifying ? "CONFIRMING..." : "CONFIRM VERIFICATION"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* RETURN FOR CORRECTION MODAL (MANDATORY REASON) */}
            {showReturnModal && (
                <div className="vreview-modal-backdrop">
                    <div className="vreview-modal">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                            <h3 style={{ margin: 0, color: "#ffffff", fontSize: "18px", display: "flex", alignItems: "center", gap: "8px" }}>
                                <ShieldAlert size={20} color="#ef4444" />
                                Return for Correction
                            </h3>
                            <button
                                type="button"
                                onClick={() => setShowReturnModal(false)}
                                style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer" }}
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <p style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: 1.5 }}>
                            Specify the exact regulatory non-compliance, missing evidence, or defect requiring rectification by the field inspector.
                        </p>

                        <label style={{ fontSize: "12px", color: "#fca5a5", fontWeight: 700 }}>
                            Substantive Return Reason (Required):
                        </label>
                        <textarea
                            className="vreview-textarea"
                            placeholder="e.g. Photographic evidence missing for main ventilation fan water gauge reading; air quantity below 280 m3/min."
                            value={returnReason}
                            onChange={(e) => setReturnReason(e.target.value)}
                            required
                        />

                        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                            <button
                                type="button"
                                onClick={() => setShowReturnModal(false)}
                                style={{ background: "#1f1f28", color: "#cbd5e1", border: "none", padding: "10px 18px", borderRadius: "6px", cursor: "pointer", fontWeight: 600 }}
                            >
                                CANCEL
                            </button>
                            <button
                                type="button"
                                className="btn-return"
                                onClick={() => void handleReturn()}
                                disabled={returning || !returnReason.trim() || returnReason.trim().length < 5}
                            >
                                {returning ? "PERSISTING..." : "CONFIRM RETURN"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}