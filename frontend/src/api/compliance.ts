import { apiGet } from "./client";

export type ThresholdViolationItem = {
    measurement_name: string;
    inspection_id: string;
    recorded_value: number;
    unit?: string | null;
    min_value?: number | null;
    max_value?: number | null;
    threshold_label?: string | null;
    regulation_reference?: string | null;
    timestamp?: string | null;
};

export type CategoryComplianceSummary = {
    category: string;
    total_schedules: number;
    overdue_count: number;
    due_today_count: number;
    upcoming_count: number;
    inspections_count: number;
    submitted_count: number;
    verified_count: number;
    review_required_count: number;
    threshold_violations_count: number;
    open_findings_count: number;
    compliance_status: "COMPLIANT" | "ACTION_REQUIRED" | "CRITICAL_NON_COMPLIANCE" | string;
};

export type AttentionItem = {
    item_id?: string;
    item_type?: string;
    severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
    category: string;
    title: string;
    description: string;
    action: string;
    reference_id?: string | null;
    created_at?: string | null;
};

export type MineComplianceSummary = {
    mine_id: string;
    mine_name: string;
    subsidiary?: string | null;
    mine_type?: string | null;
    gassy_degree?: string | null;
    as_of: string;

    // Headline metrics
    total_applicable_inspections: number;
    due_today: number;
    overdue: number;
    upcoming: number;
    submitted: number;
    verified: number;
    review_required: number;
    open_findings: number;
    threshold_violations: number;

    // Domain breakdowns
    category_compliance: CategoryComplianceSummary[];

    // Actionable attention feed
    attention_items: AttentionItem[];
};

export function getMineComplianceSummary(mineId: string): Promise<MineComplianceSummary> {
    return apiGet<MineComplianceSummary>(`/api/mines/${mineId}/compliance-summary`);
}

// ------------------------------------------------------------
// RISK & RECURRING NON-COMPLIANCE INTELLIGENCE (PHASE 2 TASK 3)
// ------------------------------------------------------------

export type CategoryRiskSummary = {
    category: string;
    risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT_DATA" | string;
    risk_score: number;
    active_signals: number;
    recurring_issues: number;
    open_findings: number;
    overdue_inspections: number;
    drivers: string[];
};

export type RecurringComplianceIssue = {
    issue_id: string;
    category: string;
    issue_type: "RECURRING_THRESHOLD_VIOLATION" | "RECURRING_FINDING" | "REPEATED_OVERDUE_INSPECTION" | "UNRESOLVED_FINDING" | "CATEGORY_DETERIORATION" | string;
    title: string;
    occurrences: number;
    first_detected_at?: string | null;
    last_detected_at?: string | null;
    severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
    status: "OPEN" | "RESOLVED" | string;
    related_inspection_ids: string[];
    related_finding_ids: string[];
    description: string;
    recommended_action: string;
};

export type MineRiskResponse = {
    mine_id: string;
    mine_name?: string | null;
    overall_risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT_DATA" | string;
    overall_risk_score: number;
    as_of?: string | null;
    categories: CategoryRiskSummary[];
    recurring_issues: RecurringComplianceIssue[];
    top_risk_drivers: string[];
};

export function getMineRisk(mineId: string): Promise<MineRiskResponse> {
    return apiGet<MineRiskResponse>(`/api/mines/${mineId}/risk`);
}

export function getMineRecurringCompliance(mineId: string): Promise<RecurringComplianceIssue[]> {
    return apiGet<RecurringComplianceIssue[]>(`/api/mines/${mineId}/recurring-compliance`);
}

