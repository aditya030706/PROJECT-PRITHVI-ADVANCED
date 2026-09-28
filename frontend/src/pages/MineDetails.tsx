import {
    createInspection,
    getMineInspections,
    getVerification,
    type Inspection,
    type VerificationResult,
} from "../api/inspections";
import {
    getMineSchedule,
    type MineInspectionSchedule,
} from "../api/schedules";
import {
    useEffect,
    useState,
} from "react";
import { useAuth } from "../auth/AuthContext";
import { hasPermission } from "../auth/permissions";
import {
    ArrowLeft,
    FileText,
    ArrowRight,
    CheckCircle2,
    HelpCircle,
    ShieldCheck,
    Zap,
    AlertTriangle,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import {
    getMine,
    getMineApplicability,
} from "../api/mines";

/* =========================================================
   TYPES
========================================================= */

type Mine = {
    mine_id: string;
    name: string;

    subsidiary?: string | null;

    state?: string | null;
    district?: string | null;

    mine_type: string;
    mining_method?: string | null;

    gassy_degree: string;

    mechanised: boolean;
    uses_hemm: boolean;
    has_winding_installation: boolean;
    blasting_operation: boolean;

    has_ventilating_district?: boolean | null;
    electric_energy_in_ventilating_district?: boolean | null;
    has_shaft_or_incline?: boolean | null;
    has_fire_risk_area?: boolean | null;
    has_water_danger?: boolean | null;

    active: boolean;
};

type ApplicabilityInspection = {
    template_id: string;
    inspection_type: string;
    status: string;
    reason: string;
    regulatory_basis: string;
    trigger_frequency: string;
};

type ApplicabilityResponse = {
    mine: {
        mine_id: string;
        name: string;
        mine_type: string;
        gassy_degree: string;
        mechanised: boolean;
        uses_hemm: boolean;
        has_winding_installation: boolean;
    };

    summary: {
        routine_applicable: number;
        needs_confirmation: number;
        event_triggered_available: number;
        not_applicable: number;
    };

    routine_inspections: ApplicabilityInspection[];

    needs_confirmation: ApplicabilityInspection[];

    event_triggered_inspections: ApplicabilityInspection[];

    not_applicable: ApplicabilityInspection[];
};

/* =========================================================
   HELPERS
========================================================= */

function formatValue(value: string | null | undefined) {
    if (!value) {
        return "Not specified";
    }

    return value
        .replaceAll("_", " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatScheduleDate(value: string | null) {
    if (!value) {
        return "Condition dependent";
    }

    const date = new Date(value);

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
}

function formatScheduleFrequency(schedule: MineInspectionSchedule) {
    if (
        schedule.interval_value &&
        schedule.interval_unit
    ) {
        return `Every ${schedule.interval_value} ${schedule.interval_unit}`;
    }

    if (schedule.frequency_type === "calendar") {
        return "Calendar based";
    }

    if (schedule.frequency_type === "conditional") {
        return "Condition based";
    }

    return formatValue(schedule.frequency_type);
}

function formatScheduleStatus(status: string) {
    return status
        .replaceAll("_", " ")
        .toUpperCase();
}

/* =========================================================
   CONDITION COMPONENT
========================================================= */

function Condition({
    label,
    value,
}: {
    label: string;
    value: boolean | null | undefined;
}) {
    if (value === null || value === undefined) {
        return (
            <div className="condition">
                <span className="condition-label">{label}</span>

                <strong className="condition-value unknown">
                    <HelpCircle size={14} />
                    UNKNOWN
                </strong>
            </div>
        );
    }

    return (
        <div className="condition">
            <span className="condition-label">{label}</span>

            <strong className={`condition-value ${value ? "yes" : "no"}`}>
                {value && <CheckCircle2 size={14} />}
                {!value && <span className="condition-dash">—</span>}
                {value ? "YES" : "NO"}
            </strong>
        </div>
    );
}

/* =========================================================
   INSPECTION RULE COMPONENT
========================================================= */

function InspectionRule({
    inspection,
    tone,
}: {
    inspection: ApplicabilityInspection;
    tone: "applicable" | "event" | "confirmation" | "excluded";
}) {
    return (
        <article className={`inspection-rule ${tone}`}>

            <div className="inspection-rule-id">
                {inspection.template_id}
            </div>

            <div className="inspection-rule-main">

                <div className="inspection-rule-title">

                    <h5>
                        {inspection.inspection_type}
                    </h5>

                    <span className={`rule-status ${tone}`}>
                        {inspection.status.replaceAll("_", " ")}
                    </span>

                </div>

                <p className="inspection-rule-reason">
                    {inspection.reason}
                </p>

                <div className="inspection-rule-meta">

                    <div>
                        <span>
                            REGULATORY BASIS
                        </span>

                        <strong>
                            {inspection.regulatory_basis}
                        </strong>
                    </div>

                    <div>
                        <span>
                            TRIGGER / FREQUENCY
                        </span>

                        <strong>
                            {inspection.trigger_frequency}
                        </strong>
                    </div>

                </div>

            </div>

        </article>
    );
}

/* =========================================================
   SUMMARY CARD
========================================================= */

function SummaryCard({
    number,
    label,
    type,
}: {
    number: number;
    label: string;
    type: "applicable" | "event" | "confirmation" | "excluded";
}) {
    return (
        <div className={`summary-block ${type}`}>

            <span>
                {label}
            </span>

            <strong>
                {String(number).padStart(2, "0")}
            </strong>

        </div>
    );
}

/* =========================================================
   MINE DETAILS
========================================================= */

function MineDetails() {
    const [schedules, setSchedules] = useState<MineInspectionSchedule[]>([]);
    const [recentInspections, setRecentInspections] =
        useState<Inspection[]>([]);

    const [latestVerification, setLatestVerification] =
        useState<VerificationResult | null>(null);

    const [documentAIError, setDocumentAIError] =
        useState<string | null>(null);

    const [documentAILoading, setDocumentAILoading] =
        useState(false);
    const [startingSchedule, setStartingSchedule] =
        useState<string | null>(null);

    const [startError, setStartError] =
        useState<string | null>(null);

    const { mineId } = useParams();

    const navigate = useNavigate();
    const { session } = useAuth();
    const canStartInspection = session && session.role ? hasPermission(session.role, "inspection.create") : false;

    const [mine, setMine] = useState<Mine | null>(null);

    const [applicability, setApplicability] =
        useState<ApplicabilityResponse | null>(null);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState<string | null>(null);

    async function handleStartInspection(
        schedule: MineInspectionSchedule
    ) {
        setStartingSchedule(
            schedule.schedule_instance_id
        );

        setStartError(null);

        try {
            const inspection =
                await createInspection({
                    mine_id: mine!.mine_id,

                    template_id:
                        schedule.template_id,

                    obligation_id:
                        schedule.obligation_id,

                    inspector_id:
                        "INSPECTOR-WEB-001",

                    inspection_date:
                        new Date()
                            .toISOString()
                            .split("T")[0],
                });

            navigate(
                `/inspections/${inspection.inspection_id}`
            );
        } catch (err) {

            setStartError(
                err instanceof Error
                    ? err.message
                    : "Unable to start inspection."
            );

        } finally {

            setStartingSchedule(null);

        }
    }

    /* -------------------------------------------------------
       LOAD MINE + APPLICABILITY
    ------------------------------------------------------- */

    useEffect(() => {
        if (!mineId) {
            setError("Mine ID is missing.");
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);

        Promise.all([
            getMine(mineId),
            getMineApplicability(mineId),
            getMineSchedule(mineId),
            getMineInspections(mineId),
        ])
            .then(
                async ([
                    mineData,
                    applicabilityData,
                    scheduleData,
                    inspectionHistory,
                ]) => {
                    setMine(mineData as Mine);

                    setApplicability(
                        applicabilityData as ApplicabilityResponse
                    );

                    setSchedules(scheduleData.schedules);
                    const inspections =
                        inspectionHistory.inspections || [];

                    setRecentInspections(inspections);

                    if (inspections.length > 0) {
                        const latest = [...inspections].sort(
                            (a, b) =>
                                new Date(
                                    b.inspection_date
                                ).getTime() -
                                new Date(
                                    a.inspection_date
                                ).getTime()
                        )[0];

                        setDocumentAILoading(true);
                        setDocumentAIError(null);

                        try {
                            const verification =
                                await getVerification(
                                    latest.inspection_id
                                );

                            setLatestVerification(
                                verification
                            );
                        } catch (verificationError) {
                            setDocumentAIError(
                                verificationError instanceof Error
                                    ? verificationError.message
                                    : "Unable to load verification data."
                            );
                        } finally {
                            setDocumentAILoading(false);
                        }
                    }
                })
            .catch((err) => {
                setError(
                    err instanceof Error
                        ? err.message
                        : "Unable to load mine information."
                );
            })
            .finally(() => {
                setLoading(false);
            });
    }, [mineId]);

    /* =======================================================
       LOADING
    ======================================================= */

    if (loading) {
        return (
            <div className="mine-details-page">
                <div className="state-card">
                    <div className="state-card-inner">
                        <div className="loading-indicator" />
                        <span>LOADING REGULATORY DATA...</span>
                    </div>
                </div>
            </div>
        );
    }

    /* =======================================================
       ERROR
    ======================================================= */

    if (error || !mine || !applicability) {
        return (
            <div className="mine-details-page">

                <button
                    className="back-button"
                    onClick={() => navigate("/")}
                >
                    <ArrowLeft size={16} />
                    BACK TO COMMAND
                </button>

                <div className="state-card state-error">
                    <div className="state-card-inner">
                        <AlertTriangle size={18} />
                        <div>
                            <strong>REGULATORY DATA LOAD FAILED</strong>
                            <span>{error || "Mine information unavailable."}</span>
                        </div>
                    </div>
                </div>

            </div>
        );
    }

    /* =======================================================
       MAIN UI
    ======================================================= */

    return (
        <div className="mine-details-page">

            {/* ═══ BACK BUTTON ════════════════════════════════ */}

            <button
                className="back-button"
                onClick={() => navigate("/")}
            >
                <ArrowLeft size={16} />
                BACK TO COMMAND
            </button>


            {/* ═══ MINE HERO / DOSSIER HEADER ═════════════════ */}

            <section className="mine-hero">

                <div className="mine-hero-content">

                    <p className="eyebrow">
                        MINE DOSSIER / {mine.mine_id}
                    </p>

                    <h1>
                        {mine.name}
                    </h1>

                    <div className="mine-hero-meta">

                        <span>
                            {formatValue(mine.mine_type)}
                        </span>

                        <span>
                            {formatValue(mine.gassy_degree)}
                        </span>

                        {mine.state && (
                            <span>
                                {mine.state}
                            </span>
                        )}

                        {mine.district && (
                            <span>
                                {mine.district}
                            </span>
                        )}

                    </div>

                </div>


                <div className="mine-hero-icon">
                    <ShieldCheck
                        size={40}
                        strokeWidth={1.2}
                    />
                </div>

            </section>


            {/* ═══ 01 / OPERATIONAL PROFILE ═══════════════════ */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <span className="section-number">
                            01 / MINE PROFILE
                        </span>

                        <h2>
                            Operational characteristics
                        </h2>

                    </div>

                    <span className="section-count">
                        {mine.active
                            ? "ACTIVE DOSSIER"
                            : "INACTIVE DOSSIER"}
                    </span>

                </div>


                <div className="conditions-grid">

                    <Condition
                        label="Mechanised"
                        value={mine.mechanised}
                    />

                    <Condition
                        label="HEMM"
                        value={mine.uses_hemm}
                    />

                    <Condition
                        label="Winding Installation"
                        value={mine.has_winding_installation}
                    />

                    <Condition
                        label="Blasting Operation"
                        value={mine.blasting_operation}
                    />

                    <Condition
                        label="Ventilating District"
                        value={mine.has_ventilating_district}
                    />

                    <Condition
                        label="Electric Energy in Ventilating District"
                        value={
                            mine.electric_energy_in_ventilating_district
                        }
                    />

                    <Condition
                        label="Shaft / Incline"
                        value={mine.has_shaft_or_incline}
                    />

                    <Condition
                        label="Fire Risk Area"
                        value={mine.has_fire_risk_area}
                    />

                    <Condition
                        label="Water Danger"
                        value={mine.has_water_danger}
                    />

                </div>

            </section>


            {/* ═══ 02 / REGULATORY APPLICABILITY ══════════════ */}

            <section className="applicability-section">

                <div className="section-heading">

                    <div>

                        <span className="section-number">
                            02 / REGULATORY APPLICABILITY
                        </span>

                        <h2>
                            Applicability assessment
                        </h2>

                    </div>

                    <div className="engine-status">
                        <Zap size={14} />
                        ENGINE ACTIVE
                    </div>

                </div>


                {/* ── SUMMARY ──────────────────────────────── */}

                <div className="applicability-summary">

                    <SummaryCard
                        number={
                            applicability.summary.routine_applicable
                        }
                        label="ROUTINE APPLICABLE"
                        type="applicable"
                    />

                    <SummaryCard
                        number={
                            applicability.summary.event_triggered_available
                        }
                        label="EVENT TRIGGERED"
                        type="event"
                    />

                    <SummaryCard
                        number={
                            applicability.summary.needs_confirmation
                        }
                        label="NEEDS CONFIRMATION"
                        type="confirmation"
                    />

                    <SummaryCard
                        number={
                            applicability.summary.not_applicable
                        }
                        label="NOT APPLICABLE"
                        type="excluded"
                    />

                </div>


                {/* ── ROUTINE INSPECTIONS ───────────────────── */}

                {applicability.routine_inspections.length > 0 && (

                    <div className="inspection-group">

                        <div className="group-heading">

                            <div>

                                <span className="decision-label">
                                    ROUTINE INSPECTIONS
                                </span>

                                <h4>
                                    Applicable requirements
                                </h4>

                            </div>

                            <span className="group-count">
                                {String(
                                    applicability.summary.routine_applicable
                                ).padStart(2, "0")}
                            </span>

                        </div>


                        <div className="inspection-list">

                            {applicability.routine_inspections.map(
                                (inspection) => (

                                    <InspectionRule
                                        key={inspection.template_id}
                                        inspection={inspection}
                                        tone="applicable"
                                    />

                                )
                            )}

                        </div>

                    </div>

                )}


                {/* ── NEEDS CONFIRMATION ───────────────────── */}

                {applicability.needs_confirmation.length > 0 && (

                    <div className="inspection-group">

                        <div className="group-heading">

                            <div>

                                <span className="decision-label">
                                    REVIEW REQUIRED
                                </span>

                                <h4>
                                    Needs confirmation
                                </h4>

                            </div>

                            <span className="group-count">
                                {String(
                                    applicability.summary.needs_confirmation
                                ).padStart(2, "0")}
                            </span>

                        </div>


                        <div className="inspection-list">

                            {applicability.needs_confirmation.map(
                                (inspection) => (

                                    <InspectionRule
                                        key={inspection.template_id}
                                        inspection={inspection}
                                        tone="confirmation"
                                    />

                                )
                            )}

                        </div>

                    </div>

                )}


                {/* ── EVENT TRIGGERED ──────────────────────── */}

                {applicability.event_triggered_inspections.length > 0 && (

                    <div className="inspection-group">

                        <div className="group-heading">

                            <div>

                                <span className="decision-label">
                                    EVENT-TRIGGERED
                                </span>

                                <h4>
                                    Available when conditions occur
                                </h4>

                            </div>

                            <span className="group-count">
                                {String(
                                    applicability.summary.event_triggered_available
                                ).padStart(2, "0")}
                            </span>

                        </div>


                        <div className="inspection-list">

                            {applicability.event_triggered_inspections.map(
                                (inspection) => (

                                    <InspectionRule
                                        key={inspection.template_id}
                                        inspection={inspection}
                                        tone="event"
                                    />

                                )
                            )}

                        </div>

                    </div>

                )}


                {/* ── NOT APPLICABLE ──────────────────────── */}

                {applicability.not_applicable.length > 0 && (

                    <div className="inspection-group">

                        <div className="group-heading">

                            <div>

                                <span className="decision-label">
                                    EXCLUDED
                                </span>

                                <h4>
                                    Not applicable
                                </h4>

                            </div>

                            <span className="group-count">
                                {String(
                                    applicability.summary.not_applicable
                                ).padStart(2, "0")}
                            </span>

                        </div>


                        <div className="inspection-list">

                            {applicability.not_applicable.map(
                                (inspection) => (

                                    <InspectionRule
                                        key={inspection.template_id}
                                        inspection={inspection}
                                        tone="excluded"
                                    />

                                )
                            )}

                        </div>

                    </div>

                )}

            </section>


            {/* ═══ 03 / COMPLIANCE SCHEDULE ═══════════════════ */}

            <section className="schedule-section">

                <div className="section-heading">

                    <div>
                        <span className="section-number">
                            03 / COMPLIANCE SCHEDULE
                        </span>

                        <h2>
                            Inspection intelligence & schedule
                        </h2>
                    </div>

                    <div className="schedule-total">
                        {String(schedules.length).padStart(2, "0")}
                        <span>ACTIVE SCHEDULES</span>
                    </div>

                </div>


                <div className="schedule-summary">

                    <div className="schedule-summary-item">
                        <span>DUE SOON</span>
                        <strong className="status-amber">
                            {
                                schedules.filter(
                                    (item) => item.status === "due_soon"
                                ).length
                            }
                        </strong>
                    </div>

                    <div className="schedule-summary-item">
                        <span>CONDITION</span>
                        <strong className="status-copper">
                            {
                                schedules.filter(
                                    (item) =>
                                        item.status === "needs_condition"
                                ).length
                            }
                        </strong>
                    </div>

                    <div className="schedule-summary-item">
                        <span>UPCOMING</span>
                        <strong>
                            {
                                schedules.filter(
                                    (item) => item.status === "upcoming"
                                ).length
                            }
                        </strong>
                    </div>

                    <div className="schedule-summary-item">
                        <span>OVERDUE</span>
                        <strong className="status-red">
                            {
                                schedules.filter(
                                    (item) => item.status === "overdue"
                                ).length
                            }
                        </strong>
                    </div>

                </div>


                {startError && (
                    <div className="inline-error">
                        <AlertTriangle size={14} />
                        {startError}
                    </div>
                )}


                <div className="schedule-list">

                    {schedules.map((schedule) => (

                        <article
                            className={`schedule-card ${schedule.status}`}
                            key={schedule.schedule_instance_id}
                        >

                            <div className="schedule-card-id">
                                {schedule.schedule_id}
                            </div>


                            <div className="schedule-card-content">

                                <div className="schedule-card-header">

                                    <div>

                                        <h3>
                                            {schedule.schedule_name}
                                        </h3>

                                        <p className="schedule-obligation">
                                            {schedule.obligation_id}
                                        </p>

                                    </div>


                                    <span
                                        className={`schedule-status ${schedule.status}`}
                                    >
                                        {formatScheduleStatus(
                                            schedule.status
                                        )}
                                    </span>

                                </div>


                                <div className="schedule-details">

                                    <div>
                                        <span>NEXT DUE</span>
                                        <strong>
                                            {formatScheduleDate(
                                                schedule.next_due_at
                                            )}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>FREQUENCY</span>
                                        <strong>
                                            {formatScheduleFrequency(
                                                schedule
                                            )}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>TRIGGER</span>
                                        <strong>
                                            {formatValue(
                                                schedule.trigger_type
                                            )}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>REGULATORY VALIDATION</span>
                                        <strong className="validation-warning">
                                            {formatValue(
                                                schedule.validation_status
                                            )}
                                        </strong>
                                    </div>

                                </div>


                                <div className="schedule-actions">

                                    {canStartInspection ? (
                                        <button
                                            className="start-inspection-button"
                                            onClick={() =>
                                                handleStartInspection(schedule)
                                            }
                                            disabled={
                                                startingSchedule ===
                                                schedule.schedule_instance_id
                                            }
                                        >

                                            {startingSchedule ===
                                                schedule.schedule_instance_id
                                                ? "STARTING..."
                                                : (
                                                    <>
                                                        START INSPECTION
                                                        <ArrowRight size={14} />
                                                    </>
                                                )}

                                        </button>
                                    ) : (
                                        <span className="schedule-readonly-status">
                                            MONITORING ACTIVE
                                        </span>
                                    )}

                                </div>

                            </div>

                        </article>

                    ))}

                </div>

            </section>
            {/* =========================================================
    04 / DOCUMENT INTELLIGENCE
========================================================= */}

            <section className="document-intelligence-section">

                <div className="section-heading">

                    <div>
                        <span className="section-number">
                            04 / DOCUMENT INTELLIGENCE
                        </span>

                        <h2>
                            Document integrity & verification
                        </h2>
                    </div>

                    <div className="engine-status">
                        <ShieldCheck size={14} />
                        DOCUMENT AI ACTIVE
                    </div>

                </div>

                {documentAILoading && (
                    <div className="state-card">
                        <div className="state-card-inner">
                            <div className="loading-indicator" />
                            <span>
                                LOADING DOCUMENT INTELLIGENCE...
                            </span>
                        </div>
                    </div>
                )}

                {!documentAILoading && documentAIError && (
                    <div className="state-card state-error">
                        <div className="state-card-inner">
                            <AlertTriangle size={18} />
                            <div>
                                <strong>
                                    DOCUMENT AI UNAVAILABLE
                                </strong>
                                <span>
                                    {documentAIError}
                                </span>
                            </div>
                        </div>
                    </div>
                )}

                {!documentAILoading &&
                    !documentAIError &&
                    !latestVerification && (
                        <div className="document-ai-empty">
                            <FileText size={20} />

                            <div>
                                <strong>
                                    NO VERIFIED INSPECTION DOCUMENT
                                </strong>

                                <span>
                                    Upload and submit an inspection
                                    report to activate Document AI.
                                </span>
                            </div>
                        </div>
                    )}

                {!documentAILoading &&
                    !documentAIError &&
                    latestVerification && (() => {

                        const signals =
                            latestVerification.signals || [];

                        const hash =
                            signals.find(
                                s =>
                                    s.name ===
                                    "Document hash integrity"
                            );

                        const text =
                            signals.find(
                                s =>
                                    s.name ===
                                    "Document text extraction"
                            );

                        const measurements =
                            signals.find(
                                s =>
                                    s.name ===
                                    "Document measurement extraction"
                            );

                        const duplicate =
                            signals.find(
                                s =>
                                    s.name ===
                                    "Exact document duplicate"
                            );

                        const similarity =
                            signals.find(
                                s =>
                                    s.name ===
                                    "Historical document similarity"
                            );

                        const latest =
                            recentInspections.length > 0
                                ? [...recentInspections].sort(
                                    (a, b) =>
                                        new Date(
                                            b.inspection_date
                                        ).getTime() -
                                        new Date(
                                            a.inspection_date
                                        ).getTime()
                                )[0]
                                : null;

                        const verificationRequired =
                            latestVerification
                                .human_decision_required;

                        const verificationClass =
                            verificationRequired
                                ? "document-ai-warning"
                                : "document-ai-pass";

                        return (
                            <div className="document-ai-panel">

                                {/* HEADER */}

                                <div className="document-ai-header">

                                    <div>
                                        <span className="document-ai-label">
                                            LATEST INSPECTION
                                        </span>

                                        <strong>
                                            {latest?.inspection_id ||
                                                latestVerification.inspection_id}
                                        </strong>
                                    </div>

                                    <span
                                        className={`document-ai-status ${verificationClass}`}
                                    >
                                        {latestVerification.status
                                            .replaceAll("_", " ")
                                            .toUpperCase()}
                                    </span>

                                </div>

                                {/* CHECKS */}

                                <div className="document-ai-checks">

                                    <div className="document-ai-check">
                                        <span>PDF INTEGRITY</span>

                                        <strong
                                            className={
                                                hash?.status === "passed"
                                                    ? "document-ai-pass"
                                                    : "document-ai-warning"
                                            }
                                        >
                                            {hash?.status === "passed"
                                                ? "✓ PASS"
                                                : "⚠ CHECK"}
                                        </strong>
                                    </div>

                                    <div className="document-ai-check">
                                        <span>TEXT EXTRACTION</span>

                                        <strong
                                            className={
                                                text?.status === "passed"
                                                    ? "document-ai-pass"
                                                    : "document-ai-warning"
                                            }
                                        >
                                            {text?.status === "passed"
                                                ? "✓ PASS"
                                                : "⚠ CHECK"}
                                        </strong>
                                    </div>

                                    <div className="document-ai-check">
                                        <span>MEASUREMENTS</span>

                                        <strong
                                            className={
                                                measurements?.score === 1
                                                    ? "document-ai-pass"
                                                    : "document-ai-warning"
                                            }
                                        >
                                            {measurements?.score != null
                                                ? `${Math.round(
                                                    measurements.score * 100
                                                )}% EXTRACTED`
                                                : "NOT AVAILABLE"}
                                        </strong>
                                    </div>

                                    <div className="document-ai-check">
                                        <span>EXACT DUPLICATE</span>

                                        <strong
                                            className={
                                                duplicate?.status ===
                                                    "duplicate"
                                                    ? "document-ai-warning"
                                                    : "document-ai-pass"
                                            }
                                        >
                                            {duplicate?.status ===
                                                "duplicate"
                                                ? "⚠ DUPLICATE"
                                                : "✓ NONE DETECTED"}
                                        </strong>
                                    </div>

                                </div>

                                {/* SIMILARITY */}

                                {similarity && (
                                    <div className="document-ai-similarity">

                                        <div>
                                            <span>
                                                HISTORICAL DOCUMENT
                                                SIMILARITY
                                            </span>

                                            <strong>
                                                {similarity.score != null
                                                    ? `${(
                                                        similarity.score *
                                                        100
                                                    ).toFixed(1)}%`
                                                    : "N/A"}
                                            </strong>
                                        </div>

                                        <div className="document-ai-similarity-detail">
                                            {similarity.explanation}
                                        </div>

                                    </div>
                                )}

                                {/* VERIFICATION */}

                                <div className="document-ai-verification">

                                    <div>

                                        <span>
                                            VERIFICATION STATUS
                                        </span>

                                        <strong>
                                            {latestVerification.status
                                                .replaceAll("_", " ")
                                                .toUpperCase()}
                                        </strong>

                                    </div>

                                    <div>

                                        <span>
                                            CONFIDENCE
                                        </span>

                                        <strong>
                                            {Math.round(
                                                latestVerification.confidence *
                                                100
                                            )}
                                            %
                                        </strong>

                                    </div>

                                    <div>

                                        <span>
                                            HUMAN REVIEW
                                        </span>

                                        <strong>
                                            {latestVerification
                                                .human_decision_required
                                                ? "REQUIRED"
                                                : "NOT REQUIRED"}
                                        </strong>

                                    </div>

                                </div>

                                {/* RECOMMENDATION */}

                                <div className="document-ai-recommendation">

                                    <AlertTriangle size={17} />

                                    <span>
                                        {latestVerification.recommendation}
                                    </span>

                                </div>

                            </div>
                        );

                    })()}

            </section>

            {/* ═══ ENGINE FOOTER ══════════════════════════════ */}

            <section className="engine-footer">

                <div className="engine-footer-icon">
                    <ShieldCheck size={20} />
                </div>

                <div>

                    <span>
                        PRITHVI REGULATORY ENGINE
                    </span>

                    <p>
                        Applicability decisions are generated from
                        the registered mine profile and configured
                        regulatory rules.
                    </p>

                </div>

                <div className="engine-footer-status">
                    <CheckCircle2 size={16} />
                    PROFILE EVALUATED
                </div>

            </section>

        </div>
    );
}

export default MineDetails;