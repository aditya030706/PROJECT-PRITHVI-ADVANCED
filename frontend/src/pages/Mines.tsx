import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    Activity,
    ArrowRight,
    CheckCircle2,
    Factory,
    MapPin,
    RefreshCw,
    Search,
    ShieldCheck,
    Truck,
} from "lucide-react";

import { getMines } from "../api/mines";

type Mine = {
    mine_id: string;
    name: string;
    mine_type: string;
    gassy_degree: string;
    state?: string | null;
    district?: string | null;
    subsidiary?: string | null;
    mining_method?: string | null;
    active?: boolean;
    mechanised?: boolean;
    uses_hemm?: boolean;
    has_winding_installation?: boolean;
    blasting_operation?: boolean;
};

/*
 * Only these three PRITHVI demonstration assets
 * should appear in the Mines portfolio.
 */
const PRITHVI_MINES = new Set([
    "MINE-BCCL-JHARIA-01",
    "MINE-ECL-RANIGANJ-01",
    "MINE-MCL-TALCHER-01",
]);

export function getMineDisplayName(name: string, mineId: string): string {
    if (mineId === "MINE-BCCL-JHARIA-01") return "Jharia Underground Mine";
    if (mineId === "MINE-ECL-RANIGANJ-01") return "Raniganj Underground Mine";
    if (mineId === "MINE-MCL-TALCHER-01") return "Talcher Opencast Mine";
    return name
        .replace(/\s+Demonstration\s+Mine/i, " Mine")
        .replace(/\s+Demonstration/i, "");
}

export function getMineOperator(subsidiary?: string | null, mineId?: string): string {
    if (subsidiary) return subsidiary.toUpperCase();
    if (mineId?.includes("BCCL")) return "BCCL";
    if (mineId?.includes("ECL")) return "ECL";
    if (mineId?.includes("MCL")) return "MCL";
    return "CIL";
}

function title(value?: string | null) {
    if (!value) return "—";

    return value
        .replaceAll("_", " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());
}

function MineCard({ mine }: { mine: Mine }) {
    const navigate = useNavigate();

    const location = [mine.district, mine.state]
        .filter(Boolean)
        .join(", ");

    const underground = mine.mine_type.toLowerCase().includes("underground");
    const displayName = getMineDisplayName(mine.name, mine.mine_id);
    const operator = getMineOperator(mine.subsidiary, mine.mine_id);

    return (
        <article
            className="mines-card"
            onClick={() => navigate(`/mines/${mine.mine_id}`)}
            onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    navigate(`/mines/${mine.mine_id}`);
                }
            }}
            role="button"
            tabIndex={0}
            aria-label={`View intelligence for ${displayName}`}
        >
            {/* STATUS + MINE ID */}
            <div className="mines-card-meta-top">
                <div className="mines-card-status">
                    <span className="status-dot-pulse" aria-hidden="true" />
                    <span>OPERATIONAL</span>
                </div>
                <div className="mines-card-id-wrapper">
                    <span className="mines-card-id">{mine.mine_id}</span>
                </div>
            </div>

            {/* IDENTITY: OPERATOR -> MINE NAME -> LOCATION */}
            <div className="mines-card-identity">
                <div className="mines-card-operator">{operator}</div>
                <h2 className="mines-card-name">{displayName}</h2>
                <div className="mines-card-location">
                    <MapPin size={13} aria-hidden="true" />
                    <span>{location || "Location not specified"}</span>
                </div>
            </div>

            {/* TAGS */}
            <div className="mines-card-tags">
                <span className="mines-card-tag">{title(mine.mine_type)}</span>
                <span className="mines-card-tag">
                    {mine.gassy_degree === "NOT_APPLICABLE"
                        ? "Gassy: N/A"
                        : title(mine.gassy_degree)}
                </span>
                <span className="mines-card-tag">
                    {underground ? "Underground" : "Opencast"}
                </span>
            </div>

            <div className="mines-card-divider" />

            {/* OPERATING PROFILE */}
            <div className="mines-card-profile">
                <div className="profile-cell">
                    <span className="profile-label">OPERATING MODE</span>
                    <strong className="profile-value">
                        {underground ? "UNDERGROUND" : "OPENCAST"}
                    </strong>
                </div>

                <div className="profile-cell">
                    <span className="profile-label">GASSY CLASS</span>
                    <strong className="profile-value">
                        {mine.gassy_degree === "NOT_APPLICABLE"
                            ? "NOT APPLICABLE"
                            : title(mine.gassy_degree).toUpperCase()}
                    </strong>
                </div>

                <div className="profile-cell">
                    <span className="profile-label">MECHANISED</span>
                    <strong className="profile-value">
                        {mine.mechanised ? "YES" : "NO"}
                    </strong>
                </div>

                <div className="profile-cell">
                    <span className="profile-label">BLASTING</span>
                    <strong className="profile-value">
                        {mine.blasting_operation ? "ACTIVE" : "NO"}
                    </strong>
                </div>
            </div>

            {/* FOOTER CTA */}
            <div className="mines-card-footer">
                <div className="mines-view-button">
                    <span>VIEW MINE INTELLIGENCE</span>
                    <ArrowRight size={14} aria-hidden="true" />
                </div>
            </div>
        </article>
    );
}

export default function Mines() {

    const [mines, setMines] = useState<Mine[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [query, setQuery] = useState("");

    async function load(refresh = false) {

        setError(null);

        if (refresh) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }

        try {

            const data = (await getMines()) as Mine[];

            const portfolio = data.filter(
                (mine) =>
                    PRITHVI_MINES.has(mine.mine_id) &&
                    mine.active !== false
            );

            setMines(portfolio);

        } catch (err) {

            setError(
                err instanceof Error
                    ? err.message
                    : "Unable to load mine portfolio."
            );

        } finally {

            setLoading(false);
            setRefreshing(false);
        }
    }

    useEffect(() => {
        void load();
    }, []);

    const filteredMines = useMemo(() => {

        const value = query.trim().toLowerCase();

        if (!value) {
            return mines;
        }

        return mines.filter((mine) =>
            [
                mine.mine_id,
                mine.name,
                mine.subsidiary,
                mine.state,
                mine.district,
                mine.mine_type,
                mine.mining_method,
            ]
                .filter(Boolean)
                .join(" ")
                .toLowerCase()
                .includes(value)
        );

    }, [mines, query]);

    const undergroundCount = mines.filter(
        (mine) =>
            mine.mine_type.toLowerCase().includes("underground")
    ).length;

    const opencastCount = mines.filter(
        (mine) =>
            mine.mine_type.toLowerCase().includes("opencast")
    ).length;

    return (
        <div className="mines-page">

            <style>{`

                .mines-page {
                    --ink: #18232c;
                    --muted: #6f7982;
                    --soft: #8c959d;
                    --border: rgba(24,34,43,.11);
                    --paper: #f7f4ee;
                    --card: #fffdf9;
                    --green: #247d52;
                    --orange: #a86a28;

                    min-height: calc(100vh - 104px);

                    padding: 30px 28px 42px;

                    background:
                        radial-gradient(
                            circle at 10% 0%,
                            rgba(174,128,65,.06),
                            transparent 35%
                        ),
                        var(--paper);

                    color: var(--ink);
                }

                .mines-shell {
                    max-width: 1540px;
                    margin: 0 auto;
                }

                /* HEADER */

                .mines-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                    gap: 25px;
                    margin-bottom: 24px;
                }

                .mines-eyebrow {
                    display: flex;
                    align-items: center;
                    gap: 8px;

                    margin: 0 0 9px;

                    color: #79572f;

                    font-size: 10px;
                    font-weight: 900;
                    letter-spacing: .14em;
                }

                .mines-eyebrow::before {
                    content: "";
                    width: 20px;
                    height: 1px;
                    background: var(--orange);
                }

                .mines-header h1 {
                    margin: 0;

                    font-size: clamp(
                        29px,
                        3vw,
                        42px
                    );

                    line-height: 1.05;
                    letter-spacing: -.035em;
                    font-weight: 850;
                }

                .mines-header p {
                    max-width: 720px;

                    margin: 10px 0 0;

                    color: var(--muted);

                    font-size: 13px;
                    line-height: 1.6;
                }

                /* TOOLBAR */

                .mines-toolbar {
                    display: flex;
                    gap: 8px;
                }

                .mines-search {
                    width: 250px;
                    height: 40px;

                    display: flex;
                    align-items: center;
                    gap: 8px;

                    padding: 0 12px;

                    border: 1px solid var(--border);
                    border-radius: 4px;

                    background: rgba(
                        255,
                        255,
                        255,
                        .72
                    );

                    color: #7c868e;
                }

                .mines-search input {
                    width: 100%;

                    border: 0;
                    outline: 0;

                    background: transparent;

                    font-size: 11px;
                    color: var(--ink);
                }

                .mines-refresh {
                    height: 40px;

                    display: flex;
                    align-items: center;
                    gap: 8px;

                    padding: 0 13px;

                    border: 1px solid #cfc6b8;
                    border-radius: 4px;

                    background: var(--card);

                    color: #394650;

                    font-size: 9px;
                    font-weight: 900;
                    letter-spacing: .08em;

                    cursor: pointer;
                }

                .mines-refresh:hover {
                    border-color: var(--orange);
                }

                /* SUMMARY */

                .mines-summary {
                    display: grid;
                    grid-template-columns:
                        repeat(4, 1fr);

                    gap: 10px;

                    margin-bottom: 25px;
                }

                .mines-summary-card {
                    min-height: 76px;

                    padding: 14px 17px;

                    border: 1px solid var(--border);
                    border-radius: 4px;

                    background:
                        rgba(255,253,249,.72);
                }

                .mines-summary-label {
                    display: flex;
                    align-items: center;
                    gap: 7px;

                    color: #828c94;

                    font-size: 9px;
                    font-weight: 900;
                    letter-spacing: .1em;
                }

                .mines-summary-value {
                    display: block;

                    margin-top: 7px;

                    font-size: 24px;
                    line-height: 1;

                    letter-spacing: -.03em;
                }

                .mines-summary-note {
                    margin-left: 7px;

                    color: #858f97;

                    font-size: 8px;
                    font-weight: 700;
                }

                /* SECTION */

                .mines-section-head {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;

                    margin-bottom: 13px;
                }

                .mines-section-head strong {
                    font-size: 10px;
                    letter-spacing: .13em;
                }

                .mines-section-head span {
                    color: var(--soft);

                    font-size: 9px;
                    font-weight: 800;
                    letter-spacing: .08em;
                }

                /* GRID */

                .mines-grid {
                    display: grid;

                    grid-template-columns:
                        repeat(3, minmax(0,1fr));

                    gap: 18px;
                }

                /* CARD */

                .mines-card {
                    display: flex;
                    flex-direction: column;

                    padding: 18px 20px 20px;

                    border: 1px solid var(--border);
                    border-radius: 4px;

                    background: var(--card, #ffffff);

                    box-shadow:
                        0 1px 4px rgba(17,20,22,.04);

                    cursor: pointer;

                    transition:
                        transform .18s ease,
                        box-shadow .18s ease,
                        border-color .18s ease;
                }

                .mines-card:hover {
                    transform: translateY(-2px);

                    border-color: var(--copper);

                    box-shadow:
                        0 8px 24px rgba(17,20,22,.08);
                }

                .mines-card:focus-visible {
                    outline: 2px solid var(--copper);
                    outline-offset: 3px;
                }

                /* CARD META TOP */

                .mines-card-meta-top {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;

                    padding-bottom: 12px;

                    border-bottom: 1px solid rgba(17,20,22,.06);
                }

                .mines-card-status {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;

                    font-family: "DM Mono", monospace;
                    font-size: 9.5px;
                    font-weight: 700;
                    letter-spacing: .10em;
                    color: #2b7a4b;
                }

                .status-dot-pulse {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: #2b7a4b;
                    box-shadow: 0 0 0 2px rgba(43,122,75,.2);
                }

                .mines-card-id-wrapper {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }

                .mines-card-id {
                    font-family: "DM Mono", monospace;
                    font-size: 10px;
                    font-weight: 600;
                    letter-spacing: .04em;
                    color: var(--steel);
                    background: rgba(17,20,22,.04);
                    padding: 3px 6px;
                    border-radius: 2px;
                }

                /* IDENTITY */

                .mines-card-identity {
                    margin-top: 14px;
                }

                .mines-card-operator {
                    font-family: "DM Mono", monospace;
                    font-size: 11px;
                    font-weight: 800;
                    letter-spacing: .14em;
                    color: var(--copper);
                    margin-bottom: 4px;
                }

                .mines-card-name {
                    margin: 0 0 6px 0;
                    font-family: "DM Sans", sans-serif;
                    font-size: 21px;
                    font-weight: 700;
                    line-height: 1.25;
                    color: var(--charcoal);
                    letter-spacing: -.02em;
                }

                .mines-card-location {
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    font-family: "DM Sans", sans-serif;
                    font-size: 12px;
                    color: var(--steel);
                }

                /* TAGS */

                .mines-card-tags {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                    margin-top: 14px;
                }

                .mines-card-tag {
                    font-family: "DM Mono", monospace;
                    font-size: 9px;
                    font-weight: 600;
                    letter-spacing: .05em;
                    text-transform: uppercase;
                    padding: 4px 7px;
                    background: #f8f6f0;
                    border: 1px solid rgba(17,20,22,.08);
                    color: #555f66;
                    border-radius: 2px;
                }

                /* DIVIDER */

                .mines-card-divider {
                    height: 1px;
                    background: rgba(17,20,22,.08);
                    margin: 16px 0 14px;
                }

                /* OPERATING PROFILE */

                .mines-card-profile {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 8px;
                }

                .profile-cell {
                    min-width: 0;
                    padding-right: 4px;
                    border-right: 1px solid rgba(17,20,22,.06);
                }

                .profile-cell:last-child {
                    border-right: none;
                    padding-right: 0;
                }

                .profile-label {
                    display: block;
                    font-family: "DM Mono", monospace;
                    font-size: 7.5px;
                    font-weight: 700;
                    letter-spacing: .08em;
                    color: #79838a;
                    line-height: 1.25;
                    margin-bottom: 4px;
                }

                .profile-value {
                    display: block;
                    font-family: "DM Mono", monospace;
                    font-size: 11px;
                    font-weight: 700;
                    color: var(--charcoal);
                    line-height: 1.2;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                /* FOOTER CTA */

                .mines-card-footer {
                    margin-top: 18px;
                }

                .mines-view-button {
                    width: 100%;
                    height: 38px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 0 12px;
                    border: 1px solid #c2bbb0;
                    border-radius: 3px;
                    background: transparent;
                    color: var(--charcoal);
                    font-family: "DM Mono", monospace;
                    font-size: 9.5px;
                    font-weight: 700;
                    letter-spacing: .09em;
                    cursor: pointer;
                    transition: all .15s ease;
                }

                .mines-card:hover .mines-view-button {
                    border-color: var(--copper);
                    background: #fbf7ef;
                    color: var(--copper);
                }

                /* EYEBROW CLUSTER & DEMO BADGE */

                .mines-eyebrow-cluster {
                    display: flex;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 12px;
                    margin-bottom: 6px;
                }

                .mines-demo-indicator {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    font-family: "DM Mono", monospace;
                    font-size: 8.5px;
                    font-weight: 700;
                    letter-spacing: .08em;
                    color: var(--steel);
                    background: rgba(104,114,119,.10);
                    padding: 3px 8px;
                    border-radius: 2px;
                    border: 1px solid rgba(104,114,119,.20);
                }

                .mines-demo-dot {
                    width: 5px;
                    height: 5px;
                    border-radius: 50%;
                    background: var(--copper);
                }

                @media(max-width:1100px) {

                    .mines-grid {
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }

                    .mines-summary {
                        grid-template-columns:
                            repeat(2,1fr);
                    }
                }

                @media(max-width:700px) {

                    .mines-page {
                        padding: 20px 14px 30px;
                    }

                    .mines-grid {
                        grid-template-columns: 1fr;
                    }

                    .mines-card-profile {
                        grid-template-columns: repeat(2, 1fr);
                        gap: 12px 8px;
                    }

                    .profile-cell:nth-child(2) {
                        border-right: none;
                    }

                    .mines-header {
                        flex-direction: column;
                        align-items: stretch;
                    }

                    .mines-toolbar {
                        width: 100%;
                    }

                    .mines-search {
                        flex: 1;
                    }

                    .mines-summary {
                        grid-template-columns: 1fr 1fr;
                    }
                }

            `}</style>

            <div className="mines-shell">

                {/* HEADER */}

                <section className="mines-header">

                    <div>

                        <div className="mines-eyebrow-cluster">
                            <span className="mines-eyebrow">
                                PROJECT PRITHVI / MINE PORTFOLIO
                            </span>
                            <span className="mines-demo-indicator">
                                <span className="mines-demo-dot" />
                                DEMONSTRATION ENVIRONMENT · SYNTHETIC MINE DATA
                            </span>
                        </div>

                        <h1>
                            Mine Portfolio Overview
                        </h1>

                        <p>
                            Select a mine to access its operational,
                            compliance, inspection and intelligence
                            workspace.
                        </p>

                    </div>

                    <div className="mines-toolbar">

                        <label className="mines-search">
                            <Search size={15} />

                            <input
                                value={query}
                                onChange={(event) =>
                                    setQuery(event.target.value)
                                }
                                placeholder="Search mines..."
                            />
                        </label>

                        <button
                            className="mines-refresh"
                            onClick={() => void load(true)}
                            disabled={
                                loading ||
                                refreshing
                            }
                        >
                            <RefreshCw size={13} />

                            {refreshing
                                ? "REFRESHING"
                                : "REFRESH"}
                        </button>

                    </div>

                </section>

                {/* SUMMARY */}

                <section className="mines-summary">

                    <div className="mines-summary-card">

                        <div className="mines-summary-label">
                            <Factory size={13} />
                            REGISTERED MINES
                        </div>

                        <strong className="mines-summary-value">
                            {String(mines.length).padStart(2, "0")}

                            <span className="mines-summary-note">
                                ACTIVE ASSETS
                            </span>
                        </strong>

                    </div>

                    <div className="mines-summary-card">

                        <div className="mines-summary-label">
                            <CheckCircle2 size={13} />
                            OPERATIONAL
                        </div>

                        <strong className="mines-summary-value">
                            {String(
                                mines.filter(
                                    (mine) =>
                                        mine.active !== false
                                ).length
                            ).padStart(2, "0")}

                            <span className="mines-summary-note">
                                CURRENTLY ACTIVE
                            </span>
                        </strong>

                    </div>

                    <div className="mines-summary-card">

                        <div className="mines-summary-label">
                            <Truck size={13} />
                            MINE PROFILE
                        </div>

                        <strong className="mines-summary-value">
                            {undergroundCount}

                            <span className="mines-summary-note">
                                UNDERGROUND
                            </span>
                        </strong>

                    </div>

                    <div className="mines-summary-card">

                        <div className="mines-summary-label">
                            <ShieldCheck size={13} />
                            OPERATING PROFILE
                        </div>

                        <strong className="mines-summary-value">
                            {opencastCount}

                            <span className="mines-summary-note">
                                OPENCAST
                            </span>
                        </strong>

                    </div>

                </section>

                {/* MINE SECTION */}

                <div className="mines-section-head">

                    <strong>
                        ACTIVE MINE ASSETS
                    </strong>

                    <span>
                        {filteredMines.length} OF {mines.length}
                    </span>

                </div>

                {loading ? (

                    <div className="mines-state">
                        Loading mine portfolio...
                    </div>

                ) : error ? (

                    <div className="mines-state">
                        <strong>
                            MINE PORTFOLIO LOAD FAILED
                        </strong>

                        <div>
                            {error}
                        </div>
                    </div>

                ) : filteredMines.length === 0 ? (

                    <div className="mines-state">
                        No matching mine assets found.
                    </div>

                ) : (

                    <div className="mines-grid">

                        {filteredMines.map((mine) => (
                            <MineCard
                                key={mine.mine_id}
                                mine={mine}
                            />
                        ))}

                    </div>
                )}

                {/* MEMBER 1 INTEGRATION POINT */}

                <div className="mines-integration">

                    <Activity size={15} />

                    <span>
                        <strong>
                            LIVE INTELLIGENCE INTEGRATION:
                        </strong>{" "}
                        select a mine to enter its intelligence
                        workspace. Live sensor telemetry, safety
                        feeds and operational data will be integrated
                        into the mine detail view.
                    </span>

                </div>

            </div>
        </div>
    );
}