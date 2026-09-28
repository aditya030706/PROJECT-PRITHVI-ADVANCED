import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getMines } from "../api/mines";
import { getDashboardSummary } from "../api/dashboard";
import {
    getPendingVerifications,
    type PendingVerification,
} from "../api/verification";

type Mine = {
    mine_id: string;
    name: string;
    mine_type: string;
    gassy_degree?: string;
    state?: string | null;
    district?: string | null;
    subsidiary?: string | null;
    mining_method?: string | null;
    active?: boolean;
};

type DashboardSummary = {
    total_mines: number;
    inspections_due: number;
    inspections_submitted: number;
    awaiting_verification: number;
    verification_required: number;
    reinspection_recommended: number;
    source_anomalies: number;
    open_corrective_actions: number;
};

type ScheduleRow = {
    mineId: string;
    mineName: string;
    due: number;
    overdue: number;
    nextDue: string;
};

function formatDate(value: string) {
    if (!value || value === "—") return "—";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
}

function severityOf(item: PendingVerification) {
    const recommendation = item.recommendation.toLowerCase();

    if (
        recommendation.includes("escalat") ||
        recommendation.includes("reinspection")
    ) {
        return "HIGH";
    }

    if (
        recommendation.includes("review") ||
        recommendation.includes("suspicious")
    ) {
        return "MEDIUM";
    }

    return "LOW";
}

export default function ManagerReports() {
    const [summary, setSummary] =
        useState<DashboardSummary | null>(null);

    const [mines, setMines] = useState<Mine[]>([]);
    const [pending, setPending] =
        useState<PendingVerification[]>([]);

    const [schedules, setSchedules] =
        useState<ScheduleRow[]>([]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let cancelled = false;

        async function load() {
            try {
                setLoading(true);
                setError("");

                const [
                    summaryData,
                    mineData,
                    pendingData,
                ] = await Promise.all([
                    getDashboardSummary(),
                    getMines(),
                    getPendingVerifications(),
                ]);

                if (cancelled) return;

                const typedSummary =
                    summaryData as DashboardSummary;

                const typedMines =
                    mineData as Mine[];

                const typedPending =
                    pendingData as PendingVerification[];

                setSummary(typedSummary);
                setMines(typedMines);
                setPending(typedPending);

                const scheduleResults: Array<
                    ScheduleRow | null
                > = await Promise.all(
                    typedMines.map(
                        async (
                            mine
                        ): Promise<ScheduleRow | null> => {
                            try {
                                const response = await fetch(
                                    `http://localhost:8000/api/mines/${mine.mine_id}/schedule`
                                );

                                if (!response.ok) {
                                    return null;
                                }

                                const rows =
                                    (await response.json()) as Array<{
                                        next_due_at?: string | null;
                                        status?: string;
                                    }>;

                                const now = Date.now();

                                const dueRows = rows.filter(
                                    (row) => {
                                        if (!row.next_due_at) {
                                            return false;
                                        }

                                        return (
                                            new Date(
                                                row.next_due_at
                                            ).getTime() <= now
                                        );
                                    }
                                );

                                const overdueRows = rows.filter(
                                    (row) => {
                                        if (!row.next_due_at) {
                                            return false;
                                        }

                                        return (
                                            row.status
                                                ?.toLowerCase()
                                                .includes("overdue") ||
                                            new Date(
                                                row.next_due_at
                                            ).getTime() < now
                                        );
                                    }
                                );

                                const nextDue =
                                    rows
                                        .filter(
                                            (
                                                row
                                            ): row is {
                                                next_due_at: string;
                                                status?: string;
                                            } =>
                                                Boolean(
                                                    row.next_due_at
                                                )
                                        )
                                        .map(
                                            (row) =>
                                                row.next_due_at
                                        )
                                        .sort(
                                            (a, b) =>
                                                new Date(a).getTime() -
                                                new Date(b).getTime()
                                        )[0] ?? "—";

                                return {
                                    mineId: mine.mine_id,
                                    mineName: mine.name,
                                    due: dueRows.length,
                                    overdue: overdueRows.length,
                                    nextDue,
                                };
                            } catch {
                                return null;
                            }
                        }
                    )
                );

                if (!cancelled) {
                    const validSchedules =
                        scheduleResults.filter(
                            (
                                row
                            ): row is ScheduleRow =>
                                row !== null
                        );

                    setSchedules(validSchedules);
                }
            } catch (err) {
                if (!cancelled) {
                    setError(
                        err instanceof Error
                            ? err.message
                            : "Unable to load management reports."
                    );
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        load();

        return () => {
            cancelled = true;
        };
    }, []);

    const highAttention = useMemo(
        () =>
            pending.filter(
                (item) =>
                    severityOf(item) === "HIGH"
            ).length,
        [pending]
    );

    const mediumAttention = useMemo(
        () =>
            pending.filter(
                (item) =>
                    severityOf(item) === "MEDIUM"
            ).length,
        [pending]
    );

    const totalDue = useMemo(
        () =>
            schedules.reduce(
                (sum, row) => sum + row.due,
                0
            ),
        [schedules]
    );

    const totalOverdue = useMemo(
        () =>
            schedules.reduce(
                (sum, row) => sum + row.overdue,
                0
            ),
        [schedules]
    );

    return (
        <main className="manager-reports-page">
            <style>{`
        .manager-reports-page {
          min-height: calc(100vh - 110px);
          padding: 32px 40px 56px;
          background: #f6f7f8;
          color: #182026;
          font-family: Inter, ui-sans-serif, system-ui,
            -apple-system, BlinkMacSystemFont,
            "Segoe UI", sans-serif;
        }

        .mr-shell {
          max-width: 1440px;
          margin: 0 auto;
        }

        .mr-header {
          display: flex;
          justify-content: space-between;
          gap: 24px;
          align-items: flex-end;
          margin-bottom: 26px;
        }

        .mr-eyebrow {
          margin: 0 0 7px;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: .14em;
          color: #69737c;
        }

        .mr-title {
          margin: 0;
          font-size: 30px;
          line-height: 1.15;
          letter-spacing: -.025em;
          font-weight: 720;
        }

        .mr-subtitle {
          margin: 8px 0 0;
          max-width: 760px;
          font-size: 14px;
          line-height: 1.6;
          color: #68727b;
        }

        .mr-status {
          min-width: 180px;
          padding: 11px 14px;
          border: 1px solid #dfe3e6;
          background: #fff;
          border-radius: 8px;
          font-size: 12px;
          color: #59636c;
          text-align: right;
        }

        .mr-status strong {
          display: block;
          margin-bottom: 3px;
          font-size: 13px;
          color: #1e292f;
        }

        .mr-error {
          margin-bottom: 20px;
          padding: 13px 15px;
          border: 1px solid #e2bcbc;
          border-radius: 8px;
          background: #fff7f7;
          color: #8b3030;
          font-size: 13px;
        }

        .mr-kpis {
          display: grid;
          grid-template-columns:
            repeat(4, minmax(0, 1fr));
          gap: 12px;
          margin-bottom: 18px;
        }

        .mr-kpi {
          min-height: 112px;
          padding: 18px;
          background: #fff;
          border: 1px solid #dfe3e6;
          border-radius: 9px;
        }

        .mr-kpi-label {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: .09em;
          color: #747e86;
          text-transform: uppercase;
        }

        .mr-kpi-value {
          margin-top: 13px;
          font-size: 29px;
          font-weight: 730;
          letter-spacing: -.025em;
        }

        .mr-kpi-note {
          margin-top: 4px;
          font-size: 11px;
          color: #78828a;
        }

        .mr-grid {
          display: grid;
          grid-template-columns:
            minmax(0, 1.35fr)
            minmax(330px, .65fr);
          gap: 18px;
        }

        .mr-panel {
          background: #fff;
          border: 1px solid #dfe3e6;
          border-radius: 9px;
          overflow: hidden;
          margin-bottom: 18px;
        }

        .mr-panel-head {
          padding: 17px 19px;
          border-bottom: 1px solid #e8eaec;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .mr-panel-title {
          margin: 0;
          font-size: 14px;
          font-weight: 720;
        }

        .mr-panel-meta {
          font-size: 11px;
          color: #7b858d;
        }

        .mr-table-wrap {
          overflow-x: auto;
        }

        .mr-table {
          width: 100%;
          border-collapse: collapse;
          min-width: 650px;
        }

        .mr-table th {
          padding: 11px 16px;
          text-align: left;
          background: #fafbfb;
          border-bottom: 1px solid #e8eaec;
          font-size: 10px;
          letter-spacing: .08em;
          color: #77818a;
          text-transform: uppercase;
        }

        .mr-table td {
          padding: 14px 16px;
          border-bottom: 1px solid #edf0f1;
          font-size: 13px;
          vertical-align: middle;
        }

        .mr-table tr:last-child td {
          border-bottom: 0;
        }

        .mr-mine {
          color: #1d2a31;
          text-decoration: none;
          font-weight: 680;
        }

        .mr-mine:hover {
          text-decoration: underline;
        }

        .mr-chip {
          display: inline-flex;
          align-items: center;
          min-height: 23px;
          padding: 0 8px;
          border: 1px solid #dfe3e6;
          border-radius: 999px;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: .06em;
        }

        .mr-chip.high {
          border-color: #d9b7b7;
          background: #fff8f8;
          color: #963f3f;
        }

        .mr-chip.medium {
          border-color: #dfd1aa;
          background: #fffcf3;
          color: #806521;
        }

        .mr-chip.low {
          background: #fafbfb;
          color: #68737b;
        }

        .mr-list {
          padding: 4px 18px 8px;
        }

        .mr-list-row {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          padding: 14px 0;
          border-bottom: 1px solid #edf0f1;
        }

        .mr-list-row:last-child {
          border-bottom: 0;
        }

        .mr-list-label {
          font-size: 12px;
          color: #69747c;
        }

        .mr-list-value {
          font-size: 13px;
          font-weight: 720;
          text-align: right;
        }

        .mr-note {
          padding: 16px 18px;
          font-size: 12px;
          line-height: 1.6;
          color: #68737b;
          background: #fafbfb;
          border-top: 1px solid #edf0f1;
        }

        .mr-empty {
          padding: 28px 18px;
          color: #78828a;
          font-size: 13px;
        }

        .mr-actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .mr-action {
          display: inline-flex;
          align-items: center;
          min-height: 34px;
          padding: 0 12px;
          border: 1px solid #d9dde0;
          border-radius: 7px;
          background: #fff;
          color: #263239;
          text-decoration: none;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: .04em;
        }

        .mr-action:hover {
          background: #f7f8f8;
        }

        .mr-footer-note {
          margin-top: 4px;
          padding: 15px 17px;
          border-left: 3px solid #9aa4ab;
          background: #fff;
          border-top: 1px solid #e2e5e7;
          border-right: 1px solid #e2e5e7;
          border-bottom: 1px solid #e2e5e7;
          border-radius: 0 7px 7px 0;
          font-size: 12px;
          line-height: 1.6;
          color: #66717a;
        }

        @media (max-width: 1050px) {
          .mr-kpis {
            grid-template-columns:
              repeat(2, minmax(0, 1fr));
          }

          .mr-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 650px) {
          .manager-reports-page {
            padding: 24px 18px 40px;
          }

          .mr-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .mr-status {
            text-align: left;
          }

          .mr-kpis {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

            <div className="mr-shell">
                <header className="mr-header">
                    <div>
                        <p className="mr-eyebrow">
                            MINE MANAGER · MANAGEMENT REPORTING
                        </p>

                        <h1 className="mr-title">
                            Compliance Reports
                        </h1>

                        <p className="mr-subtitle">
                            Management view of mine compliance,
                            inspection verification, regulatory
                            scheduling and current attention areas.
                            Data is derived from the live PRITHVI
                            backend.
                        </p>
                    </div>

                    <div className="mr-status">
                        <strong>
                            {loading
                                ? "Loading data"
                                : "Live reporting view"}
                        </strong>

                        {loading
                            ? "Synchronising…"
                            : `${mines.length} active mine records`}
                    </div>
                </header>

                {error && (
                    <div className="mr-error">
                        {error}
                    </div>
                )}

                <section className="mr-kpis">
                    <div className="mr-kpi">
                        <div className="mr-kpi-label">
                            Active Mines
                        </div>

                        <div className="mr-kpi-value">
                            {loading
                                ? "—"
                                : summary?.total_mines ??
                                mines.length}
                        </div>

                        <div className="mr-kpi-note">
                            Registered active assets
                        </div>
                    </div>

                    <div className="mr-kpi">
                        <div className="mr-kpi-label">
                            Inspections Due
                        </div>

                        <div className="mr-kpi-value">
                            {loading
                                ? "—"
                                : summary?.inspections_due ??
                                totalDue}
                        </div>

                        <div className="mr-kpi-note">
                            Current scheduling position
                        </div>
                    </div>

                    <div className="mr-kpi">
                        <div className="mr-kpi-label">
                            Awaiting Verification
                        </div>

                        <div className="mr-kpi-value">
                            {loading
                                ? "—"
                                : summary?.awaiting_verification ??
                                pending.length}
                        </div>

                        <div className="mr-kpi-note">
                            Inspection cases requiring control
                            review
                        </div>
                    </div>

                    <div className="mr-kpi">
                        <div className="mr-kpi-label">
                            Reinspection Recommended
                        </div>

                        <div className="mr-kpi-value">
                            {loading
                                ? "—"
                                : summary?.reinspection_recommended ??
                                0}
                        </div>

                        <div className="mr-kpi-note">
                            Current verification recommendation
                        </div>
                    </div>
                </section>

                <div className="mr-grid">
                    <div>
                        <section className="mr-panel">
                            <div className="mr-panel-head">
                                <h2 className="mr-panel-title">
                                    Mine-wise Compliance Position
                                </h2>

                                <span className="mr-panel-meta">
                                    Live portfolio view
                                </span>
                            </div>

                            <div className="mr-table-wrap">
                                {mines.length === 0 ? (
                                    <div className="mr-empty">
                                        No active mines are available.
                                    </div>
                                ) : (
                                    <table className="mr-table">
                                        <thead>
                                            <tr>
                                                <th>Mine</th>
                                                <th>Type</th>
                                                <th>Inspections Due</th>
                                                <th>Next Due</th>
                                                <th>Attention</th>
                                            </tr>
                                        </thead>

                                        <tbody>
                                            {mines.map((mine) => {
                                                const schedule =
                                                    schedules.find(
                                                        (row) =>
                                                            row.mineId ===
                                                            mine.mine_id
                                                    );

                                                return (
                                                    <tr
                                                        key={mine.mine_id}
                                                    >
                                                        <td>
                                                            <Link
                                                                className="mr-mine"
                                                                to={`/mines/${mine.mine_id}`}
                                                            >
                                                                {mine.name}
                                                            </Link>

                                                            <div className="mr-panel-meta">
                                                                {mine.mine_id}
                                                            </div>
                                                        </td>

                                                        <td>
                                                            {mine.mine_type}
                                                        </td>

                                                        <td>
                                                            {schedule?.due ?? "—"}
                                                        </td>

                                                        <td>
                                                            {formatDate(
                                                                schedule?.nextDue ??
                                                                "—"
                                                            )}
                                                        </td>

                                                        <td>
                                                            {schedule?.overdue ? (
                                                                <span className="mr-chip high">
                                                                    {schedule.overdue}{" "}
                                                                    OVERDUE
                                                                </span>
                                                            ) : (
                                                                <span className="mr-chip low">
                                                                    NO OVERDUE
                                                                </span>
                                                            )}
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </section>

                        <section className="mr-panel">
                            <div className="mr-panel-head">
                                <h2 className="mr-panel-title">
                                    Verification Position
                                </h2>

                                <span className="mr-panel-meta">
                                    {pending.length} pending case
                                    {pending.length === 1
                                        ? ""
                                        : "s"}
                                </span>
                            </div>

                            {pending.length === 0 ? (
                                <div className="mr-empty">
                                    No pending verification cases are
                                    currently available.
                                </div>
                            ) : (
                                <div className="mr-table-wrap">
                                    <table className="mr-table">
                                        <thead>
                                            <tr>
                                                <th>Mine</th>
                                                <th>Inspection Date</th>
                                                <th>Confidence</th>
                                                <th>Recommendation</th>
                                                <th>Attention</th>
                                            </tr>
                                        </thead>

                                        <tbody>
                                            {pending
                                                .slice(0, 12)
                                                .map((item) => {
                                                    const level =
                                                        severityOf(item);

                                                    return (
                                                        <tr
                                                            key={
                                                                item.verification_id
                                                            }
                                                        >
                                                            <td>
                                                                <Link
                                                                    className="mr-mine"
                                                                    to={`/verification/${item.inspection_id}`}
                                                                >
                                                                    {item.mine_id}
                                                                </Link>
                                                            </td>

                                                            <td>
                                                                {formatDate(
                                                                    item.inspection_date
                                                                )}
                                                            </td>

                                                            <td>
                                                                {Math.round(
                                                                    item.confidence *
                                                                    100
                                                                )}
                                                                %
                                                            </td>

                                                            <td>
                                                                {item.recommendation}
                                                            </td>

                                                            <td>
                                                                <span
                                                                    className={`mr-chip ${level.toLowerCase()}`}
                                                                >
                                                                    {level}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            <div className="mr-note">
                                Verification signals are control
                                indicators. They are not automatic
                                fraud findings and should be interpreted
                                through the existing human-review
                                workflow.
                            </div>
                        </section>
                    </div>

                    <aside>
                        <section className="mr-panel">
                            <div className="mr-panel-head">
                                <h2 className="mr-panel-title">
                                    Management Position
                                </h2>
                            </div>

                            <div className="mr-list">
                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        Inspections submitted
                                    </span>

                                    <span className="mr-list-value">
                                        {summary?.inspections_submitted ??
                                            "—"}
                                    </span>
                                </div>

                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        Verification required
                                    </span>

                                    <span className="mr-list-value">
                                        {summary?.verification_required ??
                                            "—"}
                                    </span>
                                </div>

                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        Source anomalies
                                    </span>

                                    <span className="mr-list-value">
                                        {summary?.source_anomalies ??
                                            "—"}
                                    </span>
                                </div>

                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        Open corrective actions
                                    </span>

                                    <span className="mr-list-value">
                                        {summary?.open_corrective_actions ??
                                            "—"}
                                    </span>
                                </div>

                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        Scheduled items due
                                    </span>

                                    <span className="mr-list-value">
                                        {totalDue}
                                    </span>
                                </div>

                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        Scheduled items overdue
                                    </span>

                                    <span className="mr-list-value">
                                        {totalOverdue}
                                    </span>
                                </div>
                            </div>
                        </section>

                        <section className="mr-panel">
                            <div className="mr-panel-head">
                                <h2 className="mr-panel-title">
                                    Attention Queue
                                </h2>
                            </div>

                            <div className="mr-list">
                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        High attention cases
                                    </span>

                                    <span className="mr-list-value">
                                        {highAttention}
                                    </span>
                                </div>

                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        Review attention cases
                                    </span>

                                    <span className="mr-list-value">
                                        {mediumAttention}
                                    </span>
                                </div>

                                <div className="mr-list-row">
                                    <span className="mr-list-label">
                                        Reinspection recommended
                                    </span>

                                    <span className="mr-list-value">
                                        {summary?.reinspection_recommended ??
                                            0}
                                    </span>
                                </div>
                            </div>

                            <div className="mr-note">
                                Use the Verification workspace for
                                case-level decisions and the Mine pages
                                for mine-specific compliance context.
                            </div>
                        </section>

                        <section className="mr-panel">
                            <div className="mr-panel-head">
                                <h2 className="mr-panel-title">
                                    Management Actions
                                </h2>
                            </div>

                            <div
                                style={{
                                    padding: "16px 18px",
                                }}
                            >
                                <div className="mr-actions">
                                    <Link
                                        className="mr-action"
                                        to="/mines"
                                    >
                                        VIEW MINE PORTFOLIO
                                    </Link>

                                    <Link
                                        className="mr-action"
                                        to="/verification"
                                    >
                                        OPEN VERIFICATION
                                    </Link>
                                </div>
                            </div>
                        </section>
                    </aside>
                </div>

                <div className="mr-footer-note">
                    Reporting scope is intentionally limited to
                    information currently supported by PRITHVI&apos;s
                    live APIs. Detailed corrective-action closure,
                    historical trend analytics and downloadable
                    statutory reports can be added when their
                    underlying backend data contracts are implemented.
                </div>
            </div>
        </main>
    );
}