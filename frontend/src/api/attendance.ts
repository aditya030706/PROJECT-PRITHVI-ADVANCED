/**
 * PRITHVI — GIS Attendance API Client (Phase 2 Task 8)
 *
 * Provides typed access to the GIS attendance & geofencing endpoints:
 *  POST /api/attendance/check-in
 *  GET  /api/attendance/me
 *  GET  /api/attendance/team
 *  GET  /api/attendance/mine/{mine_id}
 *  GET  /api/attendance/{attendance_id}
 *  GET  /api/attendance/anomalies
 *  GET  /api/attendance/aggregate
 *  GET  /api/mine-zones/{mine_id}
 *  POST /api/mine-zones
 *  POST /api/mines/{mine_id}/location
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// ============================================================
// TYPES
// ============================================================

export type GeofenceStatus =
  | "INSIDE_GEOFENCE"
  | "OUTSIDE_GEOFENCE"
  | "LOCATION_UNAVAILABLE"
  | "LOW_ACCURACY";

export type AttendanceStatus =
  | "VALID"
  | "OUTSIDE_GEOFENCE"
  | "LOW_LOCATION_ACCURACY"
  | "LOCATION_UNAVAILABLE"
  | "DUPLICATE_CHECK_IN"
  | "FLAGGED_FOR_REVIEW";

export type AnomalyStatus =
  | "NONE"
  | "DUPLICATE_CHECK_IN"
  | "OUTSIDE_GEOFENCE_ANOMALY"
  | "LOW_LOCATION_ACCURACY"
  | "LOCATION_UNAVAILABLE"
  | "OUTSIDE_ASSIGNED_MINE"
  | "FLAGGED_FOR_REVIEW";

export interface GeofenceResult {
  status: GeofenceStatus;
  status_label: string;
  distance_meters: number | null;
  allowed_radius_meters: number;
  accuracy_meters: number | null;
  reference_lat: number | null;
  reference_lon: number | null;
  user_lat: number | null;
  user_lon: number | null;
  zone_name: string | null;
}

export interface CheckInRequest {
  mine_id: string;
  zone_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  accuracy_meters?: number | null;
  captured_at?: string | null;
  schedule_instance_id?: string | null;
  inspection_id?: string | null;
  device_info?: string | null;
  notes?: string | null;
}

export interface CheckInResponse {
  attendance_id: string;
  status: AttendanceStatus;
  status_label: string;
  geofence: GeofenceResult;
  anomaly_detected: boolean;
  anomaly_status: AnomalyStatus;
  anomaly_label: string;
  anomaly_severity: "info" | "medium" | "high";
  server_recorded_at: string;
  evidence_id: string | null;
  message: string;
}

export interface AttendanceRecord {
  attendance_id: string;
  user_id: string;
  user_role: string;
  mine_id: string;
  zone_id: string | null;
  schedule_instance_id: string | null;
  inspection_id: string | null;
  latitude: number | null;
  longitude: number | null;
  accuracy_meters: number | null;
  captured_at: string | null;
  server_recorded_at: string;
  geofence_status: GeofenceStatus;
  distance_from_reference_meters: number | null;
  status: AttendanceStatus;
  anomaly_status: AnomalyStatus;
  evidence_id: string | null;
  device_info: string | null;
  notes: string | null;
  created_at: string;
  status_label?: string;
  anomaly_label?: string;
}

export interface TeamAttendanceSummary {
  mine_id: string | null;
  generated_at: string;
  total_records_today: number;
  valid_count: number;
  outside_geofence_count: number;
  flagged_count: number;
  compliance_rate_pct: number;
  records: AttendanceRecord[];
}

export interface AnomalySignal {
  attendance_id: string;
  user_id: string;
  mine_id: string;
  timestamp: string;
  anomaly_status: AnomalyStatus;
  anomaly_label: string;
  severity: "info" | "medium" | "high";
  detail: string;
  distance_meters: number | null;
  accuracy_meters: number | null;
}

export interface AggregateAttendanceStats {
  generated_at: string;
  total_records: number;
  valid_count: number;
  outside_geofence_count: number;
  location_unavailable_count: number;
  duplicate_count: number;
  flagged_count: number;
  compliance_rate_pct: number;
  by_mine: Record<string, number>;
}

export interface MineZone {
  mine_zone_id: string;
  mine_id: string;
  name: string;
  latitude: number;
  longitude: number;
  geofence_radius_meters: number;
  description: string | null;
  active: boolean;
  created_at: string;
}

export interface MineZonesResponse {
  mine_id: string;
  mine_latitude: number | null;
  mine_longitude: number | null;
  mine_geofence_radius_meters: number;
  zones: MineZone[];
}

// ============================================================
// API FUNCTIONS
// ============================================================

function authHeaders(userId?: string, userRole?: string): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (userId) headers["X-User-Id"] = userId;
  if (userRole) headers["X-User-Role"] = userRole;
  return headers;
}

export async function submitCheckIn(
  payload: CheckInRequest,
  userId?: string,
  userRole?: string
): Promise<CheckInResponse> {
  const res = await fetch(`${API_BASE_URL}/api/attendance/check-in`, {
    method: "POST",
    headers: authHeaders(userId, userRole),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Check-in failed: ${res.status}`);
  }
  return res.json();
}

export async function getMyAttendance(
  userId?: string,
  userRole?: string
): Promise<AttendanceRecord[]> {
  const res = await fetch(`${API_BASE_URL}/api/attendance/me`, {
    headers: authHeaders(userId, userRole),
  });
  if (!res.ok) {
    throw new Error(`Failed to load attendance history: ${res.status}`);
  }
  return res.json();
}

export async function getTeamAttendance(
  mineId?: string,
  userId?: string,
  userRole?: string
): Promise<TeamAttendanceSummary> {
  const url = new URL(`${API_BASE_URL}/api/attendance/team`);
  if (mineId) url.searchParams.set("mine_id", mineId);
  const res = await fetch(url.toString(), {
    headers: authHeaders(userId, userRole),
  });
  if (!res.ok) {
    throw new Error(`Failed to load team attendance: ${res.status}`);
  }
  return res.json();
}

export async function getAttendanceAnomalies(
  mineId?: string,
  userRole?: string
): Promise<AnomalySignal[]> {
  const url = new URL(`${API_BASE_URL}/api/attendance/anomalies`);
  if (mineId) url.searchParams.set("mine_id", mineId);
  const res = await fetch(url.toString(), {
    headers: authHeaders(undefined, userRole),
  });
  if (!res.ok) {
    throw new Error(`Failed to load anomalies: ${res.status}`);
  }
  return res.json();
}

export async function getAttendanceAggregate(
  userRole?: string
): Promise<AggregateAttendanceStats> {
  const res = await fetch(`${API_BASE_URL}/api/attendance/aggregate`, {
    headers: authHeaders(undefined, userRole),
  });
  if (!res.ok) {
    throw new Error(`Failed to load aggregate stats: ${res.status}`);
  }
  return res.json();
}

export async function getAttendanceById(
  attendanceId: string,
  userId?: string,
  userRole?: string
): Promise<AttendanceRecord> {
  const res = await fetch(`${API_BASE_URL}/api/attendance/${attendanceId}`, {
    headers: authHeaders(userId, userRole),
  });
  if (!res.ok) {
    throw new Error(`Failed to load attendance record: ${res.status}`);
  }
  return res.json();
}

export async function getMineZones(mineId: string): Promise<MineZonesResponse> {
  const res = await fetch(`${API_BASE_URL}/api/mine-zones/${mineId}`);
  if (!res.ok) {
    throw new Error(`Failed to load mine zones: ${res.status}`);
  }
  return res.json();
}

export async function createMineZone(
  payload: {
    mine_id: string;
    name: string;
    latitude: number;
    longitude: number;
    geofence_radius_meters?: number;
    description?: string;
  },
  userRole?: string
): Promise<MineZone> {
  const res = await fetch(`${API_BASE_URL}/api/mine-zones`, {
    method: "POST",
    headers: authHeaders(undefined, userRole),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to create mine zone: ${res.status}`);
  }
  return res.json();
}
