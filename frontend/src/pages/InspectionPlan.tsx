import {
    ArrowLeft,
    ArrowRight,
    CalendarClock,
    CheckCircle2,
    Clock3,
    FileCheck2,
    ShieldAlert,
    Tag,
} from "lucide-react";

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getMine } from "../api/mines";
import { getMineSchedule } from "../api/schedules";
import type { MineInspectionSchedule } from "../api/schedules";

const JHARIA_MINE_ID = "MINE-BCCL-JHARIA-01";

type MineRecord = {
    mine_id: string;
    name: string;
    subsidiary?: string;
    gassy_degree?: string;
    active?: boolean;
};

function formatDate(value: string | null) {
    if (!value) {
        return "NOT SCHEDULED";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "DATE UNAVAILABLE";
    }

    return date
        .toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
        })
        .toUpperCase();
}

function formatFrequency(schedule: MineInspectionSchedule) {
    if (schedule.frequency_label) {
        return schedule.frequency_label;
    }

    if (
        schedule.interval_value !== null &&
        schedule.interval_unit
    ) {
        return `Every ${schedule.interval_value} ${schedule.interval_unit}`;
    }

    return schedule.frequency_type || "SCHEDULED";
}

function InspectionPlan() {
    const navigate = useNavigate();

    const [mine, setMine] = useState<MineRecord | null>(null);
    const [schedules, setSchedules] = useState<MineInspectionSchedule[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const [mineData, scheduleData] = await Promise.all([
                    getMine(JHARIA_MINE_ID) as Promise<MineRecord>,
                    getMineSchedule(JHARIA_MINE_ID),
                ]);

                setMine(mineData);
                setSchedules(scheduleData.schedules ?? []);
            } catch (err) {
                setError(
                    err instanceof Error
                        ? err.message
                        : "Unable to load inspection plan."
                );
            } finally {
                setLoading(false);
            }
        }

        void load();
    }, []);

    const activeSchedules = useMemo(
        () => schedules.filter((schedule) => Boolean(schedule.active)),
        [schedules]
    );

    const now = new Date();

    const overdue = activeSchedules.filter(
        (schedule) =>
            schedule.next_due_at &&
            new Date(schedule.next_due_at) < now
    );

    const dueToday = activeSchedules.filter((schedule) => {
        if (!schedule.next_due_at) {
            return false;
        }
        const due = new Date(schedule.next_due_at);
        return due.toDateString() === now.toDateString();
    });

    const upcoming = activeSchedules.filter(
        (schedule) =>
            schedule.next_due_at &&
            new Date(schedule.next_due_at) > now
    );

    const orderedSchedules = [
        ...overdue,
        ...dueToday,
        ...upcoming,
    ];

    if (loading) {
        return (
            <div className="field-inspector-page">
                <div className="state-card">
                    LOADING JHARIA INSPECTION PLAN...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="field-inspector-page">
                <div className="state-card">
                    {error}
                </div>
            </div>
        );
    }

    return (
        <div className="field-inspector-page inspection-plan-page">
            <button
                className="secondary-action plan-back"
                onClick={() => navigate("/")}
            >
                <ArrowLeft size={15} />
                BACK TO WORKBENCH
            </button>

            <section className="field-inspector-hero plan-hero">
                <div>
                    <span className="section-number">
                        FIELD INSPECTION PLAN
                    </span>

                    <h1>
                        What must be inspected
                    </h1>

                    <p>
                        Statutory inspection register generated exclusively for
                        Jharia Underground Demonstration Mine under Coal Mines Regulations 2017.
                    </p>
                </div>

                {/* MINE SCOPE (JHARIA EXCLUSIVE) */}
                <div className="assigned-mine-card">
                    <span>
                        INSPECTION SCOPE
                    </span>

                    <strong>
                        {mine?.name ?? "Jharia Underground Demonstration Mine"}
                    </strong>

                    <small>
                        {JHARIA_MINE_ID} • BCCL • UNDERGROUND COAL (DEGREE II)
                    </small>
                </div>
            </section>

            <section className="plan-summary">
                <div>
                    <ShieldAlert size={17} />
                    <span>OVERDUE</span>
                    <strong>{overdue.length}</strong>
                </div>

                <div>
                    <CalendarClock size={17} />
                    <span>DUE TODAY</span>
                    <strong>{dueToday.length}</strong>
                </div>

                <div>
                    <Clock3 size={17} />
                    <span>UPCOMING</span>
                    <strong>{upcoming.length}</strong>
                </div>

                <div>
                    <CheckCircle2 size={17} />
                    <span>ACTIVE STATUTORY OBLIGATIONS</span>
                    <strong>{activeSchedules.length}</strong>
                </div>
            </section>

            <section className="inspector-section">
                <div className="inspector-section-heading">
                    <div>
                        <span className="section-number">
                            01 / STATUTORY REGISTER
                        </span>

                        <h2>
                            13 Applicable Statutory Inspections
                        </h2>
                    </div>
                </div>

                <div className="inspection-plan-list">
                    {orderedSchedules.length === 0 ? (
                        <div className="state-card">
                            No active inspection requirements found for Jharia Underground Mine.
                        </div>
                    ) : (
                        orderedSchedules.map((schedule) => {
                            const isOverdue = Boolean(
                                schedule.next_due_at &&
                                new Date(schedule.next_due_at) < now
                            );

                            const isDueToday = Boolean(
                                schedule.next_due_at &&
                                new Date(schedule.next_due_at).toDateString() ===
                                now.toDateString()
                            );

                            const status = isOverdue
                                ? "OVERDUE"
                                : isDueToday
                                    ? "DUE TODAY"
                                    : "UPCOMING";

                            const displayName =
                                schedule.template_name ||
                                schedule.schedule_name ||
                                schedule.name ||
                                schedule.template_id;

                            return (
                                <article
                                    className="inspection-plan-card"
                                    key={schedule.schedule_instance_id}
                                >
                                    <div className="plan-card-top">
                                        <div>
                                            <span
                                                className={
                                                    isOverdue
                                                        ? "plan-status overdue"
                                                        : isDueToday
                                                            ? "plan-status due"
                                                            : "plan-status upcoming"
                                                }
                                            >
                                                {status}
                                            </span>

                                            {schedule.inspection_family && (
                                                <span className="plan-mine-tag">
                                                    <Tag size={10} style={{ marginRight: 4 }} />
                                                    {schedule.inspection_family}
                                                </span>
                                            )}

                                            <div className="plan-code">
                                                {schedule.schedule_instance_id}
                                            </div>

                                            <h3>
                                                {displayName}
                                            </h3>
                                        </div>

                                        <button
                                            className="primary-action"
                                            onClick={() =>
                                                navigate(
                                                    `/inspections/prepare/${schedule.schedule_instance_id}`
                                                )
                                            }
                                        >
                                            PREPARE INSPECTION
                                            <ArrowRight size={15} />
                                        </button>
                                    </div>

                                    <div className="plan-card-grid">
                                        <div>
                                            <span>
                                                STATUTORY REGULATION
                                            </span>
                                            <strong>
                                                {schedule.regulation_reference || schedule.obligation_id}
                                            </strong>
                                        </div>

                                        <div>
                                            <span>
                                                RESPONSIBLE ROLE
                                            </span>
                                            <strong>
                                                {schedule.responsible_role || "Designated Competent Person"}
                                            </strong>
                                        </div>

                                        <div>
                                            <span>
                                                FREQUENCY
                                            </span>
                                            <strong>
                                                {formatFrequency(schedule)}
                                            </strong>
                                        </div>

                                        <div>
                                            <span>
                                                NEXT DUE
                                            </span>
                                            <strong>
                                                {formatDate(schedule.next_due_at)}
                                            </strong>
                                        </div>
                                    </div>

                                    <div className="plan-card-footer">
                                        <div>
                                            <FileCheck2 size={15} />
                                            <span>
                                                STATUTORY COMPLIANCE STATUS
                                            </span>
                                            <strong>
                                                {schedule.validation_status || "ACTIVE"}
                                            </strong>
                                        </div>

                                        <div>
                                            <span>
                                                TEMPLATE ID
                                            </span>
                                            <strong>
                                                {schedule.template_id}
                                            </strong>
                                        </div>
                                    </div>
                                </article>
                            );
                        })
                    )}
                </div>
            </section>
        </div>
    );
}

export default InspectionPlan;
