import {
    Scale,
    Calendar,
    ClipboardCheck,
    Camera,
    AlertTriangle,
    ShieldCheck,
    Gavel,
    ChevronRight,
} from "lucide-react";

type PipelineStep = {
    step: string;
    label: string;
    sub: string;
    regulation: string;
    icon: React.ComponentType<{ size?: number; className?: string }>;
};

const PIPELINE_STEPS: PipelineStep[] = [
    {
        step: "01",
        label: "REGULATORY OBLIGATIONS",
        sub: "Statutory mandates mapped by mine profile",
        regulation: "CMR 2017",
        icon: Scale,
    },
    {
        step: "02",
        label: "SCHEDULE",
        sub: "Periodic statutory inspection cadences",
        regulation: "Daily / Weekly / Monthly",
        icon: Calendar,
    },
    {
        step: "03",
        label: "INSPECTION",
        sub: "Designated Overman/Engineer field execution",
        regulation: "Role-Gated",
        icon: ClipboardCheck,
    },
    {
        step: "04",
        label: "EVIDENCE",
        sub: "Calibrated readings & geo-referenced photos",
        regulation: "Measurements",
        icon: Camera,
    },
    {
        step: "05",
        label: "FINDINGS",
        sub: "Threshold breaches & defect declarations",
        regulation: "Statutory Limits",
        icon: AlertTriangle,
    },
    {
        step: "06",
        label: "VERIFICATION",
        sub: "Multi-signal AI integrity & statutory checks",
        regulation: "Autonomous Rules",
        icon: ShieldCheck,
    },
    {
        step: "07",
        label: "ACTION",
        sub: "Mine Manager & DGMS audit remediation",
        regulation: "Statutory Order",
        icon: Gavel,
    },
];

export default function CompliancePipelineDiagram() {
    return (
        <div className="pipeline-container">
            <style>{`
                .pipeline-container {
                    background: #08080a;
                    border: 1px solid #1f1f25;
                    border-radius: 4px;
                    padding: 18px 22px;
                    margin-bottom: 24px;
                }

                .pipeline-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }

                .pipeline-title {
                    font-size: 11px;
                    font-weight: 800;
                    letter-spacing: 0.12em;
                    color: #8c8c96;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .pipeline-track {
                    display: grid;
                    grid-template-columns: repeat(7, 1fr);
                    gap: 8px;
                    position: relative;
                }

                .pipeline-step {
                    background: #0d0d10;
                    border: 1px solid #1c1c22;
                    border-radius: 3px;
                    padding: 12px 10px;
                    position: relative;
                    transition: all 0.2s ease;
                }

                .pipeline-step:hover {
                    background: #121216;
                    border-color: rgba(208, 145, 95, 0.4);
                    transform: translateY(-2px);
                }

                .pipeline-step-top {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }

                .pipeline-step-num {
                    font-family: "DM Mono", monospace;
                    font-size: 10px;
                    font-weight: 700;
                    color: #d0915f;
                }

                .pipeline-step-icon {
                    color: #71717a;
                }

                .pipeline-step-label {
                    font-size: 10px;
                    font-weight: 800;
                    letter-spacing: 0.04em;
                    color: #ededed;
                    margin-bottom: 4px;
                    line-height: 1.3;
                    min-height: 26px;
                }

                .pipeline-step-sub {
                    font-size: 9px;
                    color: #8c8c96;
                    line-height: 1.35;
                    margin-bottom: 8px;
                    min-height: 24px;
                }

                .pipeline-step-badge {
                    font-family: "DM Mono", monospace;
                    font-size: 8px;
                    font-weight: 600;
                    padding: 2px 5px;
                    background: #141418;
                    color: #a1a1aa;
                    border: 1px solid #27272e;
                    border-radius: 2px;
                    display: inline-block;
                }

                .pipeline-connector {
                    position: absolute;
                    right: -10px;
                    top: 50%;
                    transform: translateY(-50%);
                    color: #3f3f46;
                    z-index: 2;
                    pointer-events: none;
                }

                @media (max-width: 1024px) {
                    .pipeline-track {
                        grid-template-columns: repeat(4, 1fr);
                    }
                    .pipeline-connector { display: none; }
                }

                @media (max-width: 640px) {
                    .pipeline-track {
                        grid-template-columns: 1fr;
                    }
                }
            `}</style>

            <div className="pipeline-header">
                <div className="pipeline-title">
                    <span>PRITHVI REGULATORY ASSURANCE ARCHITECTURE</span>
                    <span style={{ color: "#d0915f" }}>— END-TO-END STATUTORY PIPELINE</span>
                </div>
                <div style={{ fontSize: "10px", color: "#71717a", fontFamily: "DM Mono, monospace" }}>
                    ZERO-FABRICATION PROTOCOL
                </div>
            </div>

            <div className="pipeline-track">
                {PIPELINE_STEPS.map((step, idx) => {
                    const StepIcon = step.icon;
                    return (
                        <div key={step.step} className="pipeline-step">
                            <div className="pipeline-step-top">
                                <span className="pipeline-step-num">{step.step}</span>
                                <div className="pipeline-step-icon">
                                    <StepIcon size={14} />
                                </div>
                            </div>
                            <div className="pipeline-step-label">{step.label}</div>
                            <div className="pipeline-step-sub">{step.sub}</div>
                            <div className="pipeline-step-badge">{step.regulation}</div>
                            {idx < PIPELINE_STEPS.length - 1 && (
                                <div className="pipeline-connector">
                                    <ChevronRight size={14} />
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
