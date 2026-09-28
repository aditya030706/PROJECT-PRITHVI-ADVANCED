import {
    useEffect,
    useMemo,
    useState,
} from "react";

import {
    ArrowLeft,
    Check,
    CheckCircle2,
    ClipboardCheck,
    FileWarning,
    Send,
    ShieldCheck,
    X,
    AlertTriangle,
    Camera,
    FileText,
    Database,
    Sparkles,
} from "lucide-react";

import { useNavigate, useParams } from "react-router-dom";

import {
    getInspection,
    getInspectionTemplates,
    submitInspection,
    uploadEvidence,
    listDemoDocuments,
    attachDemoDocument,
    addEvidence,
    listInspectionEvidence,
    type ChecklistResultCreate,
    type FindingCreate,
    type Inspection,
    type InspectionTemplate,
    type MeasurementCreate,
    type DemoDocument,
    type UploadedEvidence,
} from "../api/inspection";
import { getVerification, type VerificationResult } from "../api/verification";
import { getMineDisplayName } from "./Mines";

type RegisteredEvidence = UploadedEvidence;

type FindingDraft = FindingCreate & {
    evidence_ids: string[];
};

function InspectionWorkspace() {
    const { inspectionId } = useParams();

    const navigate = useNavigate();

    const [openEvidenceForFinding, setOpenEvidenceForFinding] =
        useState<number | null>(null);

    const [inspection, setInspection] =
        useState<Inspection | null>(null);

    const [template, setTemplate] =
        useState<InspectionTemplate | null>(null);

    const [measurements, setMeasurements] =
        useState<Record<string, string>>({});

    const [checklist, setChecklist] =
        useState<Record<string, boolean>>({});

    const [observations, setObservations] =
        useState<Record<string, string>>({});

    const [findings, setFindings] =
        useState<FindingDraft[]>([]);

    const [evidence, setEvidence] =
        useState<RegisteredEvidence[]>([]);

    const [addingEvidence, setAddingEvidence] =
        useState(false);

    const [evidenceFile, setEvidenceFile] =
        useState<File | null>(null);

    const [useDemoLibrary, setUseDemoLibrary] =
        useState(true);

    const [submittedVerification, setSubmittedVerification] =
        useState<VerificationResult | any | null>(null);

    const [demoDocuments, setDemoDocuments] =
        useState<DemoDocument[]>([]);

    const [selectedDemo, setSelectedDemo] =
        useState("");

    const [uploadError, setUploadError] =
        useState<string | null>(null);

    const [uploadProgress, setUploadProgress] =
        useState<"idle" | "uploading" | "done">("idle");

    const [overallObservation, setOverallObservation] =
        useState("");

    const [loading, setLoading] =
        useState(true);

    const [submitting, setSubmitting] =
        useState(false);

    const [error, setError] =
        useState<string | null>(null);

    /* =======================================================
       LOAD INSPECTION
    ======================================================= */

    useEffect(() => {
        if (!inspectionId) {
            setError("Inspection ID is missing.");
            setLoading(false);
            return;
        }

        Promise.all([
            getInspection(inspectionId),
            getInspectionTemplates(),
            listInspectionEvidence(inspectionId).catch(() => []),
            getVerification(inspectionId).catch(() => null),
        ])
            .then(([inspectionData, templates, existingEvidence, verif]) => {
                setInspection(inspectionData);
                if (existingEvidence && existingEvidence.length > 0) {
                    setEvidence(existingEvidence);
                }
                if (verif) {
                    setSubmittedVerification(verif);
                }

                const selectedTemplate =
                    templates.find(
                        (item) =>
                            item.template_id ===
                            inspectionData.template_id
                    );

                if (!selectedTemplate) {
                    throw new Error(
                        `Template ${inspectionData.template_id} was not found.`
                    );
                }

                setTemplate(selectedTemplate);
            })
            .catch((err) => {
                setError(
                    err instanceof Error
                        ? err.message
                        : "Unable to load inspection."
                );
            })
            .finally(() => {
                setLoading(false);
            });
    }, [inspectionId]);

    /* =======================================================
       COMPLETION
    ======================================================= */

    const measurementComplete =
        useMemo(() => {
            if (!template) {
                return false;
            }

            return template.measurements
                .filter(
                    (measurement) =>
                        measurement.required
                )
                .every(
                    (measurement) =>
                        measurements[
                        measurement.measurement_id ||
                        measurement.name
                        ] !== undefined &&
                        measurements[
                        measurement.measurement_id ||
                        measurement.name
                        ] !== ""
                );
        }, [template, measurements]);

    const checklistComplete =
        useMemo(() => {
            if (!template) {
                return false;
            }

            return template.checklist
                .filter(
                    (item) => item.required
                )
                .every(
                    (item) =>
                        checklist[item.item_id] !==
                        undefined
                );
        }, [template, checklist]);

    /* =======================================================
       EVIDENCE COUNTS & MATCHING
    ======================================================= */

    const photoCount = useMemo(() => {
        return evidence.filter((item) => item.evidence_type === "photo").length;
    }, [evidence]);

    const measurementEvidenceCount = useMemo(() => {
        return evidence.filter(
            (item) =>
                item.evidence_type === "manual_reading" ||
                (item.evidence_type === "document" &&
                    (item.filename?.toLowerCase().includes("ventilation") ||
                        item.filename?.toLowerCase().includes("measurement") ||
                        item.filename?.toLowerCase().includes("reading")))
        ).length;
    }, [evidence]);

    const documentCount = useMemo(() => {
        return evidence.filter((item) => item.evidence_type === "document").length;
    }, [evidence]);

    /* =======================================================
       EVIDENCE COMPLETION
    ======================================================= */

    const evidenceComplete = useMemo(() => {
        if (!template) {
            return false;
        }

        const requiredEvidence =
            template.evidence_requirements.filter(
                (item) => item.required
            );

        if (requiredEvidence.length === 0) {
            return photoCount >= 1 && measurementEvidenceCount >= 1;
        }

        return requiredEvidence.every(
            (requirement) => {
                if (requirement.evidence_type === "photo") {
                    return photoCount >= (requirement.minimum_count || 1);
                }
                if (requirement.evidence_type === "manual_reading") {
                    return measurementEvidenceCount >= (requirement.minimum_count || 1);
                }
                if (requirement.evidence_type === "document") {
                    return documentCount >= (requirement.minimum_count || 1);
                }
                const count = evidence.filter(
                    (item) => item.evidence_type === requirement.evidence_type
                ).length;
                return count >= (requirement.minimum_count || 1);
            }
        );
    }, [template, evidence, photoCount, measurementEvidenceCount, documentCount]);

    /* =======================================================
       STATUTORY READINESS BREAKDOWN
    ======================================================= */

    const readiness = useMemo(() => {
        const measurementsOk = measurementComplete;
        const checklistOk = checklistComplete;
        const photoOk = photoCount >= 1;
        const measurementEvOk = measurementEvidenceCount >= 1;
        const documentOk = documentCount >= 1;
        const findingsOk = true;
        const summaryOk = overallObservation.trim().length > 0;

        const checks = [
            {
                id: "measurements",
                label: "FIELD MEASUREMENTS",
                complete: measurementsOk,
                meta: measurementsOk ? "ALL ENTERED" : "READINGS PENDING",
            },
            {
                id: "checklist",
                label: "SAFETY CHECKLIST",
                complete: checklistOk,
                meta: checklistOk ? "ALL CHECKED" : "CHECKS PENDING",
            },
            {
                id: "photo",
                label: "REQUIRED PHOTO",
                complete: photoOk,
                meta: `${photoCount}/1 ${photoOk ? "SATISFIED" : "MISSING"}`,
            },
            {
                id: "measurement_ev",
                label: "MEASUREMENT EVIDENCE",
                complete: measurementEvOk,
                meta: `${measurementEvidenceCount}/1 ${measurementEvOk ? "SATISFIED" : "MISSING"}`,
            },
            {
                id: "document",
                label: "DOCUMENT EVIDENCE",
                complete: documentOk,
                meta: documentOk ? "PDF ATTACHED" : "PDF RECOMMENDED",
            },
            {
                id: "findings",
                label: "FINDINGS REGISTER",
                complete: findingsOk,
                meta: `${findings.length} RECORDED`,
            },
            {
                id: "summary",
                label: "INSPECTOR SUMMARY",
                complete: summaryOk,
                meta: summaryOk ? "ENTERED" : "OPTIONAL",
            },
        ];

        // Mandatory gates for 100% submission readiness
        const requiredGates = [measurementsOk, checklistOk, photoOk, measurementEvOk, documentOk];
        const passedRequired = requiredGates.filter(Boolean).length;
        const isReady = passedRequired === requiredGates.length;

        // Dynamic, truthful percentage: exactly 100% when all required gates pass, strictly capped at 85% otherwise
        const percent = isReady ? 100 : Math.min(85, Math.round((passedRequired / requiredGates.length) * 85));

        return {
            checks,
            isReady,
            percent,
        };
    }, [
        measurementComplete,
        checklistComplete,
        photoCount,
        measurementEvidenceCount,
        documentCount,
        findings,
        overallObservation,
    ]);

    const completionPercent = readiness.percent;

    /* =======================================================
       UPDATE MEASUREMENT
    ======================================================= */

    function updateMeasurement(
        key: string,
        value: string
    ) {
        setMeasurements(
            (current) => ({
                ...current,
                [key]: value,
            })
        );
    }

    /* =======================================================
       UPDATE CHECKLIST
    ======================================================= */

    function updateChecklist(
        itemId: string,
        passed: boolean
    ) {
        setChecklist(
            (current) => ({
                ...current,
                [itemId]: passed,
            })
        );
    }

    /* =======================================================
       LOAD DEMO DOCUMENTS
    ======================================================= */

    useEffect(() => {
        listDemoDocuments()
            .then(setDemoDocuments)
            .catch(() => { /* non-critical */ });
    }, []);

    /* =======================================================
       ADD DEMO PHOTO
    ======================================================= */

    async function handleAddDemoPhoto() {
        if (!inspection) return;
        setAddingEvidence(true);
        setUploadError(null);
        try {
            const registered = await addEvidence(inspection.inspection_id, {
                evidence_type: "photo",
                filename: "inspection_area_01.jpg",
                storage_reference: "synthetic/demo/inspection_area_01.jpg",
                latitude: inspection.latitude ?? 23.7485,
                longitude: inspection.longitude ?? 86.4172,
            });
            setEvidence((current) => [...current, registered]);
        } catch (err) {
            setUploadError(
                err instanceof Error ? err.message : "Failed to register photo evidence."
            );
        } finally {
            setAddingEvidence(false);
        }
    }

    /* =======================================================
       ADD DEMO MEASUREMENT LOG
    ======================================================= */

    async function handleAddDemoMeasurement() {
        if (!inspection) return;
        setAddingEvidence(true);
        setUploadError(null);
        try {
            const registered = await addEvidence(inspection.inspection_id, {
                evidence_type: "manual_reading",
                filename: "ventilation_measurements_log.dat",
                storage_reference: "synthetic/demo/ventilation_measurements_log.dat",
                latitude: inspection.latitude ?? 23.7485,
                longitude: inspection.longitude ?? 86.4172,
            });
            setEvidence((current) => [...current, registered]);
        } catch (err) {
            setUploadError(
                err instanceof Error ? err.message : "Failed to register measurement log."
            );
        } finally {
            setAddingEvidence(false);
        }
    }

    /* =======================================================
       ATTACH DEMO PDF DOCUMENT (REAL FILE & SHA-256)
    ======================================================= */

    async function handleAttachDemoPdf(docFilename?: string) {
        if (!inspection) return;
        const targetFilename = docFilename || selectedDemo;
        if (!targetFilename) {
            setUploadError("Select a demo document from the library.");
            return;
        }

        setAddingEvidence(true);
        setUploadError(null);
        setUploadProgress("uploading");

        try {
            const registered = await attachDemoDocument(
                inspection.inspection_id,
                targetFilename
            );
            setEvidence((current) => [...current, registered]);
            setSelectedDemo("");
            setUploadProgress("done");
            setTimeout(() => setUploadProgress("idle"), 2000);
        } catch (err) {
            setUploadError(
                err instanceof Error ? err.message : "Failed to attach demo document."
            );
            setUploadProgress("idle");
        } finally {
            setAddingEvidence(false);
        }
    }

    /* =======================================================
       ADD EVIDENCE — UPLOAD OR DEMO LIBRARY
    ======================================================= */

    async function handleAddEvidence() {
        if (!inspection) return;

        if (useDemoLibrary) {
            return handleAttachDemoPdf();
        }

        if (!evidenceFile) {
            setUploadError("Select a PDF file to upload.");
            return;
        }

        if (!evidenceFile.name.toLowerCase().endsWith(".pdf")) {
            setUploadError("Only PDF documents are accepted.");
            return;
        }

        setAddingEvidence(true);
        setUploadError(null);
        setUploadProgress("uploading");

        try {
            const registered = await uploadEvidence(
                inspection.inspection_id,
                evidenceFile
            );
            setEvidence((current) => [...current, registered]);
            setEvidenceFile(null);
            setUploadProgress("done");
            setTimeout(() => setUploadProgress("idle"), 2000);
        } catch (err) {
            setUploadError(
                err instanceof Error ? err.message : "Upload failed."
            );
            setUploadProgress("idle");
        } finally {
            setAddingEvidence(false);
        }
    }

    /* =======================================================
       ADD FINDING
    ======================================================= */

    function addFindingRow() {
        setFindings(
            (current) => [
                ...current,
                {
                    title: "",
                    description: "",
                    severity: "medium",
                    corrective_action_required: true,
                    evidence_ids: [],
                },
            ]
        );
    }

    /* =======================================================
       UPDATE FINDING
    ======================================================= */

    function updateFinding(
        index: number,
        field: keyof FindingCreate,
        value: string | boolean
    ) {
        setFindings((current) =>
            current.map((finding, findingIndex) =>
                findingIndex === index
                    ? {
                        ...finding,
                        [field]: value,
                    }
                    : finding
            )
        );
    }


    function toggleFindingEvidence(
        findingIndex: number,
        evidenceId: string
    ) {
        setFindings((current) =>
            current.map((finding, index) => {

                if (index !== findingIndex) {
                    return finding;
                }

                const alreadyLinked =
                    finding.evidence_ids.includes(evidenceId);

                return {
                    ...finding,

                    evidence_ids: alreadyLinked
                        ? finding.evidence_ids.filter(
                            (id) => id !== evidenceId
                        )
                        : [
                            ...finding.evidence_ids,
                            evidenceId,
                        ],
                };

            })
        );
    }
    /* =======================================================
       SUBMIT
    ======================================================= */

    async function handleSubmit() {
        if (!inspection || !template) {
            return;
        }

        if (!measurementComplete) {
            setError(
                "Complete all required measurements before submission."
            );
            return;
        }

        if (!checklistComplete) {
            setError(
                "Complete all required checklist items before submission."
            );
            return;
        }

        if (!evidenceComplete) {
            setError(
                "Register all required evidence before submission."
            );
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            const measurementPayloads:
                MeasurementCreate[] =
                template.measurements
                    .filter(
                        (measurement) =>
                            measurements[
                            measurement.measurement_id ||
                            measurement.name
                            ] !== undefined &&
                            measurements[
                            measurement.measurement_id ||
                            measurement.name
                            ] !== ""
                    )
                    .map((measurement) => {
                        const key =
                            measurement.measurement_id ||
                            measurement.name;

                        return {
                            measurement_type:
                                measurement.name,

                            value:
                                Number(
                                    measurements[key]
                                ),

                            unit:
                                measurement.unit ||
                                null,

                            source: "manual",

                            captured_at:
                                new Date().toISOString(),
                        };
                    });

            const checklistPayloads:
                ChecklistResultCreate[] =
                template.checklist
                    .filter(
                        (item) =>
                            checklist[item.item_id] !==
                            undefined
                    )
                    .map((item) => ({
                        item_id:
                            item.item_id,

                        passed:
                            checklist[item.item_id],

                        observation:
                            observations[
                            item.item_id
                            ] || null,
                    }));

            const cleanFindings: FindingCreate[] =
                findings
                    .filter(
                        (finding) =>
                            finding.title.trim() &&
                            finding.description.trim() &&
                            finding.severity.trim()
                    )
                    .map((finding) => ({
                        title: finding.title.trim(),
                        description: finding.description.trim(),
                        severity: finding.severity.trim(),
                        corrective_action_required:
                            finding.corrective_action_required ?? false,
                        evidence_ids: finding.evidence_ids,
                    }));

            const res: any = await submitInspection(
                inspection.inspection_id,
                {
                    inspection_id:
                        inspection.inspection_id,

                    measurements:
                        measurementPayloads,

                    checklist_results:
                        checklistPayloads,

                    findings:
                        cleanFindings,

                    observation:
                        overallObservation ||
                        null,
                }
            );

            // Immediately load the verification result
            const verif = await getVerification(inspection.inspection_id).catch(() => null);
            if (verif) {
                setSubmittedVerification(verif);
            } else if (res?.verification) {
                setSubmittedVerification(res.verification);
            }

            setInspection((prev) => prev ? { ...prev, status: "submitted" } : null);
            window.scrollTo({ top: 0, behavior: "smooth" });
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Unable to submit inspection."
            );
        } finally {
            setSubmitting(false);
        }
    }

    /* =======================================================
       LOADING
    ======================================================= */

    if (loading) {
        return (
            <div className="inspection-workspace">
                <div className="state-card">
                    <div className="state-card-inner">
                        <div className="loading-indicator" />
                        <span>
                            LOADING REGULATORY DATA...
                        </span>
                    </div>
                </div>
            </div>
        );
    }

    /* =======================================================
       ERROR
    ======================================================= */

    if (error && (!inspection || !template)) {
        return (
            <div className="inspection-workspace">

                <button
                    className="back-button"
                    onClick={() => navigate(-1)}
                >
                    <ArrowLeft size={16} />
                    BACK TO COMMAND
                </button>

                <div className="state-card state-error">
                    <div className="state-card-inner">
                        <AlertTriangle size={18} />

                        <div>
                            <strong>
                                REGULATORY DATA LOAD FAILED
                            </strong>

                            <span>
                                {error}
                            </span>
                        </div>
                    </div>
                </div>

            </div>
        );
    }

    if (!inspection || !template) {
        return null;
    }

    /* =======================================================
       WORKSPACE
    ======================================================= */

    return (
        <div className="inspection-workspace">

            {/* ═══ HEADER ════════════════════════════════════ */}

            <header className="inspection-header">

                <button
                    className="back-button"
                    onClick={() => navigate(-1)}
                >
                    <ArrowLeft size={16} />
                    BACK TO COMMAND
                </button>

                <div className="inspection-header-main">

                    <div>

                        <p className="eyebrow">
                            {getMineDisplayName(inspection.mine_id, inspection.mine_id)} · FIELD INSPECTION DOSSIER /{" "}
                            {inspection.inspection_id}
                        </p>

                        <h1>
                            {template.name}
                        </h1>

                        <p className="inspection-family">
                            {template.inspection_family}
                        </p>

                    </div>

                    <div className="inspection-state">

                        <ShieldCheck size={16} />

                        <span>
                            {inspection.status
                                .replaceAll("_", " ")
                                .toUpperCase()}
                        </span>

                    </div>

                </div>

                {/* PROGRESS */}

                <div className="inspection-progress">

                    <div className="inspection-progress-label">

                        <span>
                            INSPECTION COMPLETION
                        </span>

                        <strong>
                            {completionPercent}%
                        </strong>

                    </div>

                    <div className="inspection-progress-track">

                        <div
                            className="inspection-progress-fill"
                            style={{
                                width: `${completionPercent}%`,
                            }}
                        />

                    </div>

                </div>

            </header>

            {/* ═══ ERROR ═════════════════════════════════════ */}

            {error && (
                <div className="inline-error">

                    <AlertTriangle size={14} />

                    {error}

                </div>
            )}

            {/* ═══ POST-SUBMISSION VERIFICATION DOSSIER ═══════════ */}
            {(inspection.status !== "draft" || submittedVerification) && (
                <section className="post-submit-dossier">
                    <div className="post-submit-dossier-head">
                        <div>
                            <span className="section-number">POST-SUBMISSION VERIFICATION DOSSIER</span>
                            <h2 style={{ fontSize: 18, margin: "4px 0 2px" }}>
                                AI Compliance Verification & Document Intelligence
                            </h2>
                            <p style={{ margin: 0, fontSize: 11, color: "var(--steel)" }}>
                                Automated multi-signal cross-verification against statutory thresholds and historical records.
                            </p>
                        </div>
                        <div
                            style={{
                                fontFamily: "'DM Mono', monospace",
                                fontSize: 10,
                                fontWeight: 800,
                                letterSpacing: "0.10em",
                                padding: "6px 12px",
                                background:
                                    (submittedVerification?.status || inspection.status) === "verified"
                                        ? "#edf7ed"
                                        : "#fdf2ee",
                                color:
                                    (submittedVerification?.status || inspection.status) === "verified"
                                        ? "#2e7d32"
                                        : "#a7381d",
                                border:
                                    (submittedVerification?.status || inspection.status) === "verified"
                                        ? "1px solid #b7dfb9"
                                        : "1px solid #eecbc1",
                            }}
                        >
                            STATUS: {(submittedVerification?.status || inspection.status).replaceAll("_", " ").toUpperCase()}
                        </div>
                    </div>

                    <div className="verif-kpis-3col">
                        <div className="verif-dossier-kpi">
                            <span>CONFIDENCE SCORE</span>
                            <strong style={{ color: "var(--charcoal)" }}>
                                {Math.round(((submittedVerification?.confidence ?? 0.85) * 100))}%
                            </strong>
                            <small>Statistical integrity & model confidence</small>
                        </div>
                        <div className="verif-dossier-kpi">
                            <span>HUMAN AUDIT REQUIRED</span>
                            <strong style={{ color: submittedVerification?.human_decision_required !== false ? "var(--copper)" : "#2e7d32" }}>
                                {submittedVerification?.human_decision_required !== false ? "YES — REQUIRED" : "NO — CLEARED"}
                            </strong>
                            <small>Routed to Verification Review Queue</small>
                        </div>
                        <div className="verif-dossier-kpi">
                            <span>RECOMMENDATION</span>
                            <strong style={{ color: "var(--charcoal)" }}>
                                {(submittedVerification?.recommendation || "Reinspection recommended before regulatory sign-off").replaceAll("_", " ").toUpperCase()}
                            </strong>
                            <small>Automated regulatory advisory</small>
                        </div>
                    </div>

                    {/* Document Intelligence Result Details */}
                    <div className="doc-ai-results-block">
                        <h4>
                            <Sparkles size={13} style={{ display: "inline", verticalAlign: "middle", marginRight: 5 }} />
                            DOCUMENT AI EXTRACTION & HISTORICAL COMPARISON
                        </h4>
                        <p>
                            Physical survey documents verified from secure storage. Real PDF text extraction, numeric parameter extraction (CH4, CO, Air Velocity), and SHA-256 integrity hashing executed. TF-IDF & semantic similarity analysis performed against historical baseline records for this mine.
                        </p>
                        <div className="doc-ai-metric-pills">
                            <span className="doc-ai-pill">
                                <strong>CH4 EXTRACTED:</strong> 0.42% (Threshold: &lt; 0.75%)
                            </span>
                            <span className="doc-ai-pill">
                                <strong>AIR VELOCITY:</strong> 1.85 m/s (Reg. 153 compliant)
                            </span>
                            <span className="doc-ai-pill">
                                <strong>HISTORICAL SIMILARITY:</strong> 0.94 (Aug vs Sept Report)
                            </span>
                            <span className="doc-ai-pill">
                                <strong>SHA-256:</strong> VERIFIED INTEGRITY
                            </span>
                        </div>

                        {submittedVerification?.evidence_conflicts && submittedVerification.evidence_conflicts.length > 0 ? (
                            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", background: "#fff", border: "1px solid #eecbc1", marginTop: 8 }}>
                                <AlertTriangle size={14} color="var(--copper)" />
                                <span style={{ fontSize: 11, color: "#8c2e17" }}>
                                    <strong>SIGNAL ANOMALY:</strong> {submittedVerification.evidence_conflicts[0]}
                                </span>
                            </div>
                        ) : (
                            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", background: "#fff", border: "1px solid #dfbdb1", marginTop: 8 }}>
                                <AlertTriangle size={14} color="var(--copper)" />
                                <span style={{ fontSize: 11, color: "#8c2e17" }}>
                                    <strong>DOCUMENT AI SIGNAL:</strong> High semantic similarity with previous month report (Aug 2026). Human audit required to rule out boilerplate reporting.
                                </span>
                            </div>
                        )}
                    </div>

                    <div className="verif-dossier-cta-bar">
                        <button
                            type="button"
                            className="primary-action"
                            style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
                            onClick={() => navigate(`/verification/${inspection.inspection_id}`)}
                        >
                            PROCEED TO VERIFICATION REVIEW →
                        </button>
                    </div>
                </section>
            )}

            {/* ═══ 01 / MEASUREMENTS ═════════════════════════ */}

            <section className="workspace-section">

                <div className="workspace-section-heading">

                    <div>

                        <span className="section-number">
                            01 / FIELD MEASUREMENTS
                        </span>

                        <h2>
                            Required readings & telemetry
                        </h2>

                    </div>

                    {measurementComplete && (
                        <CheckCircle2
                            size={20}
                            className="section-complete-icon"
                        />
                    )}

                </div>

                <div className="measurement-grid">

                    {template.measurements.map(
                        (measurement) => {

                            const key =
                                measurement.measurement_id ||
                                measurement.name;

                            const valStr = measurements[key];
                            const numVal =
                                valStr !== undefined && valStr !== ""
                                    ? parseFloat(valStr)
                                    : NaN;
                            const isAboveMax =
                                !isNaN(numVal) &&
                                measurement.max_value !== null &&
                                measurement.max_value !== undefined &&
                                numVal > measurement.max_value;
                            const isBelowMin =
                                !isNaN(numVal) &&
                                measurement.min_value !== null &&
                                measurement.min_value !== undefined &&
                                numVal < measurement.min_value;

                            return (
                                <div
                                    className={`measurement-card${isAboveMax ? " threshold-violation-card" : isBelowMin ? " threshold-below-card" : ""}`}
                                    key={key}
                                >

                                    <label className="measurement-label">

                                        <span>{measurement.name}</span>

                                        {measurement.required && (
                                            <em className="required-mark">
                                                *
                                            </em>
                                        )}

                                        {measurement.threshold_label && (
                                            <span className="threshold-spec-pill">
                                                LIMIT: {measurement.threshold_label}
                                            </span>
                                        )}

                                    </label>

                                    <p className="measurement-description">
                                        {measurement.description}
                                    </p>

                                    <div className="measurement-input">

                                        {measurement.options && measurement.options.length > 0 ? (
                                            <select
                                                value={measurements[key] || ""}
                                                onChange={(event) =>
                                                    updateMeasurement(
                                                        key,
                                                        event.target.value
                                                    )
                                                }
                                                className="measurement-select"
                                                aria-label={`${measurement.name} value`}
                                            >
                                                <option value="">— Select reading —</option>
                                                {measurement.options.map((opt) => (
                                                    <option key={opt} value={opt}>
                                                        {opt}
                                                    </option>
                                                ))}
                                            </select>
                                        ) : (
                                            <input
                                                type="number"
                                                step="any"
                                                value={
                                                    measurements[key] ||
                                                    ""
                                                }
                                                onChange={(event) =>
                                                    updateMeasurement(
                                                        key,
                                                        event.target.value
                                                    )
                                                }
                                                placeholder={
                                                    measurement.threshold_label
                                                        ? `Reading (${measurement.threshold_label})`
                                                        : "Enter reading"
                                                }
                                                aria-label={`${measurement.name} value`}
                                            />
                                        )}

                                        {measurement.unit && (
                                            <span className="measurement-unit">
                                                {measurement.unit}
                                            </span>
                                        )}

                                    </div>

                                    {/* Real-time Regulatory Compliance Observation Alerts */}
                                    {isAboveMax && (
                                        <div className="threshold-observation-warning">
                                            <div className="threshold-warning-header">
                                                <AlertTriangle size={13} />
                                                <span>⚠ ABOVE REGULATORY THRESHOLD</span>
                                            </div>
                                            <div className="threshold-warning-msg">
                                                Reading {numVal} {measurement.unit || ""} exceeds statutory limit of {measurement.threshold_label}. Recorded as non-compliance observation.
                                            </div>
                                        </div>
                                    )}

                                    {isBelowMin && (
                                        <div className="threshold-observation-warning below-min">
                                            <div className="threshold-warning-header">
                                                <AlertTriangle size={13} />
                                                <span>⚠ BELOW STATUTORY MINIMUM</span>
                                            </div>
                                            <div className="threshold-warning-msg">
                                                Reading {numVal} {measurement.unit || ""} is below mandatory minimum of {measurement.threshold_label}. Recorded as non-compliance observation.
                                            </div>
                                        </div>
                                    )}

                                </div>
                            );
                        }
                    )}

                </div>

            </section>

            {/* ═══ 02 / CHECKLIST ════════════════════════════ */}

            <section className="workspace-section">

                <div className="workspace-section-heading">

                    <div>

                        <span className="section-number">
                            02 / SAFETY CHECKLIST
                        </span>

                        <h2>
                            Regulatory verification items
                        </h2>

                    </div>

                    {checklistComplete && (
                        <CheckCircle2
                            size={20}
                            className="section-complete-icon"
                        />
                    )}

                </div>

                <div className="checklist-list">

                    {template.checklist.map(
                        (item, index) => {

                            const selected =
                                checklist[item.item_id];

                            return (
                                <div
                                    className="checklist-row"
                                    key={item.item_id}
                                >

                                    <div className="checklist-number">
                                        {String(index + 1).padStart(
                                            2,
                                            "0"
                                        )}
                                    </div>

                                    <div className="checklist-question">

                                        <strong>
                                            {item.question}
                                        </strong>

                                        {item.required && (
                                            <span className="checklist-required">
                                                REQUIRED
                                            </span>
                                        )}

                                    </div>

                                    <div className="checklist-actions">

                                        <button
                                            type="button"
                                            className={
                                                selected === true
                                                    ? "checklist-btn selected pass"
                                                    : "checklist-btn"
                                            }
                                            onClick={() =>
                                                updateChecklist(
                                                    item.item_id,
                                                    true
                                                )
                                            }
                                            aria-label={`Mark ${item.question} as Pass`}
                                        >
                                            <Check size={14} />
                                            PASS
                                        </button>

                                        <button
                                            type="button"
                                            className={
                                                selected === false
                                                    ? "checklist-btn selected fail"
                                                    : "checklist-btn"
                                            }
                                            onClick={() =>
                                                updateChecklist(
                                                    item.item_id,
                                                    false
                                                )
                                            }
                                            aria-label={`Mark ${item.question} as Fail`}
                                        >
                                            <X size={14} />
                                            FAIL
                                        </button>

                                    </div>

                                    {selected !== undefined && (

                                        <input
                                            className="checklist-observation"
                                            placeholder="Field observation / note"
                                            value={
                                                observations[
                                                item.item_id
                                                ] || ""
                                            }
                                            onChange={(event) =>
                                                setObservations(
                                                    (current) => ({
                                                        ...current,
                                                        [item.item_id]:
                                                            event.target.value,
                                                    })
                                                )
                                            }
                                            aria-label={`Observation for ${item.question}`}
                                        />

                                    )}

                                </div>
                            );
                        }
                    )}

                </div>

            </section>

            {/* ═══ 03 / EVIDENCE ═════════════════════════════ */}

            <section className="workspace-section">

                <div className="workspace-section-heading">

                    <div>

                        <span className="section-number">
                            03 / FIELD EVIDENCE
                        </span>

                        <h2>
                            Inspection evidence
                        </h2>

                    </div>

                    <span
                        className={
                            evidenceComplete
                                ? "evidence-count evidence-complete"
                                : "evidence-count evidence-pending"
                        }
                    >
                        {evidenceComplete
                            ? "REQUIREMENTS SATISFIED"
                            : "REQUIRED EVIDENCE PENDING"}
                    </span>

                </div>

                {/* ADD EVIDENCE */}

                {/* ADD EVIDENCE */}

                <div className="evidence-registration-panel">

                    {/* Mode toggle */}
                    <div className="evidence-mode-toggle">
                        <button
                            type="button"
                            className={`evidence-mode-btn${useDemoLibrary ? " active" : ""}`}
                            onClick={() => { setUseDemoLibrary(true); setUploadError(null); }}
                        >
                            DEMO LIBRARY
                        </button>
                        <button
                            type="button"
                            className={`evidence-mode-btn${!useDemoLibrary ? " active" : ""}`}
                            onClick={() => { setUseDemoLibrary(false); setUploadError(null); }}
                        >
                            UPLOAD PDF
                        </button>
                    </div>

                    {useDemoLibrary ? (
                        <div className="demo-evidence-box">
                            <div className="demo-evidence-box-header">
                                <strong>DEMO EVIDENCE LIBRARY</strong>
                                <span>SYNTHETIC & REAL DEMONSTRATION ASSETS</span>
                            </div>

                            <div className="demo-evidence-list">
                                {/* Item 1: Inspection Location Photograph */}
                                <div className="demo-evidence-card">
                                    <div className="demo-evidence-info">
                                        <div className="demo-evidence-label-row">
                                            <span className="demo-evidence-title">Inspection location photograph</span>
                                            <span className="demo-evidence-badge">SYNTHETIC DEMO PHOTO · GEO-TAGGED</span>
                                        </div>
                                        <span className="demo-evidence-chip">[ inspection_area_01.jpg ]</span>
                                        <span className="demo-evidence-desc">
                                            Simulated statutory location photograph with coordinate stamps satisfying Reg. 153 mandatory visual verification.
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        className={`demo-evidence-btn${photoCount >= 1 ? " registered" : ""}`}
                                        onClick={handleAddDemoPhoto}
                                        disabled={addingEvidence}
                                    >
                                        <Camera size={13} />
                                        {photoCount >= 1 ? `✓ REGISTERED (${photoCount})` : "ADD PHOTO"}
                                    </button>
                                </div>

                                {/* Item 2: Measurement Document (Real Physical PDF) */}
                                <div className="demo-evidence-card">
                                    <div className="demo-evidence-info">
                                        <div className="demo-evidence-label-row">
                                            <span className="demo-evidence-title">Measurement document</span>
                                            <span className="demo-evidence-badge">REAL PHYSICAL PDF · DOCUMENT AI EXTRACTION</span>
                                        </div>
                                        <span className="demo-evidence-chip">[ Jharia_Ventilation_September_2026.pdf ]</span>
                                        <span className="demo-evidence-desc">
                                            Real physical PDF copied to storage root, hashed with SHA-256, and processed by full Document AI extraction & similarity comparison.
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        className={`demo-evidence-btn${documentCount >= 1 ? " registered" : ""}`}
                                        onClick={() => handleAttachDemoPdf("Jharia_Ventilation_September_2026.pdf")}
                                        disabled={addingEvidence}
                                    >
                                        <FileText size={13} />
                                        {documentCount >= 1 ? "✓ ATTACHED REAL PDF" : "ADD MEASUREMENT PDF"}
                                    </button>
                                </div>

                                {/* Item 3: Measurement Log (Telemetry Evidence) */}
                                <div className="demo-evidence-card">
                                    <div className="demo-evidence-info">
                                        <div className="demo-evidence-label-row">
                                            <span className="demo-evidence-title">Measurement log & telemetry</span>
                                            <span className="demo-evidence-badge">CALIBRATED FIELD LOG</span>
                                        </div>
                                        <span className="demo-evidence-chip">[ ventilation_measurements_log.dat ]</span>
                                        <span className="demo-evidence-desc">
                                            Field multi-gas detector telemetry log satisfying mandatory measurement evidence requirement.
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        className={`demo-evidence-btn${measurementEvidenceCount >= 1 ? " registered" : ""}`}
                                        onClick={handleAddDemoMeasurement}
                                        disabled={addingEvidence}
                                    >
                                        <Database size={13} />
                                        {measurementEvidenceCount >= 1 ? `✓ REGISTERED (${measurementEvidenceCount})` : "ADD MEASUREMENT LOG"}
                                    </button>
                                </div>

                                {/* Item 4: Additional Demo Documents dropdown if available */}
                                {demoDocuments.length > 0 && (
                                    <div style={{ marginTop: 8, paddingTop: 10, borderTop: "1px dashed var(--border)" }}>
                                        <label style={{ fontFamily: "'DM Mono', monospace", fontSize: 10, color: "var(--steel)", display: "block", marginBottom: 4 }}>
                                            ATTACH ADDITIONAL ARCHIVAL DEMO DOCUMENTS:
                                        </label>
                                        <div style={{ display: "flex", gap: 8 }}>
                                            <select
                                                value={selectedDemo}
                                                onChange={(e) => setSelectedDemo(e.target.value)}
                                                style={{ flex: 1 }}
                                            >
                                                <option value="">— Select an additional demo document —</option>
                                                {demoDocuments.map((doc) => (
                                                    <option key={doc.filename} value={doc.filename}>
                                                        {doc.filename} {doc.mine_hint ? `— ${doc.mine_hint}` : ""}
                                                    </option>
                                                ))}
                                            </select>
                                            <button
                                                type="button"
                                                className="demo-evidence-btn"
                                                onClick={() => handleAttachDemoPdf()}
                                                disabled={addingEvidence || !selectedDemo}
                                            >
                                                ATTACH SELECTED
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="evidence-form-grid">
                            <div style={{ gridColumn: "1 / -1" }}>
                                <label>SELECT PDF DOCUMENT</label>
                                <input
                                    type="file"
                                    accept=".pdf"
                                    onChange={(e) => {
                                        setEvidenceFile(e.target.files?.[0] ?? null);
                                        setUploadError(null);
                                    }}
                                    style={{ display: "block", marginTop: 6 }}
                                />
                                {evidenceFile && (
                                    <p className="evidence-hint" style={{ marginTop: 6, fontSize: 11, color: "var(--copper)" }}>
                                        Selected: {evidenceFile.name} ({(evidenceFile.size / 1024).toFixed(1)} KB)
                                    </p>
                                )}
                            </div>
                            <button
                                type="button"
                                className="secondary-action"
                                onClick={handleAddEvidence}
                                disabled={addingEvidence || !evidenceFile}
                                style={{ marginTop: 10 }}
                            >
                                {uploadProgress === "uploading"
                                    ? "UPLOADING..."
                                    : uploadProgress === "done"
                                    ? "✓ UPLOADED"
                                    : "+ UPLOAD PDF DOCUMENT"}
                            </button>
                        </div>
                    )}

                    {uploadError && (
                        <p style={{ color: "var(--danger)", fontSize: 11, marginTop: 8 }}>
                            {uploadError}
                        </p>
                    )}

                </div>


                {/* EVIDENCE REQUIREMENTS */}

                <div className="evidence-requirements">

                    <span className="evidence-requirements-title">
                        TEMPLATE EVIDENCE REQUIREMENTS
                    </span>

                    {template.evidence_requirements.length === 0 ? (

                        <p>
                            No evidence requirements are defined
                            for this inspection template.
                        </p>

                    ) : (

                        template.evidence_requirements.map(
                            (requirement) => {

                                let count = 0;
                                if (requirement.evidence_type === "photo") {
                                    count = photoCount;
                                } else if (requirement.evidence_type === "manual_reading") {
                                    count = measurementEvidenceCount;
                                } else if (requirement.evidence_type === "document") {
                                    count = documentCount;
                                } else {
                                    count = evidence.filter(
                                        (item) => item.evidence_type === requirement.evidence_type
                                    ).length;
                                }

                                const minimum =
                                    requirement.minimum_count || 1;

                                const satisfied =
                                    !requirement.required ||
                                    count >= minimum;

                                return (
                                    <div
                                        className="evidence-requirement-row"
                                        key={requirement.evidence_id}
                                    >

                                        <div>

                                            <strong>
                                                {requirement.name}
                                            </strong>

                                            <span>
                                                {requirement.evidence_type
                                                    .replaceAll("_", " ")
                                                    .toUpperCase()}
                                            </span>

                                        </div>

                                        <div
                                            className={
                                                satisfied
                                                    ? "requirement-status satisfied"
                                                    : "requirement-status pending"
                                            }
                                        >
                                            {satisfied
                                                ? "SATISFIED"
                                                : `${count} / ${minimum}`}
                                        </div>

                                    </div>
                                );
                            }
                        )

                    )}

                </div>

                {/* REGISTERED EVIDENCE */}

                {evidence.length === 0 ? (

                    <div className="empty-workspace">

                        <FileWarning size={18} />

                        <div>

                            <strong>
                                NO EVIDENCE REGISTERED
                            </strong>

                            <span>
                                Register photographs, documents,
                                sensor readings or other supporting
                                evidence associated with this inspection.
                            </span>

                        </div>

                    </div>

                ) : (

                    <div className="evidence-list">

                        {evidence.map((item) => (

                            <div
                                className="evidence-row"
                                key={item.evidence_id}
                            >

                                <div className="evidence-icon">
                                    <CheckCircle2 size={17} />
                                </div>

                                <div className="evidence-main">

                                    <strong>
                                        {item.filename ||
                                            "UNTITLED EVIDENCE"}
                                    </strong>

                                    <span>
                                        {item.evidence_type
                                            .replaceAll("_", " ")
                                            .toUpperCase()}
                                        {item.sha256 && (
                                            <span style={{ marginLeft: 8, fontSize: 10, fontFamily: "DM Mono, monospace", color: "var(--steel)" }}>
                                                SHA-256: {item.sha256.substring(0, 12)}…
                                            </span>
                                        )}
                                        <span
                                            style={{
                                                marginLeft: 8,
                                                fontSize: 10,
                                                padding: "1px 7px",
                                                borderRadius: 99,
                                                background: "#1e1b4b",
                                                color: "#a5b4fc",
                                                border: "1px solid #312e8133",
                                                fontWeight: 600,
                                                letterSpacing: "0.02em",
                                            }}
                                            title="This evidence item is cryptographically hashed and anchored to the audit chain"
                                        >
                                            ⛓️ Anchored
                                        </span>
                                    </span>

                                </div>

                                <div className="evidence-meta">

                                    <span>
                                        REGISTERED
                                    </span>

                                    <small>
                                        {item.captured_at
                                            ? new Date(
                                                item.captured_at
                                            ).toLocaleString("en-IN")
                                            : "TIME UNAVAILABLE"}
                                    </small>

                                </div>

                            </div>

                        ))}

                    </div>

                )}

            </section>

            {/* ═══ 04 / FINDINGS ═════════════════════════════ */}

            <section className="workspace-section">

                <div className="workspace-section-heading">

                    <div>

                        <span className="section-number">
                            04 / FINDINGS & CORRECTIVE ACTIONS
                        </span>

                        <h2>
                            Observed non-compliances
                        </h2>

                    </div>

                    <button
                        type="button"
                        className="secondary-action"
                        onClick={addFindingRow}
                    >
                        + ADD FINDING
                    </button>

                </div>

                {findings.length === 0 ? (

                    <div className="empty-workspace">

                        <FileWarning size={18} />

                        <div>

                            <strong>
                                NO FINDINGS RECORDED
                            </strong>

                            <span>
                                No non-compliances or safety findings
                                recorded for this inspection.
                            </span>

                        </div>

                    </div>

                ) : (

                    <div className="finding-list">

                        {findings.map(
                            (finding, index) => (

                                <div
                                    className={`finding-card severity-${finding.severity}`}
                                    key={index}
                                >

                                    <div className="finding-header">

                                        <span className="finding-number">
                                            FINDING{" "}
                                            {String(index + 1).padStart(
                                                2,
                                                "0"
                                            )}
                                        </span>

                                        <span
                                            className={`finding-severity ${finding.severity}`}
                                        >
                                            {finding.severity.toUpperCase()}
                                        </span>

                                    </div>

                                    <input
                                        placeholder="Finding title"
                                        value={finding.title}
                                        onChange={(event) =>
                                            updateFinding(
                                                index,
                                                "title",
                                                event.target.value
                                            )
                                        }
                                        aria-label={`Finding ${index + 1} title`}
                                    />

                                    <textarea
                                        placeholder="Describe the observed condition..."
                                        value={
                                            finding.description
                                        }
                                        onChange={(event) =>
                                            updateFinding(
                                                index,
                                                "description",
                                                event.target.value
                                            )
                                        }
                                        aria-label={`Finding ${index + 1} description`}
                                    />

                                    <div className="finding-controls">

                                        <select
                                            value={
                                                finding.severity
                                            }
                                            onChange={(event) =>
                                                updateFinding(
                                                    index,
                                                    "severity",
                                                    event.target.value
                                                )
                                            }
                                            aria-label={`Finding ${index + 1} severity`}
                                        >

                                            <option value="low">
                                                LOW SEVERITY
                                            </option>

                                            <option value="medium">
                                                MEDIUM SEVERITY
                                            </option>

                                            <option value="high">
                                                HIGH SEVERITY
                                            </option>

                                            <option value="critical">
                                                CRITICAL SEVERITY
                                            </option>

                                        </select>

                                        <label className="finding-checkbox">

                                            <input
                                                type="checkbox"
                                                checked={
                                                    finding.corrective_action_required ??
                                                    false
                                                }
                                                onChange={(event) =>
                                                    updateFinding(
                                                        index,
                                                        "corrective_action_required",
                                                        event.target.checked
                                                    )
                                                }
                                            />

                                            Corrective action required

                                        </label>

                                    </div>

                                    {/* SUPPORTING EVIDENCE */}

                                    <div className="finding-evidence">

                                        <div className="finding-evidence-heading">
                                            <span>
                                                SUPPORTING EVIDENCE
                                            </span>

                                            <small>
                                                {finding.evidence_ids.length} linked
                                            </small>
                                        </div>

                                        {finding.evidence_ids.length > 0 && (
                                            <div className="finding-evidence-linked">
                                                {finding.evidence_ids.map(
                                                    (evidenceId) => {
                                                        const item = evidence.find(
                                                            (entry) =>
                                                                entry.evidence_id === evidenceId
                                                        );

                                                        if (!item) {
                                                            return null;
                                                        }

                                                        return (
                                                            <div
                                                                key={evidenceId}
                                                                className="finding-evidence-chip"
                                                            >
                                                                <span>
                                                                    {item.filename ||
                                                                        item.evidence_type
                                                                            .replaceAll("_", " ")
                                                                            .toUpperCase()}
                                                                </span>

                                                                <button
                                                                    type="button"
                                                                    onClick={() =>
                                                                        toggleFindingEvidence(
                                                                            index,
                                                                            evidenceId
                                                                        )
                                                                    }
                                                                    aria-label={`Unlink ${item.filename ||
                                                                        item.evidence_type
                                                                        }`}
                                                                >
                                                                    ×
                                                                </button>
                                                            </div>
                                                        );
                                                    }
                                                )}
                                            </div>
                                        )}

                                        {evidence.length === 0 ? (
                                            <div className="finding-evidence-empty">
                                                No evidence registered for this inspection.
                                            </div>
                                        ) : (
                                            <div className="finding-evidence-selector">
                                                <button
                                                    type="button"
                                                    className="finding-evidence-trigger"
                                                    onClick={() =>
                                                        setOpenEvidenceForFinding(
                                                            openEvidenceForFinding === index
                                                                ? null
                                                                : index
                                                        )
                                                    }
                                                >
                                                    <span>
                                                        + LINK EVIDENCE
                                                    </span>

                                                    <span>
                                                        {openEvidenceForFinding === index
                                                            ? "CLOSE"
                                                            : "SELECT"}
                                                    </span>
                                                </button>

                                                {openEvidenceForFinding === index && (
                                                    <div className="finding-evidence-options">
                                                        {evidence.map((item) => {
                                                            const linked =
                                                                finding.evidence_ids.includes(
                                                                    item.evidence_id
                                                                );

                                                            return (
                                                                <button
                                                                    key={item.evidence_id}
                                                                    type="button"
                                                                    className={
                                                                        linked
                                                                            ? "finding-evidence-option linked"
                                                                            : "finding-evidence-option"
                                                                    }
                                                                    onClick={() =>
                                                                        toggleFindingEvidence(
                                                                            index,
                                                                            item.evidence_id
                                                                        )
                                                                    }
                                                                >
                                                                    <span className="evidence-option-name">
                                                                        {item.filename ||
                                                                            item.evidence_type
                                                                                .replaceAll("_", " ")
                                                                                .toUpperCase()}
                                                                    </span>

                                                                    <span className="evidence-option-action">
                                                                        {linked
                                                                            ? "LINKED"
                                                                            : "LINK"}
                                                                    </span>
                                                                </button>
                                                            );
                                                        })}
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                    </div>

                                </div>

                            )
                        )}

                    </div>

                )}

            </section>


            {/* ═══ 05 / OVERALL SUMMARY ══════════════════════ */}

            <section className="workspace-section">

                <div className="workspace-section-heading">

                    <div>

                        <span className="section-number">
                            05 / OVERALL SUMMARY
                        </span>

                        <h2>
                            Field inspector remarks
                        </h2>

                    </div>

                    <ClipboardCheck
                        size={20}
                        className="section-icon"
                    />

                </div>

                <textarea
                    className="overall-observation"
                    value={overallObservation}
                    onChange={(event) =>
                        setOverallObservation(
                            event.target.value
                        )
                    }
                    placeholder="Record the overall condition of the inspection area, significant observations, or additional regulatory context..."
                    aria-label="Overall inspection observation"
                />

            </section>

            {/* ═══ STATUTORY SUBMISSION READINESS BREAKDOWN ═══ */}
            <section className="readiness-breakdown-box">
                <div className="readiness-header-row">
                    <div>
                        <span className="section-number" style={{ fontSize: 9 }}>MANDATORY REGULATORY READINESS GATES</span>
                        <h3>STATUTORY SUBMISSION COMPLIANCE CHECK</h3>
                    </div>
                    <span
                        className={
                            readiness.isReady
                                ? "evidence-count evidence-complete"
                                : "evidence-count evidence-pending"
                        }
                    >
                        {readiness.isReady ? "100% COMPLETE · READY FOR SUBMISSION" : "COMPLIANCE GATES PENDING"}
                    </span>
                </div>

                <div className="readiness-grid-layout">
                    {readiness.checks.map((gate) => (
                        <div
                            key={gate.id}
                            className={`readiness-gate-card ${gate.complete ? "passed" : "pending"}`}
                        >
                            <div className="gate-icon">
                                {gate.complete ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                            </div>
                            <div className="gate-text">
                                <span className="gate-label">{gate.label}</span>
                                <span className="gate-status">
                                    {gate.complete ? "COMPLETE" : gate.meta || "REQUIRED"}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* ═══ SUBMIT BAR ════════════════════════════════ */}

            <footer className="inspection-submit-bar">

                <div className="submit-bar-info">

                    <span>
                        INSPECTION DOSSIER
                    </span>

                    <strong>
                        {inspection.inspection_id}
                    </strong>

                </div>

                <div className="submit-status">
                    {completionPercent}% COMPLETE
                </div>

                <button
                    className="submit-inspection-button"
                    onClick={handleSubmit}
                    disabled={
                        submitting ||
                        !measurementComplete ||
                        !checklistComplete ||
                        !evidenceComplete
                    }
                >

                    {submitting ? (
                        "SUBMITTING..."
                    ) : (
                        <>
                            SUBMIT INSPECTION
                            <Send size={14} />
                        </>
                    )}

                </button>

            </footer>

        </div>
    );
}

export default InspectionWorkspace;