"""
PRITHVI — Mine Compliance Intelligence API
===========================================

Feature 1:
Regulatory applicability + structured mine inspection +
evidence capture + verification + human review.

Run:
    python -m uvicorn app.main:app --reload --port 8000

Docs:
    http://localhost:8000/docs
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile, Header, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import database as db

from .applicability import (
    evaluate_mine,
    build_applicability_response,
)

from .scheduling import (
    refresh_mine_schedule,
    get_mine_schedule,
)

from .verification import verify_inspection

from .models import (
    Mine,
    MineType,
    Inspection,
    Measurement,
    ChecklistResult,
    Evidence,
    HumanReview,
    Finding,
    InspectionStatus,
    OrganizationUnit,
    OrganizationUnitType,
    OperationalUnit,
    OperationalUnitType,
    ContractorMaster,
    ContractorType,
    ContractMaster,
    WorkerMaster,
    WorkerType,
    OrganizationAuditEvent,
    CaseSourceType,
    CaseStatus,
    EnvironmentalDomain,
    EnvironmentalSourceType,
    DataQualityStatus,
    EnvironmentalParameter,
    EnvironmentalMeasurement,
    EnvironmentalThreshold,
    EnvironmentalObligation,
    EnvironmentalSchedule,
    EnvironmentalReport,
)

from .schemas import (
    MineCreate,
    MineResponse,
    InspectionTemplateResponse,
    InspectionCreate,
    InspectionResponse,
    MeasurementCreate,
    MeasurementResponse,
    ChecklistResultCreate,
    ChecklistResultResponse,
    EvidenceCreate,
    EvidenceResponse,
    FindingCreate,
    FindingResponse,
    InspectionSubmission,
    VerificationResultResponse,
    HumanReviewCreate,
    HumanReviewResponse,
    DashboardSummary,
    MineComplianceSummaryResponse,
    MineRiskResponse,
    RecurringComplianceIssue,
    VerificationQueueResponse,
    InspectionVerificationDetailResponse,
    VerifyInspectionRequest,
    ReturnInspectionRequest,
    VerificationActionResponse,
    ComplianceCaseResponse,
    ComplianceCaseDetailResponse,
    CorrectiveActionCreateRequest,
    CorrectiveActionResponse,
    CorrectionSubmitRequest,
    CorrectionSubmitResponse,
    CaseVerificationRequest,
    CaseVerificationResponse,
    CaseReturnRequest,
    CaseReturnResponse,
    EvidenceAnchorRequest,
    EvidenceIntegrityResponse,
    EvidenceVerifyResponse,
    InspectionAuditIntegrityResponse,
    CaseAuditIntegrityResponse,
    ProductionRecordCreate,
    ProductionRecordCorrectionRequest,
    ProductionRecordResponse,
    ProductionTargetCreate,
    ProductionTargetResponse,
    ProductionAnomalyResponse,
    MineProductionSummaryResponse,
    AreaProductionSummaryResponse,
    SubsidiaryProductionSummaryResponse,
    CorporateProductionSummaryResponse,
    DailyProductionReportResponse,
    OrganizationUnitCreate,
    OrganizationUnitUpdate,
    OrganizationUnitResponse,
    OperationalUnitCreate,
    OperationalUnitResponse,
    ContractorMasterCreate,
    ContractorMasterResponse,
    ContractMasterCreate,
    ContractMasterResponse,
    WorkerMasterCreate,
    WorkerMasterResponse,
    WorkerLineageResponse,
    HierarchyTreeNode,
    HierarchyPathResponse,
    OrganizationAuditEventResponse,
    EnvironmentalMeasurementCreate,
    EnvironmentalThresholdCreate,
    EnvironmentalReportGenerateRequest,
)

from .environmental_service import (
    record_environmental_measurement,
    calculate_environmental_risk,
    get_mine_environmental_profile,
    detect_recurring_environmental_violations,
    correlate_contractor_context,
    correlate_production_context,
    generate_environmental_report,
    finalize_environmental_report,
)

from .hierarchy_service import (
    get_hierarchy_tree,
    get_hierarchy_path,
    detect_circular_hierarchy,
    validate_parent_child,
    validate_operational_unit_compatibility,
    assert_hierarchy_access,
    resolve_mine_hierarchy,
    resolve_worker_hierarchy,
    resolve_operational_unit_hierarchy,
    resolve_contract_hierarchy,
)

from .production_service import (
    record_production_event,
    get_mine_production_summary,
    get_area_production_summary,
    get_subsidiary_production_summary,
    get_corporate_production_summary,
    generate_daily_production_report,
)

from .case_service import (
    sync_mine_compliance_cases,
    get_case_traceability,
    get_case_detail,
    create_corrective_action,
    submit_action_correction,
    verify_case_closure,
    return_case_for_correction,
)
from .compliance import get_mine_compliance_summary
from .risk import get_mine_risk_intelligence, get_mine_recurring_issues
from .verification_workflow import (
    get_mine_verification_queue,
    get_inspection_verification_dossier,
    execute_verify_inspection,
    execute_return_inspection,
)

from .integrity_service import (
    anchor_evidence as anchor_evidence_item,
    verify_evidence_integrity as verify_evidence_item,
    get_evidence_integrity as get_evidence_integrity_record,
    get_inspection_audit_integrity,
    get_case_audit_integrity,
)

from .blockchain_service import get_blockchain_status
from .ipfs_service import get_ipfs_status


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="PRITHVI — Mine Compliance Intelligence",
    description=(
        "Regulatory applicability, structured mine inspections, "
        "evidence capture, verification and human review."
    ),
    version="1.0.0",
)


# ============================================================
# CORS — REACT FRONTEND
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def on_startup() -> None:
    """
    Initialise the PRITHVI database and seed regulatory data.
    """

    db.init_db()

    try:
        from .seed_data import seed_initial_data

        seed_initial_data()

    except ImportError:
        # Seed module may not exist yet.
        # The API itself should still start.
        pass


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "prithvi",
        "version": "1.0.0",
    }


# ============================================================
# MINE MANAGEMENT
# ============================================================

@app.post(
    "/api/mines",
    response_model=MineResponse,
    status_code=201,
)
def create_mine(
    payload: MineCreate,
) -> MineResponse:
    """
    Register a mine profile.

    Mine characteristics are subsequently used by the
    regulatory applicability engine.
    """

    existing = db.get_mine(
        payload.mine_id
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A mine with this mine_id already exists.",
        )

    mine = Mine(
        mine_id=payload.mine_id,
        name=payload.name,
        subsidiary=payload.subsidiary,
        state=payload.state,
        district=payload.district,
        mine_type=payload.mine_type,
        mining_method=payload.mining_method,
        gassy_degree=payload.gassy_degree,
        mechanised=payload.mechanised,
        uses_hemm=payload.uses_hemm,
        has_winding_installation=(
            payload.has_winding_installation
        ),
        blasting_operation=(
            payload.blasting_operation
        ),
        active=True,
    )

    db.save_mine(mine)

    return _mine_response(mine)


@app.get(
    "/api/mines",
    response_model=list[MineResponse],
)
def list_mines() -> list[MineResponse]:
    """
    Return all registered mines.
    """

    mines = db.list_mines()

    return [
        _mine_response(mine)
        for mine in mines
    ]


@app.get(
    "/api/mines/{mine_id}",
    response_model=MineResponse,
)
def get_mine(
    mine_id: str,
) -> MineResponse:
    """
    Return one mine.
    """

    mine = db.get_mine(
        mine_id
    )

    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )

    return _mine_response(mine)


# ============================================================
# MINE INSPECTION SCHEDULE
# ============================================================

@app.get(
    "/api/mines/{mine_id}/schedule",
)
def get_mine_schedule_api(mine_id: str) -> dict:
    """
    Refresh and return the active inspection schedule for one mine.
    """

    mine = db.get_mine(mine_id)

    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )

    try:
        refresh_mine_schedule(mine_id)
        schedules = get_mine_schedule(mine_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return {
        "mine_id": mine_id,
        "schedules": [
            schedule
            for schedule in schedules
            if bool(schedule.get("active"))
        ],
    }


# ============================================================
# REGULATORY APPLICABILITY
# ============================================================

@app.get(
    "/api/mines/{mine_id}/applicability",
)
def get_mine_applicability(
    mine_id: str,
) -> dict:
    """
    Determine which regulatory inspection workflows
    apply to a mine.

    Applicability is deterministic and explainable.
    """

    mine = db.get_mine(
        mine_id
    )

    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )

    results = evaluate_mine(
        mine
    )

    return build_applicability_response(
        mine,
        results,
    )


# ============================================================
# MINE COMPLIANCE INTELLIGENCE (PHASE 2)
# ============================================================

@app.get(
    "/api/mines/{mine_id}/compliance-summary",
    response_model=MineComplianceSummaryResponse,
)
def get_mine_compliance_summary_endpoint(
    mine_id: str,
) -> MineComplianceSummaryResponse:
    """
    Return comprehensive, real-time statutory compliance intelligence for a mine.

    Derives from real database records:
    - total applicable inspections (e.g. 13 for Jharia)
    - due today, overdue, upcoming
    - submitted, verified, review required
    - open findings, threshold violations
    - category-level compliance for all 7 Phase 1 categories
    - prioritized actionable attention items
    """
    mine = db.get_mine(mine_id)
    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )

    summary = get_mine_compliance_summary(mine_id)
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail="Unable to derive compliance summary for this mine.",
        )

    return MineComplianceSummaryResponse(**summary)
 
 
@app.get(
    "/api/mines/{mine_id}/risk",
    response_model=MineRiskResponse,
)
def get_mine_risk_endpoint(
    mine_id: str,
) -> MineRiskResponse:
    """
    Return comprehensive, deterministic statutory compliance risk intelligence for a mine.
    Calculates overall mine risk and category-level risk posture across all 7 CMR categories.
    """
    mine = db.get_mine(mine_id)
    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )

    risk_data = get_mine_risk_intelligence(mine_id)
    if risk_data is None:
        raise HTTPException(
            status_code=404,
            detail="Unable to derive compliance risk intelligence for this mine.",
        )

    return MineRiskResponse(**risk_data)


@app.get(
    "/api/mines/{mine_id}/recurring-compliance",
    response_model=list[RecurringComplianceIssue],
)
def get_mine_recurring_compliance_endpoint(
    mine_id: str,
) -> list[RecurringComplianceIssue]:
    """
    Return recurring non-compliance patterns detected across historical inspections.
    Only returns issues supported by repeated evidence (occurrences >= 2).
    """
    mine = db.get_mine(mine_id)
    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )

    issues = get_mine_recurring_issues(mine_id)
    return [RecurringComplianceIssue(**issue) for issue in issues]
 
 
# ============================================================
# INSPECTION TEMPLATES
# ============================================================

def _template_response(t: InspectionTemplate) -> InspectionTemplateResponse:
    return InspectionTemplateResponse(
        template_id=t.template_id,
        name=t.name,
        inspection_family=t.inspection_family,
        description=t.description,
        applicable_mine_types=t.applicable_mine_types,
        regulatory_obligation_ids=t.regulatory_obligation_ids,
        frequency_or_trigger=t.frequency_or_trigger,
        frequency_label=t.frequency_label,
        responsible_role=t.responsible_role,
        regulation_reference=t.regulation_reference,
        measurements=[
            {
                "measurement_id": m.measurement_id,
                "name": m.name,
                "unit": m.unit,
                "required": m.required,
                "description": m.description,
                "min_value": m.min_value,
                "max_value": m.max_value,
                "threshold_label": m.threshold_label,
                "options": m.options,
            }
            for m in t.measurements
        ],
        checklist=[
            {
                "item_id": c.item_id,
                "question": c.question,
                "required": c.required,
                "severity_if_failed": c.severity_if_failed,
            }
            for c in t.checklist
        ],
        evidence_requirements=[
            {
                "evidence_id": e.evidence_id,
                "evidence_type": e.evidence_type.value if hasattr(e.evidence_type, "value") else str(e.evidence_type),
                "name": e.name,
                "required": e.required,
                "minimum_count": e.minimum_count,
            }
            for e in t.evidence_requirements
        ],
        active=t.active,
    )


@app.get(
    "/api/inspection-templates",
    response_model=list[InspectionTemplateResponse],
)
def list_inspection_templates() -> list[InspectionTemplateResponse]:
    """
    Return all active inspection templates with measurements, thresholds, and checklists.
    """
    conn = db._connect()
    rows = conn.execute(
        "SELECT template_id FROM inspection_templates WHERE active = 1 ORDER BY rowid"
    ).fetchall()
    conn.close()

    response = []
    for r in rows:
        tmpl = db.get_inspection_template(r["template_id"])
        if tmpl:
            response.append(_template_response(tmpl))
    return response


@app.get(
    "/api/inspection-templates/{template_id}",
    response_model=InspectionTemplateResponse,
)
def get_inspection_template_endpoint(template_id: str) -> InspectionTemplateResponse:
    """
    Retrieve one inspection template by ID.
    """
    tmpl = db.get_inspection_template(template_id)
    if tmpl is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection template not found.",
        )
    return _template_response(tmpl)


@app.get(
    "/api/mines/{mine_id}/templates",
    response_model=list[InspectionTemplateResponse],
)
def get_mine_templates_endpoint(mine_id: str) -> list[InspectionTemplateResponse]:
    """
    Return all statutory inspection templates applicable to this specific mine,
    populated with full measurements, thresholds, checklists, and evidence requirements.
    """
    mine = db.get_mine(mine_id)
    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )
    templates = db.get_templates_for_mine(mine_id)
    return [_template_response(tmpl) for tmpl in templates]


# ============================================================
# START INSPECTION
# ============================================================

@app.post(
    "/api/inspections",
    response_model=InspectionResponse,
    status_code=201,
)
def create_inspection(
    payload: InspectionCreate,
) -> InspectionResponse:
    """
    Start a new inspection.
    """

    mine = db.get_mine(
        payload.mine_id
    )

    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )

    inspection_id = (
        f"INS-"
        f"{payload.inspection_date.strftime('%Y%m%d')}-"
        f"{uuid4().hex[:8].upper()}"
    )

    inspection = Inspection(
        inspection_id=inspection_id,
        mine_id=payload.mine_id,
        template_id=payload.template_id,
        obligation_id=payload.obligation_id,
        inspector_id=payload.inspector_id,
        inspection_date=payload.inspection_date,
        started_at=datetime.now(
            timezone.utc
        ),
        submitted_at=None,
        status=InspectionStatus.DRAFT,
        latitude=payload.latitude,
        longitude=payload.longitude,
        gps_accuracy_m=payload.gps_accuracy_m,
    )

    db.save_inspection(
        inspection
    )

    return _inspection_response(
        inspection
    )


# ============================================================
# GET INSPECTION
# ============================================================

@app.get(
    "/api/inspections/{inspection_id}",
    response_model=InspectionResponse,
)
def get_inspection(
    inspection_id: str,
) -> InspectionResponse:
    """
    Retrieve one inspection.
    """

    inspection = db.get_inspection(
        inspection_id
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    return _inspection_response(
        inspection
    )


# ============================================================
# MINE INSPECTION HISTORY
# ============================================================

@app.get(
    "/api/mines/{mine_id}/inspections",
)
def mine_inspection_history(
    mine_id: str,
) -> dict:
    """
    Return inspection history for a mine.
    """

    mine = db.get_mine(
        mine_id
    )

    if mine is None:
        raise HTTPException(
            status_code=404,
            detail="Mine not found.",
        )

    return {
        "mine_id": mine_id,
        "inspections": (
            db.get_inspections_for_mine(
                mine_id
            )
        ),
    }


# ============================================================
# MEASUREMENTS
# ============================================================

@app.post(
    "/api/inspections/{inspection_id}/measurements",
    response_model=MeasurementResponse,
    status_code=201,
)
def add_measurement(
    inspection_id: str,
    payload: MeasurementCreate,
) -> MeasurementResponse:
    """
    Add one field measurement.
    """

    inspection = db.get_inspection(
        inspection_id
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    if inspection.status != InspectionStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail=(
                "Measurements can only be added "
                "while the inspection is in DRAFT."
            ),
        )

    measurement = Measurement(
        measurement_id=(
            f"MEAS-{uuid4().hex[:12].upper()}"
        ),
        inspection_id=inspection_id,
        measurement_type=(
            payload.measurement_type
        ),
        value=payload.value,
        unit=payload.unit,
        source=payload.source,
        captured_at=(
            payload.captured_at
            or datetime.now(timezone.utc)
        ),
    )

    db.save_measurement(
        measurement
    )

    return MeasurementResponse(
        measurement_id=(
            measurement.measurement_id
        ),
        inspection_id=(
            measurement.inspection_id
        ),
        measurement_type=(
            measurement.measurement_type
        ),
        value=measurement.value,
        unit=measurement.unit,
        source=measurement.source,
        captured_at=measurement.captured_at,
    )


# ============================================================
# CHECKLIST
# ============================================================

@app.post(
    "/api/inspections/{inspection_id}/checklist",
    response_model=ChecklistResultResponse,
    status_code=201,
)
def add_checklist_result(
    inspection_id: str,
    payload: ChecklistResultCreate,
) -> ChecklistResultResponse:
    """
    Record one checklist result.
    """

    inspection = db.get_inspection(
        inspection_id
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    if inspection.status != InspectionStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail=(
                "Checklist results can only be added "
                "while the inspection is in DRAFT."
            ),
        )

    result = ChecklistResult(
        result_id=(
            f"CHK-{uuid4().hex[:12].upper()}"
        ),
        inspection_id=inspection_id,
        item_id=payload.item_id,
        passed=payload.passed,
        observation=payload.observation,
    )

    db.save_checklist_result(
        result
    )

    return ChecklistResultResponse(
        result_id=result.result_id,
        inspection_id=result.inspection_id,
        item_id=result.item_id,
        passed=result.passed,
        observation=result.observation,
    )


# ============================================================
# EVIDENCE
# ============================================================

@app.post(
    "/api/inspections/{inspection_id}/evidence",
    response_model=EvidenceResponse,
    status_code=201,
)
def add_evidence(
    inspection_id: str,
    payload: EvidenceCreate,
) -> EvidenceResponse:
    """
    Register evidence against an inspection.
    """

    inspection = db.get_inspection(
        inspection_id
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    if inspection.status != InspectionStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail=(
                "Evidence can only be added "
                "while the inspection is in DRAFT."
            ),
        )

    evidence = Evidence(
        evidence_id=(
            f"EVD-{uuid4().hex[:12].upper()}"
        ),
        inspection_id=inspection_id,
        evidence_type=payload.evidence_type,
        filename=payload.filename,
        storage_reference=(
            payload.storage_reference
        ),
        captured_at=(
            payload.captured_at
            or datetime.now(timezone.utc)
        ),
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    db.save_evidence(
        evidence
    )

    return EvidenceResponse(
        evidence_id=evidence.evidence_id,
        inspection_id=evidence.inspection_id,
        evidence_type=evidence.evidence_type,
        filename=evidence.filename,
        storage_reference=(
            evidence.storage_reference
        ),
        captured_at=evidence.captured_at,
        latitude=evidence.latitude,
        longitude=evidence.longitude,
        sha256=evidence.sha256,
        perceptual_hash=evidence.perceptual_hash,
        metadata_verified=(
            evidence.metadata_verified
        ),
    )


@app.get(
    "/api/inspections/{inspection_id}/evidence",
    response_model=list[EvidenceResponse],
)
def list_inspection_evidence(
    inspection_id: str,
) -> list[EvidenceResponse]:
    """
    List all evidence records registered for an inspection.
    """
    records = db.get_evidence_for_inspection(inspection_id)
    return [
        EvidenceResponse(
            evidence_id=e.evidence_id,
            inspection_id=e.inspection_id,
            evidence_type=e.evidence_type,
            filename=e.filename,
            storage_reference=e.storage_reference,
            captured_at=e.captured_at,
            latitude=e.latitude,
            longitude=e.longitude,
            sha256=e.sha256,
            perceptual_hash=e.perceptual_hash,
            metadata_verified=e.metadata_verified,
        )
        for e in records
    ]


# ============================================================
# UPLOAD DOCUMENT EVIDENCE
# ============================================================
# Stores the physical file to DOCUMENT_ROOT/{inspection_id}/
# then registers it as an evidence record.  The existing
# verify_inspection() engine resolves files from that path.
# ============================================================

_DEMO_DIR = (
    Path(__file__).resolve().parent
    / "data"
    / "documents"
    / "demo"
)


from .document_ai import DOCUMENT_ROOT, sha256_file


@app.post(
    "/api/inspections/{inspection_id}/upload-evidence",
    status_code=201,
)
async def upload_evidence(
    inspection_id: str,
    file: UploadFile = File(...),
) -> dict:
    """
    Upload a PDF document as evidence for an inspection.

    Stores the physical file to
        DOCUMENT_ROOT/{inspection_id}/{filename}
    then registers an Evidence record so the existing
    verify_inspection() document-AI chain can process it.
    """

    inspection = db.get_inspection(inspection_id)

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    if inspection.status != InspectionStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail="Evidence can only be added while the inspection is in DRAFT.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File must have a filename.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=422,
            detail="Only PDF documents are accepted as document evidence.",
        )

    # --------------------------------------------------------
    # Store the file
    # --------------------------------------------------------

    dest_dir = DOCUMENT_ROOT / inspection_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / file.filename

    content = await file.read()

    with dest_path.open("wb") as fh:
        fh.write(content)

    # --------------------------------------------------------
    # SHA-256
    # --------------------------------------------------------

    file_hash = sha256_file(dest_path)

    relative_ref = str(
        dest_path.relative_to(DOCUMENT_ROOT)
    )

    # --------------------------------------------------------
    # Evidence DB record
    # --------------------------------------------------------

    evidence = Evidence(
        evidence_id=(
            f"EVD-{uuid4().hex[:12].upper()}"
        ),
        inspection_id=inspection_id,
        evidence_type="document",
        filename=file.filename,
        storage_reference=relative_ref,
        captured_at=datetime.now(timezone.utc),
        latitude=None,
        longitude=None,
    )

    # Persist hash before saving so it is available to the
    # verification engine without needing to re-hash.
    evidence.sha256 = file_hash

    db.save_evidence(evidence)

    return {
        "evidence_id": evidence.evidence_id,
        "inspection_id": inspection_id,
        "evidence_type": "document",
        "filename": file.filename,
        "storage_reference": relative_ref,
        "sha256": file_hash,
        "captured_at": str(evidence.captured_at),
    }


# ============================================================
# DEMO DOCUMENT LIBRARY
# ============================================================

@app.get("/api/demo-documents")
def list_demo_documents() -> list[dict]:
    """
    Return the available synthetic demonstration PDF documents.
    """

    if not _DEMO_DIR.exists():
        return []

    return [
        {
            "filename": f.name,
            "size_bytes": f.stat().st_size,
            "mine_hint": (
                "MINE-BCCL-JHARIA-01"
                if "jharia" in f.name.lower()
                else (
                    "MINE-ECL-RANIGANJ-01"
                    if "raniganj" in f.name.lower()
                    else (
                        "MINE-MCL-TALCHER-01"
                        if "talcher" in f.name.lower()
                        else None
                    )
                )
            ),
        }
        for f in sorted(_DEMO_DIR.iterdir())
        if f.suffix.lower() == ".pdf"
    ]


@app.post(
    "/api/inspections/{inspection_id}/attach-demo",
    status_code=201,
)
async def attach_demo_document(
    inspection_id: str,
    payload: dict,
) -> dict:
    """
    Copy a demo-library PDF into an inspection's document store
    and register it as evidence.  Identical physical-file and
    evidence-DB flow as upload-evidence — the existing
    verify_inspection() document chain treats it identically.
    """

    filename = payload.get("filename", "")

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="filename is required.",
        )

    src = _DEMO_DIR / filename

    if not src.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Demo document '{filename}' not found in demo library.",
        )

    inspection = db.get_inspection(inspection_id)

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    if inspection.status != InspectionStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail="Evidence can only be added while the inspection is in DRAFT.",
        )

    dest_dir = DOCUMENT_ROOT / inspection_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    import shutil
    shutil.copy2(str(src), str(dest_path))

    file_hash = sha256_file(dest_path)
    relative_ref = str(dest_path.relative_to(DOCUMENT_ROOT))

    evidence = Evidence(
        evidence_id=(
            f"EVD-{uuid4().hex[:12].upper()}"
        ),
        inspection_id=inspection_id,
        evidence_type="document",
        filename=filename,
        storage_reference=relative_ref,
        captured_at=datetime.now(timezone.utc),
        latitude=None,
        longitude=None,
    )

    evidence.sha256 = file_hash

    db.save_evidence(evidence)

    return {
        "evidence_id": evidence.evidence_id,
        "inspection_id": inspection_id,
        "evidence_type": "document",
        "filename": filename,
        "storage_reference": relative_ref,
        "sha256": file_hash,
        "captured_at": str(evidence.captured_at),
    }


# ============================================================
# FINDINGS
# ============================================================

@app.post(
    "/api/inspections/{inspection_id}/findings",
    response_model=FindingResponse,
    status_code=201,
)
def add_finding(
    inspection_id: str,
    payload: FindingCreate,
) -> FindingResponse:
    """
    Record a finding discovered during inspection.
    """

    inspection = db.get_inspection(
        inspection_id
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    if inspection.status != InspectionStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail=(
                "Findings can only be added "
                "while the inspection is in DRAFT."
            ),
        )

    invalid_evidence_ids = db.validate_evidence_for_inspection(
        inspection_id,
        payload.evidence_ids,
    )

    if invalid_evidence_ids:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "One or more evidence IDs do not belong to this inspection.",
                "invalid_evidence_ids": invalid_evidence_ids,
            },
        )

    finding = Finding(
        finding_id=(
            f"FND-{uuid4().hex[:12].upper()}"
        ),
        inspection_id=inspection_id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        corrective_action_required=(
            payload.corrective_action_required
        ),
        status="open",
    )

    db.save_finding(
        finding
    )

    return FindingResponse(
        finding_id=finding.finding_id,
        inspection_id=finding.inspection_id,
        title=finding.title,
        description=finding.description,
        severity=finding.severity,
        corrective_action_required=(
            finding.corrective_action_required
        ),
        evidence_ids=db.get_finding_evidence_ids(
            finding.finding_id
        ),
        status=finding.status,
    )


# ============================================================
# SUBMIT INSPECTION
# ============================================================

@app.post(
    "/api/inspections/{inspection_id}/submit",
)
def submit_inspection(
    inspection_id: str,
    payload: InspectionSubmission,
) -> dict:
    """
    Submit a complete inspection.

    After submission PRITHVI automatically sends the inspection
    to the verification engine.
    """

    inspection = db.get_inspection(
        inspection_id
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    if payload.inspection_id != inspection_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Payload inspection_id does not "
                "match the URL."
            ),
        )

    if inspection.status != InspectionStatus.DRAFT:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only DRAFT inspections can be submitted."
            ),
        )

    # --------------------------------------------------------
    # Measurements
    # --------------------------------------------------------

    for item in payload.measurements:

        measurement = Measurement(
            measurement_id=(
                f"MEAS-{uuid4().hex[:12].upper()}"
            ),
            inspection_id=inspection_id,
            measurement_type=(
                item.measurement_type
            ),
            value=item.value,
            unit=item.unit,
            source=item.source,
            captured_at=(
                item.captured_at
                or datetime.now(timezone.utc)
            ),
        )

        db.save_measurement(
            measurement
        )

    # --------------------------------------------------------
    # Checklist
    # --------------------------------------------------------

    for item in payload.checklist_results:

        checklist = ChecklistResult(
            result_id=(
                f"CHK-{uuid4().hex[:12].upper()}"
            ),
            inspection_id=inspection_id,
            item_id=item.item_id,
            passed=item.passed,
            observation=item.observation,
        )

        db.save_checklist_result(
            checklist
        )

    # --------------------------------------------------------
    # Findings
    # --------------------------------------------------------

    for item in payload.findings:

        finding = Finding(
            finding_id=(
                f"FND-{uuid4().hex[:12].upper()}"
            ),
            inspection_id=inspection_id,
            title=item.title,
            description=item.description,
            severity=item.severity,
            corrective_action_required=(
                item.corrective_action_required
            ),
            status="open",
        )

        invalid_evidence_ids = db.validate_evidence_for_inspection(
            inspection_id,
            item.evidence_ids,
        )

        if invalid_evidence_ids:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "One or more evidence IDs do not belong to this inspection.",
                    "invalid_evidence_ids": invalid_evidence_ids,
                },
            )

        db.save_finding(
            finding
        )

        db.save_finding_evidence(
            finding.finding_id,
            item.evidence_ids,
        )

    # --------------------------------------------------------
    # Mark submitted
    # --------------------------------------------------------

    inspection.status = (
        InspectionStatus.SUBMITTED
    )

    inspection.submitted_at = (
        datetime.now(timezone.utc)
    )

    db.save_inspection(
        inspection
    )

    # --------------------------------------------------------
    # AUTOMATIC VERIFICATION
    # --------------------------------------------------------

    verification = verify_inspection(
        inspection_id
    )

    return {
        "inspection_id": inspection_id,
        "status": inspection.status.value,
        "verification": {
            "verification_id": (
                verification.verification_id
            ),
            "status": (
                verification.status.value
            ),
            "confidence": (
                verification.confidence
            ),
            "human_decision_required": (
                verification.human_decision_required
            ),
            "source_anomalies": (
                verification.source_anomalies
            ),
            "evidence_conflicts": (
                verification.evidence_conflicts
            ),
            "recommendation": (
                verification.recommendation
            ),
            "signals": [
                {
                    "signal_id": s.signal_id,
                    "category": s.category,
                    "name": s.name,
                    "status": s.status,
                    "severity": s.severity,
                    "score": s.score,
                    "explanation": s.explanation,
                }
                for s in verification.signals
            ],
        },
        "observation": payload.observation,
        "message": (
            "Inspection submitted and "
            "verification completed."
        ),
    }


# ============================================================
# PHASE 2 TASK 4: VERIFICATION & REGULATORY REVIEW ENDPOINTS
# ============================================================

@app.get(
    "/api/mines/{mine_id}/verification",
    response_model=VerificationQueueResponse,
)
def get_mine_verification_endpoint(
    mine_id: str,
) -> VerificationQueueResponse:
    """
    Verification Center Queue for a mine.
    Returns real queue counts and prioritized inspections requiring review.
    """
    data = get_mine_verification_queue(mine_id)
    return VerificationQueueResponse(**data)


@app.get(
    "/api/inspections/{inspection_id}/verification",
    response_model=InspectionVerificationDetailResponse,
)
def get_inspection_verification_dossier_endpoint(
    inspection_id: str,
) -> InspectionVerificationDetailResponse:
    """
    Inspection Review Workspace dossier.
    Returns identity, measurements with template threshold metadata,
    checklist, evidence completeness, findings, risk context, and audit history.
    """
    data = get_inspection_verification_dossier(inspection_id)
    return InspectionVerificationDetailResponse(**data)


@app.post(
    "/api/inspections/{inspection_id}/verify",
    response_model=VerificationActionResponse,
)
def verify_inspection_endpoint(
    inspection_id: str,
    payload: Optional[VerifyInspectionRequest] = None,
) -> VerificationActionResponse:
    """
    Reviewer controlled decision: VERIFY inspection.
    Enforces server-side validation on completeness and review state.
    """
    reviewer = payload.reviewer_id if payload else "MGR-JHARIA-01"
    notes = payload.notes if payload else None
    res = execute_verify_inspection(inspection_id, reviewer_id=reviewer, notes=notes)
    return VerificationActionResponse(**res)


@app.post(
    "/api/inspections/{inspection_id}/return",
    response_model=VerificationActionResponse,
)
def return_inspection_endpoint(
    inspection_id: str,
    payload: ReturnInspectionRequest,
) -> VerificationActionResponse:
    """
    Reviewer controlled decision: REJECT / RETURN FOR CORRECTION.
    Requires a non-empty, substantive reason that persists into audit history.
    """
    res = execute_return_inspection(
        inspection_id, reviewer_id=payload.reviewer_id, reason=payload.reason
    )
    return VerificationActionResponse(**res)




# ============================================================
# PENDING VERIFICATIONS
# ============================================================

@app.get(
    "/api/verifications/pending",
)
def pending_verifications() -> list[dict]:
    """
    Return inspections awaiting verification/review.
    """

    return db.list_pending_verifications()


# ============================================================
# GET VERIFICATION
# ============================================================

@app.get(
    "/api/verifications/{inspection_id}",
)
def get_verification(
    inspection_id: str,
) -> dict:
    """
    Retrieve the latest verification result.
    """

    result = db.get_verification(
        inspection_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No verification result exists "
                "for this inspection."
            ),
        )

    return result


# ============================================================
# HUMAN REVIEW
# ============================================================

@app.post(
    "/api/reviews",
    response_model=HumanReviewResponse,
    status_code=201,
)
def create_human_review(
    payload: HumanReviewCreate,
) -> HumanReviewResponse:
    """
    Record a human administrator's decision.

    PRITHVI never converts an automated signal directly
    into a final fraud verdict.
    """

    inspection = db.get_inspection(
        payload.inspection_id
    )

    if inspection is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    review = HumanReview(
        review_id=(
            f"REV-{uuid4().hex[:12].upper()}"
        ),
        inspection_id=(
            payload.inspection_id
        ),
        reviewer_id=payload.reviewer_id,
        decision=payload.decision,
        reason=payload.reason,
        reviewed_at=datetime.now(
            timezone.utc
        ),
    )

    db.save_human_review(
        review
    )

    dec_val = review.decision.value if hasattr(review.decision, "value") else str(review.decision)
    case_id = f"ENF-2026-{review.review_id[4:10]}" if dec_val == "escalate" else None
    case_status = "OPEN" if dec_val == "escalate" else "CLOSED" if dec_val == "accept" else "PENDING_ACTION"
    next_action = (
        "Corrective action / reinspection required" if dec_val == "escalate"
        else "Schedule follow-up statutory inspection" if dec_val == "reinspection"
        else "Inspection closed and archived" if dec_val == "accept"
        else "Retained in review queue"
    )

    updated_inspection = db.get_inspection(payload.inspection_id)
    insp_status = updated_inspection.status.value if updated_inspection else None

    return HumanReviewResponse(
        review_id=review.review_id,
        inspection_id=review.inspection_id,
        reviewer_id=review.reviewer_id,
        decision=review.decision,
        reason=review.reason,
        reviewed_at=review.reviewed_at,
        case_id=case_id,
        status=case_status,
        next_action=next_action,
        inspection_status=insp_status,
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.get(
    "/api/dashboard/summary",
    response_model=DashboardSummary,
)
def dashboard_summary() -> DashboardSummary:
    """
    High-level command-centre statistics.
    """

    return DashboardSummary(
        total_mines=db.count_active_mines(),
        inspections_due=db.count_inspections_due(),
        inspections_submitted=db.count_submitted_inspections(),
        awaiting_verification=db.count_awaiting_verification(),
        verification_required=db.count_verification_required(),
        reinspection_recommended=db.count_reinspection_recommended(),
        source_anomalies=db.count_source_anomalies(),
        open_corrective_actions=db.count_open_corrective_actions(),
    )


# ============================================================
# RESPONSE HELPERS
# ============================================================

def _mine_response(
    mine: Mine,
) -> MineResponse:

    return MineResponse(
        mine_id=mine.mine_id,
        name=mine.name,
        subsidiary=mine.subsidiary,
        state=mine.state,
        district=mine.district,
        mine_type=mine.mine_type,
        mining_method=mine.mining_method,
        gassy_degree=mine.gassy_degree,
        mechanised=mine.mechanised,
        uses_hemm=mine.uses_hemm,
        has_winding_installation=(
            mine.has_winding_installation
        ),
        blasting_operation=(
            mine.blasting_operation
        ),
        active=mine.active,
    )


def _inspection_response(
    inspection: Inspection,
) -> InspectionResponse:

    return InspectionResponse(
        inspection_id=(
            inspection.inspection_id
        ),
        mine_id=inspection.mine_id,
        template_id=inspection.template_id,
        obligation_id=inspection.obligation_id,
        inspector_id=inspection.inspector_id,
        inspection_date=(
            inspection.inspection_date
        ),
        latitude=inspection.latitude,
        longitude=inspection.longitude,
        gps_accuracy_m=(
            inspection.gps_accuracy_m
        ),
        started_at=inspection.started_at,
        submitted_at=inspection.submitted_at,
        status=inspection.status,
    )


def _verification_response(
    result,
) -> VerificationResultResponse:

    return VerificationResultResponse(
        verification_id=(
            result.verification_id
        ),
        inspection_id=(
            result.inspection_id
        ),
        status=result.status,
        confidence=result.confidence,
        signals=[
            {
                "signal_id": signal.signal_id,
                "category": signal.category,
                "name": signal.name,
                "status": signal.status,
                "severity": signal.severity,
                "score": signal.score,
                "explanation": signal.explanation,
            }
            for signal in result.signals
        ],
        source_anomalies=(
            result.source_anomalies
        ),
        evidence_conflicts=(
            result.evidence_conflicts
        ),
        recommendation=(
            result.recommendation
        ),
        human_decision_required=(
            result.human_decision_required
        ),
    )


# ============================================================
# PHASE 2 TASK 6 — COMPLIANCE CASE & CORRECTIVE ACTION ENDPOINTS
# ============================================================

@app.get("/api/cases", response_model=list[ComplianceCaseResponse])
def get_compliance_cases_endpoint(
    mine_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    auto_sync: bool = Query(True),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    List compliance cases with optional filtering.
    If auto_sync is enabled and mine_id is provided, automatically synthesizes cases
    from real database signals (idempotent, no duplicates).
    """
    if auto_sync and mine_id:
        sync_mine_compliance_cases(mine_id)
    elif auto_sync and not mine_id:
        sync_mine_compliance_cases("MINE-BCCL-JHARIA-01")

    cases = db.list_compliance_cases(
        mine_id=mine_id,
        status=status,
        category=category,
        severity=severity,
    )
    return cases


@app.get("/api/cases/metrics/{mine_id}")
def get_case_metrics_endpoint(
    mine_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Retrieve real KPI metrics for the Mine Manager Command Center.
    No mock data or synthetic multipliers.
    """
    sync_mine_compliance_cases(mine_id)
    all_cases = db.list_compliance_cases(mine_id=mine_id)

    conn = db._connect()
    actions = conn.execute(
        "SELECT * FROM corrective_actions WHERE mine_id = ?", (mine_id,)
    ).fetchall()
    conn.close()

    now_iso = datetime.now(timezone.utc).isoformat()
    overdue_actions = sum(
        1 for a in actions
        if a["status"] != "COMPLETED" and a["due_at"] and a["due_at"] < now_iso
    )

    open_cases = sum(1 for c in all_cases if c["status"] in ("OPEN", "ACTION_REQUIRED", "RETURNED_FOR_CORRECTION"))
    action_required = sum(1 for c in all_cases if c["status"] in ("ACTION_REQUIRED", "OPEN"))
    verification_required = sum(1 for c in all_cases if c["status"] == "VERIFICATION_REQUIRED")
    closed_cases = sum(1 for c in all_cases if c["status"] == "CLOSED")

    return {
        "mine_id": mine_id,
        "total_cases": len(all_cases),
        "open_cases": open_cases,
        "action_required": action_required,
        "overdue_actions": overdue_actions,
        "verification_required": verification_required,
        "closed_cases": closed_cases,
    }


@app.get("/api/cases/{case_id}", response_model=ComplianceCaseDetailResponse)
def get_compliance_case_detail_endpoint(
    case_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Get full dossier for a specific compliance case.
    """
    return get_case_detail(case_id)


@app.post("/api/cases", response_model=ComplianceCaseResponse)
def create_or_sync_case_endpoint(
    mine_id: str = Query("MINE-BCCL-JHARIA-01"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Trigger case synchronization from real compliance signals.
    """
    cases = sync_mine_compliance_cases(mine_id)
    if cases:
        return cases[0]
    raise HTTPException(status_code=404, detail="No compliance cases found or generated.")


@app.get("/api/cases/{case_id}/traceability")
def get_case_traceability_endpoint(
    case_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Get the authoritative source chain: Inspection -> Measurement -> Threshold -> Finding -> Evidence -> Risk.
    """
    return get_case_traceability(case_id)


@app.get("/api/cases/{case_id}/actions", response_model=list[CorrectiveActionResponse])
def get_case_actions_endpoint(
    case_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    List corrective actions belonging to a case.
    """
    return db.list_corrective_actions_for_case(case_id)


@app.post("/api/cases/{case_id}/actions", response_model=dict)
def create_case_action_endpoint(
    case_id: str,
    payload: CorrectiveActionCreateRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Assign a corrective action to a compliance case.
    """
    role = (x_user_role or "MINE_MANAGER").upper()
    user = x_user_id or "MANAGER-01"

    if role == "FIELD_INSPECTOR":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Field inspectors cannot create or assign corrective actions.",
        )

    return create_corrective_action(
        case_id=case_id,
        payload=payload.model_dump(),
        actor_id=user,
        actor_role=role,
    )


@app.patch("/api/corrective-actions/{action_id}")
def update_corrective_action_endpoint(
    action_id: str,
    payload: dict,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Update a corrective action.
    """
    action = db.get_corrective_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Corrective action {action_id} not found.")

    conn = db._connect()
    updates = []
    vals = []
    for k in ("title", "description", "assigned_role", "assigned_user_id", "due_at", "priority", "status"):
        if k in payload and payload[k] is not None:
            updates.append(f"{k} = ?")
            vals.append(payload[k])

    if updates:
        now_iso = datetime.now(timezone.utc).isoformat()
        updates.append("updated_at = ?")
        vals.append(now_iso)
        vals.append(action_id)
        conn.execute(
            f"UPDATE corrective_actions SET {', '.join(updates)} WHERE action_id = ?",
            vals,
        )
        conn.commit()
    conn.close()

    return db.get_corrective_action(action_id)


@app.post("/api/corrective-actions/{action_id}/submit", response_model=CorrectionSubmitResponse)
def submit_action_correction_endpoint(
    action_id: str,
    payload: CorrectionSubmitRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Submit correction evidence for an action.
    Does NOT automatically close the case; transitions case to VERIFICATION_REQUIRED.
    """
    role = (x_user_role or "MINE_SUPERVISOR").upper()
    user = x_user_id or "SUPERVISOR-01"

    return submit_action_correction(
        action_id=action_id,
        payload=payload.model_dump(),
        actor_id=user,
        actor_role=role,
    )


@app.post("/api/cases/{case_id}/verify", response_model=CaseVerificationResponse)
def verify_case_endpoint(
    case_id: str,
    payload: CaseVerificationRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Statutory Reviewer verification and case closure.
    """
    role = (x_user_role or "MINE_MANAGER").upper()
    user = x_user_id or "MANAGER-01"

    if role in ("FIELD_INSPECTOR", "WORKER"):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Field inspectors cannot verify or close compliance cases.",
        )

    return verify_case_closure(
        case_id=case_id,
        reviewer_id=user,
        reviewer_role=role,
        notes=payload.notes,
    )


@app.post("/api/cases/{case_id}/return", response_model=CaseReturnResponse)
def return_case_endpoint(
    case_id: str,
    payload: CaseReturnRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Return case for correction when evidence is insufficient.
    Requires substantive reason.
    """
    role = (x_user_role or "MINE_MANAGER").upper()
    user = x_user_id or "MANAGER-01"

    if role in ("FIELD_INSPECTOR", "WORKER"):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Field inspectors cannot return compliance cases.",
        )

    return return_case_for_correction(
        case_id=case_id,
        reviewer_id=user,
        reviewer_role=role,
        reason=payload.reason,
    )


@app.get("/api/cases/{case_id}/audit")
def get_case_audit_endpoint(
    case_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Get the complete audit trail and cryptographic proofs for a case.
    """
    events = db.list_case_audit_events(case_id)
    proofs = db.list_cryptographic_proofs(case_id)
    return {
        "case_id": case_id,
        "audit_events": events,
        "cryptographic_proofs": proofs,
    }




# ============================================================
# EVIDENCE INTEGRITY & BLOCKCHAIN AUDIT CHAIN (PHASE 2 TASK 7)
# ============================================================

@app.post("/api/evidence/{evidence_id}/anchor")
def anchor_evidence_endpoint(
    evidence_id: str,
    payload: EvidenceAnchorRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Compute SHA-256, store package in IPFS (dev: local hash), and
    anchor the hash to blockchain (dev: DEMO_AUDIT_MODE).

    Allowed roles: FIELD_INSPECTOR, MINE_MANAGER, DGMS_OFFICER, SYSTEM.
    """
    role = (x_user_role or "FIELD_INSPECTOR").upper()
    user = x_user_id or payload.actor_id or "SYSTEM"

    try:
        record = anchor_evidence_item(
            evidence_id=evidence_id,
            actor_id=user,
            reference_type=payload.reference_type,
        )
        return {
            "evidence_id": evidence_id,
            "anchored": True,
            "integrity": record,
            "message": (
                f"Evidence package hashed, IPFS CID computed, and blockchain anchor "
                f"recorded in mode: {record.get('anchor_mode', 'DEMO_AUDIT_MODE')}."
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anchoring failed: {str(e)}")


@app.get("/api/evidence/{evidence_id}/integrity")
def get_evidence_integrity_endpoint(
    evidence_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return the stored integrity record for an evidence item.
    """
    record = get_evidence_integrity_record(evidence_id)
    if record is None:
        return {
            "evidence_id": evidence_id,
            "status": "AUDIT_PROOF_PENDING",
            "message": (
                "No integrity record found for this evidence. "
                "Call POST /api/evidence/{id}/anchor to create one."
            ),
            "integrity": None,
        }
    return {
        "evidence_id": evidence_id,
        "status": record.get("status"),
        "integrity": record,
    }


@app.post("/api/evidence/{evidence_id}/verify-integrity")
def verify_evidence_integrity_endpoint(
    evidence_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Recompute the content hash and compare against the stored blockchain anchor.

    Returns:
      - matches: bool
      - verification_status: INTEGRITY_VERIFIED | INTEGRITY_CHECK_FAILED | AUDIT_PROOF_PENDING
      - mode: DEMO_AUDIT_MODE | LIVE_BLOCKCHAIN
    """
    result = verify_evidence_item(evidence_id)
    return result


@app.get("/api/inspections/{inspection_id}/audit-integrity")
def get_inspection_audit_integrity_endpoint(
    inspection_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return full audit integrity chain for all evidence in an inspection.
    Auto-anchors any unanchored evidence.
    """
    try:
        return get_inspection_audit_integrity(inspection_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}/audit-integrity")
def get_case_audit_integrity_endpoint(
    case_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return audit integrity chain for all correction evidence linked to a case.
    """
    try:
        return get_case_audit_integrity(case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/integrity/status")
def get_integrity_service_status():
    """
    Return current IPFS and blockchain service status (safe to expose).
    NEVER exposes private keys or secrets.
    """
    return {
        "ipfs": get_ipfs_status(),
        "blockchain": get_blockchain_status(),
        "note": (
            "DEMO_AUDIT_MODE means IPFS and blockchain are not configured. "
            "Set IPFS_ENDPOINT, BLOCKCHAIN_RPC_URL, BLOCKCHAIN_PRIVATE_KEY "
            "environment variables for production deployment."
        ),
    }

# ============================================================
# GIS ATTENDANCE ENDPOINTS (PHASE 2 TASK 8)
# ============================================================

from app.attendance_service import (
    process_check_in,
    get_my_attendance,
    get_mine_attendance,
    get_team_attendance,
    get_anomalies,
    get_aggregate,
)
from app.database import (
    get_attendance as db_get_attendance,
    list_mine_zones,
    upsert_mine_zone,
    update_mine_coordinates,
    get_mine_with_location,
)
from app.schemas import (
    CheckInRequest,
    CheckInResponse,
    AttendanceRecordResponse,
    TeamAttendanceResponse,
    AttendanceAnomalySignal,
    AttendanceAggregateResponse,
    MineZoneRequest,
    MineZoneResponse,
    GeofenceResultResponse,
)

# Roles allowed to do field check-in
_FIELD_ROLES = {"FIELD_INSPECTOR", "MINE_SUPERVISOR", "MINE_MANAGER", "DGMS_OFFICER"}
# Roles that can view team attendance
_SUPERVISOR_ROLES = {"MINE_SUPERVISOR", "MINE_MANAGER", "DGMS_OFFICER", "CORPORATE_MANAGEMENT"}


def _require_role(effective_role: str, allowed: set[str]) -> None:
    """Raise 403 if role not in allowed set."""
    if effective_role not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{effective_role}' is not permitted for this action.",
        )


@app.post("/api/attendance/check-in")
def attendance_check_in(
    payload: CheckInRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Submit a GPS attendance check-in.
    Server performs authoritative Haversine geofence validation.
    Frontend boolean 'insideGeofence' is NEVER accepted as proof.
    """
    user_id = x_user_id or "UNKNOWN_USER"
    user_role = x_user_role or "FIELD_INSPECTOR"
    _require_role(user_role, _FIELD_ROLES)

    try:
        result = process_check_in(
            user_id=user_id,
            user_role=user_role,
            mine_id=payload.mine_id,
            zone_id=payload.zone_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy_meters=payload.accuracy_meters,
            captured_at=payload.captured_at,
            schedule_instance_id=payload.schedule_instance_id,
            inspection_id=payload.inspection_id,
            device_info=payload.device_info,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return result


@app.get("/api/attendance/me")
def get_my_attendance_endpoint(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return the authenticated user's own attendance history.
    Field inspectors can only see their own records.
    """
    user_id = x_user_id or "UNKNOWN_USER"
    user_role = x_user_role or "FIELD_INSPECTOR"
    return get_my_attendance(user_id)


@app.get("/api/attendance/team")
def get_team_attendance_endpoint(
    mine_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return team attendance summary.
    Supervisor, Manager, DGMS, Corporate only.
    """
    user_role = x_user_role or "MINE_SUPERVISOR"
    _require_role(user_role, _SUPERVISOR_ROLES)
    return get_team_attendance(mine_id=mine_id)


@app.get("/api/attendance/anomalies")
def get_attendance_anomalies_endpoint(
    mine_id: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return attendance anomaly signals.
    Supervisor+ only.
    """
    user_role = x_user_role or "MINE_SUPERVISOR"
    _require_role(user_role, _SUPERVISOR_ROLES)
    return get_anomalies(mine_id=mine_id)


@app.get("/api/attendance/aggregate")
def get_attendance_aggregate_endpoint(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return aggregate attendance statistics (no PII).
    Corporate, DGMS, Manager only.
    """
    user_role = x_user_role or "CORPORATE_MANAGEMENT"
    _require_role(user_role, {"CORPORATE_MANAGEMENT", "DGMS_OFFICER", "MINE_MANAGER"})
    return get_aggregate()


@app.get("/api/attendance/mine/{mine_id}")
def get_mine_attendance_endpoint(
    mine_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return all attendance records for a specific mine.
    Manager and DGMS only.
    """
    user_role = x_user_role or "MINE_MANAGER"
    _require_role(user_role, {"MINE_MANAGER", "DGMS_OFFICER", "CORPORATE_MANAGEMENT"})
    return get_mine_attendance(mine_id)


@app.get("/api/attendance/{attendance_id}")
def get_single_attendance_endpoint(
    attendance_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Return a single attendance record.
    Field inspector can only view own records.
    Supervisor+ can view any.
    """
    user_id = x_user_id or "UNKNOWN_USER"
    user_role = x_user_role or "FIELD_INSPECTOR"

    record = db_get_attendance(attendance_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Attendance record not found.")

    # RBAC: field inspector can only see own records
    if user_role == "FIELD_INSPECTOR" and record.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="You may only view your own attendance records.",
        )

    from app.attendance_service import _enrich_record
    return _enrich_record(record)


# ============================================================
# MINE ZONES ENDPOINTS (PHASE 2 TASK 8)
# ============================================================

@app.get("/api/mine-zones/{mine_id}")
def get_mine_zones_endpoint(mine_id: str):
    """Return all active zones for a mine (all roles)."""
    zones = list_mine_zones(mine_id)
    # Also return mine reference coordinates
    mine = get_mine_with_location(mine_id)
    return {
        "mine_id": mine_id,
        "mine_latitude": mine.get("latitude") if mine else None,
        "mine_longitude": mine.get("longitude") if mine else None,
        "mine_geofence_radius_meters": mine.get("geofence_radius_meters", 500.0) if mine else 500.0,
        "zones": zones,
    }


@app.post("/api/mine-zones")
def create_mine_zone_endpoint(
    payload: MineZoneRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Create/register a mine zone. Manager+ only."""
    user_role = x_user_role or "MINE_MANAGER"
    _require_role(user_role, {"MINE_MANAGER", "DGMS_OFFICER"})

    import uuid as _uuid
    from datetime import datetime, timezone as _tz
    zone_dict = {
        "mine_zone_id": f"ZONE-{_uuid.uuid4().hex[:10].upper()}",
        "mine_id": payload.mine_id,
        "name": payload.name,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "geofence_radius_meters": payload.geofence_radius_meters,
        "description": payload.description,
        "active": True,
        "created_at": datetime.now(_tz.utc).isoformat(),
    }
    stored = upsert_mine_zone(zone_dict)
    return stored


@app.post("/api/mines/{mine_id}/location")
def set_mine_location_endpoint(
    mine_id: str,
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_m: float = Query(default=500.0, ge=10.0, le=50000.0),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Set GPS reference coordinates for a mine. Manager+ only."""
    user_role = x_user_role or "MINE_MANAGER"
    _require_role(user_role, {"MINE_MANAGER", "DGMS_OFFICER"})
    update_mine_coordinates(mine_id, latitude, longitude, radius_m)
    return {"mine_id": mine_id, "latitude": latitude, "longitude": longitude, "radius_m": radius_m}


# ============================================================
# SCADA & SENSOR TELEMETRY ENDPOINTS (PHASE 2 TASK 9)
# ============================================================

from app.telemetry_service import (
    ingest_telemetry_batch,
    ingest_telemetry_reading,
    get_latest_mine_telemetry,
    get_mine_safety_signals,
)
from app.database import (
    list_sensors as db_list_sensors,
    get_sensor as db_get_sensor,
    list_telemetry_history as db_list_telemetry_history,
    get_telemetry_health_summary,
)
from app.schemas import (
    TelemetryBatchRequest,
    TelemetryIngestionItem,
    TelemetryIngestionResponse,
    SensorResponse,
    TelemetryReadingResponse,
    SafetySignalResponse,
    TelemetryHealthResponse,
)

_TELEMETRY_ALLOWED_ROLES = {
    "SCADA_SIMULATOR", "SCADA_SYSTEM", "SYSTEM", "MINE_MANAGER",
    "MINE_SUPERVISOR", "DGMS_OFFICER", "CORPORATE_MANAGEMENT", "FIELD_INSPECTOR"
}


@app.post("/api/telemetry/readings", response_model=TelemetryIngestionResponse)
def post_telemetry_readings_endpoint(
    payload: Union[TelemetryBatchRequest, TelemetryIngestionItem, list[TelemetryIngestionItem], dict] = Body(...),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """
    Ingest validated SCADA / IoT telemetry readings stream.
    Evaluates safety thresholds, manages deduplicated signals, and triggers cases for critical breaches.
    """
    if isinstance(payload, TelemetryBatchRequest):
        readings_raw = [r.dict() for r in payload.readings]
        source = payload.source or "SCADA_SIMULATOR"
    elif isinstance(payload, list):
        readings_raw = [r.dict() if hasattr(r, "dict") else r for r in payload]
        source = "SCADA_SIMULATOR"
    elif isinstance(payload, dict):
        if "readings" in payload and isinstance(payload["readings"], list):
            readings_raw = payload["readings"]
            source = payload.get("source", "SCADA_SIMULATOR") or "SCADA_SIMULATOR"
        else:
            readings_raw = [payload]
            source = payload.get("source", "SCADA_SIMULATOR") or "SCADA_SIMULATOR"
    else:
        readings_raw = [payload.dict() if hasattr(payload, "dict") else payload]
        source = getattr(payload, "source", "SCADA_SIMULATOR") or "SCADA_SIMULATOR"

    try:
        result = ingest_telemetry_batch(readings_raw, source=source)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telemetry ingestion failed: {str(e)}")


@app.get("/api/telemetry/mine/{mine_id}")
def get_mine_telemetry_history_endpoint(
    mine_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    sensor_type: Optional[str] = Query(None),
):
    """Return bounded history of persisted telemetry readings for a mine."""
    return db_list_telemetry_history(mine_id=mine_id, limit=limit, sensor_type=sensor_type)


@app.get("/api/telemetry/mine/{mine_id}/latest")
def get_mine_latest_telemetry_endpoint(mine_id: str):
    """Return latest reading for each sensor category in the mine with status and freshness."""
    return get_latest_mine_telemetry(mine_id)


@app.get("/api/telemetry/mine/{mine_id}/signals")
def get_mine_safety_signals_endpoint(
    mine_id: str,
    active_only: bool = Query(default=False),
):
    """Return explainable safety signals (active or full history) for a mine."""
    return get_mine_safety_signals(mine_id=mine_id, active_only=active_only)


@app.get("/api/telemetry/sensors")
def get_sensors_endpoint(mine_id: Optional[str] = Query(None)):
    """List registered sensors, optionally filtered by mine."""
    return db_list_sensors(mine_id=mine_id)


@app.get("/api/telemetry/sensors/{sensor_id}")
def get_single_sensor_endpoint(sensor_id: str):
    """Return details of a specific sensor."""
    sensor = db_get_sensor(sensor_id)
    if not sensor:
        from app.database import get_sensor_by_code
        sensor = get_sensor_by_code(sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found.")
    return sensor


@app.get("/api/telemetry/health", response_model=TelemetryHealthResponse)
def get_telemetry_health_endpoint():
    """Return diagnostic health and reporting status of the telemetry ingestion feed."""
    return get_telemetry_health_summary()


# ============================================================
# PRODUCTION & OPERATIONAL GOVERNANCE (PHASE 2 TASK 10)
# ============================================================

def _assert_production_write_authorized(effective_role: str) -> None:
    """Check role authorization for creating or updating production records."""
    norm = effective_role.upper()
    if norm in ("FIELD_INSPECTOR", "INSPECTOR"):
        raise HTTPException(
            status_code=403,
            detail="Field Inspectors are not authorized to create or edit production records. Role limited to inspection evidence.",
        )
    if norm in ("DGMS_OFFICER", "DGMS"):
        raise HTTPException(
            status_code=403,
            detail="DGMS Officers have read-only regulatory oversight of production records. Modifications prohibited.",
        )


@app.post("/api/production/records", response_model=ProductionRecordResponse)
def create_production_record_endpoint(
    record: ProductionRecordCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    role: Optional[str] = Query(None),
):
    """
    Log an operational production event record (Weighbridge / Shift Report / Surveyor / CHP).
    Executes real-time anomaly detection and safety stoppage correlation.
    """
    effective_role = x_user_role or role or "MINE_MANAGER"
    _assert_production_write_authorized(effective_role)
    actor_id = x_user_id or effective_role
    return record_production_event(record, actor_id=actor_id)


@app.get("/api/production/mine/{mine_id}", response_model=list[ProductionRecordResponse])
def get_mine_production_records_endpoint(
    mine_id: str,
    date: Optional[str] = Query(None, alias="date"),
    shift: Optional[str] = Query(None, alias="shift"),
    include_superseded: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Retrieve operational production records for a mine, sorted by date and time."""
    records = db.list_production_records(
        mine_id=mine_id,
        production_date=date,
        shift_name=shift,
        include_superseded=include_superseded,
        limit=limit,
        offset=offset,
    )
    return records


@app.get("/api/production/mine/{mine_id}/summary", response_model=MineProductionSummaryResponse)
def get_mine_production_summary_endpoint(
    mine_id: str,
    date: Optional[str] = Query(None, alias="date"),
):
    """
    Operational production summary for a mine:
    Target vs Actual, Shift performance, Downtime/Delays, Contractor share, HEMM context, and Anomalies.
    """
    return get_mine_production_summary(mine_id, date)


@app.get("/api/production/area/{area_id}/summary", response_model=AreaProductionSummaryResponse)
def get_area_production_summary_endpoint(
    area_id: str,
    date: Optional[str] = Query(None, alias="date"),
):
    """Roll up production performance across all mines under an Area."""
    return get_area_production_summary(area_id, date)


@app.get("/api/production/subsidiary/{subsidiary_id}/summary", response_model=SubsidiaryProductionSummaryResponse)
def get_subsidiary_production_summary_endpoint(
    subsidiary_id: str,
    date: Optional[str] = Query(None, alias="date"),
):
    """Roll up production performance across all areas and mines under a Subsidiary (BCCL/ECL/MCL)."""
    return get_subsidiary_production_summary(subsidiary_id, date)


@app.get("/api/production/corporate/summary", response_model=CorporateProductionSummaryResponse)
def get_corporate_production_summary_endpoint(
    date: Optional[str] = Query(None, alias="date"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    role: Optional[str] = Query(None),
):
    """
    Pan-India CIL Corporate aggregation across all operating subsidiaries.
    Hierarchical drill-down: CIL Corporate -> Subsidiary -> Area -> Mine.
    """
    return get_corporate_production_summary(date)


@app.get("/api/production/records/{record_id}")
def get_single_production_record_endpoint(record_id: str):
    """Retrieve full detail and audit history of a single production record."""
    record = db.get_production_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Production record '{record_id}' not found.")
    audit_events = db.get_production_audit_events(record_id)
    return {"record": record, "audit_events": audit_events}


@app.post("/api/production/records/{record_id}/correct", response_model=ProductionRecordResponse)
def correct_production_record_endpoint(
    record_id: str,
    req: ProductionRecordCorrectionRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    role: Optional[str] = Query(None),
):
    """
    Immutably correct a historical production record.
    Preserves original as SUPERSEDED and records an audit log event.
    """
    effective_role = x_user_role or role or "MINE_MANAGER"
    _assert_production_write_authorized(effective_role)
    actor_id = x_user_id or req.corrected_by or effective_role

    try:
        updated = db.correct_production_record(
            record_id=record_id,
            corrected_quantity=req.corrected_quantity,
            corrected_dispatch=req.corrected_dispatch,
            reason=req.reason,
            actor_id=actor_id,
            notes=req.notes,
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/production/targets/{mine_id}", response_model=list[ProductionTargetResponse])
def get_production_targets_endpoint(mine_id: str):
    """List configured statutory targets for a mine."""
    return db.list_production_targets(mine_id)


@app.post("/api/production/targets", response_model=ProductionTargetResponse)
def set_production_target_endpoint(
    req: ProductionTargetCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    role: Optional[str] = Query(None),
):
    """Configure or update daily statutory production targets for a mine."""
    effective_role = x_user_role or role or "MINE_MANAGER"
    _assert_production_write_authorized(effective_role)

    target_id = f"TGT-{req.mine_id}-{req.target_date}"
    target = ProductionTarget(
        target_id=target_id,
        mine_id=req.mine_id,
        target_date=req.target_date,
        daily_target_tonnes=req.daily_target_tonnes,
        monthly_target_tonnes=req.monthly_target_tonnes,
        dispatch_target_tonnes=req.dispatch_target_tonnes,
        set_by=req.set_by or "CORPORATE_PLANNING",
        created_at=datetime.now(timezone.utc),
    )
    db.save_production_target(target)
    saved = db.get_production_target(req.mine_id, req.target_date)
    return saved


@app.get("/api/production/anomalies/{mine_id}", response_model=list[ProductionAnomalyResponse])
def get_production_anomalies_endpoint(mine_id: str):
    """Return active explainable production anomalies for a mine."""
    return db.get_active_production_anomalies(mine_id)


@app.get("/api/production/report/daily", response_model=DailyProductionReportResponse)
def get_daily_production_report_endpoint(
    mine_id: str = Query(...),
    date: Optional[str] = Query(None),
):
    """Generate structured, database-backed Daily Mine Production Summary with cryptographic hash."""
    return generate_daily_production_report(mine_id, date)


# ============================================================
# GOVERNANCE MASTER & ORGANIZATIONAL HIERARCHY (PHASE 2 TASK 11)
# ============================================================

def _assert_hierarchy_admin(role: Optional[str]) -> None:
    norm = (role or "").upper()
    if norm not in ("ADMIN", "SUPERADMIN", "DIRECTOR", "CORPORATE_MANAGEMENT", "CORPORATE_ADMIN"):
        raise HTTPException(
            status_code=403,
            detail=f"Administrative authority required for Master Data modification. Role '{role}' unauthorized.",
        )


def _check_scope_access(
    target_unit_id: str,
    x_user_role: Optional[str] = None,
    x_user_scope_type: Optional[str] = None,
    x_user_scope_id: Optional[str] = None,
) -> None:
    if x_user_scope_type and x_user_scope_id:
        assert_hierarchy_access(
            user_role=x_user_role or "MINE_MANAGER",
            user_scope_type=x_user_scope_type,
            user_scope_id=x_user_scope_id,
            target_unit_id=target_unit_id,
        )


@app.get("/api/hierarchy", response_model=list[OrganizationUnitResponse])
def get_organization_units_endpoint(
    unit_type: Optional[str] = Query(None),
    parent_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List organizational units with optional filters."""
    return db.list_organization_units(unit_type=unit_type, parent_id=parent_id, status=status)


@app.get("/api/hierarchy/search")
def search_hierarchy_endpoint(
    q: str = Query("", description="Search term for code, name, location or operational unit"),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Search canonical hierarchy units (Ministry, CIL, Subsidiary, Area, Mine, Operational Units).
    Returns matched records with resolved governance lineage paths.
    """
    if not q or not q.strip():
        return []

    raw_results = db.search_hierarchy_nodes(q, limit=limit)
    enriched = []

    for item in raw_results:
        cat = item.get("node_category", "ORGANIZATION_UNIT")
        if cat == "ORGANIZATION_UNIT":
            unit_id = item["id"]
            u_type = item["unit_type"]
            path = get_hierarchy_path(unit_id)
            path_names = [p["name"] for p in reversed(path)]
            
            mine_type = None
            if u_type == "MINE":
                m_rec = db.get_mine(unit_id) or next((m for m in db.list_mines() if getattr(m, "organization_unit_id", None) == unit_id or m.mine_id == item["code"]), None)
                if m_rec:
                    raw_mt = m_rec.mine_type.value if hasattr(m_rec.mine_type, "value") else str(m_rec.mine_type)
                    mine_type = "UNDERGROUND" if "underground" in raw_mt.lower() else "OPENCAST" if "opencast" in raw_mt.lower() else raw_mt.upper()

            enriched.append({
                "id": unit_id,
                "name": item["name"],
                "code": item["code"],
                "type": u_type,
                "unit_type": u_type,
                "mine_type": mine_type,
                "status": item.get("status", "ACTIVE"),
                "state": item.get("state"),
                "district": item.get("district"),
                "hierarchy_path": path_names,
                "link": f"/governance?select={unit_id}",
            })
        else:
            op_id = item["id"]
            mine_id = item["mine_id"]
            mine_path = get_hierarchy_path(mine_id)
            path_names = [p["name"] for p in reversed(mine_path)] + [item["name"]]
            
            m_rec = db.get_mine(mine_id) or next((m for m in db.list_mines() if getattr(m, "organization_unit_id", None) == mine_id or m.mine_id == mine_id), None)
            raw_mt = (m_rec.mine_type.value if hasattr(m_rec.mine_type, "value") else str(m_rec.mine_type)) if m_rec else "OPENCAST"
            mine_type = "UNDERGROUND" if "underground" in raw_mt.lower() else "OPENCAST" if "opencast" in raw_mt.lower() else raw_mt.upper()

            enriched.append({
                "id": op_id,
                "name": item["name"],
                "code": item["code"],
                "type": "OPERATIONAL_UNIT",
                "unit_type": item["unit_type"],
                "mine_type": mine_type,
                "status": "ACTIVE" if item.get("active") else "INACTIVE",
                "state": None,
                "district": None,
                "hierarchy_path": path_names,
                "link": f"/governance?select={mine_id}&zone={op_id}",
            })

    return enriched


@app.get("/api/hierarchy/tree", response_model=list[HierarchyTreeNode])

def get_hierarchy_tree_endpoint(
    root_id: Optional[str] = Query(None),
    depth: int = Query(5, ge=1, le=10),
):
    """Retrieve full or rooted canonical recursive governance hierarchy tree."""
    return get_hierarchy_tree(root_id=root_id, depth=depth)


@app.get("/api/hierarchy/subsidiaries")
def get_subsidiaries_endpoint():
    """List all CIL subsidiaries/entities."""
    subs = db.list_organization_units(unit_type="SUBSIDIARY")
    return subs


@app.get("/api/hierarchy/subsidiaries/{id}")
def get_subsidiary_detail_endpoint(id: str):
    """Retrieve subsidiary details along with its child operational areas."""
    sub = db.get_organization_unit(id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Subsidiary '{id}' not found.")
    areas = db.list_organization_units(unit_type="AREA", parent_id=id)
    return {"subsidiary": sub, "areas": areas}


@app.get("/api/hierarchy/areas/{id}")
def get_area_detail_endpoint(id: str):
    """Retrieve area details along with its descendant mines."""
    area = db.get_organization_unit(id)
    if not area:
        raise HTTPException(status_code=404, detail=f"Area '{id}' not found.")
    mines = db.list_organization_units(unit_type="MINE", parent_id=id)
    return {"area": area, "mines": mines}


@app.get("/api/hierarchy/mines/{id}")
def get_mine_hierarchy_endpoint(
    id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """Retrieve canonical mine details and its complete upward lineage."""
    _check_scope_access(id, x_user_role, x_user_scope_type, x_user_scope_id)
    return resolve_mine_hierarchy(id)


@app.get("/api/hierarchy/mines/{id}/zones", response_model=list[OperationalUnitResponse])
def get_mine_operational_units_endpoint(
    id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """Retrieve operational units (Pits/Benches/Haul Roads or Shafts/Districts/Panels/Faces) for a mine."""
    _check_scope_access(id, x_user_role, x_user_scope_type, x_user_scope_id)
    return db.list_operational_units(mine_id=id)


@app.get("/api/hierarchy/mines/{id}/contracts", response_model=list[ContractMasterResponse])
def get_mine_contracts_endpoint(
    id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """Retrieve commercial and departmental contracts governing operations at a mine."""
    _check_scope_access(id, x_user_role, x_user_scope_type, x_user_scope_id)
    return db.list_contracts(mine_id=id)


@app.get("/api/hierarchy/mines/{id}/workforce", response_model=list[WorkerMasterResponse])
def get_mine_workforce_endpoint(
    id: str,
    active_only: bool = Query(False),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """Retrieve worker roster (departmental and contractor workers) assigned to a mine."""
    _check_scope_access(id, x_user_role, x_user_scope_type, x_user_scope_id)
    return db.list_workers(mine_id=id, active_only=active_only)


@app.get("/api/hierarchy/path/{unit_id}", response_model=HierarchyPathResponse)
def get_hierarchy_path_endpoint(unit_id: str):
    """Return ordered path upward: [Mine, Area, Subsidiary/Entity, CIL, Ministry]."""
    path = get_hierarchy_path(unit_id)
    target = path[0] if path else {"id": unit_id, "name": unit_id, "unit_type": "UNKNOWN"}
    return {
        "target_unit_id": target["id"],
        "target_name": target["name"],
        "target_type": target["unit_type"],
        "path": path,
    }


@app.post("/api/hierarchy/units", response_model=OrganizationUnitResponse)
def create_organization_unit_endpoint(
    req: OrganizationUnitCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    role: Optional[str] = Query(None),
):
    """Create an organizational hierarchy node (Admin only). Enforces strict parent-child rules."""
    effective_role = x_user_role or role or "ADMIN"
    _assert_hierarchy_admin(effective_role)
    actor_id = x_user_id or effective_role

    # Validate parent if specified
    if req.parent_id:
        parent = db.get_organization_unit(req.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail=f"Parent unit '{req.parent_id}' does not exist.")
        try:
            validate_parent_child(parent["unit_type"], req.unit_type)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif req.unit_type != OrganizationUnitType.MINISTRY.value:
        raise HTTPException(status_code=400, detail=f"Only MINISTRY unit can have no parent.")

    unit_id = f"ORG-{req.unit_type}-{req.code.upper()}"
    now = datetime.now(timezone.utc)
    effective_from = req.effective_from or now.strftime("%Y-%m-%d")

    unit = OrganizationUnit(
        id=unit_id,
        parent_id=req.parent_id,
        unit_type=OrganizationUnitType(req.unit_type),
        code=req.code.upper(),
        name=req.name,
        legal_name=req.legal_name,
        status=req.status,
        state=req.state,
        district=req.district,
        headquarters=req.headquarters,
        effective_from=effective_from,
        effective_to=req.effective_to,
        metadata=req.metadata,
        created_at=now,
        updated_at=now,
    )
    db.save_organization_unit(unit)

    # Immutable organizational audit event
    audit_evt = OrganizationAuditEvent(
        event_id=f"AUD-ORG-{uuid4().hex[:10]}",
        entity_type="ORGANIZATION_UNIT",
        entity_id=unit_id,
        action="CREATE_UNIT",
        actor_id=actor_id,
        previous_state=None,
        new_state=str(unit.dict()),
        reason="Administrative creation of organizational unit",
        timestamp=now,
    )
    db.save_organization_audit_event(audit_evt)

    saved = db.get_organization_unit(unit_id)
    return saved


@app.put("/api/hierarchy/units/{id}", response_model=OrganizationUnitResponse)
def update_organization_unit_endpoint(
    id: str,
    req: OrganizationUnitUpdate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    role: Optional[str] = Query(None),
):
    """Update an organizational hierarchy node (Admin only). Enforces cycle detection & parent-child rules."""
    effective_role = x_user_role or role or "ADMIN"
    _assert_hierarchy_admin(effective_role)
    actor_id = x_user_id or effective_role

    existing = db.get_organization_unit(id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Unit '{id}' not found.")

    new_parent_id = req.parent_id if req.parent_id is not None else existing["parent_id"]
    if new_parent_id != existing["parent_id"]:
        try:
            detect_circular_hierarchy(id, new_parent_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if new_parent_id:
            parent = db.get_organization_unit(new_parent_id)
            if not parent:
                raise HTTPException(status_code=400, detail=f"Parent unit '{new_parent_id}' does not exist.")
            try:
                validate_parent_child(parent["unit_type"], existing["unit_type"])
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    now = datetime.now(timezone.utc)
    updated_unit = OrganizationUnit(
        id=id,
        parent_id=new_parent_id,
        unit_type=OrganizationUnitType(existing["unit_type"]),
        code=existing["code"],
        name=req.name if req.name is not None else existing["name"],
        legal_name=req.legal_name if req.legal_name is not None else existing.get("legal_name"),
        status=req.status if req.status is not None else existing["status"],
        state=req.state if req.state is not None else existing.get("state"),
        district=req.district if req.district is not None else existing.get("district"),
        headquarters=req.headquarters if req.headquarters is not None else existing.get("headquarters"),
        effective_from=existing["effective_from"],
        effective_to=req.effective_to if req.effective_to is not None else existing.get("effective_to"),
        metadata=req.metadata if req.metadata is not None else existing.get("metadata"),
        created_at=datetime.fromisoformat(existing["created_at"]) if isinstance(existing["created_at"], str) else existing["created_at"],
        updated_at=now,
    )
    db.save_organization_unit(updated_unit)

    action = "MOVE_UNIT" if new_parent_id != existing["parent_id"] else "UPDATE_UNIT"
    audit_evt = OrganizationAuditEvent(
        event_id=f"AUD-ORG-{uuid4().hex[:10]}",
        entity_type="ORGANIZATION_UNIT",
        entity_id=id,
        action=action,
        actor_id=actor_id,
        previous_state=str(existing),
        new_state=str(updated_unit.dict()),
        reason=f"Administrative modification: {action}",
        timestamp=now,
    )
    db.save_organization_audit_event(audit_evt)

    return db.get_organization_unit(id)


@app.post("/api/hierarchy/operational-units", response_model=OperationalUnitResponse)
def create_operational_unit_endpoint(
    req: OperationalUnitCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    role: Optional[str] = Query(None),
):
    """Create an operational unit within a mine. Enforces strict mine-type compatibility."""
    effective_role = x_user_role or role or "MINE_MANAGER"
    _assert_hierarchy_admin(effective_role)
    actor_id = x_user_id or effective_role

    try:
        validate_operational_unit_compatibility(req.mine_id, req.unit_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    unit_id = f"OP-{req.unit_type}-{req.mine_id}-{req.code.upper()}"
    now = datetime.now(timezone.utc)

    op_unit = OperationalUnit(
        id=unit_id,
        mine_id=req.mine_id,
        parent_operational_unit_id=req.parent_operational_unit_id,
        unit_type=OperationalUnitType(req.unit_type),
        code=req.code.upper(),
        name=req.name,
        active=req.active,
        latitude=req.latitude,
        longitude=req.longitude,
        geofence_radius=req.geofence_radius,
        metadata=req.metadata,
        created_at=now,
        updated_at=now,
    )
    db.save_operational_unit(op_unit)

    audit_evt = OrganizationAuditEvent(
        event_id=f"AUD-OP-{uuid4().hex[:10]}",
        entity_type="OPERATIONAL_UNIT",
        entity_id=unit_id,
        action="CREATE_OPERATIONAL_UNIT",
        actor_id=actor_id,
        previous_state=None,
        new_state=str(op_unit.dict()),
        reason="Creation of operational unit",
        timestamp=now,
    )
    db.save_organization_audit_event(audit_evt)

    return db.get_operational_unit(unit_id)


@app.get("/api/hierarchy/workers/{id}/lineage", response_model=WorkerLineageResponse)
def get_worker_lineage_endpoint(id: str):
    """Resolve complete governance lineage for a worker identity."""
    return resolve_worker_hierarchy(id)


@app.get("/api/hierarchy/workers", response_model=list[WorkerMasterResponse])
def list_workers_endpoint(
    mine_id: Optional[str] = Query(None),
    contract_id: Optional[str] = Query(None),
    active_only: bool = Query(False),
):
    """List registered workers with relational contract/mine bindings."""
    return db.list_workers(mine_id=mine_id, contract_id=contract_id, active_only=active_only)


@app.post("/api/hierarchy/workers", response_model=WorkerMasterResponse)
def create_worker_endpoint(
    req: WorkerMasterCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    role: Optional[str] = Query(None),
):
    """Register a departmental or contractor worker into the workforce master."""
    effective_role = x_user_role or role or "MINE_MANAGER"
    _assert_hierarchy_admin(effective_role)

    # Validate worker code uniqueness
    existing = db.get_worker_by_code(req.worker_code)
    if existing:
        raise HTTPException(status_code=400, detail=f"Worker with code '{req.worker_code}' already exists.")

    worker_id = f"WRK-{req.worker_code.upper()}"
    now = datetime.now(timezone.utc)
    onboarding_date = req.onboarding_date or now.strftime("%Y-%m-%d")

    worker = WorkerMaster(
        id=worker_id,
        worker_code=req.worker_code.upper(),
        name=req.name,
        worker_type=WorkerType(req.worker_type),
        contractor_id=req.contractor_id,
        contract_id=req.contract_id,
        mine_id=req.mine_id,
        skill_category=req.skill_category,
        department=req.department,
        active=req.active,
        onboarding_date=onboarding_date,
        training_status=req.training_status,
        identity_reference=req.identity_reference,
        created_at=now,
        updated_at=now,
    )
    db.save_worker(worker)
    return db.get_worker(worker_id)


@app.get("/api/hierarchy/contractors", response_model=list[ContractorMasterResponse])
def list_contractors_endpoint(
    contractor_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List commercial, MDO, and departmental contractor master organizations."""
    return db.list_contractors(contractor_type=contractor_type, status=status)


@app.post("/api/hierarchy/contractors", response_model=ContractorMasterResponse)
def create_contractor_endpoint(
    req: ContractorMasterCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    role: Optional[str] = Query(None),
):
    """Create a contractor master entity (Admin only)."""
    effective_role = x_user_role or role or "ADMIN"
    _assert_hierarchy_admin(effective_role)

    contractor_id = f"CONT-{uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    contractor = ContractorMaster(
        id=contractor_id,
        legal_name=req.legal_name,
        display_name=req.display_name,
        registration_reference=req.registration_reference,
        status=req.status,
        contractor_type=ContractorType(req.contractor_type),
        created_at=now,
        updated_at=now,
    )
    db.save_contractor(contractor)
    return db.get_contractor(contractor_id)


@app.get("/api/hierarchy/contracts", response_model=list[ContractMasterResponse])
def list_contracts_endpoint(
    mine_id: Optional[str] = Query(None),
    contractor_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List contracts and MDO work orders."""
    return db.list_contracts(mine_id=mine_id, contractor_id=contractor_id, status=status)


@app.post("/api/hierarchy/contracts", response_model=ContractMasterResponse)
def create_contract_endpoint(
    req: ContractMasterCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    role: Optional[str] = Query(None),
):
    """
    Create a contract binding a contractor to a mine (Admin only).
    Automatically derives Area and Subsidiary from canonical mine lineage.
    """
    effective_role = x_user_role or role or "ADMIN"
    _assert_hierarchy_admin(effective_role)

    mine_lineage = resolve_mine_hierarchy(req.mine_id)
    area_id = mine_lineage.get("area", {}).get("id")
    subsidiary_id = mine_lineage.get("subsidiary", {}).get("id")

    contract_id = f"CNTR-{uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    contract = ContractMaster(
        id=contract_id,
        contractor_id=req.contractor_id,
        mine_id=req.mine_id,
        area_id=area_id,
        subsidiary_id=subsidiary_id,
        contract_type=ContractorType(req.contract_type),
        contract_number=req.contract_number,
        scope=req.scope,
        start_date=req.start_date,
        end_date=req.end_date,
        workforce_limit=req.workforce_limit,
        status=req.status,
        created_at=now,
        updated_at=now,
    )
    db.save_contract(contract)
    return db.get_contract(contract_id)


@app.get("/api/hierarchy/contracts/{id}")
def get_contract_lineage_endpoint(id: str):
    """Retrieve full contract details and upward governance lineage."""
    return resolve_contract_hierarchy(id)


@app.get("/api/hierarchy/audit-events", response_model=list[OrganizationAuditEventResponse])
def get_hierarchy_audit_events_endpoint(
    entity_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Retrieve immutable audit events for organizational hierarchy structural modifications."""
    return db.get_organization_audit_events(entity_id=entity_id, limit=limit)


# ============================================================
# ENVIRONMENTAL GOVERNANCE & REGULATORY REPORTING (TASK 13)
# ============================================================

@app.get("/api/environment/overview")
def get_environment_overview_endpoint(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """
    High-level environmental compliance overview aggregated across the user's authorized scope.
    """
    all_mines = db.list_mines()
    authorized_mines = []
    for m in all_mines:
        try:
            _check_scope_access(m.mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
            authorized_mines.append(m)
        except HTTPException:
            continue

    total_measurements = 0
    total_violations = 0
    total_overdue = 0
    total_open_cases = 0
    high_risk_mines_count = 0
    mine_summaries = []

    for m in authorized_mines:
        meas = db.list_environmental_measurements(mine_id=m.mine_id, limit=100)
        schs = db.list_environmental_schedules(mine_id=m.mine_id)
        cases = []
        for c in db.list_compliance_cases(mine_id=m.mine_id):
            c_cat = c.get("category") if isinstance(c, dict) else c.category
            c_src = c.get("source_type") if isinstance(c, dict) else c.source_type
            if c_cat in EnvironmentalDomain.__members__ or c_src in (CaseSourceType.ENVIRONMENTAL_VIOLATION, "ENVIRONMENTAL_VIOLATION"):
                cases.append(c)

        viols = [x for x in meas if x.status == "FLAGGED_ANOMALY"]
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        overdue = [s for s in schs if s.status == "OVERDUE" or (s.status in ("SCHEDULED", "DUE") and s.due_date < now_str)]
        open_c = [c for c in cases if (c.get("status") if isinstance(c, dict) else c.status) != CaseStatus.CLOSED]
        risk = calculate_environmental_risk(m.mine_id)

        total_measurements += len(meas)
        total_violations += len(viols)
        total_overdue += len(overdue)
        total_open_cases += len(open_c)
        if risk["risk_level"] in ("HIGH", "CRITICAL"):
            high_risk_mines_count += 1

        mine_summaries.append({
            "mine_id": m.mine_id,
            "name": m.name,
            "mine_type": "UNDERGROUND" if m.mine_type in (MineType.UNDERGROUND_COAL, "underground_coal") else "OPENCAST",
            "state": m.state,
            "district": m.district,
            "measurements_count": len(meas),
            "violations_count": len(viols),
            "overdue_count": len(overdue),
            "open_cases_count": len(open_c),
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
        })

    all_params = db.list_environmental_parameters()
    highest_risk = "LOW"
    for s in mine_summaries:
        if s["risk_level"] == "CRITICAL":
            highest_risk = "CRITICAL"
            break
        elif s["risk_level"] == "HIGH":
            highest_risk = "HIGH"
        elif s["risk_level"] == "MEDIUM" and highest_risk != "HIGH":
            highest_risk = "MEDIUM"

    return {
        "authorized_mines_count": len(authorized_mines),
        "total_parameters": len(all_params),
        "total_measurements": total_measurements,
        "risk_level": highest_risk,
        "total_measurements_recorded": total_measurements,
        "active_threshold_violations": total_violations,
        "overdue_monitoring_schedules": total_overdue,
        "open_environmental_cases": total_open_cases,
        "high_risk_mines_count": high_risk_mines_count,
        "mines": mine_summaries,
    }


@app.get("/api/environment/mines/{mine_id}")
def get_mine_environmental_profile_endpoint(
    mine_id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """
    Retrieve comprehensive environmental governance profile for an authorized mine.
    """
    _check_scope_access(mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    return get_mine_environmental_profile(mine_id)


@app.get("/api/environment/parameters")
def list_environmental_parameters_endpoint(
    domain: Optional[str] = Query(None),
    mine_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    """List configurable environmental parameters with optional domain or mine type filter."""
    return [p.dict() for p in db.list_environmental_parameters(domain=domain, mine_type=mine_type, active_only=active_only)]


@app.get("/api/environment/domains")
def list_environmental_domains_endpoint():
    """List all 8 environmental monitoring domains with their registered parameter counts."""
    all_params = db.list_environmental_parameters(active_only=False)
    domains_info = []
    descriptions = {
        "AIR": "Ambient air quality, respirable dust, PM10, PM2.5, and haul-road particulate monitoring.",
        "WATER": "Mine discharge effluent, sump water quality, pH, Total Dissolved Solids, and drainage impact.",
        "NOISE": "Day/night ambient noise levels, CHP boundary noise, and heavy equipment acoustic footprint.",
        "VIBRATION": "Blasting ground vibration (Peak Particle Velocity - PPV) and air overpressure monitoring.",
        "LAND": "Overburden dump slope stability, topsoil conservation, and subsidence monitoring.",
        "RECLAMATION": "Progressive backfilling, biological restoration, and plantation survival rates.",
        "WASTE": "Hazardous waste management, used oil containment, and bio-medical disposal.",
        "OTHER": "Environmental clearances, Consent to Operate compliance, and statutory conditions.",
    }
    for d in EnvironmentalDomain:
        count = sum(1 for p in all_params if p.domain == d)
        domains_info.append({
            "domain": d.value,
            "name": d.value.replace("_", " "),
            "description": descriptions.get(d.value, "Environmental monitoring domain."),
            "parameters_count": count,
        })
    return domains_info


@app.get("/api/environment/thresholds")
def list_environmental_thresholds_endpoint(
    parameter_id: Optional[str] = Query(None),
    mine_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    """List configurable environmental thresholds."""
    return [t.dict() for t in db.list_environmental_thresholds(parameter_id=parameter_id, mine_type=mine_type, active_only=active_only)]


@app.post("/api/environment/thresholds")
def create_environmental_threshold_endpoint(
    req: EnvironmentalThresholdCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Create or configure an environmental threshold (Admin / Corporate authorized)."""
    th_id = f"ENV-TH-{uuid4().hex[:8].upper()}"
    th = EnvironmentalThreshold(
        id=th_id,
        parameter_id=req.parameter_id,
        mine_type=req.mine_type or "ALL",
        threshold_type=req.threshold_type or "MAX_LIMIT",
        lower_limit=req.lower_limit,
        upper_limit=req.upper_limit,
        unit=req.unit,
        severity=req.severity or "HIGH",
        source_reference=req.source_reference or "DEMO / CONFIGURED RULE",
        is_demo_rule=req.is_demo_rule if req.is_demo_rule is not None else True,
        active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.save_environmental_threshold(th)
    return db.get_environmental_threshold(th_id)


@app.get("/api/environment/measurements")
def list_environmental_measurements_endpoint(
    mine_id: Optional[str] = Query(None),
    parameter_id: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """List historical environmental measurements with optional filters and scope verification."""
    if mine_id:
        _check_scope_access(mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    measurements = db.list_environmental_measurements(
        mine_id=mine_id,
        parameter_id=parameter_id,
        domain=domain,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return [m.dict() for m in measurements]


@app.post("/api/environment/measurements")
def record_environmental_measurement_endpoint(
    req: EnvironmentalMeasurementCreate,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """
    Record an environmental measurement, evaluate against configured thresholds,
    and trigger automated Finding/ComplianceCase synthesis if limits are breached.
    """
    _check_scope_access(req.mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    actor_id = x_user_role or "SYSTEM"
    return record_environmental_measurement(req.dict(), actor_id=actor_id)


@app.get("/api/environment/obligations")
def list_environmental_obligations_endpoint(
    mine_id: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    active_only: bool = Query(True),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """List statutory environmental obligations for a mine."""
    if mine_id:
        _check_scope_access(mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    obligations = db.list_environmental_obligations(mine_id=mine_id, domain=domain, active_only=active_only)
    return [o.dict() for o in obligations]


@app.get("/api/environment/schedules")
def list_environmental_schedules_endpoint(
    mine_id: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """List environmental monitoring schedule instances."""
    if mine_id:
        _check_scope_access(mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    schedules = db.list_environmental_schedules(mine_id=mine_id, domain=domain, status=status)
    return [s.dict() for s in schedules]


@app.get("/api/environment/violations")
def list_environmental_violations_endpoint(
    mine_id: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """List active environmental threshold violation events."""
    if mine_id:
        _check_scope_access(mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    measurements = db.list_environmental_measurements(mine_id=mine_id, limit=200)
    violations = [m for m in measurements if m.status == "FLAGGED_ANOMALY"]
    return [v.dict() for v in violations]


@app.get("/api/environment/risk")
def get_environmental_risk_endpoint(
    mine_id: str = Query(..., description="Target mine ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """Retrieve transparent, deterministic environmental risk score and drivers for a mine."""
    _check_scope_access(mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    return calculate_environmental_risk(mine_id)


@app.get("/api/environment/cases")
def list_environmental_cases_endpoint(
    mine_id: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """List compliance cases originated from environmental threshold breaches."""
    if mine_id:
        _check_scope_access(mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    all_cases = db.list_compliance_cases(mine_id=mine_id)
    env_cases = [c for c in all_cases if c.category in EnvironmentalDomain.__members__ or c.source_type == CaseSourceType.ENVIRONMENTAL_VIOLATION]
    return [c.dict() for c in env_cases]


@app.get("/api/environment/reports")
def list_environmental_reports_endpoint(
    mine_id: Optional[str] = Query(None),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """List generated regulatory environmental reports."""
    if mine_id:
        _check_scope_access(mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    reports = db.list_environmental_reports(mine_id=mine_id)
    return [r.dict() for r in reports]


@app.post("/api/environment/reports/generate")
def generate_environmental_report_endpoint(
    req: EnvironmentalReportGenerateRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_scope_type: Optional[str] = Header(None, alias="X-User-Scope-Type"),
    x_user_scope_id: Optional[str] = Header(None, alias="X-User-Scope-Id"),
):
    """Generate a formal traceable environmental regulatory report for a mine."""
    _check_scope_access(req.mine_id, x_user_role, x_user_scope_type, x_user_scope_id)
    actor_id = x_user_role or "SYSTEM"
    report = generate_environmental_report(
        mine_id=req.mine_id,
        period_start=req.period_start,
        period_end=req.period_end,
        report_type=req.report_type or "MONITORING_SUMMARY",
        generated_by=actor_id,
    )
    return report.dict()


@app.post("/api/environment/reports/{id}/finalize")
def finalize_environmental_report_endpoint(
    id: str,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Finalize an environmental report with cryptographic SHA-256 hash and IPFS CID."""
    actor_id = x_user_role or "REGULATORY_OFFICER"
    report = finalize_environmental_report(id, finalized_by=actor_id)
    return report.dict()


@app.get("/api/environment/reports/{id}")
def get_environmental_report_endpoint(id: str):
    """Retrieve full environmental report details and cryptographic verification proof."""
    report = db.get_environmental_report(id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Environmental report '{id}' not found")
    return report.dict()


# ============================================================
# FRONTEND
# ============================================================


STATIC_DIR = (
    Path(__file__).parent
    / "static"
)

app.mount(
    "/",
    StaticFiles(
        directory=STATIC_DIR,
        html=True,
    ),
    name="static",
)
