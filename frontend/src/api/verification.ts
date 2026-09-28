import { apiGet, apiPost } from "./client";

export type DecisionType =
    | "accept"
    | "review"
    | "reinspection"
    | "escalate"
    | "verify"
    | "return"
    | "reject";

export type VerificationSignal = {
    signal_id: string;
    inspection_id: string;
    category: string;
    name: string;
    status: string;
    severity: string;
    score: number | null;
    explanation: string;
};

export type VerificationResult = {
    verification_id: string;
    inspection_id: string;
    status: string;
    confidence: number;
    signals: VerificationSignal[];
    source_anomalies: string[];
    evidence_conflicts: string[];
    recommendation: string;
    human_decision_required: boolean;
};

export type PendingVerification = {
    verification_id: string;
    inspection_id: string;
    status: string;
    confidence: number;
    recommendation: string;
    mine_id: string;
    template_id: string;
    inspection_date: string;
};

export type HumanReviewCreate = {
    inspection_id: string;
    reviewer_id: string;
    decision: DecisionType;
    reason: string;
};

// ============================================================
// PHASE 2 TASK 4 TYPES
// ============================================================

export type VerificationQueueItem = {
    inspection_id: string;
    template_id: string;
    template_name: string;
    category: string;
    regulation_reference?: string | null;
    inspector_id: string;
    inspector_name: string;
    submitted_at?: string | null;
    inspection_date?: string | null;
    inspection_status: string;
    verification_status?: string | null;
    risk_level: "CRITICAL" | "HIGH" | "NORMAL";
    priority: "CRITICAL" | "HIGH" | "NORMAL";
    priority_reasons: string[];
    evidence_count: number;
    required_evidence_count: number;
    evidence_compliant: boolean;
    findings_count: number;
    has_violations: boolean;
};

export type VerificationQueueCounts = {
    submitted: number;
    review_required: number;
    verified: number;
    rejected: number;
    high_risk_review: number;
};

export type VerificationQueueResponse = {
    mine_id: string;
    mine_name: string;
    counts: VerificationQueueCounts;
    items: VerificationQueueItem[];
};

export type MeasurementReviewItem = {
    measurement_id: string;
    parameter: string;
    value: number;
    unit?: string | null;
    threshold?: string | null;
    threshold_label?: string | null;
    min_value?: number | null;
    max_value?: number | null;
    status: "PASS" | "VIOLATION";
    violation_type?: string | null;
};

export type ChecklistReviewItem = {
    item_id: string;
    question: string;
    required: boolean;
    severity_if_failed?: string | null;
    passed: boolean;
    status: "PASS" | "FAIL" | "NOT_APPLICABLE";
    observation?: string | null;
};

export type EvidenceReviewItem = {
    evidence_id: string;
    evidence_type: string;
    name?: string | null;
    file_path?: string | null;
    sha256_hash?: string | null;
    captured_at?: string | null;
    submitted_at?: string | null;
    checklist_item_id?: string | null;
    finding_id?: string | null;
};

export type EvidenceCompleteness = {
    required_count: number;
    actual_count: number;
    is_compliant: boolean;
    missing_requirements: string[];
};

export type FindingReviewItem = {
    finding_id: string;
    severity: string;
    description: string;
    category: string;
    measurement_id?: string | null;
    checklist_item_id?: string | null;
    evidence_linked: string[];
    status: string;
    created_at?: string | null;
};

export type VerificationAuditItem = {
    review_id: string;
    inspection_id: string;
    reviewer_id: string;
    reviewer_name?: string | null;
    decision: string;
    reason: string;
    timestamp: string;
    previous_status?: string | null;
    new_status?: string | null;
};

export type ReviewSummaryIntelligence = {
    evidence_completeness: string;
    evidence_compliant: boolean;
    measurement_compliance: string;
    has_violations: boolean;
    checklist_compliance: string;
    findings_count: number;
    risk_level: string;
    recurring_issue_status: string;
};

export type InspectionVerificationDetailResponse = {
    inspection_id: string;
    template_id: string;
    template_name: string;
    category: string;
    regulation_reference?: string | null;
    frequency?: string | null;
    mine_id: string;
    mine_name: string;
    inspector_id: string;
    inspector_name: string;
    submitted_at?: string | null;
    inspection_status: string;
    verification_status?: string | null;
    measurements: MeasurementReviewItem[];
    checklist: ChecklistReviewItem[];
    evidence: EvidenceReviewItem[];
    evidence_completeness: EvidenceCompleteness;
    findings: FindingReviewItem[];
    review_summary: ReviewSummaryIntelligence;
    risk_level: string;
    audit_history: VerificationAuditItem[];
    can_verify: boolean;
    validation_errors: string[];
};

export type VerifyInspectionPayload = {
    reviewer_id: string;
    notes?: string | null;
};

export type ReturnInspectionPayload = {
    reviewer_id: string;
    reason: string;
};

export type VerificationActionResponse = {
    inspection_id: string;
    status: string;
    decision: string;
    reviewer_id: string;
    reason?: string | null;
    timestamp: string;
    message: string;
};

// ============================================================
// API CALLS
// ============================================================

export function getPendingVerifications() {
    return apiGet(
        "/api/verifications/pending"
    ) as Promise<PendingVerification[]>;
}

export function getVerification(inspectionId: string) {
    return apiGet(
        `/api/verifications/${inspectionId}`
    ) as Promise<VerificationResult>;
}

export function createHumanReview(
    payload: HumanReviewCreate
) {
    return apiPost("/api/reviews", payload);
}

export function getMineVerificationQueue(mineId: string): Promise<VerificationQueueResponse> {
    return apiGet(`/api/mines/${mineId}/verification`) as Promise<VerificationQueueResponse>;
}

export function getInspectionVerificationDetail(inspectionId: string): Promise<InspectionVerificationDetailResponse> {
    return apiGet(`/api/inspections/${inspectionId}/verification`) as Promise<InspectionVerificationDetailResponse>;
}

export function verifyInspectionOperational(
    inspectionId: string,
    payload?: VerifyInspectionPayload
): Promise<VerificationActionResponse> {
    return apiPost(`/api/inspections/${inspectionId}/verify`, payload || {}) as Promise<VerificationActionResponse>;
}

export function returnInspectionOperational(
    inspectionId: string,
    payload: ReturnInspectionPayload
): Promise<VerificationActionResponse> {
    return apiPost(`/api/inspections/${inspectionId}/return`, payload) as Promise<VerificationActionResponse>;
}
