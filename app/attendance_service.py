"""
PRITHVI — Attendance Service (Phase 2 Task 8)

Orchestrates GPS check-in workflow:
    1. Validate inputs and RBAC
    2. Resolve mine/zone reference coordinates
    3. Run server-side Haversine geofence check
    4. Detect anomalies deterministically
    5. Persist attendance record
    6. Log audit event to existing audit_log
    7. Optionally link to inspection/schedule
    8. Return structured response

This module NEVER auto-validates attendance. Presence evidence ≠ inspection completion.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.geofence import check_geofence, detect_attendance_anomaly, GeofenceResult
from app.models import GeofenceStatus, AttendanceStatus, AnomalyStatus
from app.database import (
    insert_attendance,
    get_attendance,
    list_attendance_for_user,
    list_attendance_for_mine,
    list_recent_user_attendance,
    get_attendance_aggregate,
    list_attendance_anomalies,
    get_mine_with_location,
    get_mine_zone,
    list_mine_zones,
)

# ============================================================
# HUMAN-READABLE LABELS
# ============================================================

STATUS_LABELS: dict[str, str] = {
    "VALID": "Attendance recorded — GPS validated inside mine boundary",
    "OUTSIDE_GEOFENCE": "Outside mine boundary — review required",
    "LOCATION_UNAVAILABLE": "Location permission denied or unavailable",
    "LOW_LOCATION_ACCURACY": "GPS accuracy too low for reliable validation",
    "DUPLICATE_CHECK_IN": "Duplicate check-in — already checked in recently",
    "FLAGGED_FOR_REVIEW": "Flagged for supervisor review",
}

ANOMALY_LABELS: dict[str, str] = {
    "NONE": "No anomaly detected",
    "DUPLICATE_CHECK_IN": "Duplicate check-in within 30 minutes",
    "OUTSIDE_GEOFENCE_ANOMALY": "Check-in registered outside mine geofence",
    "LOW_LOCATION_ACCURACY": "GPS-derived location accuracy is too low",
    "LOCATION_UNAVAILABLE": "GPS location was not provided",
    "OUTSIDE_ASSIGNED_MINE": "Check-in at a mine not matching current assignment",
    "FLAGGED_FOR_REVIEW": "Supervisor flagged for manual review",
}

ANOMALY_SEVERITY: dict[str, str] = {
    "NONE": "info",
    "DUPLICATE_CHECK_IN": "medium",
    "OUTSIDE_GEOFENCE_ANOMALY": "high",
    "LOW_LOCATION_ACCURACY": "medium",
    "LOCATION_UNAVAILABLE": "high",
    "OUTSIDE_ASSIGNED_MINE": "high",
    "FLAGGED_FOR_REVIEW": "high",
}


# ============================================================
# ATTENDANCE STATUS DERIVATION
# ============================================================

def derive_attendance_status(
    geofence_status: GeofenceStatus,
    anomaly: AnomalyStatus,
) -> AttendanceStatus:
    """
    Map geofence result + anomaly to a single human-readable attendance status.
    Status is immutable after creation — corrections create new records.
    """
    if anomaly == AnomalyStatus.DUPLICATE_CHECK_IN:
        return AttendanceStatus.DUPLICATE_CHECK_IN
    if geofence_status == GeofenceStatus.LOCATION_UNAVAILABLE:
        return AttendanceStatus.LOCATION_UNAVAILABLE
    if geofence_status == GeofenceStatus.LOW_ACCURACY:
        return AttendanceStatus.LOW_LOCATION_ACCURACY
    if geofence_status == GeofenceStatus.OUTSIDE_GEOFENCE:
        return AttendanceStatus.OUTSIDE_GEOFENCE
    if anomaly != AnomalyStatus.NONE:
        return AttendanceStatus.FLAGGED_FOR_REVIEW
    return AttendanceStatus.VALID


# ============================================================
# CHECK-IN
# ============================================================

def process_check_in(
    user_id: str,
    user_role: str,
    mine_id: str,
    zone_id: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    accuracy_meters: Optional[float],
    captured_at: Optional[str],
    schedule_instance_id: Optional[str],
    inspection_id: Optional[str],
    device_info: Optional[str],
    notes: Optional[str],
    assigned_mine_id: Optional[str] = None,
) -> dict:
    """
    Full server-side attendance check-in workflow.

    Returns a dict matching CheckInResponse schema.
    Always persists the record — even if geofence fails.
    """
    now = datetime.now(timezone.utc).isoformat()

    # 1. Resolve mine reference coordinates
    mine = get_mine_with_location(mine_id)
    if mine is None:
        raise ValueError(f"Mine '{mine_id}' not found.")

    # 2. Prefer zone coordinates if a zone is specified
    ref_lat: Optional[float] = None
    ref_lon: Optional[float] = None
    allowed_radius: float = float(mine.get("geofence_radius_meters") or 500.0)

    if zone_id:
        zone = get_mine_zone(zone_id)
        if zone and zone.get("mine_id") == mine_id:
            ref_lat = zone.get("latitude")
            ref_lon = zone.get("longitude")
            allowed_radius = float(zone.get("geofence_radius_meters", 500.0))
    else:
        ref_lat = mine.get("latitude")
        ref_lon = mine.get("longitude")

    # 3. Server-side Haversine geofence check (authoritative)
    geofence: GeofenceResult = check_geofence(
        user_lat=latitude,
        user_lon=longitude,
        ref_lat=ref_lat,
        ref_lon=ref_lon,
        allowed_radius_m=allowed_radius,
        accuracy_m=accuracy_meters,
    )

    # 4. Deterministic anomaly detection
    recent = list_recent_user_attendance(user_id, limit=5)
    anomaly = detect_attendance_anomaly(
        user_id=user_id,
        mine_id=mine_id,
        geofence_status=geofence.status,
        accuracy_m=accuracy_meters,
        recent_attendance=recent,
        assigned_mine_id=assigned_mine_id,
    )

    # 5. Derive final attendance status
    att_status = derive_attendance_status(geofence.status, anomaly)

    # 6. Persist record
    attendance_id = f"ATT-{uuid.uuid4().hex[:12].upper()}"
    record = {
        "attendance_id": attendance_id,
        "user_id": user_id,
        "user_role": user_role,
        "mine_id": mine_id,
        "zone_id": zone_id,
        "schedule_instance_id": schedule_instance_id,
        "inspection_id": inspection_id,
        "latitude": latitude,
        "longitude": longitude,
        "accuracy_meters": accuracy_meters,
        "captured_at": captured_at,
        "server_recorded_at": now,
        "geofence_status": geofence.status.value,
        "distance_from_reference_meters": geofence.distance_meters,
        "status": att_status.value,
        "anomaly_status": anomaly.value,
        "device_info": device_info,
        "notes": notes,
        "created_at": now,
    }
    stored = insert_attendance(record)

    # 7. Write to existing audit_log (reuse Task 1–5 infrastructure)
    _log_attendance_audit(
        attendance_id=attendance_id,
        action="ATTENDANCE_CREATED",
        actor_id=user_id,
        details=(
            f"GPS check-in by {user_role} at mine {mine_id}. "
            f"Geofence: {geofence.status.value}. "
            f"Status: {att_status.value}. "
            f"Anomaly: {anomaly.value}."
        ),
    )
    if geofence.status != GeofenceStatus.INSIDE_GEOFENCE:
        _log_attendance_audit(
            attendance_id=attendance_id,
            action="GEOFENCE_FAILED",
            actor_id=user_id,
            details=geofence.message,
        )
    if anomaly != AnomalyStatus.NONE:
        _log_attendance_audit(
            attendance_id=attendance_id,
            action="ATTENDANCE_FLAGGED",
            actor_id=user_id,
            details=f"Anomaly detected: {anomaly.value}",
        )

    return {
        "attendance_id": attendance_id,
        "user_id": user_id,
        "mine_id": mine_id,
        "status": att_status.value,
        "status_label": STATUS_LABELS.get(att_status.value, att_status.value),
        "anomaly_status": anomaly.value,
        "geofence": {
            "status": geofence.status.value,
            "distance_meters": geofence.distance_meters,
            "allowed_radius_meters": geofence.allowed_radius_meters,
            "location_accuracy_meters": geofence.location_accuracy_meters,
            "message": geofence.message,
        },
        "message": geofence.message,
        "linked_inspection_id": inspection_id,
        "linked_schedule_instance_id": schedule_instance_id,
        "integrity_mode": "DEMO_AUDIT_MODE",
    }


# ============================================================
# QUERY HELPERS
# ============================================================

def get_my_attendance(user_id: str) -> list[dict]:
    """Return attendance records visible to the requesting user (own only)."""
    records = list_attendance_for_user(user_id)
    return [_enrich_record(r) for r in records]


def get_mine_attendance(mine_id: str) -> list[dict]:
    """Return attendance records for a mine (manager/DGMS scope)."""
    records = list_attendance_for_mine(mine_id)
    return [_enrich_record(r) for r in records]


def get_team_attendance(mine_id: Optional[str] = None) -> dict:
    """
    Return team attendance summary for supervisor/manager.
    Includes counts and anomaly list.
    """
    if mine_id:
        records = list_attendance_for_mine(mine_id)
    else:
        # Without a mine filter, return last 200 records
        from app.database import _connect
        conn = _connect()
        rows = conn.execute(
            "SELECT * FROM attendance_records ORDER BY server_recorded_at DESC LIMIT 200"
        ).fetchall()
        conn.close()
        records = [dict(r) for r in rows]

    enriched = [_enrich_record(r) for r in records]
    valid_count = sum(1 for r in enriched if r["status"] == "VALID")
    flagged = [r for r in enriched if r["anomaly_status"] != "NONE"]
    outside_gf = sum(1 for r in enriched if r["geofence_status"] == "OUTSIDE_GEOFENCE")

    return {
        "total": len(enriched),
        "valid": valid_count,
        "flagged": len(flagged),
        "outside_geofence": outside_gf,
        "records": enriched,
        "anomalies": flagged,
    }


def get_anomalies(mine_id: Optional[str] = None) -> list[dict]:
    """Return anomaly signals for DGMS/supervisor intelligence."""
    records = list_attendance_anomalies(mine_id=mine_id)
    result = []
    for r in records:
        anomaly_val = r.get("anomaly_status", "NONE")
        result.append({
            "attendance_id": r["attendance_id"],
            "user_id": r["user_id"],
            "mine_id": r["mine_id"],
            "anomaly_type": anomaly_val,
            "anomaly_label": ANOMALY_LABELS.get(anomaly_val, anomaly_val),
            "severity": ANOMALY_SEVERITY.get(anomaly_val, "medium"),
            "description": (
                f"Attendance by {r['user_role']} at mine {r['mine_id']} "
                f"flagged: {ANOMALY_LABELS.get(anomaly_val, anomaly_val)}"
            ),
            "server_recorded_at": r.get("server_recorded_at", ""),
            "linked_inspection_id": r.get("inspection_id"),
        })
    return result


def get_aggregate() -> dict:
    """Return aggregate attendance statistics (corporate scope, no PII)."""
    return get_attendance_aggregate()


# ============================================================
# PRIVATE HELPERS
# ============================================================

def _enrich_record(r: dict) -> dict:
    """Add human-readable labels to a raw attendance DB record."""
    status_val = r.get("status", "VALID")
    anomaly_val = r.get("anomaly_status", "NONE")
    return {
        **r,
        "status_label": STATUS_LABELS.get(status_val, status_val),
        "anomaly_label": ANOMALY_LABELS.get(anomaly_val, anomaly_val),
    }


def _log_attendance_audit(
    attendance_id: str,
    action: str,
    actor_id: str,
    details: str,
) -> None:
    """Write an audit event to the existing audit_log table."""
    from app.database import _connect
    from datetime import datetime, timezone

    conn = _connect()
    conn.execute(
        """
        INSERT INTO audit_log (entity_type, entity_id, action, actor_id, timestamp, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "attendance",
            attendance_id,
            action,
            actor_id,
            datetime.now(timezone.utc).isoformat(),
            details,
        ),
    )
    conn.commit()
    conn.close()
