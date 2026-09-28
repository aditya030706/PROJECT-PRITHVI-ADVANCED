"""
Tests for the current PRITHVI verification workflow.
"""

import sys
from pathlib import Path
from datetime import date, datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.database as db

from app.models import (
    Mine,
    Inspection,
    InspectionStatus,
    InspectionTemplate,
    HumanReview,
    VerificationResult,
    VerificationSignal,
    VerificationStatus,
    DecisionType,
    MineType,
    GassyDegree,
)


def create_test_parents():
    """Create the parent records required by the inspection foreign keys."""

    mine = Mine(
        mine_id="MINE-TEST-001",
        name="PRITHVI Test Mine",
        subsidiary="Test Subsidiary",
        state="Jharkhand",
        district="Dhanbad",
        mine_type=MineType.UNDERGROUND_COAL,
        mining_method="underground",
        gassy_degree=GassyDegree.DEGREE_II,
        mechanised=True,
        uses_hemm=False,
        has_winding_installation=True,
        blasting_operation=False,
        active=True,
    )

    template = InspectionTemplate(
        template_id="INS-VENT-GAS-001",
        name="Ventilation & Gas Monitoring Inspection",
        inspection_family="Ventilation & Gas",
        description="Test inspection template.",
        applicable_mine_types=[MineType.UNDERGROUND_COAL],
        regulatory_obligation_ids=[],
        frequency_or_trigger="Periodic",
        active=True,
    )

    db.save_mine(mine)
    db.save_inspection_template(template)


def create_test_inspection(inspection_id: str) -> Inspection:
    inspection = Inspection(
        inspection_id=inspection_id,
        mine_id="MINE-TEST-001",
        template_id="INS-VENT-GAS-001",
        obligation_id=None,
        inspector_id="INSPECTOR-TEST-001",
        started_at=datetime.now(timezone.utc),
        submitted_at=datetime.now(timezone.utc),
        inspection_date=date(2026, 8, 28),
        status=InspectionStatus.REVIEW_REQUIRED,
        latitude=23.7542,
        longitude=86.2678,
        gps_accuracy_m=6.5,
    )

    db.save_inspection(inspection)
    return inspection


def make_verification(
    inspection_id: str,
    verification_id: str = "VER-TEST-001",
    human_decision_required: bool = True,
):
    return VerificationResult(
        verification_id=verification_id,
        inspection_id=inspection_id,
        status=VerificationStatus.VERIFICATION_REQUIRED,
        confidence=0.78,
        signals=[
            VerificationSignal(
                signal_id="SIG-TEST-001",
                inspection_id=inspection_id,
                category="evidence",
                name="Evidence availability",
                status="insufficient_evidence",
                severity="warning",
                score=0.0,
                explanation="No supporting evidence was attached.",
            )
        ],
        source_anomalies=[],
        evidence_conflicts=[],
        recommendation=(
            "Human review required before making a determination."
        ),
        human_decision_required=human_decision_required,
    )


def test_verification_can_be_saved_and_retrieved(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        db,
        "DB_PATH",
        tmp_path / "verification.db",
    )

    db.init_db()
    create_test_parents()

    inspection_id = "INS-TEST-001"
    create_test_inspection(inspection_id)

    verification = make_verification(inspection_id)

    db.save_verification_result(verification)

    result = db.get_verification(inspection_id)

    assert result is not None
    assert result.verification_id == "VER-TEST-001"
    assert result.inspection_id == inspection_id
    assert result.status == VerificationStatus.VERIFICATION_REQUIRED
    assert result.confidence == 0.78
    assert result.human_decision_required is True


def test_pending_verification_is_listed(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        db,
        "DB_PATH",
        tmp_path / "pending.db",
    )

    db.init_db()
    create_test_parents()

    inspection_id = "INS-PENDING-001"
    create_test_inspection(inspection_id)

    verification = make_verification(
        inspection_id,
        verification_id="VER-PENDING-001",
    )

    db.save_verification_result(verification)

    pending = db.list_pending_verifications()

    assert len(pending) == 1
    assert pending[0]["inspection_id"] == inspection_id
    assert pending[0]["status"] == "verification_required"


def test_reviewed_verification_leaves_pending_queue(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        db,
        "DB_PATH",
        tmp_path / "review.db",
    )

    db.init_db()
    create_test_parents()

    inspection_id = "INS-REVIEW-001"
    create_test_inspection(inspection_id)

    verification = make_verification(
        inspection_id,
        verification_id="VER-REVIEW-001",
    )

    db.save_verification_result(verification)

    pending_before = db.list_pending_verifications()

    assert len(pending_before) == 1

    review = HumanReview(
        review_id="REV-TEST-001",
        inspection_id=inspection_id,
        reviewer_id="OFFICER-001",
        decision=DecisionType.ACCEPT,
        reason="Inspection evidence reviewed and accepted.",
        reviewed_at=datetime.now(timezone.utc),
    )

    db.save_human_review(review)

    pending_after = db.list_pending_verifications()

    assert not any(
        item["inspection_id"] == inspection_id
        for item in pending_after
    )


def test_verification_detail_preserves_signals(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        db,
        "DB_PATH",
        tmp_path / "signals.db",
    )

    db.init_db()
    create_test_parents()

    inspection_id = "INS-SIGNALS-001"
    create_test_inspection(inspection_id)

    verification = make_verification(
        inspection_id,
        verification_id="VER-SIGNALS-001",
    )

    db.save_verification_result(verification)

    result = db.get_verification(inspection_id)

    assert result is not None
    assert len(result.signals) == 1

    signal = result.signals[0]

    assert signal.category == "evidence"
    assert signal.status == "insufficient_evidence"
    assert signal.severity == "warning"
    assert signal.explanation


def test_non_reviewable_verification_is_not_pending(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        db,
        "DB_PATH",
        tmp_path / "non_pending.db",
    )

    db.init_db()
    create_test_parents()

    inspection_id = "INS-NO-REVIEW-001"
    create_test_inspection(inspection_id)

    verification = make_verification(
        inspection_id,
        verification_id="VER-NO-REVIEW-001",
        human_decision_required=False,
    )

    db.save_verification_result(verification)

    pending = db.list_pending_verifications()

    assert not any(
        item["inspection_id"] == inspection_id
        for item in pending
    )