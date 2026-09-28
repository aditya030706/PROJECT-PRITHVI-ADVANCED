"""
API request/response schemas for PRITHVI Feature 1.

The domain models remain in app.models. These schemas define the HTTP
contract used by the FastAPI inspection, evidence, verification and
human-review endpoints.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import (
    DecisionType,
    EvidenceType,
    GassyDegree,
    InspectionStatus,
    MineType,
    VerificationStatus,
)


# ============================================================
# MINE
# ============================================================

class MineCreate(BaseModel):
    mine_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    subsidiary: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    mine_type: MineType
    mining_method: Optional[str] = None
    gassy_degree: GassyDegree = GassyDegree.NOT_APPLICABLE
    mechanised: bool = False
    uses_hemm: bool = False
    has_winding_installation: bool = False
    blasting_operation: bool = False


class MineResponse(MineCreate):
    active: bool = True


# ============================================================
# INSPECTION TEMPLATE
# ============================================================

class InspectionTemplateResponse(BaseModel):
    template_id: str
    name: str
    inspection_family: str
    description: Optional[str] = None
    applicable_mine_types: list[MineType] = Field(default_factory=list)
    regulatory_obligation_ids: list[str] = Field(default_factory=list)
    frequency_or_trigger: Optional[str] = None
    frequency_label: Optional[str] = None
    responsible_role: Optional[str] = None
    regulation_reference: Optional[str] = None
    measurements: list[dict] = Field(default_factory=list)
    checklist: list[dict] = Field(default_factory=list)
    evidence_requirements: list[dict] = Field(default_factory=list)
    active: bool = True


# ============================================================
# INSPECTION
# ============================================================

class InspectionCreate(BaseModel):
    mine_id: str
    template_id: str
    obligation_id: Optional[str] = None
    inspector_id: str
    inspection_date: date
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None


class InspectionResponse(InspectionCreate):
    inspection_id: str
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    status: InspectionStatus


# ============================================================
# MEASUREMENTS
# ============================================================

class MeasurementCreate(BaseModel):
    measurement_type: str
    value: float
    unit: Optional[str] = None
    source: str = "manual"
    captured_at: Optional[datetime] = None


class MeasurementResponse(MeasurementCreate):
    measurement_id: str
    inspection_id: str


# ============================================================
# CHECKLIST
# ============================================================

class ChecklistResultCreate(BaseModel):
    item_id: str
    passed: bool
    observation: Optional[str] = None


class ChecklistResultResponse(ChecklistResultCreate):
    result_id: str
    inspection_id: str


# ============================================================
# EVIDENCE
# ============================================================

class EvidenceCreate(BaseModel):
    evidence_type: EvidenceType
    filename: Optional[str] = None
    storage_reference: Optional[str] = None
    captured_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EvidenceResponse(EvidenceCreate):
    evidence_id: str
    inspection_id: str
    sha256: Optional[str] = None
    perceptual_hash: Optional[str] = None
    metadata_verified: bool = False


# ============================================================
# FINDINGS
# ============================================================

class FindingCreate(BaseModel):
    title: str
    description: str
    severity: str
    corrective_action_required: bool = False
    evidence_ids: list[str] = Field(default_factory=list)


class FindingResponse(FindingCreate):
    finding_id: str
    inspection_id: str
    status: str = "open"


# ============================================================
# INSPECTION SUBMISSION
# ============================================================

class InspectionSubmission(BaseModel):
    inspection_id: str
    measurements: list[MeasurementCreate] = Field(default_factory=list)
    checklist_results: list[ChecklistResultCreate] = Field(default_factory=list)
    findings: list[FindingCreate] = Field(default_factory=list)
    observation: Optional[str] = None


# ============================================================
# VERIFICATION
# ============================================================

class VerificationSignalResponse(BaseModel):
    """One explainable verification signal."""

    signal_id: str
    category: str
    name: str
    status: str
    severity: str = "info"
    score: Optional[float] = None
    explanation: str


class VerificationResultResponse(BaseModel):
    verification_id: str
    inspection_id: str
    status: VerificationStatus
    confidence: float = Field(ge=0.0, le=1.0)
    signals: list[VerificationSignalResponse] = Field(default_factory=list)
    source_anomalies: list[str] = Field(default_factory=list)
    evidence_conflicts: list[str] = Field(default_factory=list)
    recommendation: str
    human_decision_required: bool = False


# ============================================================
# HUMAN REVIEW
# ============================================================

class HumanReviewCreate(BaseModel):
    inspection_id: str
    reviewer_id: str
    decision: DecisionType
    reason: str


class HumanReviewResponse(HumanReviewCreate):
    review_id: str
    reviewed_at: datetime
    case_id: Optional[str] = None
    status: Optional[str] = None
    next_action: Optional[str] = None
    inspection_status: Optional[str] = None


# ============================================================
# DASHBOARD
# ============================================================

class DashboardSummary(BaseModel):
    total_mines: int = 0
    inspections_due: int = 0
    inspections_submitted: int = 0
    awaiting_verification: int = 0
    verification_required: int = 0
    reinspection_recommended: int = 0
    source_anomalies: int = 0
    open_corrective_actions: int = 0


# ============================================================
# COMPLIANCE INTELLIGENCE (PHASE 2)
# ============================================================

class ThresholdViolationItem(BaseModel):
    inspection_id: str
    measurement_id: str
    measurement_type: str
    measurement_name: str
    template_id: str
    template_name: str
    inspection_family: str
    value: float
    unit: Optional[str] = None
    limit_value: Optional[float] = None
    threshold_label: Optional[str] = None
    violation_type: str
    captured_at: Optional[str] = None
    inspection_date: Optional[str] = None


class CategoryComplianceSummary(BaseModel):
    category: str
    total_schedules: int = 0
    overdue_count: int = 0
    due_today_count: int = 0
    upcoming_count: int = 0
    inspections_count: int = 0
    submitted_count: int = 0
    verified_count: int = 0
    review_required_count: int = 0
    threshold_violations_count: int = 0
    open_findings_count: int = 0
    compliance_status: str = "COMPLIANT"


class AttentionItem(BaseModel):
    item_id: str
    item_type: str
    severity: str
    category: str
    title: str
    description: str
    action: str
    reference_id: Optional[str] = None
    created_at: Optional[str] = None


class MineComplianceSummaryResponse(BaseModel):
    mine_id: str
    mine_name: str
    subsidiary: Optional[str] = None
    mine_type: str
    gassy_degree: str
    as_of: str
    total_applicable_inspections: int
    due_today: int
    overdue: int
    upcoming: int
    submitted: int
    verified: int
    review_required: int
    open_findings: int
    threshold_violations: int
    category_compliance: list[CategoryComplianceSummary]
    attention_items: list[AttentionItem]
    threshold_violation_details: list[ThresholdViolationItem] = Field(default_factory=list)


# ============================================================
# RISK & RECURRING NON-COMPLIANCE INTELLIGENCE (PHASE 2 TASK 3)
# ============================================================

class CategoryRiskSummary(BaseModel):
    category: str
    risk_level: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"
    risk_score: int  # 0 to 100
    active_signals: int
    recurring_issues: int
    open_findings: int
    overdue_inspections: int
    drivers: list[str] = Field(default_factory=list)


class RecurringComplianceIssue(BaseModel):
    issue_id: str
    category: str
    issue_type: str  # "RECURRING_THRESHOLD_VIOLATION", "RECURRING_FINDING", etc.
    title: str
    occurrences: int
    first_detected_at: Optional[str] = None
    last_detected_at: Optional[str] = None
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    status: str  # "OPEN", "RESOLVED"
    related_inspection_ids: list[str] = Field(default_factory=list)
    related_finding_ids: list[str] = Field(default_factory=list)
    description: str
    recommended_action: str


class MineRiskResponse(BaseModel):
    mine_id: str
    mine_name: Optional[str] = None
    overall_risk_level: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"
    overall_risk_score: int  # 0 to 100
    as_of: Optional[str] = None
    categories: list[CategoryRiskSummary] = Field(default_factory=list)
    recurring_issues: list[RecurringComplianceIssue] = Field(default_factory=list)
    top_risk_drivers: list[str] = Field(default_factory=list)


# ============================================================
# VERIFICATION & REGULATORY REVIEW INTELLIGENCE (PHASE 2 TASK 4)
# ============================================================

class VerificationQueueItem(BaseModel):
    inspection_id: str
    template_id: str
    template_name: str
    category: str
    regulation_reference: Optional[str] = None
    inspector_id: str
    inspector_name: str
    submitted_at: Optional[str] = None
    inspection_date: Optional[str] = None
    inspection_status: str
    verification_status: Optional[str] = None
    risk_level: str  # "CRITICAL", "HIGH", "NORMAL"
    priority: str    # "CRITICAL", "HIGH", "NORMAL"
    priority_reasons: list[str] = Field(default_factory=list)
    evidence_count: int
    required_evidence_count: int
    evidence_compliant: bool
    findings_count: int
    has_violations: bool


class VerificationQueueCounts(BaseModel):
    submitted: int
    review_required: int
    verified: int
    rejected: int
    high_risk_review: int


class VerificationQueueResponse(BaseModel):
    mine_id: str
    mine_name: str
    counts: VerificationQueueCounts
    items: list[VerificationQueueItem] = Field(default_factory=list)


class MeasurementReviewItem(BaseModel):
    measurement_id: str
    parameter: str
    value: float
    unit: Optional[str] = None
    threshold: Optional[str] = None
    threshold_label: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    status: str  # "PASS", "VIOLATION"
    violation_type: Optional[str] = None


class ChecklistReviewItem(BaseModel):
    item_id: str
    question: str
    required: bool
    severity_if_failed: Optional[str] = None
    passed: bool
    status: str  # "PASS", "FAIL", "NOT_APPLICABLE"
    observation: Optional[str] = None


class EvidenceReviewItem(BaseModel):
    evidence_id: str
    evidence_type: str
    name: Optional[str] = None
    file_path: Optional[str] = None
    sha256_hash: Optional[str] = None
    captured_at: Optional[str] = None
    submitted_at: Optional[str] = None
    checklist_item_id: Optional[str] = None
    finding_id: Optional[str] = None


class EvidenceCompleteness(BaseModel):
    required_count: int
    actual_count: int
    is_compliant: bool
    missing_requirements: list[str] = Field(default_factory=list)


class FindingReviewItem(BaseModel):
    finding_id: str
    severity: str
    description: str
    category: str
    measurement_id: Optional[str] = None
    checklist_item_id: Optional[str] = None
    evidence_linked: list[str] = Field(default_factory=list)
    status: str
    created_at: Optional[str] = None


class VerificationAuditItem(BaseModel):
    review_id: str
    inspection_id: str
    reviewer_id: str
    reviewer_name: Optional[str] = None
    decision: str
    reason: str
    timestamp: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None


class ReviewSummaryIntelligence(BaseModel):
    evidence_completeness: str
    evidence_compliant: bool
    measurement_compliance: str
    has_violations: bool
    checklist_compliance: str
    findings_count: int
    risk_level: str
    recurring_issue_status: str


class InspectionVerificationDetailResponse(BaseModel):
    inspection_id: str
    template_id: str
    template_name: str
    category: str
    regulation_reference: Optional[str] = None
    frequency: Optional[str] = None
    mine_id: str
    mine_name: str
    inspector_id: str
    inspector_name: str
    submitted_at: Optional[str] = None
    inspection_status: str
    verification_status: Optional[str] = None
    measurements: list[MeasurementReviewItem] = Field(default_factory=list)
    checklist: list[ChecklistReviewItem] = Field(default_factory=list)
    evidence: list[EvidenceReviewItem] = Field(default_factory=list)
    evidence_completeness: EvidenceCompleteness
    findings: list[FindingReviewItem] = Field(default_factory=list)
    review_summary: ReviewSummaryIntelligence
    risk_level: str
    audit_history: list[VerificationAuditItem] = Field(default_factory=list)
    can_verify: bool
    validation_errors: list[str] = Field(default_factory=list)


class VerifyInspectionRequest(BaseModel):
    reviewer_id: str
    notes: Optional[str] = None


class ReturnInspectionRequest(BaseModel):
    reviewer_id: str
    reason: str


class VerificationActionResponse(BaseModel):
    inspection_id: str
    status: str
    decision: str
    reviewer_id: str
    reason: Optional[str] = None
    timestamp: str
    message: str


# ============================================================
# PHASE 2 TASK 6 — COMPLIANCE CASE & ACTION SCHEMAS
# ============================================================

class CorrectiveActionCreateRequest(BaseModel):
    title: str
    description: str
    assigned_role: Optional[str] = None
    assigned_user_id: Optional[str] = None
    due_at: str
    priority: str = "MEDIUM"  # "CRITICAL", "HIGH", "MEDIUM", "LOW"


class CorrectiveActionUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_role: Optional[str] = None
    assigned_user_id: Optional[str] = None
    due_at: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class CorrectiveActionResponse(BaseModel):
    action_id: str
    case_id: Optional[str] = None
    mine_id: Optional[str] = None
    title: Optional[str] = None
    description: str
    assigned_role: Optional[str] = None
    assigned_user_id: Optional[str] = None
    assigned_to: Optional[str] = None
    due_at: Optional[str] = None
    priority: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    completed_by: Optional[str] = None


class CorrectionSubmitRequest(BaseModel):
    notes: Optional[str] = None
    evidence_id: Optional[str] = None
    filename: Optional[str] = None
    evidence_type: str = "photo"
    raw_data: Optional[str] = None


class CorrectionSubmitResponse(BaseModel):
    action_id: str
    case_id: str
    action_status: str
    case_status: str
    evidence_id: str
    sha256: str
    ipfs_cid: str
    audit_proof_status: str
    message: str


class CaseVerificationRequest(BaseModel):
    notes: Optional[str] = None


class CaseVerificationResponse(BaseModel):
    case_id: str
    status: str
    closed_at: str
    closed_by: str
    cryptographic_proof: dict
    message: str


class CaseReturnRequest(BaseModel):
    reason: str


class CaseReturnResponse(BaseModel):
    case_id: str
    status: str
    returned_by: str
    reason: str
    timestamp: str
    message: str


class CaseAuditEventResponse(BaseModel):
    event_id: str
    case_id: str
    action: str
    actor_id: str
    actor_role: Optional[str] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    reason: Optional[str] = None
    timestamp: str
    details: Optional[str] = None
    sha256: Optional[str] = None
    ipfs_cid: Optional[str] = None


class CryptographicProofResponse(BaseModel):
    proof_id: str
    case_id: str
    action_type: str
    actor_id: str
    actor_role: Optional[str] = None
    sha256: str
    ipfs_cid: str
    timestamp: str
    status: str
    ledger_standard: str
    verified: bool


class ComplianceCaseResponse(BaseModel):
    case_id: str
    mine_id: str
    mine_name: Optional[str] = None
    inspection_id: Optional[str] = None
    finding_id: Optional[str] = None
    category: str
    regulation_reference: Optional[str] = None
    title: str
    description: str
    severity: str
    risk_level: Optional[str] = None
    status: str
    source_type: str
    source_id: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    closed_by: Optional[str] = None


class ComplianceCaseDetailResponse(BaseModel):
    case: ComplianceCaseResponse
    actions: list[CorrectiveActionResponse] = Field(default_factory=list)
    correction_evidence: list[dict] = Field(default_factory=list)
    audit_events: list[CaseAuditEventResponse] = Field(default_factory=list)
    cryptographic_proofs: list[CryptographicProofResponse] = Field(default_factory=list)
    traceability: dict
    timeline: dict
    can_verify: bool

# ============================================================
# PHASE 2 TASK 7 — EVIDENCE INTEGRITY SCHEMAS
# ============================================================

class EvidenceIntegrityResponse(BaseModel):
    integrity_id: str
    evidence_id: str
    content_hash: str
    hash_algorithm: str = "SHA-256"
    ipfs_cid: Optional[str] = None
    ipfs_status: str
    blockchain_network: Optional[str] = None
    transaction_ref: Optional[str] = None
    block_ref: Optional[str] = None
    anchored_at: Optional[str] = None
    anchor_mode: str
    status: str
    verified_at: Optional[str] = None
    verification_result: Optional[str] = None
    created_at: str
    # Human-readable label
    integrity_label: Optional[str] = None
    mode_label: Optional[str] = None


class EvidenceAnchorRequest(BaseModel):
    actor_id: str = "SYSTEM"
    reference_type: str = "INSPECTION_EVIDENCE"
    notes: Optional[str] = None


class EvidenceVerifyResponse(BaseModel):
    evidence_id: str
    matches: bool
    verification_status: str
    mode: str
    details: str
    integrity: Optional[EvidenceIntegrityResponse] = None


class EvidenceWithIntegrity(BaseModel):
    evidence_id: str
    evidence_type: str
    filename: Optional[str] = None
    captured_at: Optional[str] = None
    sha256: Optional[str] = None
    integrity: Optional[EvidenceIntegrityResponse] = None


class InspectionAuditIntegrityResponse(BaseModel):
    inspection_id: str
    mine_id: Optional[str] = None
    total_evidence: int
    anchored_count: int
    verified_count: int
    pending_count: int
    integrity_coverage: str  # "FULL" | "PARTIAL" | "NONE"
    evidence_integrity: list[EvidenceWithIntegrity] = Field(default_factory=list)
    ipfs_service_status: dict = Field(default_factory=dict)
    blockchain_service_status: dict = Field(default_factory=dict)


class CaseAuditIntegrityResponse(BaseModel):
    case_id: str
    mine_id: Optional[str] = None
    total_correction_evidence: int
    anchored_count: int
    verified_count: int
    integrity_coverage: str
    evidence_integrity: list[EvidenceWithIntegrity] = Field(default_factory=list)
    ipfs_service_status: dict = Field(default_factory=dict)
    blockchain_service_status: dict = Field(default_factory=dict)


# ============================================================
# GIS ATTENDANCE SCHEMAS (PHASE 2 TASK 8)
# ============================================================

class CheckInRequest(BaseModel):
    """GPS attendance check-in submitted by a field user."""
    mine_id: str
    zone_id: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    accuracy_meters: Optional[float] = Field(None, ge=0.0)
    captured_at: Optional[str] = None          # ISO timestamp from device
    schedule_instance_id: Optional[str] = None
    inspection_id: Optional[str] = None
    device_info: Optional[str] = None
    notes: Optional[str] = None


class GeofenceResultResponse(BaseModel):
    """Result of a server-side Haversine geofence calculation."""
    status: str
    distance_meters: Optional[float] = None
    allowed_radius_meters: Optional[float] = None
    location_accuracy_meters: Optional[float] = None
    message: str


class AttendanceRecordResponse(BaseModel):
    """Single attendance record returned by the API."""
    attendance_id: str
    user_id: str
    user_role: str
    mine_id: str
    zone_id: Optional[str] = None
    schedule_instance_id: Optional[str] = None
    inspection_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_meters: Optional[float] = None
    captured_at: Optional[str] = None
    server_recorded_at: str
    geofence_status: str
    distance_from_reference_meters: Optional[float] = None
    status: str
    status_label: str        # human-readable
    anomaly_status: str
    anomaly_label: str       # human-readable
    evidence_id: Optional[str] = None
    device_info: Optional[str] = None
    notes: Optional[str] = None
    geofence_detail: Optional[GeofenceResultResponse] = None
    created_at: str


class CheckInResponse(BaseModel):
    """Response after a successful or flagged GPS check-in."""
    attendance_id: str
    user_id: str
    mine_id: str
    status: str
    status_label: str
    anomaly_status: str
    geofence: GeofenceResultResponse
    message: str
    linked_inspection_id: Optional[str] = None
    linked_schedule_instance_id: Optional[str] = None
    integrity_mode: str = "DEMO_AUDIT_MODE"


class TeamAttendanceSummary(BaseModel):
    """Summary row for a single attendance record in supervisor team view."""
    attendance_id: str
    user_id: str
    user_role: str
    mine_id: str
    status: str
    status_label: str
    anomaly_status: str
    anomaly_label: str
    server_recorded_at: str
    geofence_status: str
    distance_from_reference_meters: Optional[float] = None
    linked_inspection_id: Optional[str] = None


class TeamAttendanceResponse(BaseModel):
    """Team attendance overview for supervisors and managers."""
    total: int
    valid: int
    flagged: int
    outside_geofence: int
    records: list[TeamAttendanceSummary] = Field(default_factory=list)
    anomalies: list[TeamAttendanceSummary] = Field(default_factory=list)


class AttendanceAnomalySignal(BaseModel):
    """An attendance anomaly signal for DGMS / manager intelligence."""
    attendance_id: str
    user_id: str
    mine_id: str
    anomaly_type: str
    anomaly_label: str
    severity: str
    description: str
    server_recorded_at: str
    linked_inspection_id: Optional[str] = None


class AttendanceAggregateResponse(BaseModel):
    """Corporate-level aggregate attendance summary (no PII)."""
    total_records: int
    valid_count: int
    flagged_count: int
    outside_geofence_count: int
    mines_with_attendance: int
    anomaly_count: int


class MineZoneRequest(BaseModel):
    """Request to create/register a mine zone."""
    mine_id: str
    name: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    geofence_radius_meters: float = Field(default=500.0, ge=10.0, le=50000.0)
    description: Optional[str] = None


class MineZoneResponse(BaseModel):
    """Single mine zone record."""
    mine_zone_id: str
    mine_id: str
    name: str
    latitude: float
    longitude: float
    geofence_radius_meters: float
    description: Optional[str] = None
    active: bool
    created_at: str


# ============================================================
# SCADA / SENSOR TELEMETRY SCHEMAS (PHASE 2 TASK 9)
# ============================================================

class TelemetryIngestionItem(BaseModel):
    sensor_id: Optional[str] = None
    sensor_code: Optional[str] = None
    mine_id: str
    zone_id: Optional[str] = None
    sensor_type: str
    value: float
    unit: str
    recorded_at: Optional[str] = None
    quality_status: Optional[str] = "GOOD"
    quality: Optional[str] = None
    source: Optional[str] = "SCADA_SIMULATOR"
    simulated: bool = True


class TelemetryBatchRequest(BaseModel):
    readings: list[TelemetryIngestionItem]
    source: Optional[str] = "SCADA_SIMULATOR"
    simulated: bool = True


class TelemetryIngestionResponse(BaseModel):
    success: bool
    ingested_count: int
    evaluated_signals_count: int
    critical_signals_count: int
    new_cases_created: int
    server_timestamp: str
    readings: list[dict] = Field(default_factory=list)


class SensorResponse(BaseModel):
    sensor_id: str
    mine_id: str
    zone_id: Optional[str] = None
    sensor_code: str
    sensor_type: str
    unit: str
    display_name: str
    status: str
    simulated: bool
    created_at: str


class TelemetryReadingResponse(BaseModel):
    reading_id: str
    sensor_id: str
    mine_id: str
    zone_id: Optional[str] = None
    sensor_type: str
    value: float
    unit: str
    recorded_at: str
    received_at: str
    quality_status: str
    threshold_status: str
    source: str
    simulated: bool
    display_name: Optional[str] = None
    sensor_code: Optional[str] = None


class SafetySignalResponse(BaseModel):
    signal_id: str
    mine_id: str
    sensor_id: str
    sensor_type: str
    severity: str
    status: str
    observed_value: float
    unit: str
    threshold_definition: str
    explanation: str
    first_detected_at: str
    last_detected_at: str
    recovered_at: Optional[str] = None
    consecutive_readings: int
    linked_case_id: Optional[str] = None
    evidence_id: Optional[str] = None
    simulated: bool
    display_name: Optional[str] = None
    sensor_code: Optional[str] = None


class TelemetryHealthResponse(BaseModel):
    source: str
    total_sensors_configured: int
    total_readings_stored: int
    sensors_reporting_live: int
    active_safety_signals: int
    last_telemetry_timestamp: Optional[str] = None
    status: str


# ============================================================
# PRODUCTION & OPERATIONAL GOVERNANCE SCHEMAS (PHASE 2 TASK 10)
# ============================================================

class ProductionRecordCreate(BaseModel):
    mine_id: str
    shift_name: str
    production_date: str
    production_quantity: float
    production_unit: str = "TONNES"
    dispatch_quantity: Optional[float] = None
    production_source: str = "SHIFT_REPORT"
    operation_type: str = "UNDERGROUND_EXTRACTION"
    zone_id: Optional[str] = None
    district_section: Optional[str] = None
    face_panel: Optional[str] = None
    overburden_quantity: Optional[float] = None
    overburden_unit: Optional[str] = None
    contractor_id: Optional[str] = None
    contractor_name: Optional[str] = None
    contract_type: Optional[str] = None
    target_quantity: Optional[float] = None
    downtime_minutes: int = 0
    delay_reason: Optional[str] = None
    hemm_context: Optional[str] = None
    entered_by: str = "SYSTEM"
    source_reference: Optional[str] = None
    simulated: bool = False
    notes: Optional[str] = None


class ProductionRecordCorrectionRequest(BaseModel):
    corrected_quantity: float
    corrected_dispatch: Optional[float] = None
    reason: str
    corrected_by: str
    notes: Optional[str] = None


class ProductionRecordResponse(BaseModel):
    record_id: str
    mine_id: str
    mine_name: Optional[str] = None
    area_id: Optional[str] = None
    subsidiary_id: Optional[str] = None
    shift_name: str
    production_date: str
    production_quantity: float
    production_unit: str
    dispatch_quantity: Optional[float] = None
    production_source: str
    operation_type: str
    zone_id: Optional[str] = None
    district_section: Optional[str] = None
    face_panel: Optional[str] = None
    overburden_quantity: Optional[float] = None
    overburden_unit: Optional[str] = None
    contractor_id: Optional[str] = None
    contractor_name: Optional[str] = None
    contract_type: Optional[str] = None
    target_quantity: Optional[float] = None
    downtime_minutes: int
    delay_reason: Optional[str] = None
    hemm_context: Optional[str] = None
    entered_by: str
    source_reference: Optional[str] = None
    status: str
    is_superseded: bool
    superseded_by: Optional[str] = None
    correction_reason: Optional[str] = None
    content_hash: Optional[str] = None
    simulated: bool
    notes: Optional[str] = None
    recorded_at: str
    created_at: str


class ProductionTargetCreate(BaseModel):
    mine_id: str
    target_date: str
    daily_target_tonnes: float
    monthly_target_tonnes: Optional[float] = None
    dispatch_target_tonnes: Optional[float] = None
    set_by: str = "CORPORATE_PLANNING"


class ProductionTargetResponse(BaseModel):
    target_id: str
    mine_id: str
    target_date: str
    daily_target_tonnes: float
    monthly_target_tonnes: Optional[float] = None
    dispatch_target_tonnes: Optional[float] = None
    set_by: str
    created_at: str


class ProductionAnomalyResponse(BaseModel):
    anomaly_id: str
    mine_id: str
    mine_name: Optional[str] = None
    anomaly_type: str
    severity: str
    what: str
    why: str
    source: str
    time: str
    affected_record_ids: list[str] = Field(default_factory=list)
    recommended_review: str
    resolved: bool = False


class ShiftProductionItem(BaseModel):
    shift_name: str
    production_tonnes: float
    dispatch_tonnes: float
    target_tonnes: Optional[float] = None
    downtime_minutes: int
    records_count: int
    sources: list[str] = Field(default_factory=list)
    delays: list[str] = Field(default_factory=list)


class ContractorProductionItem(BaseModel):
    contractor_id: Optional[str] = None
    contractor_name: str
    contract_type: str
    production_tonnes: float
    percentage_share: float


class MineProductionSummaryResponse(BaseModel):
    mine_id: str
    mine_name: str
    subsidiary: str
    area_name: str
    mine_type: str
    date: str
    production_actual_tonnes: float
    production_target_tonnes: Optional[float] = None
    target_status: str  # "CONFIGURED" or "TARGET_NOT_CONFIGURED"
    variance_tonnes: Optional[float] = None
    achievement_percentage: Optional[float] = None
    dispatch_actual_tonnes: float
    dispatch_variance_tonnes: Optional[float] = None
    overburden_actual_bcm: Optional[float] = None
    total_downtime_minutes: int
    shifts: list[ShiftProductionItem] = Field(default_factory=list)
    contractor_contributions: list[ContractorProductionItem] = Field(default_factory=list)
    hemm_context_summary: Optional[str] = None
    delay_reasons: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    anomalies: list[ProductionAnomalyResponse] = Field(default_factory=list)
    active_safety_stoppage: bool
    safety_context_notes: Optional[str] = None
    compliance_status: str
    simulated: bool


class AreaProductionSummaryResponse(BaseModel):
    area_id: str
    area_name: str
    subsidiary: str
    date: str
    total_production_tonnes: float
    total_target_tonnes: Optional[float] = None
    overall_achievement_percentage: Optional[float] = None
    mines_reporting: int
    total_mines: int
    open_anomalies_count: int
    mines: list[dict] = Field(default_factory=list)


class SubsidiaryProductionSummaryResponse(BaseModel):
    subsidiary_id: str
    subsidiary_name: str
    date: str
    total_production_tonnes: float
    total_target_tonnes: Optional[float] = None
    overall_achievement_percentage: Optional[float] = None
    total_dispatch_tonnes: float
    mines_reporting: int
    total_mines: int
    open_anomalies_count: int
    critical_safety_signals_count: int
    areas: list[dict] = Field(default_factory=list)


class CorporateProductionSummaryResponse(BaseModel):
    organization: str = "Coal India Limited (CIL) Corporate"
    date: str
    pan_india_production_tonnes: float
    pan_india_target_tonnes: Optional[float] = None
    pan_india_achievement_percentage: Optional[float] = None
    total_dispatch_tonnes: float
    subsidiaries_reporting: int
    total_subsidiaries: int
    mines_reporting: int
    total_mines: int
    total_anomalies_count: int
    critical_operational_signals: int
    subsidiaries: list[SubsidiaryProductionSummaryResponse] = Field(default_factory=list)
    environment_notice: str = "DEMONSTRATION GOVERNANCE ENVIRONMENT"


class DailyProductionReportResponse(BaseModel):
    report_id: str
    report_title: str
    mine_id: str
    mine_name: str
    subsidiary: str
    area_name: str
    report_date: str
    generated_at: str
    records_included_count: int
    total_production_tonnes: float
    total_dispatch_tonnes: float
    target_tonnes: Optional[float] = None
    variance_tonnes: Optional[float] = None
    achievement_percentage: Optional[float] = None
    total_downtime_minutes: int
    source_breakdown: dict[str, float] = Field(default_factory=dict)
    shift_breakdown: list[dict] = Field(default_factory=list)
    contractor_breakdown: list[dict] = Field(default_factory=list)
    anomalies_detected: list[dict] = Field(default_factory=list)
    content_hash: str
    integrity_status: str
    blockchain_anchor_ref: Optional[str] = None


# ============================================================
# GOVERNANCE MASTER & ORGANIZATIONAL HIERARCHY (PHASE 2 TASK 11)
# ============================================================

class OrganizationUnitCreate(BaseModel):
    parent_id: Optional[str] = None
    unit_type: str
    code: str
    name: str
    legal_name: Optional[str] = None
    status: str = "ACTIVE"
    state: Optional[str] = None
    district: Optional[str] = None
    headquarters: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    metadata: Optional[str] = None


class OrganizationUnitUpdate(BaseModel):
    parent_id: Optional[str] = None
    name: Optional[str] = None
    legal_name: Optional[str] = None
    status: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    headquarters: Optional[str] = None
    effective_to: Optional[str] = None
    metadata: Optional[str] = None
    reason: str


class OrganizationUnitResponse(BaseModel):
    id: str
    parent_id: Optional[str] = None
    unit_type: str
    code: str
    name: str
    legal_name: Optional[str] = None
    status: str
    state: Optional[str] = None
    district: Optional[str] = None
    headquarters: Optional[str] = None
    effective_from: str
    effective_to: Optional[str] = None
    metadata: Optional[str] = None
    created_at: str
    updated_at: str


class OperationalUnitCreate(BaseModel):
    mine_id: str
    parent_operational_unit_id: Optional[str] = None
    unit_type: str
    code: str
    name: str
    active: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geofence_radius: Optional[float] = None
    metadata: Optional[str] = None


class OperationalUnitResponse(BaseModel):
    id: str
    mine_id: str
    parent_operational_unit_id: Optional[str] = None
    unit_type: str
    code: str
    name: str
    active: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geofence_radius: Optional[float] = None
    metadata: Optional[str] = None
    created_at: str
    updated_at: str


class ContractorMasterCreate(BaseModel):
    legal_name: str
    display_name: str
    registration_reference: Optional[str] = None
    status: str = "ACTIVE"
    contractor_type: str = "WORK_ORDER"


class ContractorMasterResponse(BaseModel):
    id: str
    legal_name: str
    display_name: str
    registration_reference: Optional[str] = None
    status: str
    contractor_type: str
    created_at: str
    updated_at: str


class ContractMasterCreate(BaseModel):
    contractor_id: str
    mine_id: str
    contract_type: str
    contract_number: str
    scope: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    workforce_limit: Optional[int] = None
    status: str = "ACTIVE"


class ContractMasterResponse(BaseModel):
    id: str
    contractor_id: str
    contractor_name: Optional[str] = None
    mine_id: str
    mine_name: Optional[str] = None
    area_id: Optional[str] = None
    subsidiary_id: Optional[str] = None
    contract_type: str
    contract_number: str
    scope: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    workforce_limit: Optional[int] = None
    status: str
    created_at: str
    updated_at: str


class WorkerMasterCreate(BaseModel):
    worker_code: str
    name: str
    worker_type: str = "DEPARTMENTAL"
    contractor_id: Optional[str] = None
    contract_id: Optional[str] = None
    mine_id: str
    skill_category: Optional[str] = None
    department: Optional[str] = None
    active: bool = True
    onboarding_date: Optional[str] = None
    training_status: str = "VALID"
    identity_reference: Optional[str] = None


class WorkerMasterResponse(BaseModel):
    id: str
    worker_code: str
    name: str
    worker_type: str
    contractor_id: Optional[str] = None
    contractor_name: Optional[str] = None
    contract_id: Optional[str] = None
    contract_number: Optional[str] = None
    mine_id: str
    mine_name: Optional[str] = None
    skill_category: Optional[str] = None
    department: Optional[str] = None
    active: bool
    onboarding_date: str
    training_status: str
    identity_reference: Optional[str] = None
    created_at: str
    updated_at: str


class WorkerLineageResponse(BaseModel):
    worker_id: str
    worker_code: str
    worker_name: str
    worker_type: str
    contract: Optional[dict] = None
    contractor: Optional[dict] = None
    mine: dict
    area: dict
    subsidiary: dict
    holding_company: dict
    ministry: dict


class HierarchyTreeNode(BaseModel):
    id: str
    parent_id: Optional[str] = None
    unit_type: str
    code: str
    name: str
    legal_name: Optional[str] = None
    status: str
    state: Optional[str] = None
    district: Optional[str] = None
    headquarters: Optional[str] = None
    mine_profile: Optional[dict] = None
    children: list["HierarchyTreeNode"] = Field(default_factory=list)


class HierarchyPathResponse(BaseModel):
    target_unit_id: str
    target_name: str
    target_type: str
    path: list[dict] = Field(default_factory=list)  # Ordered: [Mine, Area, Subsidiary, CIL, Ministry]


class OrganizationAuditEventResponse(BaseModel):
    event_id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    reason: Optional[str] = None
    timestamp: str


# ============================================================
# ENVIRONMENTAL GOVERNANCE SCHEMAS (PHASE 2 TASK 13)
# ============================================================

class EnvironmentalMeasurementCreate(BaseModel):
    mine_id: str
    parameter_id: str
    value: float
    unit: Optional[str] = None
    operational_unit_id: Optional[str] = None
    measured_at: Optional[str] = None
    source_type: Optional[str] = "MANUAL_ENTRY"
    source_reference: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_reference: Optional[str] = None
    simulated: Optional[bool] = False


class EnvironmentalThresholdCreate(BaseModel):
    parameter_id: str
    mine_type: Optional[str] = "ALL"
    threshold_type: Optional[str] = "MAX_LIMIT"
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    unit: str
    severity: Optional[str] = "HIGH"
    source_reference: Optional[str] = "DEMO / CONFIGURED RULE"
    is_demo_rule: Optional[bool] = True


class EnvironmentalReportGenerateRequest(BaseModel):
    mine_id: str
    period_start: str
    period_end: str
    report_type: Optional[str] = "MONITORING_SUMMARY"





