"""
PRITHVI — Geofence Engine (Phase 2 Task 8)

Server-side authoritative geofence validation using Haversine distance.
The server ALWAYS performs the geofence check — never trusts frontend boolean.

Functions:
    haversine_distance_m    -- geodesic distance in metres
    check_geofence          -- authoritative geofence validation
    detect_attendance_anomaly -- deterministic anomaly detection
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.models import GeofenceStatus, AnomalyStatus

# ============================================================
# CONSTANTS
# ============================================================

# GPS accuracy threshold below which attendance is flagged.
# Browser/device GPS accuracy (metres). Above this = LOW_ACCURACY.
LOW_ACCURACY_THRESHOLD_M = 100.0

# Minimum time between two check-ins for the same user (minutes).
DUPLICATE_CHECKIN_WINDOW_MINUTES = 30


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate geodesic distance between two GPS coordinates in metres.

    Uses the Haversine formula — correct for short distances on Earth's surface.
    Earth radius: 6,371,000 m (mean radius).

    Args:
        lat1, lon1: Reference point (mine/zone centre) in decimal degrees.
        lat2, lon2: User GPS location in decimal degrees.

    Returns:
        Distance in metres (float).
    """
    R = 6_371_000.0  # Earth mean radius in metres

    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)

    a = (
        math.sin(Δφ / 2) ** 2
        + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ============================================================
# GEOFENCE RESULT
# ============================================================

@dataclass
class GeofenceResult:
    """Authoritative result of a server-side geofence check."""
    status: GeofenceStatus
    distance_meters: Optional[float]
    allowed_radius_meters: Optional[float]
    location_accuracy_meters: Optional[float]
    reference_lat: Optional[float]
    reference_lon: Optional[float]
    message: str


def check_geofence(
    user_lat: Optional[float],
    user_lon: Optional[float],
    ref_lat: Optional[float],
    ref_lon: Optional[float],
    allowed_radius_m: float,
    accuracy_m: Optional[float] = None,
) -> GeofenceResult:
    """
    Server-side authoritative geofence validation.

    The backend ALWAYS calculates this result.
    Frontend boolean 'inside_geofence' is never accepted as proof.

    Args:
        user_lat/lon:       GPS-derived location submitted by client.
        ref_lat/lon:        Mine/zone reference coordinates from database.
        allowed_radius_m:   Permitted radius in metres.
        accuracy_m:         Reported GPS accuracy (metres). None = unknown.

    Returns:
        GeofenceResult with status, distance, and human-readable message.
    """
    # --- Location unavailable ---
    if user_lat is None or user_lon is None:
        return GeofenceResult(
            status=GeofenceStatus.LOCATION_UNAVAILABLE,
            distance_meters=None,
            allowed_radius_meters=allowed_radius_m,
            location_accuracy_meters=accuracy_m,
            reference_lat=ref_lat,
            reference_lon=ref_lon,
            message="GPS location was not provided. Location permission may have been denied.",
        )

    # --- Mine/zone has no reference coordinates ---
    if ref_lat is None or ref_lon is None:
        return GeofenceResult(
            status=GeofenceStatus.LOCATION_UNAVAILABLE,
            distance_meters=None,
            allowed_radius_meters=allowed_radius_m,
            location_accuracy_meters=accuracy_m,
            reference_lat=None,
            reference_lon=None,
            message=(
                "Mine/zone reference coordinates are not configured. "
                "Contact the system administrator."
            ),
        )

    # --- Low GPS accuracy ---
    if accuracy_m is not None and accuracy_m > LOW_ACCURACY_THRESHOLD_M:
        distance = haversine_distance_m(ref_lat, ref_lon, user_lat, user_lon)
        return GeofenceResult(
            status=GeofenceStatus.LOW_ACCURACY,
            distance_meters=round(distance, 1),
            allowed_radius_meters=allowed_radius_m,
            location_accuracy_meters=accuracy_m,
            reference_lat=ref_lat,
            reference_lon=ref_lon,
            message=(
                f"GPS accuracy is ±{accuracy_m:.0f} m — too low for reliable attendance validation. "
                f"Move to an open area to improve signal."
            ),
        )

    # --- Calculate Haversine distance ---
    distance = haversine_distance_m(ref_lat, ref_lon, user_lat, user_lon)

    if distance <= allowed_radius_m:
        return GeofenceResult(
            status=GeofenceStatus.INSIDE_GEOFENCE,
            distance_meters=round(distance, 1),
            allowed_radius_meters=allowed_radius_m,
            location_accuracy_meters=accuracy_m,
            reference_lat=ref_lat,
            reference_lon=ref_lon,
            message=(
                f"Inside mine boundary. "
                f"{distance:.0f} m from site reference (radius: {allowed_radius_m:.0f} m)."
            ),
        )
    else:
        return GeofenceResult(
            status=GeofenceStatus.OUTSIDE_GEOFENCE,
            distance_meters=round(distance, 1),
            allowed_radius_meters=allowed_radius_m,
            location_accuracy_meters=accuracy_m,
            reference_lat=ref_lat,
            reference_lon=ref_lon,
            message=(
                f"Outside mine boundary. "
                f"{distance:.0f} m from site reference (allowed: {allowed_radius_m:.0f} m). "
                f"Attendance flagged for supervisor review."
            ),
        )


# ============================================================
# ANOMALY DETECTION
# ============================================================

def detect_attendance_anomaly(
    user_id: str,
    mine_id: str,
    geofence_status: GeofenceStatus,
    accuracy_m: Optional[float],
    recent_attendance: list[dict],
    assigned_mine_id: Optional[str],
) -> AnomalyStatus:
    """
    Deterministic server-side anomaly detection.

    Rules (in priority order):
    1. LOCATION_UNAVAILABLE  → LOCATION_UNAVAILABLE
    2. LOW_ACCURACY          → LOW_LOCATION_ACCURACY
    3. OUTSIDE_GEOFENCE      → OUTSIDE_GEOFENCE_ANOMALY
    4. Attendance for a mine not matching user's assignment → OUTSIDE_ASSIGNED_MINE
    5. Check-in within DUPLICATE_CHECKIN_WINDOW_MINUTES of last check-in → DUPLICATE_CHECK_IN
    6. Otherwise             → NONE

    Args:
        user_id:           User submitting attendance.
        mine_id:           Mine being checked in to.
        geofence_status:   Result of check_geofence().
        accuracy_m:        GPS accuracy (metres).
        recent_attendance: List of last N attendance records for this user
                           (each dict with 'server_recorded_at', 'mine_id', 'status').
        assigned_mine_id:  Mine the user is currently assigned to (from schedule).

    Returns:
        AnomalyStatus enum value.
    """
    if geofence_status == GeofenceStatus.LOCATION_UNAVAILABLE:
        return AnomalyStatus.LOCATION_UNAVAILABLE

    if geofence_status == GeofenceStatus.LOW_ACCURACY:
        return AnomalyStatus.LOW_LOCATION_ACCURACY

    if geofence_status == GeofenceStatus.OUTSIDE_GEOFENCE:
        return AnomalyStatus.OUTSIDE_GEOFENCE_ANOMALY

    # Assigned mine mismatch
    if assigned_mine_id and assigned_mine_id != mine_id:
        return AnomalyStatus.OUTSIDE_ASSIGNED_MINE

    # Duplicate check-in
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=DUPLICATE_CHECKIN_WINDOW_MINUTES)
    for record in recent_attendance:
        try:
            recorded = datetime.fromisoformat(
                record.get("server_recorded_at", "").replace("Z", "+00:00")
            )
            if recorded.tzinfo is None:
                recorded = recorded.replace(tzinfo=timezone.utc)
            if recorded >= cutoff:
                return AnomalyStatus.DUPLICATE_CHECK_IN
        except (ValueError, AttributeError):
            continue

    return AnomalyStatus.NONE
