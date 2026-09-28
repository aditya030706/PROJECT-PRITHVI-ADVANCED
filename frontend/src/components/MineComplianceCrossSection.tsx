import { useState } from "react";
import {
    Wind,
    Cable,
    Zap,
    Truck,
    Flame,
    Shield,
    Droplets,
    CheckCircle2,
    AlertTriangle,
    AlertOctagon,
    Info,
} from "lucide-react";
import type { CategoryComplianceSummary } from "../api/compliance";

interface MineComplianceCrossSectionProps {
    categories: CategoryComplianceSummary[];
    selectedCategory: string | null;
    onSelectCategory: (category: string | null) => void;
}

type DomainPin = {
    categoryKey: string;
    title: string;
    sublabel: string;
    depth: string;
    xPercent: number;
    yPercent: number;
    icon: React.ComponentType<{ size?: number; className?: string; color?: string }>;
};

const DOMAIN_PINS: DomainPin[] = [
    {
        categoryKey: "Shaft & Winding",
        title: "Shaft & Winding",
        sublabel: "Headframe, Winder Engine & Cages (CMR 75-80)",
        depth: "0m – 450m",
        xPercent: 24,
        yPercent: 18,
        icon: Cable,
    },
    {
        categoryKey: "HEMM",
        title: "HEMM Fleet & Mobility",
        sublabel: "Heavy Earthmoving Machinery & Drills (CMR 135)",
        depth: "Surface Depot",
        xPercent: 82,
        yPercent: 14,
        icon: Truck,
    },
    {
        categoryKey: "Ventilation & Gas",
        title: "Ventilation & Gas",
        sublabel: "Main Exhaust Fan & Return Airway (CMR 119, 156)",
        depth: "-300m Fan Drift",
        xPercent: 52,
        yPercent: 32,
        icon: Wind,
    },
    {
        categoryKey: "Electrical",
        title: "Electrical Infrastructure",
        sublabel: "Flameproof Switchgear & Substation (CMR 160-170)",
        depth: "-250m Station",
        xPercent: 70,
        yPercent: 44,
        icon: Zap,
    },
    {
        categoryKey: "Roof / Strata",
        title: "Roof & Strata (SCAMP)",
        sublabel: "Support System & Tell-Tale Monitoring (CMR 85-95)",
        depth: "-420m Working Horizon",
        xPercent: 32,
        yPercent: 62,
        icon: Shield,
    },
    {
        categoryKey: "Blasting",
        title: "Blasting & Explosives",
        sublabel: "Face Danger Zone & Magazine Clearing (CMR 155-158)",
        depth: "-520m Working Face",
        xPercent: 78,
        yPercent: 72,
        icon: Flame,
    },
    {
        categoryKey: "Water / Drainage",
        title: "Water & Pumping Station",
        sublabel: "Main Underground Sump & High-Head Pumps (CMR 145)",
        depth: "-580m Deep Basin",
        xPercent: 42,
        yPercent: 88,
        icon: Droplets,
    },
];

export default function MineComplianceCrossSection({
    categories,
    selectedCategory,
    onSelectCategory,
}: MineComplianceCrossSectionProps) {
    const [hoveredDomain, setHoveredDomain] = useState<string | null>(null);

    // Map categories by name for quick lookup
    const catMap = new Map<string, CategoryComplianceSummary>();
    categories.forEach((c) => catMap.set(c.category.toLowerCase().trim(), c));

    function getDomainSummary(domainKey: string) {
        return (
            catMap.get(domainKey.toLowerCase().trim()) ||
            categories.find((c) =>
                c.category.toLowerCase().includes(domainKey.toLowerCase().split(" ")[0])
            )
        );
    }

    function getStatusBadge(status?: string) {
        if (status === "CRITICAL_NON_COMPLIANCE") {
            return {
                label: "CRITICAL",
                tone: "critical",
                icon: AlertOctagon,
                color: "#ef4444",
                bg: "rgba(239, 68, 68, 0.15)",
                border: "rgba(239, 68, 68, 0.4)",
            };
        }
        if (status === "ACTION_REQUIRED") {
            return {
                label: "ATTENTION",
                tone: "attention",
                icon: AlertTriangle,
                color: "#f59e0b",
                bg: "rgba(245, 158, 11, 0.15)",
                border: "rgba(245, 158, 11, 0.4)",
            };
        }
        return {
            label: "COMPLIANT",
            tone: "compliant",
            icon: CheckCircle2,
            color: "#10b981",
            bg: "rgba(16, 185, 129, 0.15)",
            border: "rgba(16, 185, 129, 0.4)",
        };
    }

    return (
        <div className="mine-vis-container">
            <style>{`
                .mine-vis-container {
                    position: relative;
                    background: #08080a;
                    border: 1px solid #202026;
                    border-radius: 4px;
                    overflow: hidden;
                    box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.9);
                }

                .mine-vis-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 20px;
                    border-bottom: 1px solid #1c1c22;
                    background: #0c0c0f;
                    backdrop-filter: blur(8px);
                }

                .mine-vis-title {
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 0.08em;
                    color: #ededed;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .mine-vis-badge {
                    font-family: "DM Mono", monospace;
                    font-size: 9px;
                    font-weight: 600;
                    padding: 3px 8px;
                    background: rgba(208, 145, 95, 0.12);
                    color: #d0915f;
                    border: 1px solid rgba(208, 145, 95, 0.25);
                    border-radius: 2px;
                }

                .mine-vis-canvas-wrapper {
                    position: relative;
                    width: 100%;
                    min-height: 480px;
                    height: 520px;
                    user-select: none;
                }

                .mine-svg-canvas {
                    width: 100%;
                    height: 100%;
                    display: block;
                }

                /* Stratigraphic depth lines */
                .depth-marker {
                    font-family: "DM Mono", monospace;
                    font-size: 10px;
                    fill: #71717a;
                    font-weight: 500;
                }

                .depth-line {
                    stroke: #1c1c22;
                    stroke-dasharray: 3 4;
                    stroke-width: 1;
                }

                /* Domain Pin Interactive Overlay */
                .domain-pin {
                    position: absolute;
                    transform: translate(-50%, -50%);
                    cursor: pointer;
                    z-index: 10;
                    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
                }

                .domain-pin-inner {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 6px 12px;
                    border-radius: 20px;
                    backdrop-filter: blur(12px);
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.8);
                    transition: all 0.2s ease;
                }

                .domain-pin:hover {
                    transform: translate(-50%, -52%) scale(1.05);
                    z-index: 25;
                }

                .domain-pin.active .domain-pin-inner {
                    box-shadow: 0 0 20px rgba(208, 145, 95, 0.5);
                    border-width: 1.5px;
                }

                .pin-pulse {
                    position: absolute;
                    inset: -4px;
                    border-radius: 24px;
                    opacity: 0;
                    pointer-events: none;
                }

                .domain-pin.critical .pin-pulse {
                    border: 2px solid #ef4444;
                    animation: pinPulse 2s infinite ease-out;
                    opacity: 0.8;
                }

                .domain-pin.attention .pin-pulse {
                    border: 2px solid #f59e0b;
                    animation: pinPulse 2.5s infinite ease-out;
                    opacity: 0.7;
                }

                @keyframes pinPulse {
                    0% { transform: scale(0.95); opacity: 0.8; }
                    100% { transform: scale(1.3); opacity: 0; }
                }

                .pin-name {
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.04em;
                    color: #f4f4f5;
                    white-space: nowrap;
                }

                .pin-status-pill {
                    font-family: "DM Mono", monospace;
                    font-size: 8px;
                    font-weight: 700;
                    padding: 1px 6px;
                    border-radius: 10px;
                    letter-spacing: 0.05em;
                }

                /* Domain Detail Card Hover/Selected */
                .domain-popover {
                    position: absolute;
                    bottom: 16px;
                    left: 20px;
                    right: 20px;
                    background: rgba(11, 11, 14, 0.97);
                    border: 1px solid #282830;
                    border-radius: 4px;
                    padding: 14px 18px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 16px;
                    backdrop-filter: blur(16px);
                    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.9);
                    z-index: 30;
                    animation: fadeIn 0.2s ease-out;
                }

                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(6px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                .popover-meta {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .popover-icon {
                    width: 38px;
                    height: 38px;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #141418;
                    border: 1px solid #24242c;
                    color: #e2e8f0;
                }

                .popover-text h4 {
                    margin: 0;
                    font-size: 13px;
                    font-weight: 700;
                    color: #f4f4f5;
                }

                .popover-text p {
                    margin: 3px 0 0;
                    font-size: 11px;
                    color: #a1a1aa;
                }

                .popover-stats {
                    display: flex;
                    gap: 16px;
                }

                .popover-stat-item {
                    text-align: right;
                }

                .popover-stat-label {
                    font-size: 9px;
                    font-family: "DM Mono", monospace;
                    color: #71717a;
                    letter-spacing: 0.05em;
                }

                .popover-stat-val {
                    font-size: 14px;
                    font-weight: 700;
                    color: #ffffff;
                    margin-top: 2px;
                }

                .mine-vis-legend {
                    display: flex;
                    gap: 16px;
                    align-items: center;
                    padding: 10px 20px;
                    background: #08080a;
                    border-top: 1px solid #1c1c22;
                    font-size: 10px;
                    color: #71717a;
                }

                .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }

                .legend-dot {
                    width: 7px;
                    height: 7px;
                    border-radius: 50%;
                }
            `}</style>

            <div className="mine-vis-header">
                <div className="mine-vis-title">
                    <Info size={14} color="#d0915f" />
                    <span>JHARIA UNDERGROUND COMPLIANCE STRATIGRAPHY & SECTOR ARCHITECTURE</span>
                </div>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <span className="mine-vis-badge">DEGREE II GASSY</span>
                    <span className="mine-vis-badge">DEPTH: 300m – 600m</span>
                    <span className="mine-vis-badge">SEAM XIV & XI</span>
                </div>
            </div>

            <div className="mine-vis-canvas-wrapper">
                <svg
                    className="mine-svg-canvas"
                    viewBox="0 0 1000 520"
                    preserveAspectRatio="none"
                >
                    <defs>
                        {/* Strata Gradients — Neutral Charcoal & Coal */}
                        <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#08080a" />
                            <stop offset="100%" stopColor="#101014" />
                        </linearGradient>
                        <linearGradient id="overburdenGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#141418" />
                            <stop offset="100%" stopColor="#0e0e11" />
                        </linearGradient>
                        <linearGradient id="seamGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#050507" />
                            <stop offset="100%" stopColor="#020203" />
                        </linearGradient>
                        <linearGradient id="shaftGlow" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="rgba(208, 145, 95, 0.03)" />
                            <stop offset="50%" stopColor="rgba(208, 145, 95, 0.10)" />
                            <stop offset="100%" stopColor="rgba(208, 145, 95, 0.03)" />
                        </linearGradient>
                    </defs>

                    {/* Stratigraphic layers */}
                    {/* Sky / Surface Boundary at Y=100 */}
                    <rect x="0" y="0" width="1000" height="100" fill="url(#skyGrad)" />
                    {/* Surface Line */}
                    <path
                        d="M 0,100 Q 250,96 500,100 T 1000,97"
                        stroke="#26262b"
                        strokeWidth="2"
                        fill="none"
                    />

                    {/* Overburden strata (0m to -250m) */}
                    <rect x="0" y="100" width="1000" height="150" fill="url(#overburdenGrad)" />
                    <line x1="0" y1="250" x2="1000" y2="250" className="depth-line" />
                    <text x="16" y="244" className="depth-marker">-250m (Overburden Sandstone)</text>

                    {/* Upper Coal Seam XIV (-250m to -350m) */}
                    <rect x="0" y="250" width="1000" height="100" fill="url(#seamGrad)" opacity="0.9" />
                    <line x1="0" y1="350" x2="1000" y2="350" className="depth-line" />
                    <text x="16" y="344" className="depth-marker">-350m (Seam XIV Horizon)</text>

                    {/* Interburden rock (-350m to -450m) */}
                    <rect x="0" y="350" width="1000" height="100" fill="url(#overburdenGrad)" opacity="0.95" />
                    <line x1="0" y1="450" x2="1000" y2="450" className="depth-line" />
                    <text x="16" y="444" className="depth-marker">-450m (Shale / Sandstone)</text>

                    {/* Deep Main Coal Seam XI (-450m to -520m) */}
                    <rect x="0" y="450" width="1000" height="70" fill="url(#seamGrad)" />
                    <text x="16" y="504" className="depth-marker">-520m (Main Thick Seam XI)</text>

                    {/* Deepest Incline / Sump floor at -580m (visual base) */}
                    <path
                        d="M 300,450 L 500,515 L 750,450"
                        stroke="rgba(16, 185, 129, 0.25)"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                        fill="rgba(16, 185, 129, 0.03)"
                    />

                    {/* Central Vertical Winding Shaft (Left: X=240, width=44) */}
                    <rect x="220" y="40" width="40" height="420" fill="url(#shaftGlow)" />
                    <line x1="220" y1="40" x2="220" y2="460" stroke="#2a2a30" strokeWidth="1.5" />
                    <line x1="260" y1="40" x2="260" y2="460" stroke="#2a2a30" strokeWidth="1.5" />
                    {/* Winding guide cables */}
                    <line x1="233" y1="40" x2="233" y2="460" stroke="#3a3a42" strokeWidth="0.8" strokeDasharray="6 2" />
                    <line x1="247" y1="40" x2="247" y2="460" stroke="#3a3a42" strokeWidth="0.8" strokeDasharray="6 2" />

                    {/* Surface Headframe Structure */}
                    <polygon points="210,100 240,30 270,100" fill="none" stroke="#4a4a54" strokeWidth="2" />
                    <circle cx="240" cy="30" r="10" fill="none" stroke="#d0915f" strokeWidth="2" />
                    <line x1="240" y1="30" x2="240" y2="100" stroke="#71717a" strokeWidth="1.5" />

                    {/* Ventilation Fan & Upcast Shaft (Right: X=520, width=36) */}
                    <rect x="502" y="55" width="36" height="320" fill="rgba(16, 185, 129, 0.03)" />
                    <line x1="502" y1="55" x2="502" y2="375" stroke="#26262c" strokeWidth="1.5" />
                    <line x1="538" y1="55" x2="538" y2="375" stroke="#26262c" strokeWidth="1.5" />
                    {/* Surface Fan Evasee */}
                    <polygon points="492,55 502,98 538,98 548,55" fill="rgba(16, 185, 129, 0.12)" stroke="#10b981" strokeWidth="1.5" />

                    {/* Underground Gallery Networks / Roadways in Seam XIV */}
                    <rect x="120" y="275" width="800" height="22" fill="#040406" stroke="#1c1c22" strokeWidth="1" />
                    {/* Cross-cuts & Air crossings */}
                    <rect x="360" y="250" width="18" height="70" fill="#040406" stroke="#1c1c22" />
                    <rect x="680" y="250" width="18" height="70" fill="#040406" stroke="#1c1c22" />

                    {/* Deep Working Face Galleries in Seam XI */}
                    <rect x="180" y="465" width="760" height="26" fill="#020203" stroke="#222228" strokeWidth="1" />
                    {/* Incline tunnel connecting Seams */}
                    <path
                        d="M 260,297 L 350,465"
                        stroke="#2a2a30"
                        strokeWidth="14"
                        fill="none"
                        strokeLinecap="round"
                    />
                    <path
                        d="M 260,297 L 350,465"
                        stroke="#040406"
                        strokeWidth="10"
                        fill="none"
                        strokeLinecap="round"
                    />

                    {/* Air Flow Direction Arrows */}
                    {/* Intake fresh air down Shaft */}
                    <path d="M 230,120 L 230,140 M 227,135 L 230,140 L 233,135" stroke="#d4d4d8" strokeWidth="2" strokeLinecap="round" />
                    <path d="M 230,220 L 230,240 M 227,235 L 230,240 L 233,235" stroke="#d4d4d8" strokeWidth="2" strokeLinecap="round" />
                    {/* Return air up ventilation shaft */}
                    <path d="M 520,240 L 520,220 M 517,225 L 520,220 L 523,225" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
                    <path d="M 520,140 L 520,120 M 517,125 L 520,120 L 523,125" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
                </svg>

                {/* 7 Category Domain Pins */}
                {DOMAIN_PINS.map((pin) => {
                    const sum = getDomainSummary(pin.categoryKey);
                    const statusMeta = getStatusBadge(sum?.compliance_status);
                    const isSelected = selectedCategory === pin.categoryKey;
                    const PinIcon = pin.icon;

                    return (
                        <div
                            key={pin.categoryKey}
                            className={`domain-pin ${statusMeta.tone} ${isSelected ? "active" : ""}`}
                            style={{
                                left: `${pin.xPercent}%`,
                                top: `${pin.yPercent}%`,
                            }}
                            onClick={() => {
                                onSelectCategory(isSelected ? null : pin.categoryKey);
                            }}
                            onMouseEnter={() => setHoveredDomain(pin.categoryKey)}
                            onMouseLeave={() => setHoveredDomain(null)}
                            title={`Click to filter ${pin.title}`}
                        >
                            <div className="pin-pulse" />
                            <div
                                className="domain-pin-inner"
                                style={{
                                    background: isSelected
                                        ? "rgba(26, 36, 48, 0.95)"
                                        : "rgba(15, 23, 32, 0.85)",
                                    borderColor: isSelected ? "#d0915f" : statusMeta.border,
                                    borderWidth: "1px",
                                    borderStyle: "solid",
                                }}
                            >
                                <div
                                    style={{
                                        color: statusMeta.color,
                                        display: "flex",
                                        alignItems: "center",
                                    }}
                                >
                                    <PinIcon size={14} />
                                </div>
                                <span className="pin-name">{pin.title}</span>
                                <span
                                    className="pin-status-pill"
                                    style={{
                                        color: statusMeta.color,
                                        background: statusMeta.bg,
                                    }}
                                >
                                    {statusMeta.label}
                                </span>
                            </div>
                        </div>
                    );
                })}

                {/* Popover / Inspector Strip on Pin Hover or Selection */}
                {(hoveredDomain || selectedCategory) && (() => {
                    const activeKey = hoveredDomain || selectedCategory;
                    const pin = DOMAIN_PINS.find((p) => p.categoryKey === activeKey);
                    if (!pin) return null;
                    const sum = getDomainSummary(pin.categoryKey);
                    const statusMeta = getStatusBadge(sum?.compliance_status);
                    const PinIcon = pin.icon;

                    return (
                        <div className="domain-popover">
                            <div className="popover-meta">
                                <div className="popover-icon" style={{ borderColor: statusMeta.border }}>
                                    <PinIcon size={18} color={statusMeta.color} />
                                </div>
                                <div className="popover-text">
                                    <h4>
                                        {pin.title} · <span style={{ color: statusMeta.color }}>{statusMeta.label}</span>
                                    </h4>
                                    <p>{pin.sublabel} — Depth: {pin.depth}</p>
                                </div>
                            </div>

                            <div className="popover-stats">
                                <div className="popover-stat-item">
                                    <div className="popover-stat-label">SCHEDULES</div>
                                    <div className="popover-stat-val">{sum?.total_schedules ?? 0} active</div>
                                </div>
                                <div className="popover-stat-item">
                                    <div className="popover-stat-label">SUBMITTED</div>
                                    <div className="popover-stat-val">{sum?.submitted_count ?? 0}</div>
                                </div>
                                <div className="popover-stat-item">
                                    <div className="popover-stat-label">REVIEW REQ</div>
                                    <div className="popover-stat-val" style={{ color: (sum?.review_required_count ?? 0) > 0 ? "#f59e0b" : "#94a3b8" }}>
                                        {sum?.review_required_count ?? 0}
                                    </div>
                                </div>
                                <div className="popover-stat-item">
                                    <div className="popover-stat-label">VIOLATIONS</div>
                                    <div className="popover-stat-val" style={{ color: (sum?.threshold_violations_count ?? 0) > 0 ? "#ef4444" : "#10b981" }}>
                                        {sum?.threshold_violations_count ?? 0}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })()}
            </div>

            <div className="mine-vis-legend">
                <span style={{ fontWeight: 600, color: "#94a3b8" }}>STATUS INTEGRITY:</span>
                <div className="legend-item">
                    <span className="legend-dot" style={{ background: "#10b981" }} />
                    <span>COMPLIANT (All measurements within thresholds)</span>
                </div>
                <div className="legend-item">
                    <span className="legend-dot" style={{ background: "#f59e0b" }} />
                    <span>ATTENTION REQUIRED (Due today or review pending)</span>
                </div>
                <div className="legend-item">
                    <span className="legend-dot" style={{ background: "#ef4444" }} />
                    <span>CRITICAL (Statutory threshold breach)</span>
                </div>
                <span style={{ marginLeft: "auto", color: "#64748b" }}>
                    Click any sector badge to filter inspection obligations
                </span>
            </div>
        </div>
    );
}
