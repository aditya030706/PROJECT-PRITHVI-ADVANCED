"""
Persistence layer for PRITHVI Feature 1.

PRITHVI architecture:

Mine
    ↓
Regulatory Obligation
    ↓
Inspection Template
    ↓
Inspection
    ↓
Measurements / Checklist / Evidence
    ↓
Verification
    ↓
Human Review
    ↓
Corrective Action

SQLite is used for the SIH prototype because it requires no separate
database server. The architecture is intentionally structured so the
persistence layer can later be migrated to PostgreSQL.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import (
    ChecklistResult,
    CorrectiveAction,
    ComplianceCase,
    CaseSourceType,
    CaseStatus,
    CaseCorrectionEvidence,
    CaseAuditEvent,
    Evidence,
    Finding,
    Inspection,
    InspectionStatus,
    InspectionTemplate,
    Measurement,
    MeasurementDefinition,
    ChecklistItem,
    EvidenceRequirement,
    EvidenceType,
    MineType,
    Mine,
    RegulatoryObligation,
    RegulatorySource,
    Sensor,
    SensorReading,
    VerificationResult,
    VerificationSignal,
    HumanReview,
    RegulatoryScheduleRule,
    MineInspectionSchedule,
    ProductionRecord,
    ProductionTarget,
    ProductionAnomaly,
    ProductionSource,
    ContractType,
    ProductionOperationType,
    ProductionRecordStatus,
    OrganizationUnit,
    OperationalUnit,
    ContractorMaster,
    ContractMaster,
    WorkerMaster,
    OrganizationAuditEvent,
    OrganizationUnitType,
    OperationalUnitType,
    ContractorType,
    WorkerType,
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


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_PATH = Path(__file__).parent / "data" / "prithvi.db"


def _connect() -> sqlite3.Connection:
    """
    Open a SQLite connection.

    Row factory allows rows to be accessed using column names.
    WAL mode and busy_timeout prevent 'database is locked' errors.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row

    # Foreign-key enforcement & WAL concurrency
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")

    return conn



# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db() -> None:
    """
    Create all PRITHVI tables.

    Safe to call every time the application starts.
    """

    conn = _connect()

    # --------------------------------------------------------
    # MINES
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mines (
            mine_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            subsidiary TEXT,
            state TEXT,
            district TEXT,
            mine_type TEXT NOT NULL,
            mining_method TEXT,
            gassy_degree TEXT NOT NULL,
            mechanised INTEGER NOT NULL DEFAULT 0,
            uses_hemm INTEGER NOT NULL DEFAULT 0,
            has_winding_installation INTEGER NOT NULL DEFAULT 0,
            blasting_operation INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    # --------------------------------------------------------
    # REGULATORY SOURCES
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS regulatory_sources (
            source_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            regulation_number TEXT,
            chapter TEXT,
            description TEXT NOT NULL,
            source_document TEXT,
            source_reference TEXT
        )
        """
    )

    # --------------------------------------------------------
    # REGULATORY OBLIGATIONS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS regulatory_obligations (
            obligation_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            title TEXT NOT NULL,
            requirement_type TEXT NOT NULL,
            requirement TEXT NOT NULL,
            applicability TEXT NOT NULL,
            frequency_or_trigger TEXT,
            responsible_role TEXT,
            required_record_or_evidence TEXT,
            active INTEGER NOT NULL DEFAULT 1,

            FOREIGN KEY(source_id)
                REFERENCES regulatory_sources(source_id)
        )
        """
    )

    # --------------------------------------------------------
    # INSPECTION TEMPLATES
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inspection_templates (
            template_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            inspection_family TEXT NOT NULL,
            description TEXT,
            frequency_or_trigger TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    # Which mine types can use a template.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS template_mine_types (
            template_id TEXT NOT NULL,
            mine_type TEXT NOT NULL,

            PRIMARY KEY(template_id, mine_type),

            FOREIGN KEY(template_id)
                REFERENCES inspection_templates(template_id)
                ON DELETE CASCADE
        )
        """
    )

    # Which regulations support a template.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS template_obligations (
            template_id TEXT NOT NULL,
            obligation_id TEXT NOT NULL,

            PRIMARY KEY(template_id, obligation_id),

            FOREIGN KEY(template_id)
                REFERENCES inspection_templates(template_id)
                ON DELETE CASCADE,

            FOREIGN KEY(obligation_id)
                REFERENCES regulatory_obligations(obligation_id)
        )
        """
    )

    # --------------------------------------------------------
    # TEMPLATE MEASUREMENTS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS template_measurements (
            measurement_id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            name TEXT NOT NULL,
            unit TEXT,
            required INTEGER NOT NULL DEFAULT 1,
            description TEXT,

            FOREIGN KEY(template_id)
                REFERENCES inspection_templates(template_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # TEMPLATE CHECKLIST
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS template_checklist (
            item_id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            question TEXT NOT NULL,
            required INTEGER NOT NULL DEFAULT 1,
            severity_if_failed TEXT,

            FOREIGN KEY(template_id)
                REFERENCES inspection_templates(template_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # TEMPLATE EVIDENCE REQUIREMENTS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS template_evidence_requirements (
            evidence_id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            name TEXT NOT NULL,
            required INTEGER NOT NULL DEFAULT 1,
            minimum_count INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY(template_id)
                REFERENCES inspection_templates(template_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # INSPECTIONS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inspections (
            inspection_id TEXT PRIMARY KEY,

            mine_id TEXT NOT NULL,

            template_id TEXT NOT NULL,

            obligation_id TEXT,

            inspector_id TEXT NOT NULL,

            started_at TEXT,
            submitted_at TEXT,

            inspection_date TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'draft',

            latitude REAL,
            longitude REAL,
            gps_accuracy_m REAL,

            FOREIGN KEY(mine_id)
                REFERENCES mines(mine_id),

            FOREIGN KEY(template_id)
                REFERENCES inspection_templates(template_id),

            FOREIGN KEY(obligation_id)
                REFERENCES regulatory_obligations(obligation_id)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_inspections_mine_date
        ON inspections(mine_id, inspection_date)
        """
    )

    # --------------------------------------------------------
    # MEASUREMENTS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS measurements (
            measurement_id TEXT PRIMARY KEY,

            inspection_id TEXT NOT NULL,

            measurement_type TEXT NOT NULL,

            value REAL NOT NULL,

            unit TEXT,

            source TEXT NOT NULL DEFAULT 'manual',

            captured_at TEXT,

            FOREIGN KEY(inspection_id)
                REFERENCES inspections(inspection_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # CHECKLIST RESULTS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS checklist_results (
            result_id TEXT PRIMARY KEY,

            inspection_id TEXT NOT NULL,

            item_id TEXT NOT NULL,

            passed INTEGER NOT NULL,

            observation TEXT,

            FOREIGN KEY(inspection_id)
                REFERENCES inspections(inspection_id)
                ON DELETE CASCADE,

            FOREIGN KEY(item_id)
                REFERENCES template_checklist(item_id)
        )
        """
    )

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id TEXT PRIMARY KEY,

            inspection_id TEXT NOT NULL,

            evidence_type TEXT NOT NULL,

            filename TEXT,

            storage_reference TEXT,

            captured_at TEXT,

            latitude REAL,
            longitude REAL,

            sha256 TEXT,

            perceptual_hash TEXT,

            metadata_verified INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY(inspection_id)
                REFERENCES inspections(inspection_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # SENSORS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sensors (
            sensor_id TEXT PRIMARY KEY,

            mine_id TEXT NOT NULL,

            sensor_type TEXT NOT NULL,

            location_description TEXT,

            latitude REAL,
            longitude REAL,

            calibration_status TEXT,

            last_calibrated_at TEXT,

            reliability_score REAL NOT NULL DEFAULT 1.0,

            active INTEGER NOT NULL DEFAULT 1,

            FOREIGN KEY(mine_id)
                REFERENCES mines(mine_id)
        )
        """
    )

    # --------------------------------------------------------
    # SENSOR READINGS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_readings (
            reading_id TEXT PRIMARY KEY,

            sensor_id TEXT NOT NULL,

            mine_id TEXT NOT NULL,

            reading_time TEXT NOT NULL,

            measurement_type TEXT NOT NULL,

            value REAL NOT NULL,

            unit TEXT,

            FOREIGN KEY(sensor_id)
                REFERENCES sensors(sensor_id),

            FOREIGN KEY(mine_id)
                REFERENCES mines(mine_id)
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_sensor_readings_sensor_time
        ON sensor_readings(sensor_id, reading_time)
        """
    )

    # --------------------------------------------------------
    # FINDINGS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS findings (
            finding_id TEXT PRIMARY KEY,

            inspection_id TEXT NOT NULL,

            title TEXT NOT NULL,

            description TEXT NOT NULL,

            severity TEXT NOT NULL,

            corrective_action_required INTEGER NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'open',

            FOREIGN KEY(inspection_id)
                REFERENCES inspections(inspection_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # CORRECTIVE ACTIONS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS corrective_actions (
            action_id TEXT PRIMARY KEY,

            finding_id TEXT,

            description TEXT NOT NULL,

            assigned_to TEXT,

            due_date TEXT,

            completed_at TEXT,

            status TEXT NOT NULL DEFAULT 'open',

            FOREIGN KEY(finding_id)
                REFERENCES findings(finding_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # VERIFICATION SIGNALS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verification_signals (
            signal_id TEXT PRIMARY KEY,

            inspection_id TEXT NOT NULL,

            category TEXT NOT NULL,

            name TEXT NOT NULL,

            status TEXT NOT NULL,

            severity TEXT NOT NULL DEFAULT 'info',

            score REAL,

            explanation TEXT NOT NULL,

            FOREIGN KEY(inspection_id)
                REFERENCES inspections(inspection_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # VERIFICATION RESULTS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verification_results (
            verification_id TEXT PRIMARY KEY,

            inspection_id TEXT NOT NULL,

            status TEXT NOT NULL,

            confidence REAL NOT NULL,

            recommendation TEXT NOT NULL,

            human_decision_required INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY(inspection_id)
                REFERENCES inspections(inspection_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # SOURCE ANOMALIES
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verification_source_anomalies (
            verification_id TEXT NOT NULL,
            source_id TEXT NOT NULL,

            PRIMARY KEY(verification_id, source_id),

            FOREIGN KEY(verification_id)
                REFERENCES verification_results(verification_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # EVIDENCE CONFLICTS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verification_conflicts (
            verification_id TEXT NOT NULL,
            conflict TEXT NOT NULL,

            FOREIGN KEY(verification_id)
                REFERENCES verification_results(verification_id)
                ON DELETE CASCADE
        )
        """
    )

    # --------------------------------------------------------
    # HUMAN REVIEWS
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS human_reviews (
            review_id TEXT PRIMARY KEY,

            inspection_id TEXT NOT NULL,

            reviewer_id TEXT NOT NULL,

            decision TEXT NOT NULL,

            reason TEXT NOT NULL,

            reviewed_at TEXT NOT NULL,

            FOREIGN KEY(inspection_id)
                REFERENCES inspections(inspection_id)
        )
        """
    )

    # --------------------------------------------------------
    # REGULATORY SCHEDULE RULES
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS regulatory_schedule_rules (
            schedule_id TEXT PRIMARY KEY,
            obligation_id TEXT NOT NULL,
            template_id TEXT NOT NULL,
            name TEXT NOT NULL,
            frequency_type TEXT NOT NULL,
            interval_value INTEGER,
            interval_unit TEXT,
            trigger_type TEXT,
            applicable_mine_types TEXT,
            applicable_gassy_degrees TEXT,
            condition_description TEXT,
            responsible_role TEXT,
            regulation_reference TEXT,
            source_document TEXT,
            source_reference TEXT,
            source_date TEXT,
            effective_from TEXT,
            effective_to TEXT,
            validation_status TEXT NOT NULL DEFAULT 'REQUIRES_VALIDATION',
            active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(obligation_id) REFERENCES regulatory_obligations(obligation_id),
            FOREIGN KEY(template_id) REFERENCES inspection_templates(template_id)
        )
        """
    )

    # Non-destructive migration for databases created before the
    # regulatory source/version fields were introduced.
    existing_schedule_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(regulatory_schedule_rules)"
        ).fetchall()
    }
    for column_name in (
        "regulation_reference",
        "source_document",
        "source_date",
        "effective_from",
        "effective_to",
    ):
        if column_name not in existing_schedule_columns:
            conn.execute(
                f"ALTER TABLE regulatory_schedule_rules ADD COLUMN {column_name} TEXT"
            )

    # Non-destructive migration: inspection_templates — add metadata columns
    existing_template_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(inspection_templates)"
        ).fetchall()
    }
    for col in ("responsible_role", "regulation_reference", "frequency_label"):
        if col not in existing_template_columns:
            conn.execute(
                f"ALTER TABLE inspection_templates ADD COLUMN {col} TEXT"
            )

    # Non-destructive migration: template_measurements — add threshold columns
    existing_meas_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(template_measurements)"
        ).fetchall()
    }
    for col, col_type in (
        ("min_value", "REAL"),
        ("max_value", "REAL"),
        ("threshold_label", "TEXT"),
        ("options", "TEXT"),
    ):
        if col not in existing_meas_columns:
            conn.execute(
                f"ALTER TABLE template_measurements ADD COLUMN {col} {col_type}"
            )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mine_inspection_schedules (
            schedule_instance_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            schedule_id TEXT NOT NULL,
            last_completed_at TEXT,
            next_due_at TEXT,
            status TEXT NOT NULL DEFAULT 'upcoming',
            generated_at TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id),
            FOREIGN KEY(schedule_id) REFERENCES regulatory_schedule_rules(schedule_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mine_schedule_due
        ON mine_inspection_schedules(mine_id, next_due_at)
        """
    )

    # Ensure human_reviews has previous_status and new_status columns
    try:
        conn.execute("ALTER TABLE human_reviews ADD COLUMN previous_status TEXT")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE human_reviews ADD COLUMN new_status TEXT")
    except Exception:
        pass

    # --------------------------------------------------------
    # DGMS ENFORCEMENT & REGULATORY ACTIONS (PHASE 2 TASK 5)
    # --------------------------------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS enforcement_actions (
            action_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            inspection_id TEXT,
            action_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            reason TEXT NOT NULL,
            officer_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_enforcement_mine
        ON enforcement_actions(mine_id, created_at)
        """
    )

    # --------------------------------------------------------
    # FINDING ↔ EVIDENCE RELATIONSHIP
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS finding_evidence (
            finding_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            PRIMARY KEY (finding_id, evidence_id),
            FOREIGN KEY(finding_id) REFERENCES findings(finding_id) ON DELETE CASCADE,
            FOREIGN KEY(evidence_id) REFERENCES evidence(evidence_id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_finding_evidence_evidence
        ON finding_evidence(evidence_id)
        """
    )

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,

            entity_type TEXT NOT NULL,

            entity_id TEXT NOT NULL,

            action TEXT NOT NULL,

            actor_id TEXT,

            timestamp TEXT NOT NULL,

            details TEXT
        )
        """
    )

    # --------------------------------------------------------
    # COMPLIANCE CASES (PHASE 2 TASK 6)
    # --------------------------------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS compliance_cases (
            case_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            inspection_id TEXT,
            finding_id TEXT,
            category TEXT NOT NULL,
            regulation_reference TEXT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            risk_level TEXT,
            status TEXT NOT NULL DEFAULT 'OPEN',
            source_type TEXT NOT NULL,
            source_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT,
            closed_by TEXT,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id),
            FOREIGN KEY(inspection_id) REFERENCES inspections(inspection_id)
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_compliance_cases_source
        ON compliance_cases(source_type, source_id)
        WHERE source_id IS NOT NULL
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_compliance_cases_mine_status
        ON compliance_cases(mine_id, status)
        """
    )

    # Non-destructive migration for corrective_actions: ensure finding_id is nullable and add Task 6 columns
    table_info = conn.execute("PRAGMA table_info(corrective_actions)").fetchall()
    finding_col = next((row for row in table_info if row["name"] == "finding_id"), None)
    if finding_col and finding_col["notnull"] == 1:
        # Rebuild table to remove NOT NULL constraint from finding_id
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute(
            """
            CREATE TABLE corrective_actions_migration (
                action_id TEXT PRIMARY KEY,
                finding_id TEXT,
                case_id TEXT,
                mine_id TEXT,
                title TEXT,
                description TEXT NOT NULL,
                assigned_role TEXT,
                assigned_user_id TEXT,
                assigned_to TEXT,
                due_at TEXT,
                due_date TEXT,
                priority TEXT NOT NULL DEFAULT 'MEDIUM',
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT,
                completed_by TEXT,
                FOREIGN KEY(finding_id) REFERENCES findings(finding_id) ON DELETE CASCADE,
                FOREIGN KEY(case_id) REFERENCES compliance_cases(case_id) ON DELETE CASCADE
            )
            """
        )
        existing_names = {row["name"] for row in table_info}
        cols_to_select = [
            "action_id",
            "finding_id",
            "case_id" if "case_id" in existing_names else "NULL AS case_id",
            "mine_id" if "mine_id" in existing_names else "NULL AS mine_id",
            "title" if "title" in existing_names else "NULL AS title",
            "description",
            "assigned_role" if "assigned_role" in existing_names else "NULL AS assigned_role",
            "assigned_user_id" if "assigned_user_id" in existing_names else "NULL AS assigned_user_id",
            "assigned_to",
            "due_at" if "due_at" in existing_names else "NULL AS due_at",
            "due_date",
            "priority" if "priority" in existing_names else "'MEDIUM' AS priority",
            "status",
            "created_at" if "created_at" in existing_names else "NULL AS created_at",
            "updated_at" if "updated_at" in existing_names else "NULL AS updated_at",
            "completed_at",
            "completed_by" if "completed_by" in existing_names else "NULL AS completed_by",
        ]
        conn.execute(
            f"INSERT INTO corrective_actions_migration SELECT {', '.join(cols_to_select)} FROM corrective_actions"
        )
        conn.execute("DROP TABLE corrective_actions")
        conn.execute("ALTER TABLE corrective_actions_migration RENAME TO corrective_actions")
        conn.execute("PRAGMA foreign_keys = ON")

    existing_action_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(corrective_actions)").fetchall()
    }
    for col, col_type in (
        ("case_id", "TEXT"),
        ("mine_id", "TEXT"),
        ("title", "TEXT"),
        ("assigned_role", "TEXT"),
        ("assigned_user_id", "TEXT"),
        ("due_at", "TEXT"),
        ("priority", "TEXT NOT NULL DEFAULT 'MEDIUM'"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
        ("completed_by", "TEXT"),
    ):
        if col not in existing_action_cols:
            conn.execute(f"ALTER TABLE corrective_actions ADD COLUMN {col} {col_type}")

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_corrective_actions_case
        ON corrective_actions(case_id)
        """
    )

    # --------------------------------------------------------
    # CASE CORRECTION EVIDENCE (PHASE 2 TASK 6)
    # --------------------------------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS case_correction_evidence (
            evidence_link_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            action_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            submitted_by TEXT NOT NULL,
            notes TEXT,
            sha256 TEXT,
            ipfs_cid TEXT,
            audit_proof_status TEXT NOT NULL DEFAULT 'AUDIT_PROOF_RECORDED',
            FOREIGN KEY(case_id) REFERENCES compliance_cases(case_id) ON DELETE CASCADE,
            FOREIGN KEY(action_id) REFERENCES corrective_actions(action_id) ON DELETE CASCADE,
            FOREIGN KEY(evidence_id) REFERENCES evidence(evidence_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_case_evidence_case
        ON case_correction_evidence(case_id)
        """
    )

    # --------------------------------------------------------
    # CASE AUDIT EVENTS (PHASE 2 TASK 6)
    # --------------------------------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS case_audit_events (
            event_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            actor_role TEXT,
            previous_state TEXT,
            new_state TEXT,
            reason TEXT,
            timestamp TEXT NOT NULL,
            details TEXT,
            sha256 TEXT,
            ipfs_cid TEXT,
            FOREIGN KEY(case_id) REFERENCES compliance_cases(case_id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_case_audit_case
        ON case_audit_events(case_id, timestamp)
        """
    )

    # --------------------------------------------------------
    # CRYPTOGRAPHIC PROOFS LEDGER (PHASE 2 TASK 6)
    # --------------------------------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cryptographic_proofs (
            proof_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            actor_role TEXT,
            sha256 TEXT NOT NULL,
            ipfs_cid TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'AUDIT_PROOF_RECORDED',
            ledger_standard TEXT NOT NULL DEFAULT 'PRITHVI-STATUTORY-AUDIT-V1',
            verified INTEGER NOT NULL DEFAULT 1,
            payload TEXT,
            FOREIGN KEY(case_id) REFERENCES compliance_cases(case_id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_crypto_proofs_case
        ON cryptographic_proofs(case_id, timestamp)
        """
    )

    # --------------------------------------------------------
    # EVIDENCE INTEGRITY LEDGER (PHASE 2 TASK 7)
    # --------------------------------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_integrity (
            integrity_id TEXT PRIMARY KEY,
            evidence_id TEXT NOT NULL UNIQUE,
            content_hash TEXT NOT NULL,
            hash_algorithm TEXT NOT NULL DEFAULT 'SHA-256',
            ipfs_cid TEXT,
            ipfs_status TEXT NOT NULL DEFAULT 'PENDING',
            blockchain_network TEXT,
            transaction_ref TEXT,
            block_ref TEXT,
            anchored_at TEXT,
            anchor_mode TEXT NOT NULL DEFAULT 'DEMO_AUDIT_MODE',
            status TEXT NOT NULL DEFAULT 'PENDING',
            verified_at TEXT,
            verification_result TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(evidence_id) REFERENCES evidence(evidence_id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_evidence_integrity_evidence_id
        ON evidence_integrity(evidence_id)
        """
    )

    # Non-destructive migration: evidence table — add integrity columns for Task 7
    existing_evidence_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(evidence)").fetchall()
    }
    for col, col_type in (
        ("ipfs_cid", "TEXT"),
        ("anchor_status", "TEXT"),
    ):
        if col not in existing_evidence_cols:
            conn.execute(f"ALTER TABLE evidence ADD COLUMN {col} {col_type}")

    # --------------------------------------------------------
    # GIS ATTENDANCE — PHASE 2 TASK 8
    # --------------------------------------------------------

    # Non-destructive migration: add lat/lon to mines table
    existing_mine_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(mines)").fetchall()
    }
    for col, col_type in (
        ("latitude", "REAL"),
        ("longitude", "REAL"),
        ("geofence_radius_meters", "REAL"),
    ):
        if col not in existing_mine_cols:
            conn.execute(f"ALTER TABLE mines ADD COLUMN {col} {col_type}")

    # Mine zones — named geographic areas within a mine
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mine_zones (
            mine_zone_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            geofence_radius_meters REAL NOT NULL DEFAULT 500.0,
            description TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mine_zones_mine_id
        ON mine_zones(mine_id)
        """
    )

    # Attendance records
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_records (
            attendance_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            user_role TEXT NOT NULL,
            mine_id TEXT NOT NULL,
            zone_id TEXT,
            schedule_instance_id TEXT,
            inspection_id TEXT,
            latitude REAL,
            longitude REAL,
            accuracy_meters REAL,
            captured_at TEXT,
            server_recorded_at TEXT NOT NULL,
            geofence_status TEXT NOT NULL,
            distance_from_reference_meters REAL,
            status TEXT NOT NULL DEFAULT 'VALID',
            anomaly_status TEXT NOT NULL DEFAULT 'NONE',
            evidence_id TEXT,
            device_info TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_attendance_user_mine
        ON attendance_records(user_id, mine_id, server_recorded_at)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_attendance_mine_date
        ON attendance_records(mine_id, server_recorded_at)
        """
    )

    # --------------------------------------------------------
    # SCADA / SENSOR TELEMETRY — PHASE 2 TASK 9
    # --------------------------------------------------------

    # Sensor definitions
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sensors (
            sensor_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            zone_id TEXT,
            sensor_code TEXT NOT NULL UNIQUE,
            sensor_type TEXT NOT NULL,
            unit TEXT NOT NULL,
            display_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            simulated INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sensors_mine
        ON sensors(mine_id)
        """
    )

    # Non-destructive migration: sensors table columns
    existing_sensor_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(sensors)").fetchall()
    }
    for col, col_type in (
        ("zone_id", "TEXT"),
        ("sensor_code", "TEXT"),
        ("unit", "TEXT"),
        ("display_name", "TEXT"),
        ("status", "TEXT DEFAULT 'ACTIVE'"),
        ("simulated", "INTEGER DEFAULT 1"),
        ("created_at", "TEXT"),
    ):
        if col not in existing_sensor_cols:
            conn.execute(f"ALTER TABLE sensors ADD COLUMN {col} {col_type}")

    # Telemetry readings stream
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS telemetry_readings (
            reading_id TEXT PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            mine_id TEXT NOT NULL,
            zone_id TEXT,
            sensor_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            received_at TEXT NOT NULL,
            quality_status TEXT NOT NULL DEFAULT 'GOOD',
            threshold_status TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'SCADA_SIMULATOR',
            simulated INTEGER NOT NULL DEFAULT 1,
            evidence_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(sensor_id) REFERENCES sensors(sensor_id),
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_telemetry_mine_time
        ON telemetry_readings(mine_id, recorded_at)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_time
        ON telemetry_readings(sensor_id, recorded_at)
        """
    )

    # Safety signals (explainable deduplicated conditions)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS safety_signals (
            signal_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            sensor_id TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            observed_value REAL NOT NULL,
            unit TEXT NOT NULL,
            threshold_definition TEXT NOT NULL,
            explanation TEXT NOT NULL,
            first_detected_at TEXT NOT NULL,
            last_detected_at TEXT NOT NULL,
            recovered_at TEXT,
            consecutive_readings INTEGER NOT NULL DEFAULT 1,
            linked_case_id TEXT,
            evidence_id TEXT,
            simulated INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(sensor_id) REFERENCES sensors(sensor_id),
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_safety_signals_mine_active
        ON safety_signals(mine_id, status)
        """
    )

    # --------------------------------------------------------
    # PRODUCTION & OPERATIONAL GOVERNANCE (PHASE 2 TASK 10)
    # --------------------------------------------------------

    # Non-destructive migration: add area_id and area_name to mines table
    existing_mine_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(mines)").fetchall()
    }
    for col, col_type in (
        ("area_id", "TEXT"),
        ("area_name", "TEXT"),
    ):
        if col not in existing_mine_columns:
            conn.execute(f"ALTER TABLE mines ADD COLUMN {col} {col_type}")

    # Production Records
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS production_records (
            record_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            area_id TEXT,
            subsidiary_id TEXT,
            shift_name TEXT NOT NULL,
            production_date TEXT NOT NULL,
            production_quantity REAL NOT NULL,
            production_unit TEXT NOT NULL DEFAULT 'TONNES',
            dispatch_quantity REAL,
            production_source TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            zone_id TEXT,
            district_section TEXT,
            face_panel TEXT,
            overburden_quantity REAL,
            overburden_unit TEXT,
            contractor_id TEXT,
            contractor_name TEXT,
            contract_type TEXT,
            target_quantity REAL,
            downtime_minutes INTEGER NOT NULL DEFAULT 0,
            delay_reason TEXT,
            hemm_context TEXT,
            entered_by TEXT NOT NULL,
            source_reference TEXT,
            status TEXT NOT NULL DEFAULT 'RECORDED',
            is_superseded INTEGER NOT NULL DEFAULT 0,
            superseded_by TEXT,
            correction_reason TEXT,
            content_hash TEXT,
            simulated INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            recorded_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prod_mine_date
        ON production_records(mine_id, production_date)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prod_mine_shift
        ON production_records(mine_id, shift_name)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prod_area
        ON production_records(area_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prod_subsidiary
        ON production_records(subsidiary_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prod_status
        ON production_records(status, is_superseded)
        """
    )

    # Production Targets
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS production_targets (
            target_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            target_date TEXT NOT NULL,
            daily_target_tonnes REAL NOT NULL,
            monthly_target_tonnes REAL,
            dispatch_target_tonnes REAL,
            set_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id),
            UNIQUE(mine_id, target_date)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prod_targets_mine_date
        ON production_targets(mine_id, target_date)
        """
    )

    # Production Audit Events (Immutable change log for corrections)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS production_audit_events (
            event_id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            previous_state TEXT,
            new_state TEXT,
            reason TEXT,
            timestamp TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY(record_id) REFERENCES production_records(record_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prod_audit_record
        ON production_audit_events(record_id, timestamp)
        """
    )

    # Production Anomalies
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS production_anomalies (
            anomaly_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            anomaly_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            what TEXT NOT NULL,
            why TEXT NOT NULL,
            source TEXT NOT NULL,
            time TEXT NOT NULL,
            affected_record_ids TEXT,
            recommended_review TEXT NOT NULL,
            resolved INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_prod_anomalies_mine
        ON production_anomalies(mine_id, resolved)
        """
    )

    # --------------------------------------------------------
    # GOVERNANCE MASTER & ORGANIZATIONAL HIERARCHY (PHASE 2 TASK 11)
    # --------------------------------------------------------

    # Non-destructive migration: organization_unit_id in mines
    if "organization_unit_id" not in existing_mine_columns:
        conn.execute("ALTER TABLE mines ADD COLUMN organization_unit_id TEXT")

    # Canonical recursive organization units
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_units (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            unit_type TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            legal_name TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            state TEXT,
            district TEXT,
            headquarters TEXT,
            effective_from TEXT NOT NULL,
            effective_to TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(parent_id) REFERENCES organization_units(id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_org_parent
        ON organization_units(parent_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_org_type
        ON organization_units(unit_type)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_org_code
        ON organization_units(code)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_org_status
        ON organization_units(status)
        """
    )

    # Operational units (Mine -> Pit/Bench/Haulroad OR Shaft/District/Panel/Face)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS operational_units (
            id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            parent_operational_unit_id TEXT,
            unit_type TEXT NOT NULL,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            latitude REAL,
            longitude REAL,
            geofence_radius REAL,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id),
            FOREIGN KEY(parent_operational_unit_id) REFERENCES operational_units(id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_op_mine
        ON operational_units(mine_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_op_parent
        ON operational_units(parent_operational_unit_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_op_type
        ON operational_units(unit_type)
        """
    )

    # Contractor master records
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contractors (
            id TEXT PRIMARY KEY,
            legal_name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            registration_reference TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            contractor_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_contractor_type
        ON contractors(contractor_type)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_contractor_status
        ON contractors(status)
        """
    )

    # Contract master records
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contracts (
            id TEXT PRIMARY KEY,
            contractor_id TEXT NOT NULL,
            mine_id TEXT NOT NULL,
            area_id TEXT,
            subsidiary_id TEXT,
            contract_type TEXT NOT NULL,
            contract_number TEXT NOT NULL UNIQUE,
            scope TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT,
            workforce_limit INTEGER,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(contractor_id) REFERENCES contractors(id),
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_contract_mine
        ON contracts(mine_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_contract_contractor
        ON contracts(contractor_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_contract_status
        ON contracts(status)
        """
    )

    # Worker master records (Separate identity from application users)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            worker_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            worker_type TEXT NOT NULL,
            contractor_id TEXT,
            contract_id TEXT,
            mine_id TEXT NOT NULL,
            skill_category TEXT,
            department TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            onboarding_date TEXT NOT NULL,
            training_status TEXT NOT NULL DEFAULT 'VALID',
            identity_reference TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(contractor_id) REFERENCES contractors(id),
            FOREIGN KEY(contract_id) REFERENCES contracts(id),
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_worker_mine
        ON workers(mine_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_worker_contract
        ON workers(contract_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_worker_code
        ON workers(worker_code)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_worker_active
        ON workers(active)
        """
    )

    # Organizational hierarchy structural audit log
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_audit_events (
            event_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            previous_state TEXT,
            new_state TEXT,
            reason TEXT,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_org_audit_entity
        ON organization_audit_events(entity_id, timestamp)
        """
    )

    # --------------------------------------------------------
    # ENVIRONMENTAL GOVERNANCE (PHASE 2 TASK 13)
    # --------------------------------------------------------

    # 1. Environmental Parameters Master
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS environmental_parameters (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            unit TEXT NOT NULL,
            description TEXT,
            mine_type_applicability TEXT NOT NULL DEFAULT 'ALL',
            active INTEGER NOT NULL DEFAULT 1,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_param_domain
        ON environmental_parameters(domain)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_param_code
        ON environmental_parameters(code)
        """
    )

    # 2. Environmental Configurable Thresholds
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS environmental_thresholds (
            id TEXT PRIMARY KEY,
            parameter_id TEXT NOT NULL,
            mine_type TEXT NOT NULL DEFAULT 'ALL',
            threshold_type TEXT NOT NULL DEFAULT 'MAX_LIMIT',
            lower_limit REAL,
            upper_limit REAL,
            unit TEXT NOT NULL,
            applicable_from TEXT,
            applicable_to TEXT,
            severity TEXT NOT NULL DEFAULT 'HIGH',
            source_reference TEXT NOT NULL DEFAULT 'DEMO / CONFIGURED RULE',
            is_demo_rule INTEGER NOT NULL DEFAULT 1,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(parameter_id) REFERENCES environmental_parameters(id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_th_param
        ON environmental_thresholds(parameter_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_th_active
        ON environmental_thresholds(active)
        """
    )

    # 3. Environmental Statutory Obligations
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS environmental_obligations (
            obligation_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            code TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            domain TEXT NOT NULL,
            applicable_mine_type TEXT NOT NULL DEFAULT 'ALL',
            frequency TEXT NOT NULL DEFAULT 'MONTHLY',
            responsible_role TEXT NOT NULL DEFAULT 'ENVIRONMENTAL_OFFICER',
            regulatory_source TEXT NOT NULL DEFAULT 'MoEFCC / CPCB Statutory Framework',
            evidence_requirements TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            start_date TEXT NOT NULL,
            end_date TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_ob_mine
        ON environmental_obligations(mine_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_ob_domain
        ON environmental_obligations(domain)
        """
    )

    # 4. Environmental Monitoring Schedules
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS environmental_schedules (
            schedule_id TEXT PRIMARY KEY,
            obligation_id TEXT NOT NULL,
            mine_id TEXT NOT NULL,
            parameter_id TEXT,
            operational_unit_id TEXT,
            domain TEXT NOT NULL,
            due_date TEXT NOT NULL,
            responsible_role TEXT NOT NULL DEFAULT 'ENVIRONMENTAL_OFFICER',
            status TEXT NOT NULL DEFAULT 'SCHEDULED',
            completed_at TEXT,
            measurement_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(obligation_id) REFERENCES environmental_obligations(obligation_id),
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id),
            FOREIGN KEY(parameter_id) REFERENCES environmental_parameters(id),
            FOREIGN KEY(operational_unit_id) REFERENCES operational_units(id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_sch_mine
        ON environmental_schedules(mine_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_sch_due
        ON environmental_schedules(due_date)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_sch_status
        ON environmental_schedules(status)
        """
    )

    # 5. Environmental Measurements
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS environmental_measurements (
            id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            operational_unit_id TEXT,
            parameter_id TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            measured_at TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'MANUAL_ENTRY',
            source_reference TEXT,
            latitude REAL,
            longitude REAL,
            device_reference TEXT,
            entered_by TEXT NOT NULL DEFAULT 'SYSTEM',
            status TEXT NOT NULL DEFAULT 'RECORDED',
            evidence_id TEXT,
            data_quality_status TEXT NOT NULL DEFAULT 'VALID',
            quality_notes TEXT,
            simulated INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id),
            FOREIGN KEY(operational_unit_id) REFERENCES operational_units(id),
            FOREIGN KEY(parameter_id) REFERENCES environmental_parameters(id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_meas_mine
        ON environmental_measurements(mine_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_meas_param
        ON environmental_measurements(parameter_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_meas_time
        ON environmental_measurements(measured_at)
        """
    )

    # 6. Environmental Regulatory Reports
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS environmental_reports (
            report_id TEXT PRIMARY KEY,
            mine_id TEXT NOT NULL,
            reporting_period_start TEXT NOT NULL,
            reporting_period_end TEXT NOT NULL,
            title TEXT NOT NULL,
            report_type TEXT NOT NULL DEFAULT 'MONITORING_SUMMARY',
            status TEXT NOT NULL DEFAULT 'GENERATED',
            summary TEXT,
            measurements_count INTEGER NOT NULL DEFAULT 0,
            violations_count INTEGER NOT NULL DEFAULT 0,
            open_cases_count INTEGER NOT NULL DEFAULT 0,
            corrective_actions_count INTEGER NOT NULL DEFAULT 0,
            lineage_snapshot TEXT,
            source_record_hashes TEXT,
            content_hash TEXT,
            ipfs_cid TEXT,
            generated_by TEXT NOT NULL DEFAULT 'SYSTEM',
            generated_at TEXT NOT NULL,
            finalized_at TEXT,
            finalized_by TEXT,
            FOREIGN KEY(mine_id) REFERENCES mines(mine_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_rep_mine
        ON environmental_reports(mine_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_env_rep_status
        ON environmental_reports(status)
        """
    )

    conn.commit()
    conn.close()



# ============================================================
# MINE FUNCTIONS
# ============================================================

def save_mine(mine: Mine) -> None:
    conn = _connect()

    conn.execute(
        """
        INSERT INTO mines (
            mine_id,
            name,
            subsidiary,
            state,
            district,
            mine_type,
            mining_method,
            gassy_degree,
            mechanised,
            uses_hemm,
            has_winding_installation,
            blasting_operation,
            active,
            organization_unit_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(mine_id) DO UPDATE SET
            name = excluded.name, subsidiary = excluded.subsidiary, state = excluded.state, district = excluded.district,
            mine_type = excluded.mine_type, mining_method = excluded.mining_method, gassy_degree = excluded.gassy_degree,
            mechanised = excluded.mechanised, uses_hemm = excluded.uses_hemm, has_winding_installation = excluded.has_winding_installation,
            blasting_operation = excluded.blasting_operation, active = excluded.active,
            organization_unit_id = excluded.organization_unit_id
        """,
        (
            mine.mine_id,
            mine.name,
            mine.subsidiary,
            mine.state,
            mine.district,
            mine.mine_type.value,
            mine.mining_method,
            mine.gassy_degree.value,
            int(mine.mechanised),
            int(mine.uses_hemm),
            int(mine.has_winding_installation),
            int(mine.blasting_operation),
            int(mine.active),
            getattr(mine, "organization_unit_id", None),
        ),
    )

    conn.commit()
    conn.close()


def get_mine(mine_id: str) -> Optional[Mine]:
    conn = _connect()

    row = conn.execute(
        """
        SELECT *
        FROM mines
        WHERE mine_id = ?
        """,
        (mine_id,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return Mine(
        mine_id=row["mine_id"],
        name=row["name"],
        subsidiary=row["subsidiary"],
        state=row["state"],
        district=row["district"],
        mine_type=row["mine_type"],
        mining_method=row["mining_method"],
        gassy_degree=row["gassy_degree"],
        mechanised=bool(row["mechanised"]),
        uses_hemm=bool(row["uses_hemm"]),
        has_winding_installation=bool(
            row["has_winding_installation"]
        ),
        blasting_operation=bool(row["blasting_operation"]),
        active=bool(row["active"]),
        organization_unit_id=row["organization_unit_id"] if "organization_unit_id" in row.keys() else None,
    )


def list_mines() -> list[Mine]:
    conn = _connect()

    rows = conn.execute(
        """
        SELECT *
        FROM mines
        WHERE active = 1
        ORDER BY name
        """
    ).fetchall()

    conn.close()

    return [
        Mine(
            mine_id=row["mine_id"],
            name=row["name"],
            subsidiary=row["subsidiary"],
            state=row["state"],
            district=row["district"],
            mine_type=row["mine_type"],
            mining_method=row["mining_method"],
            gassy_degree=row["gassy_degree"],
            mechanised=bool(row["mechanised"]),
            uses_hemm=bool(row["uses_hemm"]),
            has_winding_installation=bool(
                row["has_winding_installation"]
            ),
            blasting_operation=bool(row["blasting_operation"]),
            active=bool(row["active"]),
            organization_unit_id=row["organization_unit_id"] if "organization_unit_id" in row.keys() else None,
        )
        for row in rows
    ]


# ============================================================
# REGULATORY SOURCE
# ============================================================

def save_regulatory_source(
    source: RegulatorySource,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO regulatory_sources (
            source_id,
            title,
            regulation_number,
            chapter,
            description,
            source_document,
            source_reference
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id) DO UPDATE SET
            title = excluded.title,
            regulation_number = excluded.regulation_number,
            chapter = excluded.chapter,
            description = excluded.description,
            source_document = excluded.source_document,
            source_reference = excluded.source_reference
        """,
        (
            source.source_id,
            source.title,
            source.regulation_number,
            source.chapter,
            source.description,
            source.source_document,
            source.source_reference,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# REGULATORY OBLIGATION
# ============================================================

def save_obligation(
    obligation: RegulatoryObligation,
) -> None:

    save_regulatory_source(obligation.regulation)

    conn = _connect()

    conn.execute(
        """
        INSERT INTO regulatory_obligations (
            obligation_id,
            source_id,
            title,
            requirement_type,
            requirement,
            applicability,
            frequency_or_trigger,
            responsible_role,
            required_record_or_evidence,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(obligation_id) DO UPDATE SET
            source_id = excluded.source_id,
            title = excluded.title,
            requirement_type = excluded.requirement_type,
            requirement = excluded.requirement,
            applicability = excluded.applicability,
            frequency_or_trigger = excluded.frequency_or_trigger,
            responsible_role = excluded.responsible_role,
            required_record_or_evidence = excluded.required_record_or_evidence,
            active = excluded.active
        """,
        (
            obligation.obligation_id,
            obligation.regulation.source_id,
            obligation.title,
            obligation.requirement_type,
            obligation.requirement,
            obligation.applicability,
            obligation.frequency_or_trigger,
            obligation.responsible_role,
            obligation.required_record_or_evidence,
            int(obligation.active),
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# INSPECTION TEMPLATE
# ============================================================

def save_inspection_template(
    template: InspectionTemplate,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO inspection_templates (
            template_id,
            name,
            inspection_family,
            description,
            frequency_or_trigger,
            frequency_label,
            responsible_role,
            regulation_reference,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(template_id) DO UPDATE SET
            name = excluded.name,
            inspection_family = excluded.inspection_family,
            description = excluded.description,
            frequency_or_trigger = excluded.frequency_or_trigger,
            frequency_label = excluded.frequency_label,
            responsible_role = excluded.responsible_role,
            regulation_reference = excluded.regulation_reference,
            active = excluded.active
        """,
        (
            template.template_id,
            template.name,
            template.inspection_family,
            template.description,
            template.frequency_or_trigger,
            template.frequency_label,
            template.responsible_role,
            template.regulation_reference,
            int(template.active),
        ),
    )

    # Mine types

    for mine_type in template.applicable_mine_types:

        conn.execute(
            """
            INSERT INTO template_mine_types (
                template_id,
                mine_type
            )
            VALUES (?, ?)
            ON CONFLICT(template_id, mine_type) DO NOTHING
            """,
            (
                template.template_id,
                mine_type.value,
            ),
        )

    # Obligations

    for obligation_id in template.regulatory_obligation_ids:

        conn.execute(
            """
            INSERT INTO template_obligations (
                template_id,
                obligation_id
            )
            VALUES (?, ?)
            ON CONFLICT(template_id, obligation_id) DO NOTHING
            """,
            (
                template.template_id,
                obligation_id,
            ),
        )

    # Measurements

    for measurement in template.measurements:

        conn.execute(
            """
            INSERT INTO template_measurements (
                measurement_id,
                template_id,
                name,
                unit,
                required,
                description,
                min_value,
                max_value,
                threshold_label,
                options
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(measurement_id) DO UPDATE SET
                template_id = excluded.template_id, name = excluded.name, unit = excluded.unit,
                required = excluded.required, description = excluded.description,
                min_value = excluded.min_value, max_value = excluded.max_value,
                threshold_label = excluded.threshold_label, options = excluded.options
            """,
            (
                measurement.measurement_id,
                template.template_id,
                measurement.name,
                measurement.unit,
                int(measurement.required),
                measurement.description,
                measurement.min_value,
                measurement.max_value,
                measurement.threshold_label,
                json.dumps(measurement.options) if measurement.options else None,
            ),
        )

    # Checklist

    for item in template.checklist:

        conn.execute(
            """
            INSERT INTO template_checklist (
                item_id,
                template_id,
                question,
                required,
                severity_if_failed
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                template_id = excluded.template_id, question = excluded.question,
                required = excluded.required, severity_if_failed = excluded.severity_if_failed
            """,
            (
                item.item_id,
                template.template_id,
                item.question,
                int(item.required),
                item.severity_if_failed,
            ),
        )

    # Evidence requirements

    for evidence in template.evidence_requirements:

        conn.execute(
            """
            INSERT INTO template_evidence_requirements (
                evidence_id,
                template_id,
                evidence_type,
                name,
                required,
                minimum_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                template_id = excluded.template_id, evidence_type = excluded.evidence_type,
                name = excluded.name, required = excluded.required, minimum_count = excluded.minimum_count
            """,
            (
                evidence.evidence_id,
                template.template_id,
                evidence.evidence_type.value,
                evidence.name,
                int(evidence.required),
                evidence.minimum_count,
            ),
        )

    conn.commit()
    conn.close()


def get_inspection_template(
    template_id: str,
) -> Optional[InspectionTemplate]:
    conn = _connect()

    row = conn.execute(
        """
        SELECT *
        FROM inspection_templates
        WHERE template_id = ?
        """,
        (template_id,),
    ).fetchone()

    if row is None:
        conn.close()
        return None

    mine_type_rows = conn.execute(
        """
        SELECT mine_type
        FROM template_mine_types
        WHERE template_id = ?
        ORDER BY mine_type
        """,
        (template_id,),
    ).fetchall()

    ob_rows = conn.execute(
        """
        SELECT obligation_id
        FROM template_obligations
        WHERE template_id = ?
        ORDER BY obligation_id
        """,
        (template_id,),
    ).fetchall()

    meas_rows = conn.execute(
        """
        SELECT *
        FROM template_measurements
        WHERE template_id = ?
        ORDER BY rowid
        """,
        (template_id,),
    ).fetchall()

    measurements = []
    for m in meas_rows:
        options = None
        if "options" in m.keys() and m["options"]:
            try:
                options = json.loads(m["options"])
            except Exception:
                options = None
        measurements.append(
            MeasurementDefinition(
                measurement_id=m["measurement_id"],
                name=m["name"],
                unit=m["unit"],
                required=bool(m["required"]),
                description=m["description"],
                min_value=m["min_value"] if "min_value" in m.keys() else None,
                max_value=m["max_value"] if "max_value" in m.keys() else None,
                threshold_label=m["threshold_label"] if "threshold_label" in m.keys() else None,
                options=options,
            )
        )

    chk_rows = conn.execute(
        """
        SELECT *
        FROM template_checklist
        WHERE template_id = ?
        ORDER BY rowid
        """,
        (template_id,),
    ).fetchall()

    checklist = [
        ChecklistItem(
            item_id=c["item_id"],
            question=c["question"],
            required=bool(c["required"]),
            severity_if_failed=c["severity_if_failed"],
        )
        for c in chk_rows
    ]

    ev_rows = conn.execute(
        """
        SELECT *
        FROM template_evidence_requirements
        WHERE template_id = ?
        ORDER BY rowid
        """,
        (template_id,),
    ).fetchall()

    evidence = [
        EvidenceRequirement(
            evidence_id=e["evidence_id"],
            evidence_type=EvidenceType(e["evidence_type"]),
            name=e["name"],
            required=bool(e["required"]),
            minimum_count=e["minimum_count"],
        )
        for e in ev_rows
    ]

    conn.close()

    row_keys = row.keys()
    return InspectionTemplate(
        template_id=row["template_id"],
        name=row["name"],
        inspection_family=row["inspection_family"],
        description=row["description"],
        applicable_mine_types=[MineType(item["mine_type"]) for item in mine_type_rows],
        regulatory_obligation_ids=[item["obligation_id"] for item in ob_rows],
        frequency_or_trigger=row["frequency_or_trigger"],
        frequency_label=row["frequency_label"] if "frequency_label" in row_keys else None,
        responsible_role=row["responsible_role"] if "responsible_role" in row_keys else None,
        regulation_reference=row["regulation_reference"] if "regulation_reference" in row_keys else None,
        measurements=measurements,
        checklist=checklist,
        evidence_requirements=evidence,
        active=bool(row["active"]),
    )


def get_templates_for_mine(
    mine_id: str,
) -> list[InspectionTemplate]:
    mine = get_mine(mine_id)
    if mine is None:
        return []

    conn = _connect()
    rows = conn.execute(
        """
        SELECT DISTINCT t.template_id
        FROM inspection_templates t
        JOIN template_mine_types mt ON t.template_id = mt.template_id
        WHERE t.active = 1 AND mt.mine_type = ?
        ORDER BY t.rowid
        """,
        (mine.mine_type.value,),
    ).fetchall()
    conn.close()

    templates = []
    for r in rows:
        tmpl = get_inspection_template(r["template_id"])
        if tmpl:
            templates.append(tmpl)
    return templates


# ============================================================
# INSPECTION
# ============================================================

def save_inspection(
    inspection: Inspection,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO inspections (
            inspection_id,
            mine_id,
            template_id,
            obligation_id,
            inspector_id,
            started_at,
            submitted_at,
            inspection_date,
            status,
            latitude,
            longitude,
            gps_accuracy_m
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(inspection_id) DO UPDATE SET
            mine_id = excluded.mine_id, template_id = excluded.template_id, obligation_id = excluded.obligation_id,
            inspector_id = excluded.inspector_id, started_at = excluded.started_at, submitted_at = excluded.submitted_at,
            inspection_date = excluded.inspection_date, status = excluded.status, latitude = excluded.latitude,
            longitude = excluded.longitude, gps_accuracy_m = excluded.gps_accuracy_m
        """,
        (
            inspection.inspection_id,
            inspection.mine_id,
            inspection.template_id,
            inspection.obligation_id,
            inspection.inspector_id,
            inspection.started_at.isoformat()
            if inspection.started_at
            else None,
            inspection.submitted_at.isoformat()
            if inspection.submitted_at
            else None,
            inspection.inspection_date.isoformat(),
            inspection.status.value,
            inspection.latitude,
            inspection.longitude,
            inspection.gps_accuracy_m,
        ),
    )

    conn.commit()
    conn.close()


def get_inspection(
    inspection_id: str,
) -> Optional[Inspection]:

    conn = _connect()

    row = conn.execute(
        """
        SELECT *
        FROM inspections
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return Inspection(
        inspection_id=row["inspection_id"],
        mine_id=row["mine_id"],
        template_id=row["template_id"],
        obligation_id=row["obligation_id"],
        inspector_id=row["inspector_id"],
        started_at=row["started_at"],
        submitted_at=row["submitted_at"],
        inspection_date=row["inspection_date"],
        status=row["status"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        gps_accuracy_m=row["gps_accuracy_m"],
    )


# ============================================================
# MEASUREMENTS
# ============================================================

def save_measurement(
    measurement: Measurement,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO measurements (
            measurement_id,
            inspection_id,
            measurement_type,
            value,
            unit,
            source,
            captured_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(measurement_id) DO UPDATE SET
            inspection_id = excluded.inspection_id, measurement_type = excluded.measurement_type,
            value = excluded.value, unit = excluded.unit, source = excluded.source, captured_at = excluded.captured_at
        """,
        (
            measurement.measurement_id,
            measurement.inspection_id,
            measurement.measurement_type,
            measurement.value,
            measurement.unit,
            measurement.source,
            measurement.captured_at.isoformat()
            if measurement.captured_at
            else None,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# CHECKLIST RESULTS
# ============================================================

def save_checklist_result(
    result: ChecklistResult,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO checklist_results (
            result_id,
            inspection_id,
            item_id,
            passed,
            observation
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(result_id) DO UPDATE SET
            inspection_id = excluded.inspection_id, item_id = excluded.item_id,
            passed = excluded.passed, observation = excluded.observation
        """,
        (
            result.result_id,
            result.inspection_id,
            result.item_id,
            int(result.passed),
            result.observation,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# EVIDENCE
# ============================================================

def save_evidence(
    evidence: Evidence,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO evidence (
            evidence_id,
            inspection_id,
            evidence_type,
            filename,
            storage_reference,
            captured_at,
            latitude,
            longitude,
            sha256,
            perceptual_hash,
            metadata_verified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(evidence_id) DO UPDATE SET
            inspection_id = excluded.inspection_id, evidence_type = excluded.evidence_type,
            filename = excluded.filename, storage_reference = excluded.storage_reference, captured_at = excluded.captured_at,
            latitude = excluded.latitude, longitude = excluded.longitude, sha256 = excluded.sha256,
            perceptual_hash = excluded.perceptual_hash, metadata_verified = excluded.metadata_verified
        """,
        (
            evidence.evidence_id,
            evidence.inspection_id,
            evidence.evidence_type.value,
            evidence.filename,
            evidence.storage_reference,
            evidence.captured_at.isoformat()
            if evidence.captured_at
            else None,
            evidence.latitude,
            evidence.longitude,
            evidence.sha256,
            evidence.perceptual_hash,
            int(evidence.metadata_verified),
        ),
    )

    conn.commit()
    conn.close()


def get_evidence_for_inspection(
    inspection_id: str,
) -> list[Evidence]:
    conn = _connect()

    rows = conn.execute(
        """
        SELECT *
        FROM evidence
        WHERE inspection_id = ?
        ORDER BY rowid ASC
        """,
        (inspection_id,),
    ).fetchall()

    conn.close()

    result = []
    for r in rows:
        captured = None
        if r["captured_at"]:
            try:
                captured = datetime.fromisoformat(r["captured_at"])
            except Exception:
                captured = None

        result.append(
            Evidence(
                evidence_id=r["evidence_id"],
                inspection_id=r["inspection_id"],
                evidence_type=EvidenceType(r["evidence_type"]),
                filename=r["filename"],
                storage_reference=r["storage_reference"],
                captured_at=captured,
                latitude=r["latitude"],
                longitude=r["longitude"],
                sha256=r["sha256"],
                perceptual_hash=r["perceptual_hash"],
                metadata_verified=bool(r["metadata_verified"]),
            )
        )

    return result


# ============================================================
# SENSORS
# ============================================================

def save_sensor(
    sensor: Sensor,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO sensors (
            sensor_id,
            mine_id,
            sensor_type,
            location_description,
            latitude,
            longitude,
            calibration_status,
            last_calibrated_at,
            reliability_score,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sensor_id) DO UPDATE SET
            mine_id = excluded.mine_id, sensor_type = excluded.sensor_type, location_description = excluded.location_description,
            latitude = excluded.latitude, longitude = excluded.longitude, calibration_status = excluded.calibration_status,
            last_calibrated_at = excluded.last_calibrated_at, reliability_score = excluded.reliability_score, active = excluded.active
        """,
        (
            sensor.sensor_id,
            sensor.mine_id,
            sensor.sensor_type,
            sensor.location_description,
            sensor.latitude,
            sensor.longitude,
            sensor.calibration_status,
            sensor.last_calibrated_at.isoformat()
            if sensor.last_calibrated_at
            else None,
            sensor.reliability_score,
            int(sensor.active),
        ),
    )

    conn.commit()
    conn.close()


def save_sensor_reading(
    reading: SensorReading,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO sensor_readings (
            reading_id,
            sensor_id,
            mine_id,
            reading_time,
            measurement_type,
            value,
            unit
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(reading_id) DO UPDATE SET
            sensor_id = excluded.sensor_id, mine_id = excluded.mine_id, reading_time = excluded.reading_time,
            measurement_type = excluded.measurement_type, value = excluded.value, unit = excluded.unit
        """,
        (
            reading.reading_id,
            reading.sensor_id,
            reading.mine_id,
            reading.reading_time.isoformat(),
            reading.measurement_type,
            reading.value,
            reading.unit,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# FINDINGS
# ============================================================

def save_finding(
    finding: Finding,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO findings (
            finding_id,
            inspection_id,
            title,
            description,
            severity,
            corrective_action_required,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(finding_id) DO UPDATE SET
            inspection_id = excluded.inspection_id, title = excluded.title, description = excluded.description,
            severity = excluded.severity, corrective_action_required = excluded.corrective_action_required, status = excluded.status
        """,
        (
            finding.finding_id,
            finding.inspection_id,
            finding.title,
            finding.description,
            finding.severity,
            int(finding.corrective_action_required),
            finding.status,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# FINDING ↔ EVIDENCE
# ============================================================

def save_finding_evidence(finding_id: str, evidence_ids: list[str]) -> None:
    conn = _connect()
    conn.execute(
        "DELETE FROM finding_evidence WHERE finding_id = ?",
        (finding_id,),
    )
    for evidence_id in evidence_ids:
        conn.execute(
            """
            INSERT OR IGNORE INTO finding_evidence (finding_id, evidence_id)
            VALUES (?, ?)
            """,
            (finding_id, evidence_id),
        )
    conn.commit()
    conn.close()


def get_finding_evidence_ids(finding_id: str) -> list[str]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT evidence_id
        FROM finding_evidence
        WHERE finding_id = ?
        ORDER BY evidence_id
        """,
        (finding_id,),
    ).fetchall()
    conn.close()
    return [row["evidence_id"] for row in rows]


def validate_evidence_for_inspection(
    inspection_id: str,
    evidence_ids: list[str],
) -> list[str]:
    if not evidence_ids:
        return []
    conn = _connect()
    placeholders = ",".join("?" for _ in evidence_ids)
    rows = conn.execute(
        f"""
        SELECT evidence_id
        FROM evidence
        WHERE inspection_id = ?
          AND evidence_id IN ({placeholders})
        """,
        [inspection_id, *evidence_ids],
    ).fetchall()
    conn.close()
    valid_ids = {row["evidence_id"] for row in rows}
    return [eid for eid in evidence_ids if eid not in valid_ids]


def get_findings_for_inspection(inspection_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT finding_id, inspection_id, title, description, severity,
               corrective_action_required, status
        FROM findings
        WHERE inspection_id = ?
        ORDER BY finding_id
        """,
        (inspection_id,),
    ).fetchall()
    results = []
    for row in rows:
        evidence_rows = conn.execute(
            """
            SELECT evidence_id
            FROM finding_evidence
            WHERE finding_id = ?
            ORDER BY evidence_id
            """,
            (row["finding_id"],),
        ).fetchall()
        results.append({
            "finding_id": row["finding_id"],
            "inspection_id": row["inspection_id"],
            "title": row["title"],
            "description": row["description"],
            "severity": row["severity"],
            "corrective_action_required": bool(row["corrective_action_required"]),
            "status": row["status"],
            "evidence_ids": [item["evidence_id"] for item in evidence_rows],
        })
    conn.close()
    return results


# ============================================================
# DGMS ENFORCEMENT ACTIONS (PHASE 2 TASK 5)
# ============================================================

def save_enforcement_action(action: dict) -> None:
    """
    Persist a DGMS regulatory enforcement / escalation action.
    """
    conn = _connect()
    conn.execute(
        """
        INSERT INTO enforcement_actions (
            action_id,
            mine_id,
            inspection_id,
            action_type,
            severity,
            reason,
            officer_id,
            status,
            created_at,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(action_id) DO UPDATE SET
            status = excluded.status,
            notes = excluded.notes
        """,
        (
            action["action_id"],
            action["mine_id"],
            action.get("inspection_id"),
            action["action_type"],
            action["severity"],
            action["reason"],
            action["officer_id"],
            action.get("status", "OPEN"),
            action["created_at"],
            action.get("notes"),
        ),
    )
    conn.commit()
    conn.close()

    log_event(
        entity_type="enforcement_action",
        entity_id=action["action_id"],
        action=f"dgms_{action['action_type'].lower()}",
        actor_id=action["officer_id"],
        details=f"Mine: {action['mine_id']}. Reason: {action['reason']}",
    )


def list_enforcement_actions(mine_id: Optional[str] = None) -> list[dict]:
    """
    Retrieve past DGMS regulatory enforcement / escalation actions.
    """
    conn = _connect()
    if mine_id:
        rows = conn.execute(
            """
            SELECT ea.*, m.name as mine_name
            FROM enforcement_actions ea
            LEFT JOIN mines m ON ea.mine_id = m.mine_id
            WHERE ea.mine_id = ?
            ORDER BY ea.created_at DESC
            """,
            (mine_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT ea.*, m.name as mine_name
            FROM enforcement_actions ea
            LEFT JOIN mines m ON ea.mine_id = m.mine_id
            ORDER BY ea.created_at DESC
            """
        ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# REGULATORY SCHEDULE RULES
# ============================================================

def save_schedule_rule(rule: RegulatoryScheduleRule) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO regulatory_schedule_rules (
            schedule_id, obligation_id, template_id, name, frequency_type,
            interval_value, interval_unit, trigger_type, applicable_mine_types,
            applicable_gassy_degrees, condition_description, responsible_role,
            regulation_reference, source_document, source_reference, source_date,
            effective_from, effective_to, validation_status, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(schedule_id) DO UPDATE SET
            obligation_id=excluded.obligation_id, template_id=excluded.template_id,
            name=excluded.name, frequency_type=excluded.frequency_type,
            interval_value=excluded.interval_value, interval_unit=excluded.interval_unit,
            trigger_type=excluded.trigger_type, applicable_mine_types=excluded.applicable_mine_types,
            applicable_gassy_degrees=excluded.applicable_gassy_degrees,
            condition_description=excluded.condition_description, responsible_role=excluded.responsible_role,
            regulation_reference=excluded.regulation_reference, source_document=excluded.source_document,
            source_reference=excluded.source_reference, source_date=excluded.source_date,
            effective_from=excluded.effective_from, effective_to=excluded.effective_to,
            validation_status=excluded.validation_status, active=excluded.active
        """,
        (
            rule.schedule_id, rule.obligation_id, rule.template_id, rule.name,
            rule.frequency_type.value, rule.interval_value,
            rule.interval_unit.value if rule.interval_unit else None, rule.trigger_type,
            json.dumps([x.value for x in rule.applicable_mine_types]),
            json.dumps([x.value for x in rule.applicable_gassy_degrees]),
            rule.condition_description, rule.responsible_role, rule.regulation_reference,
            rule.source_document, rule.source_reference,
            rule.source_date.isoformat() if rule.source_date else None,
            rule.effective_from.isoformat() if rule.effective_from else None,
            rule.effective_to.isoformat() if rule.effective_to else None,
            rule.validation_status, int(rule.active),
        ),
    )
    conn.commit()
    conn.close()


def list_schedule_rules() -> list[RegulatoryScheduleRule]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM regulatory_schedule_rules WHERE active = 1 ORDER BY schedule_id"
    ).fetchall()
    conn.close()
    return [
        RegulatoryScheduleRule(
            schedule_id=r["schedule_id"], obligation_id=r["obligation_id"],
            template_id=r["template_id"], name=r["name"], frequency_type=r["frequency_type"],
            interval_value=r["interval_value"], interval_unit=r["interval_unit"],
            trigger_type=r["trigger_type"],
            applicable_mine_types=json.loads(r["applicable_mine_types"] or "[]"),
            applicable_gassy_degrees=json.loads(r["applicable_gassy_degrees"] or "[]"),
            condition_description=r["condition_description"], responsible_role=r["responsible_role"],
            regulation_reference=r["regulation_reference"], source_document=r["source_document"],
            source_reference=r["source_reference"],
            source_date=datetime.fromisoformat(r["source_date"]) if r["source_date"] else None,
            effective_from=datetime.fromisoformat(r["effective_from"]) if r["effective_from"] else None,
            effective_to=datetime.fromisoformat(r["effective_to"]) if r["effective_to"] else None,
            validation_status=r["validation_status"], active=bool(r["active"]),
        )
        for r in rows
    ]


def save_mine_inspection_schedule(schedule: MineInspectionSchedule) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO mine_inspection_schedules (
            schedule_instance_id, mine_id, schedule_id, last_completed_at,
            next_due_at, status, generated_at, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(schedule_instance_id) DO UPDATE SET
            mine_id=excluded.mine_id, schedule_id=excluded.schedule_id,
            last_completed_at=excluded.last_completed_at, next_due_at=excluded.next_due_at,
            status=excluded.status, generated_at=excluded.generated_at, active=excluded.active
        """,
        (
            schedule.schedule_instance_id, schedule.mine_id, schedule.schedule_id,
            schedule.last_completed_at.isoformat() if schedule.last_completed_at else None,
            schedule.next_due_at.isoformat() if schedule.next_due_at else None,
            schedule.status, schedule.generated_at.isoformat(), int(schedule.active),
        ),
    )
    conn.commit()
    conn.close()


def deactivate_mine_inspection_schedule(schedule_instance_id: str) -> None:
    conn = _connect()
    conn.execute("UPDATE mine_inspection_schedules SET active = 0 WHERE schedule_instance_id = ?", (schedule_instance_id,))
    conn.commit()
    conn.close()


def deactivate_inactive_mine_schedules(mine_id: str, active_schedule_ids: set[str]) -> None:
    conn = _connect()
    if not active_schedule_ids:
        conn.execute("UPDATE mine_inspection_schedules SET active = 0 WHERE mine_id = ?", (mine_id,))
    else:
        placeholders = ",".join("?" for _ in active_schedule_ids)
        conn.execute(
            f"UPDATE mine_inspection_schedules SET active = 0 WHERE mine_id = ? AND schedule_id NOT IN ({placeholders})",
            (mine_id, *active_schedule_ids),
        )
    conn.commit()
    conn.close()


def get_schedules_for_mine(mine_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT s.schedule_instance_id, s.mine_id, s.schedule_id, s.last_completed_at,
               s.next_due_at, s.status, s.generated_at, s.active,
               r.name AS schedule_name, r.name, r.template_id, r.obligation_id,
               r.frequency_type, r.interval_value, r.interval_unit, r.trigger_type,
               r.validation_status,
               COALESCE(r.responsible_role, t.responsible_role) AS responsible_role,
               COALESCE(r.regulation_reference, t.regulation_reference) AS regulation_reference,
               COALESCE(t.name, r.name) AS template_name,
               t.inspection_family,
               t.frequency_label
        FROM mine_inspection_schedules s
        JOIN regulatory_schedule_rules r ON s.schedule_id = r.schedule_id
        LEFT JOIN inspection_templates t ON r.template_id = t.template_id
        WHERE s.mine_id = ? AND s.active = 1
        ORDER BY CASE WHEN s.next_due_at IS NULL THEN 1 ELSE 0 END, s.next_due_at
        """,
        (mine_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# CORRECTIVE ACTIONS
# ============================================================

def save_corrective_action(
    action: CorrectiveAction,
) -> None:
    save_corrective_action_v2(action)


# ============================================================
# VERIFICATION
# ============================================================

def save_verification_result(
    result: VerificationResult,
) -> None:

    conn = _connect()

    conn.execute(
        """
        INSERT INTO verification_results (
            verification_id,
            inspection_id,
            status,
            confidence,
            recommendation,
            human_decision_required
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(verification_id) DO UPDATE SET
            inspection_id = excluded.inspection_id, status = excluded.status, confidence = excluded.confidence,
            recommendation = excluded.recommendation, human_decision_required = excluded.human_decision_required
        """,
        (
            result.verification_id,
            result.inspection_id,
            result.status.value,
            result.confidence,
            result.recommendation,
            int(result.human_decision_required),
        ),
    )

    # Replace signals for this inspection.
    conn.execute(
        """
        DELETE FROM verification_signals
        WHERE inspection_id = ?
        """,
        (result.inspection_id,),
    )

    for signal in result.signals:

        conn.execute(
            """
            INSERT INTO verification_signals (
                signal_id,
                inspection_id,
                category,
                name,
                status,
                severity,
                score,
                explanation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.signal_id,
                signal.inspection_id,
                signal.category,
                signal.name,
                signal.status,
                signal.severity,
                signal.score,
                signal.explanation,
            ),
        )

    # Replace anomaly references.
    conn.execute(
        """
        DELETE FROM verification_source_anomalies
        WHERE verification_id = ?
        """,
        (result.verification_id,),
    )

    for source_id in result.source_anomalies:

        conn.execute(
            """
            INSERT INTO verification_source_anomalies (
                verification_id,
                source_id
            )
            VALUES (?, ?)
            """,
            (
                result.verification_id,
                source_id,
            ),
        )

    # Replace conflicts.
    conn.execute(
        """
        DELETE FROM verification_conflicts
        WHERE verification_id = ?
        """,
        (result.verification_id,),
    )

    for conflict in result.evidence_conflicts:

        conn.execute(
            """
            INSERT INTO verification_conflicts (
                verification_id,
                conflict
            )
            VALUES (?, ?)
            """,
            (
                result.verification_id,
                conflict,
            ),
        )

    conn.commit()
    conn.close()


# ============================================================
# HUMAN REVIEW
# ============================================================

def save_human_review(
    review: HumanReview,
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
) -> None:

    conn = _connect()

    # Determine current/previous status if not explicitly provided
    if previous_status is None:
        curr_row = conn.execute(
            "SELECT status FROM inspections WHERE inspection_id = ?",
            (review.inspection_id,),
        ).fetchone()
        previous_status = curr_row[0] if curr_row else None

    # Determine new status if not explicitly provided
    dec_val = review.decision.value if hasattr(review.decision, "value") else str(review.decision)
    if new_status is None:
        if dec_val in ("verify", "accept"):
            new_status = InspectionStatus.VERIFIED.value
        elif dec_val in ("return", "reject"):
            new_status = InspectionStatus.REJECTED.value
        elif dec_val == "reinspection":
            new_status = InspectionStatus.REINSPECTION_RECOMMENDED.value
        elif dec_val in ("escalate", "review"):
            new_status = InspectionStatus.REVIEW_REQUIRED.value

    conn.execute(
        """
        INSERT INTO human_reviews (
            review_id,
            inspection_id,
            reviewer_id,
            decision,
            reason,
            reviewed_at,
            previous_status,
            new_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(review_id) DO UPDATE SET
            inspection_id = excluded.inspection_id,
            reviewer_id = excluded.reviewer_id,
            decision = excluded.decision,
            reason = excluded.reason,
            reviewed_at = excluded.reviewed_at,
            previous_status = excluded.previous_status,
            new_status = excluded.new_status
        """,
        (
            review.review_id,
            review.inspection_id,
            review.reviewer_id,
            dec_val,
            review.reason,
            review.reviewed_at.isoformat() if hasattr(review.reviewed_at, "isoformat") else str(review.reviewed_at),
            previous_status,
            new_status,
        ),
    )

    if new_status:
        conn.execute(
            """
            UPDATE inspections
            SET status = ?
            WHERE inspection_id = ?
            """,
            (new_status, review.inspection_id),
        )

    conn.commit()
    conn.close()

    log_event(
        entity_type="inspection",
        entity_id=review.inspection_id,
        action=f"human_review_{dec_val}",
        actor_id=review.reviewer_id,
        details=f"Status: {previous_status} -> {new_status}. Reason: {review.reason}",
    )


def get_inspection_human_reviews(inspection_id: str) -> list[dict]:
    """
    Retrieve full audit trail of all human review decisions for an inspection.
    """
    conn = _connect()
    rows = conn.execute(
        """
        SELECT
            review_id,
            inspection_id,
            reviewer_id,
            decision,
            reason,
            reviewed_at,
            previous_status,
            new_status
        FROM human_reviews
        WHERE inspection_id = ?
        ORDER BY reviewed_at DESC
        """,
        (inspection_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# AUDIT LOG
# ============================================================

def log_event(
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: Optional[str] = None,
    details: Optional[str] = None,
) -> None:

    from datetime import datetime, timezone

    conn = _connect()

    conn.execute(
        """
        INSERT INTO audit_log (
            entity_type,
            entity_id,
            action,
            actor_id,
            timestamp,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entity_type,
            entity_id,
            action,
            actor_id,
            datetime.now(timezone.utc).isoformat(),
            details,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# BASIC QUERIES
# ============================================================

def list_pending_verifications() -> list[dict]:
    """
    Return only the latest human-review-required verification for each
    inspection. Historical verification attempts remain stored.
    """
    conn = _connect()

    rows = conn.execute(
        """
        SELECT
            v.verification_id,
            v.inspection_id,
            v.status,
            v.confidence,
            v.recommendation,
            i.mine_id,
            i.template_id,
            i.inspection_date
        FROM verification_results v
        JOIN inspections i
            ON v.inspection_id = i.inspection_id
        WHERE v.human_decision_required = 1
          AND NOT EXISTS (
              SELECT 1 FROM human_reviews hr
              WHERE hr.inspection_id = v.inspection_id
          )
          AND v.verification_id = (
              SELECT v2.verification_id
              FROM verification_results v2
              WHERE v2.inspection_id = v.inspection_id
              ORDER BY v2.rowid DESC
              LIMIT 1
          )
        ORDER BY i.inspection_date DESC
        """
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_inspections_for_mine(
    mine_id: str,
) -> list[dict]:

    conn = _connect()

    rows = conn.execute(
        """
        SELECT
            i.*,
            t.name AS inspection_name,
            t.inspection_family
        FROM inspections i
        JOIN inspection_templates t
            ON i.template_id = t.template_id
        WHERE i.mine_id = ?
        ORDER BY i.inspection_date DESC
        """,
        (mine_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]# ============================================================
# DASHBOARD KPI QUERIES
# ============================================================

def count_submitted_inspections() -> int:
    """Count inspections that have actually been submitted."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM inspections
        WHERE submitted_at IS NOT NULL
        """
    ).fetchone()
    conn.close()
    return int(row[0] or 0)


def count_reinspection_recommended() -> int:
    """Count unique inspections whose latest verification recommends reinspection."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM verification_results v
        WHERE v.status = 'reinspection_recommended'
          AND v.verification_id = (
              SELECT v2.verification_id
              FROM verification_results v2
              WHERE v2.inspection_id = v.inspection_id
              ORDER BY v2.rowid DESC
              LIMIT 1
          )
        """
    ).fetchone()
    conn.close()
    return int(row[0] or 0)


def count_source_anomalies() -> int:
    """Count unique inspections whose latest verification has a source anomaly."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM verification_results v
        WHERE v.verification_id = (
            SELECT v2.verification_id
            FROM verification_results v2
            WHERE v2.inspection_id = v.inspection_id
            ORDER BY v2.rowid DESC
            LIMIT 1
        )
          AND EXISTS (
              SELECT 1
              FROM verification_source_anomalies a
              WHERE a.verification_id = v.verification_id
          )
        """
    ).fetchone()
    conn.close()
    return int(row[0] or 0)


def count_open_corrective_actions() -> int:
    """Count corrective actions that are not in a terminal closed state."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM corrective_actions
        WHERE LOWER(COALESCE(status, 'open'))
              NOT IN ('closed', 'resolved', 'completed')
        """
    ).fetchone()
    conn.close()
    return int(row[0] or 0)


def count_awaiting_verification() -> int:
    """Count unique inspections whose latest verification requires human review."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM verification_results v
        WHERE v.human_decision_required = 1
          AND v.verification_id = (
              SELECT v2.verification_id
              FROM verification_results v2
              WHERE v2.inspection_id = v.inspection_id
              ORDER BY v2.rowid DESC
              LIMIT 1
          )
        """
    ).fetchone()
    conn.close()
    return int(row[0] or 0)


def count_verification_required() -> int:
    """Count unique inspections whose latest verification requires verification."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM verification_results v
        WHERE v.status = 'verification_required'
          AND v.verification_id = (
              SELECT v2.verification_id
              FROM verification_results v2
              WHERE v2.inspection_id = v.inspection_id
              ORDER BY v2.rowid DESC
              LIMIT 1
          )
        """
    ).fetchone()
    conn.close()
    return int(row[0] or 0)


def count_inspections_due() -> int:
    """
    Count active schedule instances with a concrete due date that is
    now due or overdue. Conditional schedules without a due timestamp
    are excluded.
    """
    now = datetime.now(timezone.utc).isoformat()

    conn = _connect()
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM mine_inspection_schedules
        WHERE active = 1
          AND next_due_at IS NOT NULL
          AND next_due_at <= ?
        """,
        (now,),
    ).fetchone()
    conn.close()
    return int(row[0] or 0)


def count_active_mines() -> int:
    """Count active mines in the registry."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM mines
        WHERE active = 1
        """
    ).fetchone()
    conn.close()
    return int(row[0] or 0)
    # ============================================================
# VERIFICATION RETRIEVAL
# ============================================================

class DotDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{name}'")
    def __setattr__(self, name, value):
        self[name] = value

def get_verification(inspection_id: str) -> Optional[DotDict]:
    conn = _connect()

    row = conn.execute(
        """
        SELECT
            v.*,
            i.mine_id,
            i.template_id,
            i.inspector_id,
            i.inspection_date
        FROM verification_results v
        JOIN inspections i
            ON v.inspection_id = i.inspection_id
        WHERE v.inspection_id = ?
        ORDER BY v.rowid DESC
        LIMIT 1
        """,
        (inspection_id,),
    ).fetchone()

    if row is None:
        conn.close()
        return None

    res = DotDict(row)
    if "human_decision_required" in res:
        res["human_decision_required"] = bool(res["human_decision_required"])

    # Attach signals
    sig_rows = conn.execute(
        """
        SELECT *
        FROM verification_signals
        WHERE inspection_id = ?
        ORDER BY rowid
        """,
        (inspection_id,),
    ).fetchall()
    res["signals"] = [DotDict(s) for s in sig_rows]

    # Attach source anomalies
    v_id = res.get("verification_id")
    anom_rows = conn.execute(
        """
        SELECT source_id
        FROM verification_source_anomalies
        WHERE verification_id = ?
        ORDER BY rowid
        """,
        (v_id,),
    ).fetchall()
    res["source_anomalies"] = [a["source_id"] for a in anom_rows]

    # Attach conflicts
    conf_rows = conn.execute(
        """
        SELECT conflict
        FROM verification_conflicts
        WHERE verification_id = ?
        ORDER BY rowid
        """,
        (v_id,),
    ).fetchall()
    res["evidence_conflicts"] = [c["conflict"] for c in conf_rows]

    conn.close()
    return res


# ============================================================
# HISTORICAL DOCUMENT TEXT RETRIEVAL
# ============================================================

def get_previous_document_texts(inspection_id: str) -> list[dict]:
    """
    Retrieve text of previously submitted inspection documents
    for the same mine, to enable semantic & TF-IDF similarity checks.
    """
    from .document_ai import DOCUMENT_ROOT, extract_pdf_text

    inspection = get_inspection(inspection_id)
    if inspection is None:
        return []

    mine_id = inspection.mine_id
    results: list[dict] = []
    seen_texts: set[str] = set()

    conn = _connect()

    # 1. Query past inspections for this mine
    rows = conn.execute(
        """
        SELECT inspection_id
        FROM inspections
        WHERE mine_id = ? AND inspection_id != ?
        ORDER BY started_at DESC
        """,
        (mine_id, inspection_id),
    ).fetchall()

    for r in rows:
        prev_id = r["inspection_id"]
        ev_rows = conn.execute(
            """
            SELECT filename
            FROM evidence
            WHERE inspection_id = ? AND LOWER(evidence_type) = 'document'
            """,
            (prev_id,),
        ).fetchall()

        for ev in ev_rows:
            fname = ev["filename"]
            if not fname:
                continue
            doc_path = DOCUMENT_ROOT / prev_id / fname
            if doc_path.exists() and doc_path.is_file():
                try:
                    text, _ = extract_pdf_text(doc_path)
                    if text and text.strip() and text not in seen_texts:
                        seen_texts.add(text)
                        results.append({
                            "inspection_id": prev_id,
                            "filename": fname,
                            "text": text,
                        })
                except Exception:
                    pass

    conn.close()

    # 2. Add baseline demonstration document scoped to this mine
    demo_dir = DOCUMENT_ROOT / "demo"
    if demo_dir.exists():
        demo_map = {
            "MINE-BCCL-JHARIA-01": ("Jharia_Ventilation_August_2026.pdf", "INSP-BCCL-2026-AUG-BASELINE"),
            "MINE-ECL-RANIGANJ-01": ("Raniganj_Ventilation_August_2026.pdf", "INSP-ECL-2026-AUG-BASELINE"),
            "MINE-MCL-TALCHER-01": ("Talcher_HEMM_August_2026.pdf", "INSP-MCL-2026-AUG-BASELINE"),
        }
        if mine_id in demo_map:
            baseline_file, baseline_id = demo_map[mine_id]
            baseline_path = demo_dir / baseline_file
            if baseline_path.exists():
                try:
                    text, _ = extract_pdf_text(baseline_path)
                    if text and text.strip() and text not in seen_texts:
                        seen_texts.add(text)
                        results.append({
                            "inspection_id": baseline_id,
                            "filename": baseline_file,
                            "text": text,
                        })
                except Exception:
                    pass

    return results


# ============================================================
# PHASE 2 TASK 6 — COMPLIANCE CASE PERSISTENCE & QUERIES
# ============================================================

def save_compliance_case(case: ComplianceCase) -> None:
    conn = _connect()
    c_at = case.created_at.isoformat() if isinstance(case.created_at, datetime) else str(case.created_at)
    u_at = case.updated_at.isoformat() if isinstance(case.updated_at, datetime) else str(case.updated_at)
    cl_at = case.closed_at.isoformat() if isinstance(case.closed_at, datetime) else (str(case.closed_at) if case.closed_at else None)
    st = case.status.value if hasattr(case.status, "value") else str(case.status)
    src_t = case.source_type.value if hasattr(case.source_type, "value") else str(case.source_type)

    conn.execute(
        """
        INSERT INTO compliance_cases (
            case_id, mine_id, inspection_id, finding_id, category,
            regulation_reference, title, description, severity, risk_level,
            status, source_type, source_id, created_at, updated_at,
            closed_at, closed_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(case_id) DO UPDATE SET
            mine_id = excluded.mine_id,
            inspection_id = excluded.inspection_id,
            finding_id = excluded.finding_id,
            category = excluded.category,
            regulation_reference = excluded.regulation_reference,
            title = excluded.title,
            description = excluded.description,
            severity = excluded.severity,
            risk_level = excluded.risk_level,
            status = excluded.status,
            source_type = excluded.source_type,
            source_id = excluded.source_id,
            updated_at = excluded.updated_at,
            closed_at = excluded.closed_at,
            closed_by = excluded.closed_by
        """,
        (
            case.case_id,
            case.mine_id,
            case.inspection_id,
            case.finding_id,
            case.category,
            case.regulation_reference,
            case.title,
            case.description,
            case.severity,
            case.risk_level,
            st,
            src_t,
            case.source_id,
            c_at,
            u_at,
            cl_at,
            case.closed_by,
        ),
    )
    conn.commit()
    conn.close()


def get_compliance_case(case_id: str) -> Optional[dict]:
    conn = _connect()
    row = conn.execute(
        """
        SELECT c.*, m.name AS mine_name
        FROM compliance_cases c
        LEFT JOIN mines m ON c.mine_id = m.mine_id
        WHERE c.case_id = ?
        """,
        (case_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_compliance_case_by_source(source_type: str, source_id: str) -> Optional[dict]:
    conn = _connect()
    row = conn.execute(
        """
        SELECT c.*, m.name AS mine_name
        FROM compliance_cases c
        LEFT JOIN mines m ON c.mine_id = m.mine_id
        WHERE c.source_type = ? AND c.source_id = ?
        LIMIT 1
        """,
        (source_type, source_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


class CaseRecord(dict):
    """
    Dictionary supporting both dictionary indexing and attribute access.
    """
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'CaseRecord' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


def list_compliance_cases(
    mine_id: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    source_type: Optional[str] = None,
) -> list[Any]:
    conn = _connect()
    query = """
        SELECT c.*, m.name AS mine_name
        FROM compliance_cases c
        LEFT JOIN mines m ON c.mine_id = m.mine_id
        WHERE 1 = 1
    """
    params: list[Any] = []

    if mine_id:
        query += " AND c.mine_id = ?"
        params.append(mine_id)
    if status and status.upper() != "ALL":
        query += " AND c.status = ?"
        params.append(status.upper())
    if category:
        query += " AND LOWER(c.category) = LOWER(?)"
        params.append(category)
    if severity:
        query += " AND UPPER(c.severity) = UPPER(?)"
        params.append(severity)
    if source_type:
        query += " AND c.source_type = ?"
        params.append(str(source_type))

    query += " ORDER BY c.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [CaseRecord(dict(r)) for r in rows]


def update_compliance_case_status(
    case_id: str,
    status: str,
    updated_at: Optional[str] = None,
    closed_at: Optional[str] = None,
    closed_by: Optional[str] = None,
) -> None:
    now_iso = updated_at or datetime.now(timezone.utc).isoformat()
    conn = _connect()
    conn.execute(
        """
        UPDATE compliance_cases
        SET status = ?,
            updated_at = ?,
            closed_at = CASE WHEN ? IS NOT NULL THEN ? ELSE closed_at END,
            closed_by = CASE WHEN ? IS NOT NULL THEN ? ELSE closed_by END
        WHERE case_id = ?
        """,
        (status, now_iso, closed_at, closed_at, closed_by, closed_by, case_id),
    )
    conn.commit()
    conn.close()


def save_corrective_action_v2(action: CorrectiveAction) -> None:
    conn = _connect()
    c_at = action.created_at.isoformat() if isinstance(action.created_at, datetime) else str(action.created_at or "")
    u_at = action.updated_at.isoformat() if isinstance(action.updated_at, datetime) else str(action.updated_at or "")
    comp_at = action.completed_at.isoformat() if isinstance(action.completed_at, datetime) else (str(action.completed_at) if action.completed_at else None)
    due_val = action.due_at or (action.due_date.isoformat() if action.due_date else None)

    conn.execute(
        """
        INSERT INTO corrective_actions (
            action_id, case_id, finding_id, mine_id, title,
            description, assigned_role, assigned_user_id, assigned_to,
            due_at, due_date, priority, status,
            created_at, updated_at, completed_at, completed_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(action_id) DO UPDATE SET
            case_id = COALESCE(excluded.case_id, corrective_actions.case_id),
            finding_id = COALESCE(excluded.finding_id, corrective_actions.finding_id),
            mine_id = COALESCE(excluded.mine_id, corrective_actions.mine_id),
            title = COALESCE(excluded.title, corrective_actions.title),
            description = excluded.description,
            assigned_role = excluded.assigned_role,
            assigned_user_id = excluded.assigned_user_id,
            assigned_to = excluded.assigned_to,
            due_at = excluded.due_at,
            due_date = excluded.due_date,
            priority = excluded.priority,
            status = excluded.status,
            updated_at = excluded.updated_at,
            completed_at = excluded.completed_at,
            completed_by = excluded.completed_by
        """,
        (
            action.action_id,
            action.case_id,
            action.finding_id,
            action.mine_id,
            action.title,
            action.description,
            action.assigned_role,
            action.assigned_user_id,
            action.assigned_to or action.assigned_user_id,
            due_val,
            due_val,
            action.priority,
            action.status,
            c_at or datetime.now(timezone.utc).isoformat(),
            u_at or datetime.now(timezone.utc).isoformat(),
            comp_at,
            action.completed_by,
        ),
    )
    conn.commit()
    conn.close()


def get_corrective_action(action_id: str) -> Optional[dict]:
    conn = _connect()
    row = conn.execute(
        """
        SELECT *
        FROM corrective_actions
        WHERE action_id = ?
        """,
        (action_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_corrective_actions_for_case(case_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT *
        FROM corrective_actions
        WHERE case_id = ?
        ORDER BY created_at ASC
        """,
        (case_id,),
    ).fetchall()
    conn.close()
    return [CaseRecord(dict(r)) for r in rows]


def list_corrective_actions(
    case_id: Optional[str] = None,
    mine_id: Optional[str] = None,
) -> list[Any]:
    conn = _connect()
    query = "SELECT * FROM corrective_actions WHERE 1 = 1"
    params: list[Any] = []
    if case_id:
        query += " AND case_id = ?"
        params.append(case_id)
    if mine_id:
        query += " AND mine_id = ?"
        params.append(mine_id)
    query += " ORDER BY created_at ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [CaseRecord(dict(r)) for r in rows]


def save_case_correction_evidence(
    evidence_link_id: str,
    case_id: str,
    action_id: str,
    evidence_id: str,
    submitted_at: str,
    submitted_by: str,
    notes: Optional[str] = None,
    sha256: Optional[str] = None,
    ipfs_cid: Optional[str] = None,
    audit_proof_status: str = "AUDIT_PROOF_RECORDED",
) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO case_correction_evidence (
            evidence_link_id, case_id, action_id, evidence_id,
            submitted_at, submitted_by, notes, sha256, ipfs_cid, audit_proof_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(evidence_link_id) DO UPDATE SET
            notes = excluded.notes,
            sha256 = excluded.sha256,
            ipfs_cid = excluded.ipfs_cid,
            audit_proof_status = excluded.audit_proof_status
        """,
        (
            evidence_link_id,
            case_id,
            action_id,
            evidence_id,
            submitted_at,
            submitted_by,
            notes,
            sha256,
            ipfs_cid,
            audit_proof_status,
        ),
    )
    conn.commit()
    conn.close()


def list_case_correction_evidence(case_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT cce.*, e.evidence_type, e.filename, e.storage_reference, e.captured_at
        FROM case_correction_evidence cce
        LEFT JOIN evidence e ON cce.evidence_id = e.evidence_id
        WHERE cce.case_id = ?
        ORDER BY cce.submitted_at DESC
        """,
        (case_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def record_case_audit_event(
    event_id: str,
    case_id: str,
    action: str,
    actor_id: str,
    actor_role: Optional[str] = None,
    previous_state: Optional[str] = None,
    new_state: Optional[str] = None,
    reason: Optional[str] = None,
    timestamp: Optional[str] = None,
    details: Optional[str] = None,
    sha256: Optional[str] = None,
    ipfs_cid: Optional[str] = None,
) -> None:
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    conn = _connect()
    conn.execute(
        """
        INSERT INTO case_audit_events (
            event_id, case_id, action, actor_id, actor_role,
            previous_state, new_state, reason, timestamp, details,
            sha256, ipfs_cid
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            case_id,
            action,
            actor_id,
            actor_role,
            previous_state,
            new_state,
            reason,
            ts,
            details,
            sha256,
            ipfs_cid,
        ),
    )
    conn.commit()
    conn.close()


def list_case_audit_events(case_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT *
        FROM case_audit_events
        WHERE case_id = ?
        ORDER BY timestamp ASC
        """,
        (case_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_cryptographic_proof(proof: dict) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO cryptographic_proofs (
            proof_id, case_id, action_type, actor_id, actor_role,
            sha256, ipfs_cid, timestamp, status, ledger_standard,
            verified, payload
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(proof_id) DO UPDATE SET
            status = excluded.status,
            verified = excluded.verified
        """,
        (
            proof["proof_id"],
            proof["case_id"],
            proof["action_type"],
            proof["actor_id"],
            proof.get("actor_role", "OPERATIONAL_ACTOR"),
            proof["sha256"],
            proof["ipfs_cid"],
            proof["timestamp"],
            proof.get("status", "AUDIT_PROOF_RECORDED"),
            proof.get("ledger_standard", "PRITHVI-STATUTORY-AUDIT-V1"),
            int(proof.get("verified", True)),
            proof.get("payload") if isinstance(proof.get("payload"), str) else json.dumps(proof.get("payload", {})),
        ),
    )
    conn.commit()
    conn.close()


def list_cryptographic_proofs(case_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT *
        FROM cryptographic_proofs
        WHERE case_id = ?
        ORDER BY timestamp ASC
        """,
        (case_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ============================================================
# EVIDENCE INTEGRITY FUNCTIONS (PHASE 2 TASK 7)
# ============================================================

def save_evidence_integrity(record: dict) -> None:
    """Insert or update an evidence_integrity record."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO evidence_integrity (
            integrity_id, evidence_id, content_hash, hash_algorithm,
            ipfs_cid, ipfs_status, blockchain_network, transaction_ref,
            block_ref, anchored_at, anchor_mode, status,
            verified_at, verification_result, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(evidence_id) DO UPDATE SET
            content_hash = excluded.content_hash,
            ipfs_cid = excluded.ipfs_cid,
            ipfs_status = excluded.ipfs_status,
            blockchain_network = excluded.blockchain_network,
            transaction_ref = excluded.transaction_ref,
            block_ref = excluded.block_ref,
            anchored_at = excluded.anchored_at,
            anchor_mode = excluded.anchor_mode,
            status = excluded.status,
            verified_at = excluded.verified_at,
            verification_result = excluded.verification_result
        """,
        (
            record["integrity_id"],
            record["evidence_id"],
            record["content_hash"],
            record.get("hash_algorithm", "SHA-256"),
            record.get("ipfs_cid"),
            record.get("ipfs_status", "PENDING"),
            record.get("blockchain_network"),
            record.get("transaction_ref"),
            record.get("block_ref"),
            record.get("anchored_at"),
            record.get("anchor_mode", "DEMO_AUDIT_MODE"),
            record.get("status", "PENDING"),
            record.get("verified_at"),
            record.get("verification_result"),
            record["created_at"],
        ),
    )
    conn.commit()
    conn.close()


def get_evidence_integrity_by_evidence_id(evidence_id: str) -> Optional[dict]:
    """Return the integrity record for a given evidence_id, or None."""
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM evidence_integrity WHERE evidence_id = ?",
        (evidence_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_evidence_integrity_for_inspection(inspection_id: str) -> list[dict]:
    """Return all integrity records for evidence belonging to an inspection."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT ei.*
        FROM evidence_integrity ei
        JOIN evidence e ON e.evidence_id = ei.evidence_id
        WHERE e.inspection_id = ?
        ORDER BY ei.created_at ASC
        """,
        (inspection_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_evidence_integrity_for_case(case_id: str) -> list[dict]:
    """Return integrity records for all correction evidence linked to a case."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT ei.*
        FROM evidence_integrity ei
        JOIN case_correction_evidence cce ON cce.evidence_id = ei.evidence_id
        WHERE cce.case_id = ?
        ORDER BY ei.created_at ASC
        """,
        (case_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_evidence_integrity_verification(
    evidence_id: str,
    verification_result: str,
    verified_at: str,
    status: str,
) -> None:
    """Update the verification result on an integrity record."""
    conn = _connect()
    conn.execute(
        """
        UPDATE evidence_integrity
        SET verified_at = ?,
            verification_result = ?,
            status = ?
        WHERE evidence_id = ?
        """,
        (verified_at, verification_result, status, evidence_id),
    )
    conn.commit()
    conn.close()


# ============================================================
# MINE ZONE CRUD (PHASE 2 TASK 8)
# ============================================================

def upsert_mine_zone(zone: dict) -> dict:
    """Insert or update a mine zone record. Returns the stored zone dict."""
    from datetime import datetime, timezone
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO mine_zones (
            mine_zone_id, mine_id, name,
            latitude, longitude, geofence_radius_meters,
            description, active, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(mine_zone_id) DO UPDATE SET
            name = excluded.name,
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            geofence_radius_meters = excluded.geofence_radius_meters,
            description = excluded.description,
            active = excluded.active
        """,
        (
            zone["mine_zone_id"],
            zone["mine_id"],
            zone["name"],
            zone["latitude"],
            zone["longitude"],
            zone.get("geofence_radius_meters", 500.0),
            zone.get("description"),
            1 if zone.get("active", True) else 0,
            zone.get("created_at", now),
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM mine_zones WHERE mine_zone_id = ?",
        (zone["mine_zone_id"],),
    ).fetchone()
    conn.close()
    return dict(row) if row else zone


def get_mine_zone(zone_id: str) -> dict | None:
    """Return a single mine zone or None."""
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM mine_zones WHERE mine_zone_id = ?", (zone_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_mine_zones(mine_id: str) -> list[dict]:
    """Return all active zones for a mine."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM mine_zones WHERE mine_id = ? AND active = 1 ORDER BY name",
        (mine_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_mine_coordinates(mine_id: str, latitude: float, longitude: float, radius_m: float = 500.0) -> None:
    """Set the geospatial reference for a mine (non-destructive migration target)."""
    conn = _connect()
    conn.execute(
        """
        UPDATE mines
        SET latitude = ?, longitude = ?, geofence_radius_meters = ?
        WHERE mine_id = ?
        """,
        (latitude, longitude, radius_m, mine_id),
    )
    conn.commit()
    conn.close()


def get_mine_with_location(mine_id: str) -> dict | None:
    """Return a mine record including lat/lon if set."""
    conn = _connect()
    row = conn.execute("SELECT * FROM mines WHERE mine_id = ?", (mine_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ============================================================
# ATTENDANCE RECORD CRUD (PHASE 2 TASK 8)
# ============================================================

def insert_attendance(record: dict) -> dict:
    """Insert a new attendance record. Returns the stored record."""
    from datetime import datetime, timezone
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO attendance_records (
            attendance_id, user_id, user_role, mine_id,
            zone_id, schedule_instance_id, inspection_id,
            latitude, longitude, accuracy_meters,
            captured_at, server_recorded_at,
            geofence_status, distance_from_reference_meters,
            status, anomaly_status,
            evidence_id, device_info, notes, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["attendance_id"],
            record["user_id"],
            record["user_role"],
            record["mine_id"],
            record.get("zone_id"),
            record.get("schedule_instance_id"),
            record.get("inspection_id"),
            record.get("latitude"),
            record.get("longitude"),
            record.get("accuracy_meters"),
            record.get("captured_at"),
            record.get("server_recorded_at", now),
            record["geofence_status"],
            record.get("distance_from_reference_meters"),
            record.get("status", "VALID"),
            record.get("anomaly_status", "NONE"),
            record.get("evidence_id"),
            record.get("device_info"),
            record.get("notes"),
            record.get("created_at", now),
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM attendance_records WHERE attendance_id = ?",
        (record["attendance_id"],),
    ).fetchone()
    conn.close()
    return dict(row) if row else record


def get_attendance(attendance_id: str) -> dict | None:
    """Return a single attendance record or None."""
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM attendance_records WHERE attendance_id = ?",
        (attendance_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_attendance_for_user(user_id: str, limit: int = 50) -> list[dict]:
    """Return attendance records for a specific user, most recent first."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT * FROM attendance_records
        WHERE user_id = ?
        ORDER BY server_recorded_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_attendance_for_mine(mine_id: str, limit: int = 200) -> list[dict]:
    """Return attendance records for a specific mine, most recent first."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT * FROM attendance_records
        WHERE mine_id = ?
        ORDER BY server_recorded_at DESC
        LIMIT ?
        """,
        (mine_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_recent_user_attendance(user_id: str, limit: int = 5) -> list[dict]:
    """Return the most recent N attendance records for anomaly detection."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT * FROM attendance_records
        WHERE user_id = ?
        ORDER BY server_recorded_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_aggregate() -> dict:
    """Return aggregate attendance counts across all mines (no PII)."""
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM attendance_records").fetchone()[0]
    valid = conn.execute(
        "SELECT COUNT(*) FROM attendance_records WHERE status = 'VALID'"
    ).fetchone()[0]
    flagged = conn.execute(
        "SELECT COUNT(*) FROM attendance_records WHERE anomaly_status != 'NONE'"
    ).fetchone()[0]
    outside_gf = conn.execute(
        "SELECT COUNT(*) FROM attendance_records WHERE geofence_status = 'OUTSIDE_GEOFENCE'"
    ).fetchone()[0]
    mines_count = conn.execute(
        "SELECT COUNT(DISTINCT mine_id) FROM attendance_records"
    ).fetchone()[0]
    conn.close()
    return {
        "total_records": total,
        "valid_count": valid,
        "flagged_count": flagged,
        "outside_geofence_count": outside_gf,
        "mines_with_attendance": mines_count,
        "anomaly_count": flagged,
    }


def list_attendance_anomalies(mine_id: str | None = None, limit: int = 100) -> list[dict]:
    """Return attendance records with anomalies, optionally filtered by mine."""
    conn = _connect()
    if mine_id:
        rows = conn.execute(
            """
            SELECT * FROM attendance_records
            WHERE anomaly_status != 'NONE' AND mine_id = ?
            ORDER BY server_recorded_at DESC
            LIMIT ?
            """,
            (mine_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT * FROM attendance_records
            WHERE anomaly_status != 'NONE'
            ORDER BY server_recorded_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# SCADA / SENSOR TELEMETRY CRUD (PHASE 2 TASK 9)
# ============================================================

def upsert_sensor(s: dict) -> dict:
    """Insert or update a registered sensor."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO sensors (
            sensor_id, mine_id, zone_id, sensor_code,
            sensor_type, unit, display_name, status,
            simulated, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sensor_id) DO UPDATE SET
            mine_id = excluded.mine_id,
            zone_id = excluded.zone_id,
            sensor_code = excluded.sensor_code,
            sensor_type = excluded.sensor_type,
            unit = excluded.unit,
            display_name = excluded.display_name,
            status = excluded.status,
            simulated = excluded.simulated
        """,
        (
            s["sensor_id"],
            s["mine_id"],
            s.get("zone_id"),
            s["sensor_code"],
            s["sensor_type"],
            s["unit"],
            s["display_name"],
            s.get("status", "ACTIVE"),
            int(s.get("simulated", True)),
            s["created_at"],
        ),
    )
    conn.commit()
    conn.close()
    return s


def get_sensor(sensor_id: str) -> dict | None:
    """Fetch a sensor by ID."""
    conn = _connect()
    row = conn.execute("SELECT * FROM sensors WHERE sensor_id = ?", (sensor_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_sensor_by_code(sensor_code: str) -> dict | None:
    """Fetch a sensor by unique sensor_code."""
    conn = _connect()
    row = conn.execute("SELECT * FROM sensors WHERE sensor_code = ?", (sensor_code,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_sensors(mine_id: str | None = None) -> list[dict]:
    """List registered sensors, optionally filtered by mine."""
    conn = _connect()
    if mine_id:
        rows = conn.execute(
            "SELECT * FROM sensors WHERE mine_id = ? ORDER BY sensor_type, sensor_code",
            (mine_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM sensors ORDER BY mine_id, sensor_type").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_telemetry_reading(r: dict) -> dict:
    """Insert a telemetry reading into telemetry_readings."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO telemetry_readings (
            reading_id, sensor_id, mine_id, zone_id,
            sensor_type, value, unit, recorded_at,
            received_at, quality_status, threshold_status,
            source, simulated, evidence_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            r["reading_id"],
            r["sensor_id"],
            r["mine_id"],
            r.get("zone_id"),
            r["sensor_type"],
            float(r["value"]),
            r["unit"],
            r["recorded_at"],
            r["received_at"],
            r.get("quality_status", "GOOD"),
            r["threshold_status"],
            r.get("source", "SCADA_SIMULATOR"),
            int(r.get("simulated", True)),
            r.get("evidence_id"),
            r["created_at"],
        ),
    )
    conn.commit()
    conn.close()
    return r


def get_latest_telemetry_by_mine(mine_id: str) -> list[dict]:
    """
    Get the most recent reading for each sensor in a mine, joining with sensor display name.
    """
    conn = _connect()
    rows = conn.execute(
        """
        SELECT t.*, s.display_name, s.sensor_code
        FROM telemetry_readings t
        JOIN sensors s ON t.sensor_id = s.sensor_id
        WHERE t.mine_id = ?
        AND t.reading_id IN (
            SELECT reading_id FROM telemetry_readings
            WHERE mine_id = ?
            GROUP BY sensor_id
            HAVING recorded_at = MAX(recorded_at)
        )
        ORDER BY s.sensor_type
        """,
        (mine_id, mine_id),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_telemetry_history(
    mine_id: str,
    limit: int = 100,
    sensor_type: str | None = None,
) -> list[dict]:
    """Retrieve historical telemetry readings for a mine."""
    conn = _connect()
    if sensor_type:
        rows = conn.execute(
            """
            SELECT t.*, s.display_name, s.sensor_code
            FROM telemetry_readings t
            JOIN sensors s ON t.sensor_id = s.sensor_id
            WHERE t.mine_id = ? AND t.sensor_type = ?
            ORDER BY t.recorded_at DESC
            LIMIT ?
            """,
            (mine_id, sensor_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT t.*, s.display_name, s.sensor_code
            FROM telemetry_readings t
            JOIN sensors s ON t.sensor_id = s.sensor_id
            WHERE t.mine_id = ?
            ORDER BY t.recorded_at DESC
            LIMIT ?
            """,
            (mine_id, limit),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_signal_for_sensor(sensor_id: str) -> dict | None:
    """Find currently active safety signal for a sensor."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT * FROM safety_signals
        WHERE sensor_id = ? AND status = 'ACTIVE'
        ORDER BY last_detected_at DESC
        LIMIT 1
        """,
        (sensor_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_safety_signals(mine_id: str | None = None) -> list[dict]:
    """List all currently active safety signals."""
    conn = _connect()
    if mine_id:
        rows = conn.execute(
            """
            SELECT sig.*, s.display_name, s.sensor_code
            FROM safety_signals sig
            JOIN sensors s ON sig.sensor_id = s.sensor_id
            WHERE sig.mine_id = ? AND sig.status = 'ACTIVE'
            ORDER BY sig.last_detected_at DESC
            """,
            (mine_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT sig.*, s.display_name, s.sensor_code
            FROM safety_signals sig
            JOIN sensors s ON sig.sensor_id = s.sensor_id
            WHERE sig.status = 'ACTIVE'
            ORDER BY sig.last_detected_at DESC
            """
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_safety_signals_history(mine_id: str | None = None, limit: int = 100) -> list[dict]:
    """List safety signals (active and recovered) chronologically."""
    conn = _connect()
    if mine_id:
        rows = conn.execute(
            """
            SELECT sig.*, s.display_name, s.sensor_code
            FROM safety_signals sig
            JOIN sensors s ON sig.sensor_id = s.sensor_id
            WHERE sig.mine_id = ?
            ORDER BY sig.last_detected_at DESC
            LIMIT ?
            """,
            (mine_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT sig.*, s.display_name, s.sensor_code
            FROM safety_signals sig
            JOIN sensors s ON sig.sensor_id = s.sensor_id
            ORDER BY sig.last_detected_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_safety_signal(sig: dict) -> dict:
    """Insert or update a safety signal."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO safety_signals (
            signal_id, mine_id, sensor_id, sensor_type,
            severity, status, observed_value, unit,
            threshold_definition, explanation, first_detected_at,
            last_detected_at, recovered_at, consecutive_readings,
            linked_case_id, evidence_id, simulated, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(signal_id) DO UPDATE SET
            severity = excluded.severity,
            status = excluded.status,
            observed_value = excluded.observed_value,
            last_detected_at = excluded.last_detected_at,
            recovered_at = excluded.recovered_at,
            consecutive_readings = excluded.consecutive_readings,
            linked_case_id = COALESCE(excluded.linked_case_id, safety_signals.linked_case_id),
            evidence_id = COALESCE(excluded.evidence_id, safety_signals.evidence_id)
        """,
        (
            sig["signal_id"],
            sig["mine_id"],
            sig["sensor_id"],
            sig["sensor_type"],
            sig["severity"],
            sig.get("status", "ACTIVE"),
            float(sig["observed_value"]),
            sig["unit"],
            sig["threshold_definition"],
            sig["explanation"],
            sig["first_detected_at"],
            sig["last_detected_at"],
            sig.get("recovered_at"),
            int(sig.get("consecutive_readings", 1)),
            sig.get("linked_case_id"),
            sig.get("evidence_id"),
            int(sig.get("simulated", True)),
            sig["created_at"],
        ),
    )
    conn.commit()
    conn.close()
    return sig


def resolve_safety_signal(signal_id: str, recovered_at: str) -> None:
    """Mark an active safety signal as RECOVERED."""
    conn = _connect()
    conn.execute(
        """
        UPDATE safety_signals
        SET status = 'RECOVERED', recovered_at = ?
        WHERE signal_id = ?
        """,
        (recovered_at, signal_id),
    )
    conn.commit()
    conn.close()


def link_safety_signal_case(signal_id: str, case_id: str) -> None:
    """Link a synthesized ComplianceCase to an active safety signal."""
    conn = _connect()
    conn.execute(
        """
        UPDATE safety_signals
        SET linked_case_id = ?
        WHERE signal_id = ?
        """,
        (case_id, signal_id),
    )
    conn.commit()
    conn.close()


def get_telemetry_health_summary() -> dict:
    """Get diagnostic health stats for telemetry ingestion."""
    conn = _connect()
    total_sensors = conn.execute("SELECT COUNT(*) FROM sensors").fetchone()[0]
    total_readings = conn.execute("SELECT COUNT(*) FROM telemetry_readings").fetchone()[0]
    active_signals = conn.execute("SELECT COUNT(*) FROM safety_signals WHERE status = 'ACTIVE'").fetchone()[0]
    last_row = conn.execute("SELECT MAX(received_at) FROM telemetry_readings").fetchone()
    last_received_at = last_row[0] if last_row and last_row[0] else None

    # Count sensors reporting within last 5 minutes
    reporting_count = conn.execute(
        """
        SELECT COUNT(DISTINCT sensor_id) FROM telemetry_readings
        WHERE datetime(received_at) >= datetime('now', '-5 minutes')
        """
    ).fetchone()[0]

    conn.close()
    return {
        "source": "SIMULATED",
        "total_sensors_configured": total_sensors,
        "total_readings_stored": total_readings,
        "sensors_reporting_live": reporting_count,
        "active_safety_signals": active_signals,
        "last_telemetry_timestamp": last_received_at,
        "status": "OPERATIONAL" if total_sensors > 0 else "NO_SENSORS",
    }


# ============================================================
# PRODUCTION & OPERATIONAL GOVERNANCE (PHASE 2 TASK 10)
# ============================================================

def save_production_record(record: ProductionRecord) -> None:
    """Insert or update a production record."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO production_records (
            record_id, mine_id, area_id, subsidiary_id, shift_name,
            production_date, production_quantity, production_unit,
            dispatch_quantity, production_source, operation_type,
            zone_id, district_section, face_panel,
            overburden_quantity, overburden_unit,
            contractor_id, contractor_name, contract_type,
            target_quantity, downtime_minutes, delay_reason, hemm_context,
            entered_by, source_reference, status, is_superseded, superseded_by,
            correction_reason, content_hash, simulated, notes,
            recorded_at, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(record_id) DO UPDATE SET
            production_quantity = excluded.production_quantity,
            dispatch_quantity = excluded.dispatch_quantity,
            downtime_minutes = excluded.downtime_minutes,
            delay_reason = excluded.delay_reason,
            status = excluded.status,
            is_superseded = excluded.is_superseded,
            superseded_by = excluded.superseded_by,
            correction_reason = excluded.correction_reason,
            content_hash = excluded.content_hash,
            updated_at = excluded.updated_at
        """,
        (
            record.record_id,
            record.mine_id,
            record.area_id,
            record.subsidiary_id,
            record.shift_name,
            record.production_date,
            record.production_quantity,
            record.production_unit,
            record.dispatch_quantity,
            record.production_source.value if hasattr(record.production_source, "value") else str(record.production_source),
            record.operation_type.value if hasattr(record.operation_type, "value") else str(record.operation_type),
            record.zone_id,
            record.district_section,
            record.face_panel,
            record.overburden_quantity,
            record.overburden_unit,
            record.contractor_id,
            record.contractor_name,
            record.contract_type.value if record.contract_type and hasattr(record.contract_type, "value") else (str(record.contract_type) if record.contract_type else None),
            record.target_quantity,
            record.downtime_minutes,
            record.delay_reason,
            record.hemm_context,
            record.entered_by,
            record.source_reference,
            record.status.value if hasattr(record.status, "value") else str(record.status),
            1 if record.is_superseded else 0,
            record.superseded_by,
            record.correction_reason,
            record.content_hash,
            1 if record.simulated else 0,
            record.notes,
            record.recorded_at.isoformat() if isinstance(record.recorded_at, datetime) else str(record.recorded_at),
            record.created_at.isoformat() if isinstance(record.created_at, datetime) else str(record.created_at),
            record.updated_at.isoformat() if isinstance(record.updated_at, datetime) else str(record.updated_at),
        ),
    )
    conn.commit()
    conn.close()


def get_production_record(record_id: str) -> Optional[dict]:
    """Retrieve single production record by ID with mine name."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT r.*, m.name AS mine_name, m.subsidiary AS mine_subsidiary, m.area_name AS mine_area_name
        FROM production_records r
        LEFT JOIN mines m ON r.mine_id = m.mine_id
        WHERE r.record_id = ?
        """,
        (record_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_production_records(
    mine_id: Optional[str] = None,
    production_date: Optional[str] = None,
    shift_name: Optional[str] = None,
    include_superseded: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List production records with optional filters."""
    conn = _connect()
    query = """
        SELECT r.*, m.name AS mine_name, m.subsidiary AS mine_subsidiary, m.area_name AS mine_area_name
        FROM production_records r
        LEFT JOIN mines m ON r.mine_id = m.mine_id
        WHERE 1=1
    """
    params: list = []
    if mine_id:
        query += " AND r.mine_id = ?"
        params.append(mine_id)
    if production_date:
        query += " AND r.production_date = ?"
        params.append(production_date)
    if shift_name:
        query += " AND r.shift_name = ?"
        params.append(shift_name)
    if not include_superseded:
        query += " AND r.is_superseded = 0"

    query += " ORDER BY r.production_date DESC, r.recorded_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_production_target(target: ProductionTarget) -> None:
    """Configure or update a production target for a mine."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO production_targets (
            target_id, mine_id, target_date, daily_target_tonnes,
            monthly_target_tonnes, dispatch_target_tonnes, set_by, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(mine_id, target_date) DO UPDATE SET
            daily_target_tonnes = excluded.daily_target_tonnes,
            monthly_target_tonnes = excluded.monthly_target_tonnes,
            dispatch_target_tonnes = excluded.dispatch_target_tonnes,
            set_by = excluded.set_by
        """,
        (
            target.target_id,
            target.mine_id,
            target.target_date,
            target.daily_target_tonnes,
            target.monthly_target_tonnes,
            target.dispatch_target_tonnes,
            target.set_by,
            target.created_at.isoformat() if isinstance(target.created_at, datetime) else str(target.created_at),
        ),
    )
    conn.commit()
    conn.close()


def get_production_target(mine_id: str, target_date: str) -> Optional[dict]:
    """Get production target for a specific mine and date."""
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM production_targets WHERE mine_id = ? AND target_date = ?",
        (mine_id, target_date),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_production_targets(mine_id: str) -> list[dict]:
    """List all configured targets for a mine."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM production_targets WHERE mine_id = ? ORDER BY target_date DESC",
        (mine_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def correct_production_record(
    record_id: str,
    corrected_quantity: float,
    corrected_dispatch: Optional[float],
    reason: str,
    actor_id: str,
    notes: Optional[str] = None,
) -> dict:
    """
    Immutably correct a production record:
    1. Mark original as SUPERSEDED with superseded_by pointer.
    2. Create new corrected ProductionRecord linked to previous.
    3. Generate and record a ProductionAuditEvent.
    """
    import hashlib
    from uuid import uuid4

    conn = _connect()
    orig = conn.execute("SELECT * FROM production_records WHERE record_id = ?", (record_id,)).fetchone()
    if not orig:
        conn.close()
        raise ValueError(f"Production record {record_id} not found")

    orig_dict = dict(orig)
    if orig_dict.get("is_superseded"):
        conn.close()
        raise ValueError("Cannot correct an already superseded record")

    new_record_id = f"PROD-{uuid4().hex[:10].upper()}"
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Mark original as superseded
    conn.execute(
        """
        UPDATE production_records
        SET is_superseded = 1, status = 'SUPERSEDED', superseded_by = ?,
            correction_reason = ?, updated_at = ?
        WHERE record_id = ?
        """,
        (new_record_id, reason, now_iso, record_id),
    )

    # Compute new content hash
    content_raw = f"{orig_dict['mine_id']}|{orig_dict['production_date']}|{orig_dict['shift_name']}|{corrected_quantity}|{corrected_dispatch}|{reason}|{now_iso}"
    content_hash = hashlib.sha256(content_raw.encode("utf-8")).hexdigest()

    # Insert new corrected record
    conn.execute(
        """
        INSERT INTO production_records (
            record_id, mine_id, area_id, subsidiary_id, shift_name,
            production_date, production_quantity, production_unit,
            dispatch_quantity, production_source, operation_type,
            zone_id, district_section, face_panel,
            overburden_quantity, overburden_unit,
            contractor_id, contractor_name, contract_type,
            target_quantity, downtime_minutes, delay_reason, hemm_context,
            entered_by, source_reference, status, is_superseded, superseded_by,
            correction_reason, content_hash, simulated, notes,
            recorded_at, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_record_id,
            orig_dict["mine_id"],
            orig_dict["area_id"],
            orig_dict["subsidiary_id"],
            orig_dict["shift_name"],
            orig_dict["production_date"],
            corrected_quantity,
            orig_dict["production_unit"],
            corrected_dispatch if corrected_dispatch is not None else orig_dict["dispatch_quantity"],
            orig_dict["production_source"],
            orig_dict["operation_type"],
            orig_dict["zone_id"],
            orig_dict["district_section"],
            orig_dict["face_panel"],
            orig_dict["overburden_quantity"],
            orig_dict["overburden_unit"],
            orig_dict["contractor_id"],
            orig_dict["contractor_name"],
            orig_dict["contract_type"],
            orig_dict["target_quantity"],
            orig_dict["downtime_minutes"],
            orig_dict["delay_reason"],
            orig_dict["hemm_context"],
            actor_id,
            orig_dict["source_reference"],
            "RECORDED",
            0,
            None,
            f"Corrected from {record_id}: {reason}",
            content_hash,
            orig_dict["simulated"],
            notes or orig_dict["notes"],
            orig_dict["recorded_at"],
            now_iso,
            now_iso,
        ),
    )

    # Record audit event
    audit_event_id = f"PAUD-{uuid4().hex[:10].upper()}"
    conn.execute(
        """
        INSERT INTO production_audit_events (
            event_id, record_id, action, actor_id, previous_state, new_state, reason, timestamp, details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_event_id,
            record_id,
            "CORRECTION",
            actor_id,
            f"Quantity: {orig_dict['production_quantity']}, Dispatch: {orig_dict['dispatch_quantity']}",
            f"Quantity: {corrected_quantity}, Dispatch: {corrected_dispatch}, New Record: {new_record_id}",
            reason,
            now_iso,
            f"Audit proof: {content_hash}",
        ),
    )

    conn.commit()

    new_row = conn.execute("SELECT * FROM production_records WHERE record_id = ?", (new_record_id,)).fetchone()
    conn.close()
    return dict(new_row)


def save_production_audit_event(
    event_id: str,
    record_id: str,
    action: str,
    actor_id: str,
    previous_state: Optional[str] = None,
    new_state: Optional[str] = None,
    reason: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    """Persist an audit event for production record actions."""
    conn = _connect()
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO production_audit_events (
            event_id, record_id, action, actor_id, previous_state, new_state, reason, timestamp, details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, record_id, action, actor_id, previous_state, new_state, reason, now_iso, details),
    )
    conn.commit()
    conn.close()


def get_production_audit_events(record_id: str) -> list[dict]:
    """Retrieve audit history for a production record."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM production_audit_events WHERE record_id = ? ORDER BY timestamp DESC",
        (record_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_production_anomaly(anomaly: ProductionAnomaly) -> None:
    """Save an explainable production anomaly."""
    conn = _connect()
    affected_ids_str = ",".join(anomaly.affected_record_ids)
    conn.execute(
        """
        INSERT INTO production_anomalies (
            anomaly_id, mine_id, anomaly_type, severity, what, why,
            source, time, affected_record_ids, recommended_review,
            resolved, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(anomaly_id) DO UPDATE SET
            resolved = excluded.resolved,
            recommended_review = excluded.recommended_review
        """,
        (
            anomaly.anomaly_id,
            anomaly.mine_id,
            anomaly.anomaly_type,
            anomaly.severity,
            anomaly.what,
            anomaly.why,
            anomaly.source,
            anomaly.time.isoformat() if isinstance(anomaly.time, datetime) else str(anomaly.time),
            affected_ids_str,
            anomaly.recommended_review,
            1 if anomaly.resolved else 0,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_active_production_anomalies(mine_id: Optional[str] = None) -> list[dict]:
    """Retrieve active (unresolved) production anomalies."""
    conn = _connect()
    if mine_id:
        rows = conn.execute(
            """
            SELECT a.*, m.name AS mine_name
            FROM production_anomalies a
            LEFT JOIN mines m ON a.mine_id = m.mine_id
            WHERE a.mine_id = ? AND a.resolved = 0
            ORDER BY a.created_at DESC
            """,
            (mine_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT a.*, m.name AS mine_name
            FROM production_anomalies a
            LEFT JOIN mines m ON a.mine_id = m.mine_id
            WHERE a.resolved = 0
            ORDER BY a.created_at DESC
            """
        ).fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["affected_record_ids"] = d["affected_record_ids"].split(",") if d.get("affected_record_ids") else []
        d["resolved"] = bool(d.get("resolved"))
        result.append(d)
    return result


def resolve_production_anomaly(anomaly_id: str) -> bool:
    """Mark a production anomaly as resolved."""
    conn = _connect()
    cursor = conn.execute(
        "UPDATE production_anomalies SET resolved = 1 WHERE anomaly_id = ?",
        (anomaly_id,),
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def update_mine_hierarchy_info(mine_id: str, area_id: str, area_name: str) -> None:
    """Ensure a mine has its area_id and area_name populated."""
    conn = _connect()
    conn.execute(
        "UPDATE mines SET area_id = ?, area_name = ? WHERE mine_id = ?",
        (area_id, area_name, mine_id),
    )
    conn.commit()
    conn.close()


# ============================================================
# GOVERNANCE MASTER & ORGANIZATIONAL HIERARCHY (PHASE 2 TASK 11)
# ============================================================

def save_organization_unit(unit: OrganizationUnit) -> None:
    """Insert or update a canonical organization unit."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO organization_units (
            id, parent_id, unit_type, code, name, legal_name,
            status, state, district, headquarters,
            effective_from, effective_to, metadata, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            parent_id = excluded.parent_id,
            name = excluded.name,
            legal_name = excluded.legal_name,
            status = excluded.status,
            state = excluded.state,
            district = excluded.district,
            headquarters = excluded.headquarters,
            effective_to = excluded.effective_to,
            metadata = excluded.metadata,
            updated_at = excluded.updated_at
        """,
        (
            unit.id,
            unit.parent_id,
            unit.unit_type.value if hasattr(unit.unit_type, "value") else str(unit.unit_type),
            unit.code,
            unit.name,
            unit.legal_name,
            unit.status,
            unit.state,
            unit.district,
            unit.headquarters,
            unit.effective_from,
            unit.effective_to,
            unit.metadata,
            unit.created_at.isoformat() if isinstance(unit.created_at, datetime) else str(unit.created_at),
            unit.updated_at.isoformat() if isinstance(unit.updated_at, datetime) else str(unit.updated_at),
        ),
    )
    conn.commit()
    conn.close()


def get_organization_unit(unit_id: str) -> Optional[dict]:
    """Retrieve single organization unit by ID."""
    conn = _connect()
    row = conn.execute("SELECT * FROM organization_units WHERE id = ?", (unit_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_organization_units(
    parent_id: Optional[str] = None,
    unit_type: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    """List organization units with optional filtering."""
    conn = _connect()
    query = "SELECT * FROM organization_units WHERE 1=1"
    params: list = []
    if parent_id is not None:
        if parent_id == "ROOT":
            query += " AND parent_id IS NULL"
        else:
            query += " AND parent_id = ?"
            params.append(parent_id)
    if unit_type:
        query += " AND unit_type = ?"
        params.append(unit_type)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY name ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_operational_unit(unit: OperationalUnit) -> None:
    """Insert or update an operational unit."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO operational_units (
            id, mine_id, parent_operational_unit_id, unit_type,
            code, name, active, latitude, longitude, geofence_radius,
            metadata, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            active = excluded.active,
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            geofence_radius = excluded.geofence_radius,
            metadata = excluded.metadata,
            updated_at = excluded.updated_at
        """,
        (
            unit.id,
            unit.mine_id,
            unit.parent_operational_unit_id,
            unit.unit_type.value if hasattr(unit.unit_type, "value") else str(unit.unit_type),
            unit.code,
            unit.name,
            1 if unit.active else 0,
            unit.latitude,
            unit.longitude,
            unit.geofence_radius,
            unit.metadata,
            unit.created_at.isoformat() if isinstance(unit.created_at, datetime) else str(unit.created_at),
            unit.updated_at.isoformat() if isinstance(unit.updated_at, datetime) else str(unit.updated_at),
        ),
    )
    conn.commit()
    conn.close()


def get_operational_unit(unit_id: str) -> Optional[dict]:
    """Retrieve operational unit by ID."""
    conn = _connect()
    row = conn.execute("SELECT * FROM operational_units WHERE id = ?", (unit_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["active"] = bool(d["active"])
    return d


def list_operational_units(
    mine_id: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> list[dict]:
    """List operational units for a mine or parent operational unit."""
    conn = _connect()
    query = "SELECT * FROM operational_units WHERE 1=1"
    params: list = []
    if mine_id:
        query += " AND mine_id = ?"
        params.append(mine_id)
    if parent_id is not None:
        if parent_id == "ROOT":
            query += " AND parent_operational_unit_id IS NULL"
        else:
            query += " AND parent_operational_unit_id = ?"
            params.append(parent_id)
    query += " ORDER BY code ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["active"] = bool(d["active"])
        result.append(d)
    return result


def save_contractor(contractor: ContractorMaster) -> None:
    """Insert or update a contractor master entity."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO contractors (
            id, legal_name, display_name, registration_reference,
            status, contractor_type, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            legal_name = excluded.legal_name,
            display_name = excluded.display_name,
            registration_reference = excluded.registration_reference,
            status = excluded.status,
            contractor_type = excluded.contractor_type,
            updated_at = excluded.updated_at
        """,
        (
            contractor.id,
            contractor.legal_name,
            contractor.display_name,
            contractor.registration_reference,
            contractor.status,
            contractor.contractor_type.value if hasattr(contractor.contractor_type, "value") else str(contractor.contractor_type),
            contractor.created_at.isoformat() if isinstance(contractor.created_at, datetime) else str(contractor.created_at),
            contractor.updated_at.isoformat() if isinstance(contractor.updated_at, datetime) else str(contractor.updated_at),
        ),
    )
    conn.commit()
    conn.close()


def get_contractor(contractor_id: str) -> Optional[dict]:
    """Retrieve contractor by ID."""
    conn = _connect()
    row = conn.execute("SELECT * FROM contractors WHERE id = ?", (contractor_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_contractors(status: Optional[str] = None) -> list[dict]:
    """List contractor master entities."""
    conn = _connect()
    query = "SELECT * FROM contractors WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY display_name ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_contract(contract: ContractMaster) -> None:
    """Insert or update a contract master association."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO contracts (
            id, contractor_id, mine_id, area_id, subsidiary_id,
            contract_type, contract_number, scope, start_date, end_date,
            workforce_limit, status, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            contractor_id = excluded.contractor_id,
            contract_type = excluded.contract_type,
            scope = excluded.scope,
            end_date = excluded.end_date,
            workforce_limit = excluded.workforce_limit,
            status = excluded.status,
            updated_at = excluded.updated_at
        """,
        (
            contract.id,
            contract.contractor_id,
            contract.mine_id,
            contract.area_id,
            contract.subsidiary_id,
            contract.contract_type.value if hasattr(contract.contract_type, "value") else str(contract.contract_type),
            contract.contract_number,
            contract.scope,
            contract.start_date,
            contract.end_date,
            contract.workforce_limit,
            contract.status,
            contract.created_at.isoformat() if isinstance(contract.created_at, datetime) else str(contract.created_at),
            contract.updated_at.isoformat() if isinstance(contract.updated_at, datetime) else str(contract.updated_at),
        ),
    )
    conn.commit()
    conn.close()


def get_contract(contract_id: str) -> Optional[dict]:
    """Retrieve contract with contractor and mine display details."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT c.*, k.display_name AS contractor_name, m.name AS mine_name
        FROM contracts c
        LEFT JOIN contractors k ON c.contractor_id = k.id
        LEFT JOIN mines m ON c.mine_id = m.mine_id
        WHERE c.id = ?
        """,
        (contract_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_contracts(
    mine_id: Optional[str] = None,
    contractor_id: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    """List contracts with optional filtering."""
    conn = _connect()
    query = """
        SELECT c.*, k.display_name AS contractor_name, m.name AS mine_name
        FROM contracts c
        LEFT JOIN contractors k ON c.contractor_id = k.id
        LEFT JOIN mines m ON c.mine_id = m.mine_id
        WHERE 1=1
    """
    params: list = []
    if mine_id:
        query += " AND c.mine_id = ?"
        params.append(mine_id)
    if contractor_id:
        query += " AND c.contractor_id = ?"
        params.append(contractor_id)
    if status:
        query += " AND c.status = ?"
        params.append(status)
    query += " ORDER BY c.start_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_worker(worker: WorkerMaster) -> None:
    """Insert or update a worker master record."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO workers (
            id, worker_code, name, worker_type, contractor_id,
            contract_id, mine_id, skill_category, department,
            active, onboarding_date, training_status, identity_reference,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            worker_type = excluded.worker_type,
            contractor_id = excluded.contractor_id,
            contract_id = excluded.contract_id,
            mine_id = excluded.mine_id,
            skill_category = excluded.skill_category,
            department = excluded.department,
            active = excluded.active,
            training_status = excluded.training_status,
            identity_reference = excluded.identity_reference,
            updated_at = excluded.updated_at
        """,
        (
            worker.id,
            worker.worker_code,
            worker.name,
            worker.worker_type.value if hasattr(worker.worker_type, "value") else str(worker.worker_type),
            worker.contractor_id,
            worker.contract_id,
            worker.mine_id,
            worker.skill_category,
            worker.department,
            1 if worker.active else 0,
            worker.onboarding_date,
            worker.training_status,
            worker.identity_reference,
            worker.created_at.isoformat() if isinstance(worker.created_at, datetime) else str(worker.created_at),
            worker.updated_at.isoformat() if isinstance(worker.updated_at, datetime) else str(worker.updated_at),
        ),
    )
    conn.commit()
    conn.close()


def get_worker(worker_id: str) -> Optional[dict]:
    """Retrieve worker by ID with contract and mine names."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT w.*, c.contract_number, k.display_name AS contractor_name, m.name AS mine_name
        FROM workers w
        LEFT JOIN contracts c ON w.contract_id = c.id
        LEFT JOIN contractors k ON w.contractor_id = k.id
        LEFT JOIN mines m ON w.mine_id = m.mine_id
        WHERE w.id = ?
        """,
        (worker_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["active"] = bool(d["active"])
    return d


def get_worker_by_code(worker_code: str) -> Optional[dict]:
    """Retrieve worker by unique employee/contractor worker code."""
    conn = _connect()
    row = conn.execute(
        """
        SELECT w.*, c.contract_number, k.display_name AS contractor_name, m.name AS mine_name
        FROM workers w
        LEFT JOIN contracts c ON w.contract_id = c.id
        LEFT JOIN contractors k ON w.contractor_id = k.id
        LEFT JOIN mines m ON w.mine_id = m.mine_id
        WHERE w.worker_code = ?
        """,
        (worker_code,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["active"] = bool(d["active"])
    return d


def list_workers(
    mine_id: Optional[str] = None,
    contract_id: Optional[str] = None,
    active_only: bool = False,
) -> list[dict]:
    """List workers for a mine or contract."""
    conn = _connect()
    query = """
        SELECT w.*, c.contract_number, k.display_name AS contractor_name, m.name AS mine_name
        FROM workers w
        LEFT JOIN contracts c ON w.contract_id = c.id
        LEFT JOIN contractors k ON w.contractor_id = k.id
        LEFT JOIN mines m ON w.mine_id = m.mine_id
        WHERE 1=1
    """
    params: list = []
    if mine_id:
        query += " AND w.mine_id = ?"
        params.append(mine_id)
    if contract_id:
        query += " AND w.contract_id = ?"
        params.append(contract_id)
    if active_only:
        query += " AND w.active = 1"
    query += " ORDER BY w.name ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["active"] = bool(d["active"])
        result.append(d)
    return result


def save_organization_audit_event(event: OrganizationAuditEvent) -> None:
    """Record an immutable audit event for master hierarchy structural changes."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO organization_audit_events (
            event_id, entity_type, entity_id, action, actor_id,
            previous_state, new_state, reason, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.event_id,
            event.entity_type,
            event.entity_id,
            event.action,
            event.actor_id,
            event.previous_state,
            event.new_state,
            event.reason,
            event.timestamp.isoformat() if isinstance(event.timestamp, datetime) else str(event.timestamp),
        ),
    )
    conn.commit()
    conn.close()


def get_organization_audit_events(entity_id: Optional[str] = None, limit: int = 100) -> list[dict]:
    """Retrieve audit events for organizational master changes."""
    conn = _connect()
    if entity_id:
        rows = conn.execute(
            "SELECT * FROM organization_audit_events WHERE entity_id = ? ORDER BY timestamp DESC LIMIT ?",
            (entity_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM organization_audit_events ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_hierarchy_nodes(q: str, limit: int = 20) -> list[dict]:
    """Search organization and operational units matching text query."""
    if not q or not q.strip():
        return []
    conn = _connect()
    cleaned = q.strip()
    pattern = f"%{cleaned}%"
    exact_pat = f"{cleaned}%"

    org_query = """
        SELECT id, parent_id, unit_type, code, name, legal_name, status, state, district, headquarters
        FROM organization_units
        WHERE name LIKE ? OR code LIKE ? OR district LIKE ? OR state LIKE ? OR headquarters LIKE ?
        ORDER BY 
            CASE 
                WHEN code LIKE ? THEN 1
                WHEN name LIKE ? THEN 2
                ELSE 3
            END,
            name ASC
        LIMIT ?
    """
    org_rows = conn.execute(org_query, (pattern, pattern, pattern, pattern, pattern, exact_pat, exact_pat, limit)).fetchall()

    op_query = """
        SELECT id, mine_id, parent_operational_unit_id, unit_type, code, name, active
        FROM operational_units
        WHERE name LIKE ? OR code LIKE ?
        ORDER BY 
            CASE 
                WHEN code LIKE ? THEN 1
                WHEN name LIKE ? THEN 2
                ELSE 3
            END,
            name ASC
        LIMIT ?
    """
    op_rows = conn.execute(op_query, (pattern, pattern, exact_pat, exact_pat, limit)).fetchall()
    conn.close()

    results = []
    for r in org_rows:
        d = dict(r)
        d["node_category"] = "ORGANIZATION_UNIT"
        results.append(d)
    for r in op_rows:
        d = dict(r)
        d["node_category"] = "OPERATIONAL_UNIT"
        d["active"] = bool(d["active"])
        results.append(d)
    return results[:limit]


# ============================================================
# ENVIRONMENTAL GOVERNANCE HELPER FUNCTIONS (PHASE 2 TASK 13)
# ============================================================

def save_environmental_parameter(param: EnvironmentalParameter) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT OR REPLACE INTO environmental_parameters (
            id, code, name, domain, unit, description,
            mine_type_applicability, active, metadata, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            param.id,
            param.code,
            param.name,
            param.domain.value if hasattr(param.domain, "value") else str(param.domain),
            param.unit,
            param.description,
            param.mine_type_applicability,
            1 if param.active else 0,
            param.metadata,
            param.created_at.isoformat() if isinstance(param.created_at, datetime) else str(param.created_at),
            param.updated_at.isoformat() if isinstance(param.updated_at, datetime) else str(param.updated_at),
        ),
    )
    conn.commit()
    conn.close()


def get_environmental_parameter(param_id: str) -> Optional[EnvironmentalParameter]:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM environmental_parameters WHERE id = ? OR code = ?",
        (param_id, param_id),
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["active"] = bool(d["active"])
    d["domain"] = EnvironmentalDomain(d["domain"])
    d["created_at"] = datetime.fromisoformat(d["created_at"])
    d["updated_at"] = datetime.fromisoformat(d["updated_at"])
    return EnvironmentalParameter(**d)


def list_environmental_parameters(
    domain: Optional[str] = None,
    mine_type: Optional[str] = None,
    active_only: bool = True,
) -> list[EnvironmentalParameter]:
    conn = _connect()
    query = "SELECT * FROM environmental_parameters WHERE 1=1"
    params = []
    if active_only:
        query += " AND active = 1"
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    query += " ORDER BY domain ASC, name ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["active"] = bool(d["active"])
        d["domain"] = EnvironmentalDomain(d["domain"])
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d["updated_at"] = datetime.fromisoformat(d["updated_at"])
        # Mine type applicability check
        if mine_type and d["mine_type_applicability"] != "ALL":
            if mine_type.upper() not in d["mine_type_applicability"].upper():
                continue
        results.append(EnvironmentalParameter(**d))
    return results


def save_environmental_threshold(th: EnvironmentalThreshold) -> None:
    conn = _connect()
    created_at = th.created_at.isoformat() if isinstance(th.created_at, datetime) else (th.created_at or datetime.now().isoformat())
    conn.execute(
        """
        INSERT OR REPLACE INTO environmental_thresholds (
            id, parameter_id, mine_type, threshold_type,
            lower_limit, upper_limit, unit, applicable_from, applicable_to,
            severity, source_reference, is_demo_rule, active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            th.id,
            th.parameter_id,
            th.mine_type,
            th.threshold_type,
            th.lower_limit,
            th.upper_limit,
            th.unit,
            th.applicable_from,
            th.applicable_to,
            th.severity,
            th.source_reference,
            1 if th.is_demo_rule else 0,
            1 if th.active else 0,
            created_at,
        ),
    )
    conn.commit()
    conn.close()


def get_environmental_threshold(th_id: str) -> Optional[EnvironmentalThreshold]:
    conn = _connect()
    row = conn.execute("SELECT * FROM environmental_thresholds WHERE id = ?", (th_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["is_demo_rule"] = bool(d["is_demo_rule"])
    d["active"] = bool(d["active"])
    if d.get("created_at"):
        d["created_at"] = datetime.fromisoformat(d["created_at"])
    return EnvironmentalThreshold(**d)


def list_environmental_thresholds(
    parameter_id: Optional[str] = None,
    mine_type: Optional[str] = None,
    active_only: bool = True,
) -> list[EnvironmentalThreshold]:
    conn = _connect()
    query = "SELECT * FROM environmental_thresholds WHERE 1=1"
    params = []
    if active_only:
        query += " AND active = 1"
    if parameter_id:
        query += " AND parameter_id = ?"
        params.append(parameter_id)
    if mine_type:
        query += " AND (mine_type = 'ALL' OR mine_type = ?)"
        params.append(mine_type)
    query += " ORDER BY parameter_id ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["is_demo_rule"] = bool(d["is_demo_rule"])
        d["active"] = bool(d["active"])
        if d.get("created_at"):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        results.append(EnvironmentalThreshold(**d))
    return results


def save_environmental_obligation(ob: EnvironmentalObligation) -> None:
    conn = _connect()
    created_at = ob.created_at.isoformat() if isinstance(ob.created_at, datetime) else (ob.created_at or datetime.now().isoformat())
    conn.execute(
        """
        INSERT OR REPLACE INTO environmental_obligations (
            obligation_id, mine_id, code, title, description,
            domain, applicable_mine_type, frequency, responsible_role,
            regulatory_source, evidence_requirements, active,
            start_date, end_date, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ob.obligation_id,
            ob.mine_id,
            ob.code,
            ob.title,
            ob.description,
            ob.domain.value if hasattr(ob.domain, "value") else str(ob.domain),
            ob.applicable_mine_type,
            ob.frequency,
            ob.responsible_role,
            ob.regulatory_source,
            ob.evidence_requirements,
            1 if ob.active else 0,
            ob.start_date,
            ob.end_date,
            created_at,
        ),
    )
    conn.commit()
    conn.close()


def get_environmental_obligation(ob_id: str) -> Optional[EnvironmentalObligation]:
    conn = _connect()
    row = conn.execute("SELECT * FROM environmental_obligations WHERE obligation_id = ? OR code = ?", (ob_id, ob_id)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["active"] = bool(d["active"])
    d["domain"] = EnvironmentalDomain(d["domain"])
    if d.get("created_at"):
        d["created_at"] = datetime.fromisoformat(d["created_at"])
    return EnvironmentalObligation(**d)


def list_environmental_obligations(
    mine_id: Optional[str] = None,
    domain: Optional[str] = None,
    active_only: bool = True,
) -> list[EnvironmentalObligation]:
    conn = _connect()
    query = "SELECT * FROM environmental_obligations WHERE 1=1"
    params = []
    if active_only:
        query += " AND active = 1"
    if mine_id:
        query += " AND mine_id = ?"
        params.append(mine_id)
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    query += " ORDER BY mine_id ASC, code ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["active"] = bool(d["active"])
        d["domain"] = EnvironmentalDomain(d["domain"])
        if d.get("created_at"):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        results.append(EnvironmentalObligation(**d))
    return results


def save_environmental_schedule(sch: EnvironmentalSchedule) -> None:
    conn = _connect()
    created_at = sch.created_at.isoformat() if isinstance(sch.created_at, datetime) else (sch.created_at or datetime.now().isoformat())
    conn.execute(
        """
        INSERT OR REPLACE INTO environmental_schedules (
            schedule_id, obligation_id, mine_id, parameter_id,
            operational_unit_id, domain, due_date, responsible_role,
            status, completed_at, measurement_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sch.schedule_id,
            sch.obligation_id,
            sch.mine_id,
            sch.parameter_id,
            sch.operational_unit_id,
            sch.domain.value if hasattr(sch.domain, "value") else str(sch.domain),
            sch.due_date,
            sch.responsible_role,
            sch.status,
            sch.completed_at,
            sch.measurement_id,
            created_at,
        ),
    )
    conn.commit()
    conn.close()


def get_environmental_schedule(sch_id: str) -> Optional[EnvironmentalSchedule]:
    conn = _connect()
    row = conn.execute("SELECT * FROM environmental_schedules WHERE schedule_id = ?", (sch_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["domain"] = EnvironmentalDomain(d["domain"])
    if d.get("created_at"):
        d["created_at"] = datetime.fromisoformat(d["created_at"])
    return EnvironmentalSchedule(**d)


def list_environmental_schedules(
    mine_id: Optional[str] = None,
    domain: Optional[str] = None,
    status: Optional[str] = None,
) -> list[EnvironmentalSchedule]:
    conn = _connect()
    query = "SELECT * FROM environmental_schedules WHERE 1=1"
    params = []
    if mine_id:
        query += " AND mine_id = ?"
        params.append(mine_id)
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY due_date ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["domain"] = EnvironmentalDomain(d["domain"])
        if d.get("created_at"):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        results.append(EnvironmentalSchedule(**d))
    return results


def save_environmental_measurement(m: EnvironmentalMeasurement) -> None:
    conn = _connect()
    measured_at = m.measured_at.isoformat() if isinstance(m.measured_at, datetime) else str(m.measured_at)
    created_at = m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at)
    updated_at = m.updated_at.isoformat() if isinstance(m.updated_at, datetime) else str(m.updated_at)
    source_type = m.source_type.value if hasattr(m.source_type, "value") else str(m.source_type)
    quality_status = m.data_quality_status.value if hasattr(m.data_quality_status, "value") else str(m.data_quality_status)

    conn.execute(
        """
        INSERT OR REPLACE INTO environmental_measurements (
            id, mine_id, operational_unit_id, parameter_id,
            value, unit, measured_at, source_type, source_reference,
            latitude, longitude, device_reference, entered_by,
            status, evidence_id, data_quality_status, quality_notes,
            simulated, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            m.id,
            m.mine_id,
            m.operational_unit_id,
            m.parameter_id,
            m.value,
            m.unit,
            measured_at,
            source_type,
            m.source_reference,
            m.latitude,
            m.longitude,
            m.device_reference,
            m.entered_by,
            m.status,
            m.evidence_id,
            quality_status,
            m.quality_notes,
            1 if m.simulated else 0,
            created_at,
            updated_at,
        ),
    )
    conn.commit()
    conn.close()


def get_environmental_measurement(m_id: str) -> Optional[EnvironmentalMeasurement]:
    conn = _connect()
    row = conn.execute(
        """
        SELECT m.*, p.code as parameter_code, p.name as parameter_name, p.domain as parameter_domain
        FROM environmental_measurements m
        LEFT JOIN environmental_parameters p ON m.parameter_id = p.id
        WHERE m.id = ?
        """,
        (m_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["simulated"] = bool(d["simulated"])
    d["source_type"] = EnvironmentalSourceType(d["source_type"])
    d["data_quality_status"] = DataQualityStatus(d["data_quality_status"])
    d["measured_at"] = datetime.fromisoformat(d["measured_at"])
    d["created_at"] = datetime.fromisoformat(d["created_at"])
    d["updated_at"] = datetime.fromisoformat(d["updated_at"])
    if d.get("parameter_domain"):
        d["domain"] = EnvironmentalDomain(d["parameter_domain"])
        del d["parameter_domain"]
    return EnvironmentalMeasurement(**d)


def list_environmental_measurements(
    mine_id: Optional[str] = None,
    parameter_id: Optional[str] = None,
    domain: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 200,
) -> list[EnvironmentalMeasurement]:
    conn = _connect()
    query = """
        SELECT m.*, p.code as parameter_code, p.name as parameter_name, p.domain as parameter_domain
        FROM environmental_measurements m
        LEFT JOIN environmental_parameters p ON m.parameter_id = p.id
        WHERE 1=1
    """
    params = []
    if mine_id:
        query += " AND m.mine_id = ?"
        params.append(mine_id)
    if parameter_id:
        query += " AND (m.parameter_id = ? OR p.code = ?)"
        params.extend([parameter_id, parameter_id])
    if domain:
        query += " AND p.domain = ?"
        params.append(domain)
    if start_date:
        query += " AND m.measured_at >= ?"
        params.append(start_date)
    if end_date:
        query += " AND m.measured_at <= ?"
        params.append(end_date)
    query += " ORDER BY m.measured_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["simulated"] = bool(d["simulated"])
        d["source_type"] = EnvironmentalSourceType(d["source_type"])
        d["data_quality_status"] = DataQualityStatus(d["data_quality_status"])
        d["measured_at"] = datetime.fromisoformat(d["measured_at"])
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d["updated_at"] = datetime.fromisoformat(d["updated_at"])
        if d.get("parameter_domain"):
            d["domain"] = EnvironmentalDomain(d["parameter_domain"])
            del d["parameter_domain"]
        results.append(EnvironmentalMeasurement(**d))
    return results


def save_environmental_report(rep: EnvironmentalReport) -> None:
    conn = _connect()
    generated_at = rep.generated_at.isoformat() if isinstance(rep.generated_at, datetime) else str(rep.generated_at)
    finalized_at = rep.finalized_at.isoformat() if isinstance(rep.finalized_at, datetime) else (str(rep.finalized_at) if rep.finalized_at else None)
    conn.execute(
        """
        INSERT OR REPLACE INTO environmental_reports (
            report_id, mine_id, reporting_period_start, reporting_period_end,
            title, report_type, status, summary, measurements_count,
            violations_count, open_cases_count, corrective_actions_count,
            lineage_snapshot, source_record_hashes, content_hash, ipfs_cid,
            generated_by, generated_at, finalized_at, finalized_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rep.report_id,
            rep.mine_id,
            rep.reporting_period_start,
            rep.reporting_period_end,
            rep.title,
            rep.report_type,
            rep.status,
            rep.summary,
            rep.measurements_count,
            rep.violations_count,
            rep.open_cases_count,
            rep.corrective_actions_count,
            rep.lineage_snapshot,
            rep.source_record_hashes,
            rep.content_hash,
            rep.ipfs_cid,
            rep.generated_by,
            generated_at,
            finalized_at,
            rep.finalized_by,
        ),
    )
    conn.commit()
    conn.close()


def get_environmental_report(report_id: str) -> Optional[EnvironmentalReport]:
    conn = _connect()
    row = conn.execute("SELECT * FROM environmental_reports WHERE report_id = ?", (report_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["generated_at"] = datetime.fromisoformat(d["generated_at"])
    if d.get("finalized_at"):
        d["finalized_at"] = datetime.fromisoformat(d["finalized_at"])
    return EnvironmentalReport(**d)


def list_environmental_reports(mine_id: Optional[str] = None) -> list[EnvironmentalReport]:
    conn = _connect()
    query = "SELECT * FROM environmental_reports WHERE 1=1"
    params = []
    if mine_id:
        query += " AND mine_id = ?"
        params.append(mine_id)
    query += " ORDER BY generated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["generated_at"] = datetime.fromisoformat(d["generated_at"])
        if d.get("finalized_at"):
            d["finalized_at"] = datetime.fromisoformat(d["finalized_at"])
        results.append(EnvironmentalReport(**d))
    return results






