import {
    ArrowRight,
    AlertTriangle,
    CalendarClock,
    ClipboardCheck,
    Clock3,
    Wind,
    Compass,
    Zap,
    Truck,
    Flame,
    Shield,
    Droplets,
} from "lucide-react";

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getMine } from "../api/mines";
import { getMineSchedule } from "../api/schedules";
import type { MineInspectionSchedule } from "../api/schedules";
import { getMineTemplates } from "../api/inspection";
import type { InspectionTemplate } from "../api/inspection";

const INSPECTOR_MINE_ID = "MINE-BCCL-JHARIA-01";

type InspectorMine = {
    mine_id: string;
    name: string;
    subsidiary?: string;
    mining_method?: string;
    gassy_degree?: string;
};

// Authoritative 7 Categories in statutory order
const CATEGORY_ORDER = [
    {
        key: "Ventilation & Gas",
        index: "01",
        name: "Ventilation & Gas",
        expectedCount: 3,
        icon: Wind,
        description: "Atmospheric monitoring, methane dilution, main fan pressure & ventilation surveys under Regs 119 & 156.",
        color: "#d97706",
    },
    {
        key: "Shaft & Winding",
        index: "02",
        name: "Shaft & Winding",
        expectedCount: 2,
        icon: Compass,
        description: "Weekly shaft clearance examinations and monthly winding gear safety audits under Regs 75, 76–80.",
        color: "#2563eb",
    },
    {
        key: "Electrical",
        index: "03",
        name: "Electrical",
        expectedCount: 2,
        icon: Zap,
        description: "Underground earthing continuity, flameproof (FLP) enclosure testing and substation safety under Regs 160–170.",
        color: "#eab308",
    },
    {
        key: "HEMM",
        index: "04",
        name: "HEMM",
        expectedCount: 2,
        icon: Truck,
        description: "Heavy Earth Moving Machinery pre-start checklists and weekly mechanical brake testing under Reg 135.",
        color: "#10b981",
    },
    {
        key: "Blasting",
        index: "05",
        name: "Blasting",
        expectedCount: 2,
        icon: Flame,
        description: "Pre-blast gas screening, danger zone clearance, and post-blast misfire/fume inspections under Regs 155–158.",
        color: "#ef4444",
    },
    {
        key: "Roof / Strata",
        index: "06",
        name: "Roof / Strata",
        expectedCount: 1,
        icon: Shield,
        description: "Strata Control & Monitoring Plan (SCAMP) compliance, roof sounding, and tell-tale monitoring under Regs 85–95.",
        color: "#8b5cf6",
    },
    {
        key: "Water / Drainage",
        index: "07",
        name: "Water / Drainage",
        expectedCount: 1,
        icon: Droplets,
        description: "Main underground sump capacity, seepage inflow rates, and emergency standby pump readiness under Reg 145.",
        color: "#06b6d4",
    },
];

function formatDate(value: string | null | undefined): string {
    if (!value) {
        return "TRIGGER-BASED / EVENT";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "DATE UNAVAILABLE";
    }

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).toUpperCase();
}

function computeScheduleStatus(
    schedule?: MineInspectionSchedule,
    now: Date = new Date()
): { label: string; modifier: string } {
    if (!schedule) {
        return { label: "UPCOMING", modifier: "upcoming" };
    }

    const rawStatus = (schedule.status || "").toLowerCase();

    if (rawStatus === "needs_condition" || rawStatus === "event_triggered") {
        if (schedule.trigger_type === "pre_blast") {
            return { label: "BEFORE BLAST", modifier: "event" };
        }
        if (schedule.trigger_type === "post_blast") {
            return { label: "AFTER BLAST", modifier: "event" };
        }
        return { label: "CONDITIONAL", modifier: "event" };
    }

    if (schedule.next_due_at) {
        const due = new Date(schedule.next_due_at);
        if (due < now) {
            return { label: "OVERDUE", modifier: "overdue" };
        }
        if (due.toDateString() === now.toDateString()) {
            return { label: "DUE TODAY", modifier: "due" };
        }
        const diffDays = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
        if (diffDays <= 7) {
            return { label: "DUE SOON", modifier: "due-soon" };
        }
    }

    if (rawStatus === "due") {
        return { label: "DUE TODAY", modifier: "due" };
    }
    if (rawStatus === "due_soon") {
        return { label: "DUE SOON", modifier: "due-soon" };
    }
    if (rawStatus === "overdue") {
        return { label: "OVERDUE", modifier: "overdue" };
    }

    return { label: "UPCOMING", modifier: "upcoming" };
}

function FieldInspectorHome() {
    const navigate = useNavigate();

    const [mine, setMine] = useState<InspectorMine | null>(null);
    const [templates, setTemplates] = useState<InspectionTemplate[]>([]);
    const [schedules, setSchedules] = useState<MineInspectionSchedule[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
    const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>("ALL");

    useEffect(() => {
        async function load() {
            try {
                const [mineData, scheduleData, templateData] = await Promise.all([
                    getMine(INSPECTOR_MINE_ID),
                    getMineSchedule(INSPECTOR_MINE_ID),
                    getMineTemplates(INSPECTOR_MINE_ID),
                ]);

                setMine(mineData as InspectorMine);
                setSchedules(scheduleData.schedules || []);
                setTemplates(templateData || []);
            } catch (err) {
                setError(
                    err instanceof Error
                        ? err.message
                        : "Unable to load inspection workbench."
                );
            } finally {
                setLoading(false);
            }
        }

        load();
    }, []);

    const now = useMemo(() => new Date(), []);

    // Combine templates with their schedule records
    const combinedInspections = useMemo(() => {
        const schedMap = new Map<string, MineInspectionSchedule>();
        schedules.forEach((s) => {
            if (s.template_id) {
                schedMap.set(s.template_id, s);
            }
        });

        return templates.map((tmpl) => {
            const sched = schedMap.get(tmpl.template_id);
            const statusInfo = computeScheduleStatus(sched, now);

            return {
                template: tmpl,
                schedule: sched,
                statusInfo,
            };
        });
    }, [templates, schedules, now]);

    // Breakdown counts for operational KPIs
    const kpis = useMemo(() => {
        let dueToday = 0;
        let dueSoon = 0;
        let overdue = 0;
        let conditional = 0;
        let upcoming = 0;

        combinedInspections.forEach(({ statusInfo }) => {
            if (statusInfo.modifier === "due") dueToday++;
            else if (statusInfo.modifier === "due-soon") dueSoon++;
            else if (statusInfo.modifier === "overdue") overdue++;
            else if (statusInfo.modifier === "event") conditional++;
            else upcoming++;
        });

        return { dueToday, dueSoon, overdue, conditional, upcoming, total: combinedInspections.length };
    }, [combinedInspections]);

    // Grouping by category
    const groupedByCategory = useMemo(() => {
        const groups: Record<string, typeof combinedInspections> = {};
        CATEGORY_ORDER.forEach((cat) => {
            groups[cat.key] = [];
        });

        combinedInspections.forEach((item) => {
            const family = item.template.inspection_family || "Other";
            if (!groups[family]) {
                groups[family] = [];
            }
            groups[family].push(item);
        });

        return groups;
    }, [combinedInspections]);

    // Filtered categories
    const displayedCategories = useMemo(() => {
        return CATEGORY_ORDER.filter((cat) => {
            if (selectedCategory !== "ALL" && cat.key !== selectedCategory) {
                return false;
            }
            return true;
        });
    }, [selectedCategory]);

    if (loading) {
        return (
            <div className="field-inspector-page">
                <div className="state-card">
                    <div className="state-card-inner">
                        <div className="loading-indicator" />
                        <span>LOADING STATUTORY INSPECTION SYSTEM...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (error || !mine) {
        return (
            <div className="field-inspector-page">
                <div className="state-card">
                    <div className="state-card-inner">
                        <AlertTriangle size={20} />
                        <span>{error || "Assigned mine could not be loaded."}</span>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="field-inspector-page">
            {/* =====================================================
                HERO: INSTITUTIONAL COMPLIANCE HEADER
            ===================================================== */}
            <section className="field-inspector-hero">
                <div>
                    <span className="section-number">
                        FIELD OPERATIONS · STATUTORY COMPLIANCE
                    </span>
                    <h1>Field Inspector Workbench</h1>
                    <p>
                        Mandatory statutory inspection mandates, scheduled shifts, regulatory thresholds
                        and evidence capture for active coal extraction under Coal Mines Regulations, 2017.
                    </p>
                </div>

                <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
                    <div className="assigned-mine-card">
                        <span>ASSIGNED DEMONSTRATION MINE</span>
                        <strong>{mine.name}</strong>
                        <small>
                            {mine.mine_id} · {mine.subsidiary || "BCCL"} · {mine.gassy_degree?.replaceAll("_", " ") || "DEGREE II"}
                        </small>
                    </div>
                    <button
                        type="button"
                        onClick={() => navigate("/field")}
                        style={{
                            background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
                            color: "#ffffff",
                            border: "none",
                            padding: "0.85rem 1.25rem",
                            borderRadius: 8,
                            cursor: "pointer",
                            fontWeight: 700,
                            fontSize: "0.9rem",
                            display: "flex",
                            alignItems: "center",
                            gap: "0.5rem",
                            boxShadow: "0 4px 12px rgba(16, 185, 129, 0.25)",
                        }}
                    >
                        <Compass size={18} />
                        GIS Geofence Check-In
                    </button>
                </div>
            </section>

            {/* =====================================================
                STATUTORY SCOPE BREAKDOWN BANNER — 13 MANDATES (3/2/2/2/2/1/1)
            ===================================================== */}
            <section className="scope-breakdown-banner">
                <div className="scope-breakdown-header">
                    <div className="scope-title-row">
                        <ClipboardCheck size={16} className="scope-icon" />
                        <span className="scope-title">
                            STATUTORY SCOPE BREAKDOWN — {templates.length} APPLICABLE INSPECTION MANDATES
                        </span>
                    </div>
                    <span className="scope-status-badge">
                        AUTHORITATIVE CMR 2017 PROFILE
                    </span>
                </div>

                <div className="scope-breakdown-grid">
                    {CATEGORY_ORDER.map((cat) => {
                        const items = groupedByCategory[cat.key] || [];
                        const Icon = cat.icon;
                        const isSelected = selectedCategory === cat.key;

                        return (
                            <button
                                type="button"
                                key={cat.key}
                                className={`scope-category-pill${isSelected ? " selected" : ""}`}
                                onClick={() => setSelectedCategory(isSelected ? "ALL" : cat.key)}
                                title={`Filter by ${cat.name}`}
                            >
                                <Icon size={14} className="category-pill-icon" />
                                <strong className="category-pill-count">{items.length}</strong>
                                <span className="category-pill-label">{cat.name.toUpperCase()}</span>
                            </button>
                        );
                    })}
                </div>
            </section>

            {/* =====================================================
                OPERATIONAL STATUS KPIS
            ===================================================== */}
            <section className="inspector-stat-grid">
                <div
                    className={`inspector-stat${selectedStatusFilter === "due" ? " active-filter" : ""}`}
                    onClick={() => setSelectedStatusFilter(selectedStatusFilter === "due" ? "ALL" : "due")}
                    role="button"
                    tabIndex={0}
                >
                    <ClipboardCheck size={18} />
                    <span>DUE TODAY</span>
                    <strong>{kpis.dueToday}</strong>
                </div>

                <div
                    className={`inspector-stat${selectedStatusFilter === "due-soon" ? " active-filter" : ""}`}
                    onClick={() => setSelectedStatusFilter(selectedStatusFilter === "due-soon" ? "ALL" : "due-soon")}
                    role="button"
                    tabIndex={0}
                >
                    <CalendarClock size={18} />
                    <span>DUE SOON</span>
                    <strong>{kpis.dueSoon}</strong>
                </div>

                <div
                    className={`inspector-stat${selectedStatusFilter === "upcoming" ? " active-filter" : ""}`}
                    onClick={() => setSelectedStatusFilter(selectedStatusFilter === "upcoming" ? "ALL" : "upcoming")}
                    role="button"
                    tabIndex={0}
                >
                    <Clock3 size={18} />
                    <span>UPCOMING</span>
                    <strong>{kpis.upcoming}</strong>
                </div>

                <div
                    className={`inspector-stat${selectedStatusFilter === "event" ? " active-filter" : ""}`}
                    onClick={() => setSelectedStatusFilter(selectedStatusFilter === "event" ? "ALL" : "event")}
                    role="button"
                    tabIndex={0}
                >
                    <Flame size={18} />
                    <span>CONDITIONAL / EVENT</span>
                    <strong>{kpis.conditional}</strong>
                </div>
            </section>

            {/* Filter Reset Banner if filtering */}
            {(selectedCategory !== "ALL" || selectedStatusFilter !== "ALL") && (
                <div className="filter-active-bar">
                    <span>
                        FILTER ACTIVE:{" "}
                        {selectedCategory !== "ALL" && `CATEGORY: ${selectedCategory.toUpperCase()} `}
                        {selectedStatusFilter !== "ALL" && `STATUS: ${selectedStatusFilter.toUpperCase()}`}
                    </span>
                    <button
                        type="button"
                        className="reset-filter-btn"
                        onClick={() => {
                            setSelectedCategory("ALL");
                            setSelectedStatusFilter("ALL");
                        }}
                    >
                        SHOW ALL 13 INSPECTIONS
                    </button>
                </div>
            )}

            {/* =====================================================
                THE 7 STATUTORY CATEGORIES & 13 INSPECTION CARDS
            ===================================================== */}
            <div className="categories-container">
                {displayedCategories.map((cat) => {
                    const allItems = groupedByCategory[cat.key] || [];
                    const filteredItems = allItems.filter((item) => {
                        if (selectedStatusFilter === "ALL") return true;
                        return item.statusInfo.modifier === selectedStatusFilter;
                    });

                    if (filteredItems.length === 0 && selectedStatusFilter !== "ALL") {
                        return null;
                    }

                    const Icon = cat.icon;

                    return (
                        <section className="category-section" key={cat.key}>
                            {/* Category Section Header */}
                            <div className="category-section-header">
                                <div className="category-header-left">
                                    <span className="category-index-badge">
                                        CATEGORY {cat.index} / 07
                                    </span>
                                    <div className="category-title-group">
                                        <div className="category-icon-wrapper">
                                            <Icon size={20} />
                                        </div>
                                        <h2>{cat.name}</h2>
                                        <span className="category-count-badge">
                                            {allItems.length} STATUTORY MANDATE{allItems.length === 1 ? "" : "S"}
                                        </span>
                                    </div>
                                    <p className="category-description">
                                        {cat.description}
                                    </p>
                                </div>
                            </div>

                            {/* Inspection Cards Grid */}
                            <div className="inspector-cards-grid">
                                {filteredItems.map(({ template, schedule, statusInfo }) => {
                                    const scheduleInstanceId =
                                        schedule?.schedule_instance_id ||
                                        `SCHINST-${mine.mine_id}-${template.template_id}`;

                                    const nextDue = schedule?.next_due_at;
                                    const frequencyLabel =
                                        template.frequency_label ||
                                        schedule?.frequency_label ||
                                        template.frequency_or_trigger ||
                                        "Statutory interval";
                                    const regulationRef =
                                        template.regulation_reference ||
                                        schedule?.regulation_reference ||
                                        "CMR 2017";
                                    const responsibleRole =
                                        template.responsible_role ||
                                        schedule?.responsible_role ||
                                        "Competent Person";

                                    return (
                                        <article
                                            className={`statutory-inspection-card status-${statusInfo.modifier}`}
                                            key={template.template_id}
                                        >
                                            {/* Card Top Identity */}
                                            <div className="card-top-bar">
                                                <span className={`status-pill ${statusInfo.modifier}`}>
                                                    {statusInfo.label}
                                                </span>
                                                <span className="template-family-tag">
                                                    {template.inspection_family.toUpperCase()}
                                                </span>
                                            </div>

                                            {/* Inspection Title */}
                                            <h3 className="card-inspection-title">
                                                {template.name}
                                            </h3>

                                            <p className="card-inspection-desc">
                                                {template.description || "Statutory inspection mandate under CMR 2017."}
                                            </p>

                                            {/* 4-Field Data Grid: Never hardcoded */}
                                            <div className="card-attributes-grid">
                                                <div className="card-attribute">
                                                    <span className="attr-label">FREQUENCY</span>
                                                    <strong className="attr-value">{frequencyLabel}</strong>
                                                </div>

                                                <div className="card-attribute">
                                                    <span className="attr-label">REGULATION</span>
                                                    <strong className="attr-value">{regulationRef}</strong>
                                                </div>

                                                <div className="card-attribute">
                                                    <span className="attr-label">RESPONSIBLE ROLE</span>
                                                    <strong className="attr-value">{responsibleRole}</strong>
                                                </div>

                                                <div className="card-attribute">
                                                    <span className="attr-label">NEXT DUE</span>
                                                    <strong className="attr-value">{formatDate(nextDue)}</strong>
                                                </div>
                                            </div>

                                            {/* Scope Chips */}
                                            <div className="card-scope-chips">
                                                <span className="scope-chip">
                                                    {template.measurements.length} MEASUREMENTS
                                                </span>
                                                <span className="scope-chip">
                                                    {template.checklist.length} CHECKS
                                                </span>
                                                <span className="scope-chip">
                                                    {template.evidence_requirements.length} EVIDENCE
                                                </span>
                                            </div>

                                            {/* Card Action Button */}
                                            <div className="card-action-row">
                                                <button
                                                    type="button"
                                                    className="start-inspection-btn"
                                                    onClick={() =>
                                                        navigate(
                                                            `/inspections/start/${scheduleInstanceId}`
                                                        )
                                                    }
                                                >
                                                    START INSPECTION
                                                    <ArrowRight size={15} />
                                                </button>
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        </section>
                    );
                })}
            </div>

            {/* Bottom Methodology Principle */}
            <section className="inspector-principle">
                <div>
                    <span className="section-number">PRITHVI INDUSTRIAL PROTOCOL</span>
                    <h2>Deterministic Statutory Compliance</h2>
                    <p>
                        All 13 inspections are derived deterministically from the Jharia Underground
                        Demonstration Mine profile (Underground Coal · Degree II · Mechanised HEMM ·
                        Winding · Blasting) under Coal Mines Regulations, 2017. All field measurements,
                        calibrated thresholds, and digital evidence dossiers are verified cryptographically.
                    </p>
                </div>
                <button
                    type="button"
                    className="primary-action"
                    onClick={() => navigate("/inspections/plan")}
                >
                    VIEW STATUTORY SCHEDULE PLAN
                    <ArrowRight size={15} />
                </button>
            </section>
        </div>
    );
}

export default FieldInspectorHome;