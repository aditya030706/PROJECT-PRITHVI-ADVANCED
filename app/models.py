"""
Core data models for PRITHVI Feature 1.

PRITHVI is an evidence-backed mine compliance verification system.

Architecture:

Mine
  -> Regulatory Obligation
  -> Inspection Template
  -> Inspection
  -> Measurements / Checklist / Evidence
  -> Verification
  -> Human Decision
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# ENUMS
# ============================================================

class MineType(str, Enum):
    UNDERGROUND_COAL = "underground_coal"
    OPENCAST_COAL = "opencast_coal"
    MIXED = "mixed"


class GassyDegree(str, Enum):
    NON_GASSY = "non_gassy"
    DEGREE_I = "degree_i"
    DEGREE_II = "degree_ii"
    DEGREE_III = "degree_iii"
    NOT_APPLICABLE = "not_applicable"


class InspectionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    REVIEW_REQUIRED = "review_required"
    REINSPECTION_RECOMMENDED = "reinspection_recommended"
    REJECTED = "rejected"
    CLOSED = "closed"


class EvidenceType(str, Enum):
    PHOTO = "photo"
    DOCUMENT = "document"
    VIDEO = "video"
    VOICE = "voice"
    SENSOR = "sensor"
    MANUAL_READING = "manual_reading"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    MINOR_DISCREPANCY = "minor_discrepancy"
    SOURCE_ANOMALY = "source_anomaly"
    VERIFICATION_REQUIRED = "verification_required"
    REINSPECTION_RECOMMENDED = "reinspection_recommended"


class DecisionType(str, Enum):
    ACCEPT = "accept"
    REVIEW = "review"
    REINSPECTION = "reinspection"
    ESCALATE = "escalate"
    VERIFY = "verify"
    RETURN = "return"
    REJECT = "reject"


class CaseSourceType(str, Enum):
    THRESHOLD_VIOLATION = "THRESHOLD_VIOLATION"
    FINDING = "FINDING"
    RECURRING_NON_COMPLIANCE = "RECURRING_NON_COMPLIANCE"
    OVERDUE_INSPECTION = "OVERDUE_INSPECTION"
    REGULATORY_ACTION = "REGULATORY_ACTION"
    SCADA_TELEMETRY = "SCADA_TELEMETRY"
    OPERATIONAL_PRODUCTION = "OPERATIONAL_PRODUCTION"
    ENVIRONMENTAL_VIOLATION = "ENVIRONMENTAL_VIOLATION"
    ENVIRONMENTAL_MONITORING = "ENVIRONMENTAL_MONITORING"


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    CORRECTION_SUBMITTED = "CORRECTION_SUBMITTED"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION"
    CLOSED = "CLOSED"


class ActionPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================
# MINE
# ============================================================

class Mine(BaseModel):
    """
    Master profile of a mine.

    This information is used by the applicability engine to determine
    which regulatory obligations and inspection templates apply.
    """

    mine_id: str
    name: str
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

    # --------------------------------------------------------
    # ADDITIONAL APPLICABILITY CHARACTERISTICS
    # --------------------------------------------------------

    has_ventilating_district: Optional[bool] = None

    electric_energy_in_ventilating_district: Optional[bool] = None

    has_shaft_or_incline: Optional[bool] = None

    has_fire_risk_area: Optional[bool] = None

    has_water_danger: Optional[bool] = None

    active: bool = True
    organization_unit_id: Optional[str] = None


# ============================================================
# REGULATORY SOURCE
# ============================================================

class RegulatorySource(BaseModel):
    """
    Traceability record for the regulatory source behind an obligation.
    """

    source_id: str
    title: str
    regulation_number: Optional[str] = None

    chapter: Optional[str] = None

    description: str

    source_document: Optional[str] = None

    # Human-readable reference to the source location.
    source_reference: Optional[str] = None


# ============================================================
# REGULATORY OBLIGATION
# ============================================================

class RegulatoryObligation(BaseModel):
    """
    A structured compliance requirement derived from a regulatory source.
    """

    obligation_id: str

    regulation: RegulatorySource

    title: str

    requirement_type: str

    requirement: str

    applicability: str

    frequency_or_trigger: Optional[str] = None

    responsible_role: Optional[str] = None

    required_record_or_evidence: Optional[str] = None

    active: bool = True


# ============================================================
# INSPECTION TEMPLATE
# ============================================================

class MeasurementDefinition(BaseModel):
    """
    Defines a measurement expected by an inspection template.
    """

    measurement_id: str

    name: str

    unit: Optional[str] = None

    required: bool = True

    description: Optional[str] = None

    # Regulatory threshold — displayed in InspectionWorkspace when set.
    # Values outside the range trigger the compliance observation indicator.
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    threshold_label: Optional[str] = None

    # Dropdown options for select-type measurements
    options: Optional[list[str]] = None


class ChecklistItem(BaseModel):
    """
    A structured inspection checklist item.
    """

    item_id: str

    question: str

    required: bool = True

    severity_if_failed: Optional[str] = None


class EvidenceRequirement(BaseModel):
    """
    Defines evidence required for an inspection.
    """

    evidence_id: str

    evidence_type: EvidenceType

    name: str

    required: bool = True

    minimum_count: int = 0


class InspectionTemplate(BaseModel):
    """
    Defines how a particular inspection should be performed.
    """

    template_id: str

    name: str

    inspection_family: str

    description: Optional[str] = None

    applicable_mine_types: list[MineType] = Field(default_factory=list)

    regulatory_obligation_ids: list[str] = Field(default_factory=list)

    frequency_or_trigger: Optional[str] = None

    # Human-readable frequency label for the UI card.
    # Example: "Required every shift (3 times/day)"
    frequency_label: Optional[str] = None

    # Responsible role from CMR 2017
    responsible_role: Optional[str] = None

    # Regulation reference — e.g. "Regulation 119"
    regulation_reference: Optional[str] = None

    measurements: list[MeasurementDefinition] = Field(
        default_factory=list
    )

    checklist: list[ChecklistItem] = Field(
        default_factory=list
    )

    evidence_requirements: list[EvidenceRequirement] = Field(
        default_factory=list
    )

    active: bool = True


# ============================================================
# INSPECTION
# ============================================================

class Inspection(BaseModel):
    """
    A real inspection instance performed for a mine.
    """

    inspection_id: str

    mine_id: str

    template_id: str

    obligation_id: Optional[str] = None

    inspector_id: str

    started_at: Optional[datetime] = None

    submitted_at: Optional[datetime] = None

    inspection_date: date

    status: InspectionStatus = InspectionStatus.DRAFT

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    gps_accuracy_m: Optional[float] = None


# ============================================================
# MEASUREMENT
# ============================================================

class Measurement(BaseModel):
    """
    A measurement collected during an inspection.
    """

    measurement_id: str

    inspection_id: str

    measurement_type: str

    value: float

    unit: Optional[str] = None

    source: str = "manual"

    captured_at: Optional[datetime] = None


# ============================================================
# CHECKLIST RESULT
# ============================================================

class ChecklistResult(BaseModel):
    """
    Result of one inspection checklist item.
    """

    result_id: str

    inspection_id: str

    item_id: str

    passed: bool

    observation: Optional[str] = None


# ============================================================
# EVIDENCE
# ============================================================

class Evidence(BaseModel):
    """
    Evidence attached to an inspection.

    For photographs we can later store:
      - SHA-256
      - perceptual hash
      - EXIF timestamp
      - GPS
      - device information
    """

    evidence_id: str

    inspection_id: str

    evidence_type: EvidenceType

    filename: Optional[str] = None

    storage_reference: Optional[str] = None

    captured_at: Optional[datetime] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    sha256: Optional[str] = None

    perceptual_hash: Optional[str] = None

    metadata_verified: bool = False


# ============================================================
# SENSOR
# ============================================================

class Sensor(BaseModel):
    """
    Registered operational sensor.

    Reliability belongs to the source, not merely to the reading.
    """

    sensor_id: str

    mine_id: str

    sensor_type: str

    location_description: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    calibration_status: Optional[str] = None

    last_calibrated_at: Optional[datetime] = None

    reliability_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0
    )

    active: bool = True


# ============================================================
# SENSOR READING
# ============================================================

class SensorReading(BaseModel):
    """
    Individual reading from a registered sensor.

    Unlike the old model, readings are timestamped and tied to
    an actual sensor.
    """

    reading_id: str

    sensor_id: str

    mine_id: str

    reading_time: datetime

    measurement_type: str

    value: float

    unit: Optional[str] = None


# ============================================================
# FINDING
# ============================================================

class Finding(BaseModel):
    """
    A problem or observation discovered during an inspection.
    """

    finding_id: str

    inspection_id: str

    title: str

    description: str

    severity: str

    corrective_action_required: bool = False

    status: str = "open"


# ============================================================
# CORRECTIVE ACTION
# ============================================================

class CorrectiveAction(BaseModel):
    action_id: str
    case_id: Optional[str] = None
    finding_id: Optional[str] = None
    mine_id: Optional[str] = None
    title: Optional[str] = None
    description: str
    assigned_role: Optional[str] = None
    assigned_user_id: Optional[str] = None
    assigned_to: Optional[str] = None
    due_at: Optional[str] = None
    due_date: Optional[date] = None
    priority: str = "MEDIUM"
    status: str = "OPEN"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None


# ============================================================
# COMPLIANCE CASE
# ============================================================

class ComplianceCase(BaseModel):
    case_id: str
    mine_id: str
    inspection_id: Optional[str] = None
    finding_id: Optional[str] = None
    category: str
    regulation_reference: Optional[str] = None
    title: str
    description: str
    severity: str
    risk_level: Optional[str] = None
    status: CaseStatus = CaseStatus.OPEN
    source_type: CaseSourceType
    source_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None


# ============================================================
# CASE CORRECTION EVIDENCE
# ============================================================

class CaseCorrectionEvidence(BaseModel):
    evidence_link_id: str
    case_id: str
    action_id: str
    evidence_id: str
    submitted_at: datetime
    submitted_by: str
    notes: Optional[str] = None
    sha256: Optional[str] = None
    ipfs_cid: Optional[str] = None
    audit_proof_status: str = "AUDIT_PROOF_RECORDED"


# ============================================================
# CASE AUDIT EVENT
# ============================================================

class CaseAuditEvent(BaseModel):
    event_id: str
    case_id: str
    action: str
    actor_id: str
    actor_role: Optional[str] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime
    details: Optional[str] = None


# ============================================================
# VERIFICATION SIGNAL
# ============================================================

class VerificationSignal(BaseModel):
    """
    One piece of evidence contributing to verification.

    IMPORTANT:
    A signal is NOT itself a final verdict.
    """

    signal_id: str

    inspection_id: str

    category: str

    name: str

    status: str

    severity: str = "info"

    score: Optional[float] = None

    explanation: str


# ============================================================
# VERIFICATION RESULT
# ============================================================

class VerificationResult(BaseModel):
    """
    Final evidence-fusion result.

    This replaces the old IntegrityScoreResult.

    The result distinguishes:
      - report inconsistency
      - source anomaly
      - insufficient evidence
      - reinspection recommendation

    A single anomalous source must not automatically flag a report.
    """

    verification_id: str

    inspection_id: str

    status: VerificationStatus

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    signals: list[VerificationSignal] = Field(
        default_factory=list
    )

    source_anomalies: list[str] = Field(
        default_factory=list
    )

    evidence_conflicts: list[str] = Field(
        default_factory=list
    )

    recommendation: str

    human_decision_required: bool = False


# ============================================================
# HUMAN REVIEW
# ============================================================

class HumanReview(BaseModel):

    review_id: str

    inspection_id: str

    reviewer_id: str

    decision: DecisionType

    reason: str

    reviewed_at: datetime

# ============================================================
# REGULATORY SCHEDULE
# ============================================================

class ScheduleFrequencyType(str, Enum):
    """
    Defines how a regulatory requirement is scheduled.
    """

    INTERVAL = "interval"
    CALENDAR = "calendar"
    SHIFT = "shift"
    EVENT = "event"
    CONTINUOUS = "continuous"
    CONDITIONAL = "conditional"


class ScheduleUnit(str, Enum):
    """
    Time unit used for interval-based schedules.
    """

    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


class RegulatoryScheduleRule(BaseModel):
    """
    Machine-readable regulatory scheduling rule.

    This represents the regulatory requirement itself.
    It does NOT represent a particular mine's due date.
    """

    schedule_id: str

    obligation_id: str

    template_id: str

    name: str

    frequency_type: ScheduleFrequencyType

    interval_value: Optional[int] = None

    interval_unit: Optional[ScheduleUnit] = None

    trigger_type: Optional[str] = None

    applicable_mine_types: list[MineType] = Field(
        default_factory=list
    )

    applicable_gassy_degrees: list[GassyDegree] = Field(
        default_factory=list
    )

    condition_description: Optional[str] = None

    responsible_role: Optional[str] = None

    # --------------------------------------------------------
    # REGULATORY SOURCE / VERSIONING
    # --------------------------------------------------------

    regulation_reference: Optional[str] = None

    source_document: Optional[str] = None

    source_reference: Optional[str] = None

    source_date: Optional[datetime] = None

    effective_from: Optional[datetime] = None

    effective_to: Optional[datetime] = None

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    validation_status: str = "REQUIRES_VALIDATION"

    active: bool = True
# ============================================================
# MINE SCHEDULE INSTANCE
# ============================================================

class MineInspectionSchedule(BaseModel):
    """
    A mine-specific instance of a regulatory schedule.

    This is where PRITHVI stores:
      - when the inspection was last completed
      - when it is next due
      - whether it is overdue
    """

    schedule_instance_id: str

    mine_id: str

    schedule_id: str

    last_completed_at: Optional[datetime] = None

    next_due_at: Optional[datetime] = None

    status: str = "upcoming"

    generated_at: datetime

    active: bool = True    

# ============================================================
# EVIDENCE INTEGRITY (PHASE 2 TASK 7)
# ============================================================

class IntegrityStatus(str, Enum):
    PENDING = "PENDING"
    ANCHORED = "ANCHORED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class AnchorMode(str, Enum):
    DEMO_AUDIT_MODE = "DEMO_AUDIT_MODE"
    LIVE_BLOCKCHAIN = "LIVE_BLOCKCHAIN"


class IPFSStatus(str, Enum):
    PENDING = "PENDING"
    STORED = "STORED"
    IPFS_NOT_CONFIGURED = "IPFS_NOT_CONFIGURED"
    FAILED = "FAILED"


class EvidenceIntegrityRecord(BaseModel):
    integrity_id: str
    evidence_id: str
    content_hash: str
    hash_algorithm: str = "SHA-256"
    ipfs_cid: Optional[str] = None
    ipfs_status: IPFSStatus = IPFSStatus.PENDING
    blockchain_network: Optional[str] = None
    transaction_ref: Optional[str] = None
    block_ref: Optional[str] = None
    anchored_at: Optional[datetime] = None
    anchor_mode: AnchorMode = AnchorMode.DEMO_AUDIT_MODE
    status: IntegrityStatus = IntegrityStatus.PENDING
    verified_at: Optional[datetime] = None
    verification_result: Optional[str] = None
    created_at: datetime


# ============================================================
# GIS ATTENDANCE (PHASE 2 TASK 8)
# ============================================================

class GeofenceStatus(str, Enum):
    INSIDE_GEOFENCE = "INSIDE_GEOFENCE"
    OUTSIDE_GEOFENCE = "OUTSIDE_GEOFENCE"
    LOCATION_UNAVAILABLE = "LOCATION_UNAVAILABLE"
    LOW_ACCURACY = "LOW_ACCURACY"


class AttendanceStatus(str, Enum):
    VALID = "VALID"
    OUTSIDE_GEOFENCE = "OUTSIDE_GEOFENCE"
    LOCATION_UNAVAILABLE = "LOCATION_UNAVAILABLE"
    LOW_LOCATION_ACCURACY = "LOW_LOCATION_ACCURACY"
    DUPLICATE_CHECK_IN = "DUPLICATE_CHECK_IN"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"


class AnomalyStatus(str, Enum):
    NONE = "NONE"
    DUPLICATE_CHECK_IN = "DUPLICATE_CHECK_IN"
    OUTSIDE_GEOFENCE_ANOMALY = "OUTSIDE_GEOFENCE_ANOMALY"
    LOW_LOCATION_ACCURACY = "LOW_LOCATION_ACCURACY"
    LOCATION_UNAVAILABLE = "LOCATION_UNAVAILABLE"
    OUTSIDE_ASSIGNED_MINE = "OUTSIDE_ASSIGNED_MINE"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"


class MineZone(BaseModel):
    """A named geographic zone within or associated with a mine."""
    mine_zone_id: str
    mine_id: str
    name: str
    latitude: float
    longitude: float
    geofence_radius_meters: float = 500.0
    description: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None


class AttendanceRecord(BaseModel):
    """GPS-derived field attendance record with server-side geofence validation."""
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
    captured_at: Optional[datetime] = None
    server_recorded_at: datetime
    geofence_status: GeofenceStatus
    distance_from_reference_meters: Optional[float] = None
    status: AttendanceStatus
    anomaly_status: AnomalyStatus = AnomalyStatus.NONE
    evidence_id: Optional[str] = None
    device_info: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# ============================================================
# SCADA / SENSOR TELEMETRY (PHASE 2 TASK 9)
# ============================================================

class SensorType(str, Enum):
    METHANE = "METHANE"
    AIRFLOW = "AIRFLOW"
    VENTILATION_FAN = "VENTILATION_FAN"
    DUST = "DUST"
    SLOPE_DISPLACEMENT = "SLOPE_DISPLACEMENT"
    PORE_PRESSURE = "PORE_PRESSURE"
    RAINFALL = "RAINFALL"


class ThresholdStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class QualityStatus(str, Enum):
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    BAD = "BAD"


class SignalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RECOVERED = "RECOVERED"
    ESCALATED = "ESCALATED"


class SensorDefinition(BaseModel):
    """Registered industrial mine sensor profile (simulated or operational)."""
    sensor_id: str
    mine_id: str
    zone_id: Optional[str] = None
    sensor_code: str
    sensor_type: SensorType
    unit: str
    display_name: str
    status: str = "ACTIVE"
    simulated: bool = True
    created_at: datetime


class TelemetryReading(BaseModel):
    """Structured telemetry reading from SCADA simulator / field sensors."""
    reading_id: str
    sensor_id: str
    mine_id: str
    zone_id: Optional[str] = None
    sensor_type: SensorType
    value: float
    unit: str
    recorded_at: datetime
    received_at: datetime
    quality_status: QualityStatus = QualityStatus.GOOD
    threshold_status: ThresholdStatus
    source: str = "SCADA_SIMULATOR"
    simulated: bool = True
    evidence_id: Optional[str] = None
    created_at: datetime


class SafetySignal(BaseModel):
    """Active or historical explainable safety condition derived from telemetry."""
    signal_id: str
    mine_id: str
    sensor_id: str
    sensor_type: SensorType
    severity: ThresholdStatus
    status: SignalStatus = SignalStatus.ACTIVE
    observed_value: float
    unit: str
    threshold_definition: str
    explanation: str
    first_detected_at: datetime
    last_detected_at: datetime
    recovered_at: Optional[datetime] = None
    consecutive_readings: int = 1
    linked_case_id: Optional[str] = None
    evidence_id: Optional[str] = None
    simulated: bool = True
    created_at: datetime


# ============================================================
# PRODUCTION & OPERATIONAL GOVERNANCE (PHASE 2 TASK 10)
# ============================================================

class ProductionSource(str, Enum):
    WEIGHBRIDGE = "WEIGHBRIDGE"
    CHP = "CHP"
    SURVEYOR = "SURVEYOR"
    SHIFT_REPORT = "SHIFT_REPORT"
    MANUAL_ENTRY = "MANUAL_ENTRY"
    API = "API"
    FILE_IMPORT = "FILE_IMPORT"
    SIMULATED_SOURCE = "SIMULATED_SOURCE"


class ContractType(str, Enum):
    DEPARTMENTAL = "DEPARTMENTAL"
    WORK_ORDER = "WORK_ORDER"
    MDO = "MDO"


class ProductionOperationType(str, Enum):
    OPENCAST_MINING = "OPENCAST_MINING"
    UNDERGROUND_EXTRACTION = "UNDERGROUND_EXTRACTION"


class ProductionRecordStatus(str, Enum):
    RECORDED = "RECORDED"
    VERIFIED = "VERIFIED"
    SUPERSEDED = "SUPERSEDED"


class ProductionRecord(BaseModel):
    """
    Persistent operational production event record.
    Used across hierarchy levels (Mine -> Area -> Subsidiary -> CIL Corporate).
    """
    record_id: str
    mine_id: str
    area_id: Optional[str] = None
    subsidiary_id: Optional[str] = None
    shift_name: str
    production_date: str
    production_quantity: float
    production_unit: str = "TONNES"
    dispatch_quantity: Optional[float] = None
    production_source: ProductionSource
    operation_type: ProductionOperationType
    zone_id: Optional[str] = None
    district_section: Optional[str] = None
    face_panel: Optional[str] = None
    overburden_quantity: Optional[float] = None
    overburden_unit: Optional[str] = None
    contractor_id: Optional[str] = None
    contractor_name: Optional[str] = None
    contract_type: Optional[ContractType] = None
    target_quantity: Optional[float] = None
    downtime_minutes: int = 0
    delay_reason: Optional[str] = None
    hemm_context: Optional[str] = None
    entered_by: str
    source_reference: Optional[str] = None
    status: ProductionRecordStatus = ProductionRecordStatus.RECORDED
    is_superseded: bool = False
    superseded_by: Optional[str] = None
    correction_reason: Optional[str] = None
    content_hash: Optional[str] = None
    simulated: bool = False
    notes: Optional[str] = None
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime


class ProductionTarget(BaseModel):
    """
    Configured statutory production targets for a mine.
    """
    target_id: str
    mine_id: str
    target_date: str
    daily_target_tonnes: float
    monthly_target_tonnes: Optional[float] = None
    dispatch_target_tonnes: Optional[float] = None
    set_by: str
    created_at: datetime


class ProductionAnomaly(BaseModel):
    """
    Explainable operational production anomaly signal.
    """
    anomaly_id: str
    mine_id: str
    anomaly_type: str
    severity: str
    what: str
    why: str
    source: str
    time: datetime
    affected_record_ids: list[str] = Field(default_factory=list)
    recommended_review: str
    resolved: bool = False


# ============================================================
# GOVERNANCE MASTER & ORGANIZATIONAL HIERARCHY (PHASE 2 TASK 11)
# ============================================================

class OrganizationUnitType(str, Enum):
    MINISTRY = "MINISTRY"
    CIL = "CIL"
    SUBSIDIARY = "SUBSIDIARY"
    AREA = "AREA"
    MINE = "MINE"


class OperationalUnitType(str, Enum):
    # Opencast operational units
    PIT = "PIT"
    BENCH = "BENCH"
    HAUL_ROAD = "HAUL_ROAD"
    DUMP_STOCK = "DUMP_STOCK"
    HEMM_PARK = "HEMM_PARK"
    # Underground operational units
    SHAFT_INCLINE = "SHAFT_INCLINE"
    VENTILATION_DISTRICT = "VENTILATION_DISTRICT"
    PANEL = "PANEL"
    SECTION = "SECTION"
    WORKING_FACE = "WORKING_FACE"


class ContractorType(str, Enum):
    DEPARTMENTAL = "DEPARTMENTAL"
    WORK_ORDER = "WORK_ORDER"
    MDO = "MDO"
    SERVICE = "SERVICE"


class WorkerType(str, Enum):
    DEPARTMENTAL = "DEPARTMENTAL"
    CONTRACTOR = "CONTRACTOR"
    MDO = "MDO"
    OTHER = "OTHER"


class OrganizationUnit(BaseModel):
    """
    Canonical recursive organization unit node.
    Hierarchy: MINISTRY -> CIL -> SUBSIDIARY/ENTITY -> AREA -> MINE
    """
    id: str
    parent_id: Optional[str] = None
    unit_type: OrganizationUnitType
    code: str
    name: str
    legal_name: Optional[str] = None
    status: str = "ACTIVE"
    state: Optional[str] = None
    district: Optional[str] = None
    headquarters: Optional[str] = None
    effective_from: str
    effective_to: Optional[str] = None
    metadata: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OperationalUnit(BaseModel):
    """
    Operational unit within a mine.
    Underground: Shaft/Incline -> Ventilation District -> Panel -> Section -> Working Face
    Opencast: Pit -> Bench -> Haul Road / Dump / HEMM Park
    """
    id: str
    mine_id: str
    parent_operational_unit_id: Optional[str] = None
    unit_type: OperationalUnitType
    code: str
    name: str
    active: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geofence_radius: Optional[float] = None
    metadata: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ContractorMaster(BaseModel):
    """
    Contractor entity master record.
    Supports Departmental, Work-Order, MDO, and Service contractors.
    """
    id: str
    legal_name: str
    display_name: str
    registration_reference: Optional[str] = None
    status: str = "ACTIVE"
    contractor_type: ContractorType
    created_at: datetime
    updated_at: datetime


class ContractMaster(BaseModel):
    """
    Contract association linking a Contractor to a Mine, Area, and Subsidiary.
    """
    id: str
    contractor_id: str
    mine_id: str
    area_id: Optional[str] = None
    subsidiary_id: Optional[str] = None
    contract_type: ContractorType
    contract_number: str
    scope: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    workforce_limit: Optional[int] = None
    status: str = "ACTIVE"
    created_at: datetime
    updated_at: datetime


class WorkerMaster(BaseModel):
    """
    Worker identity master (independent from application users).
    Resolves lineage: Worker -> Contract -> Contractor -> Mine -> Area -> Subsidiary -> CIL -> Ministry.
    """
    id: str
    worker_code: str
    name: str
    worker_type: WorkerType
    contractor_id: Optional[str] = None
    contract_id: Optional[str] = None
    mine_id: str
    skill_category: Optional[str] = None
    department: Optional[str] = None
    active: bool = True
    onboarding_date: str
    training_status: str = "VALID"
    identity_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OrganizationAuditEvent(BaseModel):
    """
    Audit ledger tracking organizational hierarchy structural modifications.
    """
    event_id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime


# ============================================================
# ENVIRONMENTAL GOVERNANCE & MONITORING (PHASE 2 TASK 13)
# ============================================================

class EnvironmentalDomain(str, Enum):
    AIR = "AIR"
    WATER = "WATER"
    NOISE = "NOISE"
    VIBRATION = "VIBRATION"
    LAND = "LAND"
    RECLAMATION = "RECLAMATION"
    WASTE = "WASTE"
    OTHER = "OTHER"


class EnvironmentalSourceType(str, Enum):
    FIELD_OBSERVATION = "FIELD_OBSERVATION"
    MANUAL_ENTRY = "MANUAL_ENTRY"
    SENSOR = "SENSOR"
    API = "API"
    FILE_IMPORT = "FILE_IMPORT"
    SIMULATED = "SIMULATED"


class DataQualityStatus(str, Enum):
    VALID = "VALID"
    DATA_QUALITY_ERROR = "DATA_QUALITY_ERROR"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class EnvironmentalParameter(BaseModel):
    """
    Configurable environmental parameter master.
    Defines parameter code, domain, measurement units, and mine-type applicability.
    """
    id: str
    code: str
    name: str
    domain: EnvironmentalDomain
    unit: str
    description: Optional[str] = None
    mine_type_applicability: str = "ALL"  # ALL, UNDERGROUND, OPENCAST
    active: bool = True
    metadata: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EnvironmentalMeasurement(BaseModel):
    """
    Individual environmental measurement or field observation event.
    Traced to Mine, Operational Unit, and verified against thresholds.
    """
    id: str
    mine_id: str
    operational_unit_id: Optional[str] = None
    parameter_id: str
    parameter_code: Optional[str] = None
    parameter_name: Optional[str] = None
    domain: Optional[EnvironmentalDomain] = None
    value: float
    unit: str
    measured_at: datetime
    source_type: EnvironmentalSourceType = EnvironmentalSourceType.MANUAL_ENTRY
    source_reference: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_reference: Optional[str] = None
    entered_by: str = "SYSTEM"
    status: str = "RECORDED"  # RECORDED, VERIFIED, FLAGGED_ANOMALY, SUPERSEDED
    evidence_id: Optional[str] = None
    data_quality_status: DataQualityStatus = DataQualityStatus.VALID
    quality_notes: Optional[str] = None
    simulated: bool = False
    created_at: datetime
    updated_at: datetime


class EnvironmentalThreshold(BaseModel):
    """
    Configurable environmental rule/threshold definition.
    If not from verified statutory sources, labelled explicitly as DEMO / CONFIGURED RULE.
    """
    id: str
    parameter_id: str
    mine_type: str = "ALL"  # ALL, UNDERGROUND, OPENCAST
    threshold_type: str = "MAX_LIMIT"  # MAX_LIMIT, MIN_LIMIT, RANGE, BENCHMARK
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    unit: str
    applicable_from: Optional[str] = None
    applicable_to: Optional[str] = None
    severity: str = "HIGH"  # LOW, MEDIUM, HIGH, CRITICAL
    source_reference: str = "DEMO / CONFIGURED RULE"
    is_demo_rule: bool = True
    active: bool = True
    created_at: Optional[datetime] = None


class EnvironmentalObligation(BaseModel):
    """
    Environmental statutory or clearance obligation (Consent to Operate, EC conditions, etc.).
    """
    obligation_id: str
    mine_id: str
    code: str
    title: str
    description: str
    domain: EnvironmentalDomain
    applicable_mine_type: str = "ALL"
    frequency: str = "MONTHLY"
    responsible_role: str = "ENVIRONMENTAL_OFFICER"
    regulatory_source: str = "MoEFCC / CPCB Statutory Framework"
    evidence_requirements: Optional[str] = None
    active: bool = True
    start_date: str
    end_date: Optional[str] = None
    created_at: Optional[datetime] = None


class EnvironmentalSchedule(BaseModel):
    """
    Scheduled environmental monitoring instance.
    """
    schedule_id: str
    obligation_id: str
    mine_id: str
    parameter_id: Optional[str] = None
    operational_unit_id: Optional[str] = None
    domain: EnvironmentalDomain
    due_date: str
    responsible_role: str = "ENVIRONMENTAL_OFFICER"
    status: str = "SCHEDULED"  # SCHEDULED, DUE, OVERDUE, SUBMITTED, VERIFICATION_REQUIRED, VERIFIED, NON_COMPLIANT
    completed_at: Optional[str] = None
    measurement_id: Optional[str] = None
    created_at: Optional[datetime] = None


class EnvironmentalReport(BaseModel):
    """
    Formal environmental regulatory governance report with cryptographic traceability.
    """
    report_id: str
    mine_id: str
    reporting_period_start: str
    reporting_period_end: str
    title: str
    report_type: str = "MONITORING_SUMMARY"
    status: str = "GENERATED"  # DRAFT, GENERATED, REVIEW_REQUIRED, FINALIZED
    summary: Optional[str] = None
    measurements_count: int = 0
    violations_count: int = 0
    open_cases_count: int = 0
    corrective_actions_count: int = 0
    lineage_snapshot: Optional[str] = None
    source_record_hashes: Optional[str] = None
    content_hash: Optional[str] = None
    ipfs_cid: Optional[str] = None
    generated_by: str = "SYSTEM"
    generated_at: datetime
    finalized_at: Optional[datetime] = None
    finalized_by: Optional[str] = None





