import { useEffect, useMemo, useState } from "react";
import {
    AlertTriangle,
    ArrowRight,
    ClipboardCheck,
    Clock3,
    ShieldCheck,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getMines } from "../api/mines";
import { getMineInspections } from "../api/inspections";

type Mine = {
    mine_id: string;
    name: string;
};

type Inspection = {
    inspection_id: string;
    mine_id: string;
    template_id: string;
    obligation_id: string | null;
    inspector_id: string;
    started_at: string | null;
    submitted_at: string | null;
    inspection_date: string;
    status: string;
    latitude: number | null;
    longitude: number | null;
    gps_accuracy_m: number | null;
    inspection_name?: string;
    inspection_family?: string;
};

type MineInspectionHistory = {
    mine_id: string;
    inspections: Inspection[];
};

type Filter =
    | "all"
    | "draft"
    | "submitted"
    | "verification_required"
    | "verified";

function normalizeStatus(status: string): string {
    return status
        .toLowerCase()
        .trim()
        .replace(/[\s-]+/g, "_");
}

function formatStatus(status: string): string {
    return status
        .replace(/_/g, " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDate(value: string): string {
    if (!value) {
        return "DATE NOT AVAILABLE";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).toUpperCase();
}

function getStatusClass(status: string): string {
    const normalized = normalizeStatus(status);

    if (
        normalized === "verified" ||
        normalized === "approved" ||
        normalized === "completed"
    ) {
        return "inspection-status status-verified";
    }

    if (
        normalized === "verification_required" ||
        normalized === "flagged"
    ) {
        return "inspection-status status-warning";
    }

    if (
        normalized === "rejected" ||
        normalized === "failed"
    ) {
        return "inspection-status status-danger";
    }

    if (
        normalized === "draft" ||
        normalized === "in_progress"
    ) {
        return "inspection-status status-progress";
    }

    return "inspection-status";
}

function Inspections() {
    const navigate = useNavigate();

    const [mines, setMines] = useState<Mine[]>([]);
    const [selectedMine, setSelectedMine] = useState("");

    const [inspections, setInspections] = useState<Inspection[]>(
        []
    );

    const [filter, setFilter] = useState<Filter>("all");

    const [loadingMines, setLoadingMines] = useState(true);
    const [loadingInspections, setLoadingInspections] =
        useState(false);

    const [error, setError] = useState<string | null>(null);

    /* =========================================================
       LOAD MINES
    ========================================================= */

    useEffect(() => {
        let mounted = true;

        async function loadMines() {
            try {
                setLoadingMines(true);
                setError(null);

                const response = await getMines();

                if (!mounted) {
                    return;
                }

                const data = Array.isArray(response)
                    ? response
                    : [];

                setMines(data as Mine[]);

                if (data.length > 0) {
                    setSelectedMine(
                        String(
                            (data[0] as Mine).mine_id
                        )
                    );
                }
            } catch (err) {
                if (!mounted) {
                    return;
                }

                setError(
                    err instanceof Error
                        ? err.message
                        : "Unable to load mine registry."
                );
            } finally {
                if (mounted) {
                    setLoadingMines(false);
                }
            }
        }

        loadMines();

        return () => {
            mounted = false;
        };
    }, []);

    /* =========================================================
       LOAD INSPECTIONS FOR SELECTED MINE
    ========================================================= */

    useEffect(() => {
        if (!selectedMine) {
            setInspections([]);
            return;
        }

        let mounted = true;

        async function loadInspections() {
            try {
                setLoadingInspections(true);
                setError(null);

                const response =
                    await getMineInspections(
                        selectedMine
                    ) as MineInspectionHistory;

                if (!mounted) {
                    return;
                }

                setInspections(
                    Array.isArray(response?.inspections)
                        ? response.inspections
                        : []
                );
            } catch (err) {
                if (!mounted) {
                    return;
                }

                setInspections([]);

                setError(
                    err instanceof Error
                        ? err.message
                        : "Unable to load inspection history."
                );
            } finally {
                if (mounted) {
                    setLoadingInspections(false);
                }
            }
        }

        loadInspections();

        return () => {
            mounted = false;
        };
    }, [selectedMine]);

    /* =========================================================
       FILTER
    ========================================================= */

    const filteredInspections = useMemo(() => {
        if (filter === "all") {
            return inspections;
        }

        return inspections.filter(
            (inspection) =>
                normalizeStatus(
                    inspection.status
                ) === filter
        );
    }, [filter, inspections]);

    /* =========================================================
       COUNTS
    ========================================================= */

    const counts = useMemo(() => {
        const result = {
            all: inspections.length,
            draft: 0,
            submitted: 0,
            verification_required: 0,
            verified: 0,
        };

        inspections.forEach((inspection) => {
            const status = normalizeStatus(
                inspection.status
            );

            if (status === "draft") {
                result.draft += 1;
            }

            if (status === "submitted") {
                result.submitted += 1;
            }

            if (
                status ===
                "verification_required"
            ) {
                result.verification_required += 1;
            }

            if (
                status === "verified" ||
                status === "approved" ||
                status === "completed"
            ) {
                result.verified += 1;
            }
        });

        return result;
    }, [inspections]);

    /* =========================================================
       RENDER
    ========================================================= */

    return (
        <div className="dashboard">

            {/* =================================================
               HEADER
            ================================================= */}

            <section className="dashboard-header">

                <div className="dashboard-hero-main">

                    <p className="eyebrow">
                        PROJECT PRITHVI / INSPECTION OPERATIONS
                    </p>

                    <h1>
                        Inspection
                        <br />
                        Operations
                    </h1>

                    <p className="hero-description">
                        Monitor inspection activity, submission
                        status, and verification workflow across
                        registered mine assets.
                    </p>

                </div>

                <div className="dashboard-header-meta">

                    <div className="op-intel-card">

                        <span className="op-intel-label">
                            TOTAL INSPECTIONS
                        </span>

                        <strong className="op-intel-val">
                            {loadingInspections
                                ? "--"
                                : counts.all}
                        </strong>

                    </div>

                    <div className="op-intel-card">

                        <span className="op-intel-label">
                            VERIFICATION QUEUE
                        </span>

                        <strong className="op-intel-val status-amber">
                            {loadingInspections
                                ? "--"
                                : counts.verification_required}
                        </strong>

                    </div>

                </div>

            </section>

            {/* =================================================
               CONTROL BAR
            ================================================= */}

            <section className="mine-section">

                <div className="section-heading">

                    <div>

                        <p className="eyebrow">
                            OPERATIONAL CONTROL
                        </p>

                        <h2>
                            Inspection register
                        </h2>

                    </div>

                </div>

                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "minmax(240px, 360px) 1fr",
                        gap: "24px",
                        alignItems: "end",
                        marginBottom: "28px",
                    }}
                >

                    <label
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "8px",
                        }}
                    >

                        <span
                            style={{
                                fontSize: "11px",
                                letterSpacing: "0.08em",
                                fontWeight: 700,
                                color: "var(--steel)",
                            }}
                        >
                            MINE
                        </span>

                        <select
                            value={selectedMine}
                            onChange={(event) => {
                                setSelectedMine(
                                    event.target.value
                                );
                                setFilter("all");
                            }}
                            disabled={
                                loadingMines ||
                                mines.length === 0
                            }
                            style={{
                                width: "100%",
                                height: "44px",
                                padding: "0 12px",
                                border:
                                    "1px solid var(--border)",
                                background:
                                    "var(--paper)",
                                color:
                                    "var(--charcoal)",
                                borderRadius:
                                    "var(--radius-sm)",
                            }}
                        >

                            {loadingMines && (
                                <option>
                                    Loading mines...
                                </option>
                            )}

                            {!loadingMines &&
                                mines.length === 0 && (
                                    <option>
                                        No mines available
                                    </option>
                                )}

                            {mines.map((mine) => (
                                <option
                                    key={mine.mine_id}
                                    value={mine.mine_id}
                                >
                                    {mine.name} —{" "}
                                    {mine.mine_id}
                                </option>
                            ))}

                        </select>

                    </label>

                    <div
                        style={{
                            display: "flex",
                            gap: "8px",
                            flexWrap: "wrap",
                        }}
                    >

                        <FilterButton
                            label="ALL"
                            count={counts.all}
                            active={filter === "all"}
                            onClick={() =>
                                setFilter("all")
                            }
                        />

                        <FilterButton
                            label="DRAFT"
                            count={counts.draft}
                            active={filter === "draft"}
                            onClick={() =>
                                setFilter("draft")
                            }
                        />

                        <FilterButton
                            label="SUBMITTED"
                            count={counts.submitted}
                            active={
                                filter === "submitted"
                            }
                            onClick={() =>
                                setFilter("submitted")
                            }
                        />

                        <FilterButton
                            label="VERIFICATION REQUIRED"
                            count={
                                counts.verification_required
                            }
                            active={
                                filter ===
                                "verification_required"
                            }
                            onClick={() =>
                                setFilter(
                                    "verification_required"
                                )
                            }
                        />

                        <FilterButton
                            label="VERIFIED"
                            count={counts.verified}
                            active={
                                filter === "verified"
                            }
                            onClick={() =>
                                setFilter("verified")
                            }
                        />

                    </div>

                </div>

                {/* =================================================
                   ERROR
                ================================================= */}

                {error && (
                    <div className="state-card state-error">

                        <div className="state-card-inner">

                            <AlertTriangle
                                size={18}
                            />

                            <div>

                                <strong>
                                    DATA LOAD FAILED
                                </strong>

                                <span>
                                    {error}
                                </span>

                            </div>

                        </div>

                    </div>
                )}

                {/* =================================================
                   LOADING
                ================================================= */}

                {loadingInspections && (
                    <div className="state-card">

                        <div className="state-card-inner">

                            <Clock3 size={18} />

                            <span>
                                LOADING INSPECTION REGISTER...
                            </span>

                        </div>

                    </div>
                )}

                {/* =================================================
                   EMPTY
                ================================================= */}

                {!loadingInspections &&
                    !error &&
                    filteredInspections.length === 0 && (
                        <div className="state-card">

                            <div className="state-card-inner">

                                <ClipboardCheck
                                    size={18}
                                />

                                <div>

                                    <strong>
                                        NO INSPECTIONS FOUND
                                    </strong>

                                    <span>
                                        No inspections match
                                        the selected mine and
                                        current filter.
                                    </span>

                                </div>

                            </div>

                        </div>
                    )}

                {/* =================================================
                   INSPECTION LIST
                ================================================= */}

                {!loadingInspections &&
                    filteredInspections.length > 0 && (
                        <div
                            style={{
                                display: "grid",
                                gap: "12px",
                            }}
                        >

                            {filteredInspections.map(
                                (inspection) => (
                                    <InspectionRow
                                        key={
                                            inspection.inspection_id
                                        }
                                        inspection={
                                            inspection
                                        }
                                        onOpen={() =>
                                            navigate(
                                                `/inspections/${inspection.inspection_id}`
                                            )
                                        }
                                    />
                                )
                            )}

                        </div>
                    )}

            </section>

        </div>
    );
}

/* =========================================================
   FILTER BUTTON
========================================================= */

function FilterButton({
    label,
    count,
    active,
    onClick,
}: {
    label: string;
    count: number;
    active: boolean;
    onClick: () => void;
}) {
    return (
        <button
            type="button"
            onClick={onClick}
            style={{
                minHeight: "36px",
                padding: "0 12px",
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                border: active
                    ? "1px solid var(--charcoal)"
                    : "1px solid var(--border)",
                background: active
                    ? "var(--charcoal)"
                    : "transparent",
                color: active
                    ? "var(--paper)"
                    : "var(--charcoal)",
                borderRadius: "var(--radius-sm)",
                fontSize: "11px",
                fontWeight: 700,
                letterSpacing: "0.04em",
            }}
        >
            {label}

            <span
                style={{
                    opacity: 0.65,
                }}
            >
                {count}
            </span>
        </button>
    );
}

/* =========================================================
   INSPECTION ROW
========================================================= */

function InspectionRow({
    inspection,
    onOpen,
}: {
    inspection: Inspection;
    onOpen: () => void;
}) {
    const normalizedStatus =
        normalizeStatus(inspection.status);

    const isVerificationRequired =
        normalizedStatus ===
        "verification_required";

    return (
        <article
            style={{
                display: "grid",
                gridTemplateColumns:
                    "minmax(260px, 1fr) auto auto",
                gap: "24px",
                alignItems: "center",
                padding: "20px 22px",
                border:
                    "1px solid var(--border)",
                background:
                    "rgba(255,255,255,0.24)",
                borderRadius:
                    "var(--radius-md)",
            }}
        >

            {/* IDENTITY */}

            <div>

                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        marginBottom: "6px",
                    }}
                >

                    <ClipboardCheck
                        size={15}
                        color="var(--copper)"
                    />

                    <code
                        style={{
                            fontFamily:
                                "DM Mono, monospace",
                            fontSize: "12px",
                        }}
                    >
                        {inspection.inspection_id}
                    </code>

                </div>

                <h3
                    style={{
                        margin: "0 0 5px",
                        fontSize: "16px",
                    }}
                >
                    {inspection.inspection_name ||
                        "Inspection"}
                </h3>

                <p
                    style={{
                        margin: 0,
                        fontSize: "12px",
                        color: "var(--steel)",
                    }}
                >
                    {inspection.inspection_family ||
                        "Regulatory inspection"}
                    {" · "}
                    {formatDate(
                        inspection.inspection_date
                    )}
                </p>

            </div>

            {/* STATUS */}

            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-end",
                    gap: "7px",
                }}
            >

                <span
                    className={getStatusClass(
                        inspection.status
                    )}
                >
                    {isVerificationRequired && (
                        <ShieldCheck
                            size={12}
                        />
                    )}

                    {formatStatus(
                        inspection.status
                    )}
                </span>

                {inspection.inspector_id && (
                    <span
                        style={{
                            fontSize: "11px",
                            color: "var(--steel)",
                            fontFamily:
                                "DM Mono, monospace",
                        }}
                    >
                        {inspection.inspector_id}
                    </span>
                )}

            </div>

            {/* ACTION */}

            <button
                type="button"
                onClick={onOpen}
                style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    minHeight: "38px",
                    padding: "0 13px",
                    border:
                        "1px solid var(--border)",
                    background:
                        "var(--charcoal)",
                    color:
                        "var(--paper)",
                    borderRadius:
                        "var(--radius-sm)",
                    fontSize: "11px",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                }}
            >
                OPEN

                <ArrowRight
                    size={14}
                />
            </button>

        </article>
    );
}

export default Inspections;