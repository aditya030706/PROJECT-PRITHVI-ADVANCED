/**
 * PRITHVI — Phase 2 Task 13: Environmental Governance & Monitoring API Client
 * =========================================================================
 * Provides typed access to environmental parameters, measurements, thresholds,
 * obligations, monitoring schedules, compliance violation cases, risk calculations,
 * and traceable regulatory reports.
 */

const API_BASE_URL = "http://127.0.0.1:8000";

export type EnvironmentalDomain =
  | "AIR"
  | "WATER"
  | "NOISE"
  | "VIBRATION"
  | "LAND"
  | "RECLAMATION"
  | "WASTE"
  | "OTHER";

export type EnvironmentalSourceType =
  | "FIELD_OBSERVATION"
  | "MANUAL_ENTRY"
  | "SENSOR"
  | "API"
  | "FILE_IMPORT"
  | "SIMULATED";

export type DataQualityStatus =
  | "VALID"
  | "DATA_QUALITY_ERROR"
  | "REQUIRES_REVIEW";

export interface EnvironmentalParameter {
  id: string;
  code: string;
  name: string;
  domain: EnvironmentalDomain;
  unit: string;
  description?: string | null;
  mine_type_applicability: string;
  active: boolean;
  metadata?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentalMeasurement {
  id: string;
  mine_id: string;
  operational_unit_id?: string | null;
  parameter_id: string;
  parameter_code?: string | null;
  parameter_name?: string | null;
  domain?: EnvironmentalDomain | null;
  value: number;
  unit: string;
  measured_at: string;
  source_type: EnvironmentalSourceType;
  source_reference?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  device_reference?: string | null;
  entered_by: string;
  status: string;
  evidence_id?: string | null;
  data_quality_status: DataQualityStatus;
  quality_notes?: string | null;
  simulated: boolean;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentalThreshold {
  id: string;
  parameter_id: string;
  parameter_name?: string | null;
  mine_type: string;
  threshold_type: string;
  lower_limit?: number | null;
  upper_limit?: number | null;
  unit: string;
  applicable_from?: string | null;
  applicable_to?: string | null;
  severity: string;
  source_reference: string;
  is_demo_rule: boolean;
  active: boolean;
  created_at?: string | null;
}

export interface EnvironmentalObligation {
  obligation_id: string;
  mine_id: string;
  code: string;
  title: string;
  description: string;
  domain: EnvironmentalDomain;
  applicable_mine_type: string;
  frequency: string;
  responsible_role: string;
  regulatory_source: string;
  evidence_requirements?: string | null;
  active: boolean;
  start_date: string;
  end_date?: string | null;
  created_at?: string | null;
}

export interface EnvironmentalSchedule {
  schedule_id: string;
  obligation_id: string;
  obligation_title?: string | null;
  mine_id: string;
  parameter_id?: string | null;
  parameter_name?: string | null;
  operational_unit_id?: string | null;
  domain: EnvironmentalDomain;
  due_date: string;
  responsible_role: string;
  status: string;
  completed_at?: string | null;
  measurement_id?: string | null;
  created_at?: string | null;
}

export interface EnvironmentalReport {
  report_id: string;
  mine_id: string;
  reporting_period_start: string;
  reporting_period_end: string;
  title: string;
  report_type: string;
  status: string;
  summary?: string | null;
  measurements_count: number;
  violations_count: number;
  open_cases_count: number;
  corrective_actions_count: number;
  lineage_snapshot?: string | null;
  source_record_hashes?: string | null;
  content_hash?: string | null;
  ipfs_cid?: string | null;
  generated_by: string;
  generated_at: string;
  finalized_at?: string | null;
  finalized_by?: string | null;
}

export interface DomainRiskDetail {
  score: number;
  level: string;
  breaches: number;
}

export interface EnvironmentalRisk {
  mine_id: string;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  active_breaches_count: number;
  recurring_violations_count: number;
  overdue_schedules_count: number;
  domain_risks: Record<string, DomainRiskDetail>;
  explanation: string;
}

export interface DomainBreakdown {
  domain: EnvironmentalDomain;
  parameter_count: number;
  measurement_count: number;
  violation_count: number;
}

export interface EnvironmentalOverview {
  mine_id?: string | null;
  total_parameters: number;
  total_measurements: number;
  total_violations: number;
  open_cases_count: number;
  overdue_schedules_count: number;
  risk_level: string;
  risk_score: number;
  domains_breakdown: DomainBreakdown[];
  recent_measurements: EnvironmentalMeasurement[];
  recent_violations: any[];
}

export interface EnvironmentalMeasurementCreate {
  mine_id: string;
  operational_unit_id?: string | null;
  parameter_id: string;
  value: number;
  unit: string;
  measured_at: string;
  source_type?: EnvironmentalSourceType;
  source_reference?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  device_reference?: string | null;
  status?: string;
  evidence_id?: string | null;
  simulated?: boolean;
}

export interface EnvironmentalThresholdCreate {
  parameter_id: string;
  mine_type?: string;
  threshold_type?: string;
  lower_limit?: number | null;
  upper_limit?: number | null;
  unit: string;
  applicable_from?: string | null;
  applicable_to?: string | null;
  severity?: string;
  source_reference?: string;
  is_demo_rule?: boolean;
}

export interface EnvironmentalReportGenerateRequest {
  mine_id: string;
  reporting_period_start: string;
  reporting_period_end: string;
  title: string;
  report_type?: string;
}

// -------------------------------------------------------------
// API Helper
// -------------------------------------------------------------

function getAuthHeaders(): HeadersInit {
  const role = localStorage.getItem("prithvi_role") || "DIRECTOR_TECHNICAL";
  const userId = localStorage.getItem("prithvi_user_id") || "DIR-TECH-01";
  const orgScope = localStorage.getItem("prithvi_org_scope") || "ORG-CIL-CIL";
  return {
    "X-User-Role": role,
    "X-User-Id": userId,
    "X-User-Org-Scope": orgScope,
  };
}

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(`API Error ${res.status}: ${errorDetail}`);
  }

  return res.json() as Promise<T>;
}

// -------------------------------------------------------------
// Service Methods
// -------------------------------------------------------------

export async function getEnvironmentOverview(mineId?: string): Promise<EnvironmentalOverview> {
  const query = mineId ? `?mine_id=${encodeURIComponent(mineId)}` : "";
  return fetchJson<EnvironmentalOverview>(`/api/environment/overview${query}`);
}

export async function getMineEnvironmentalProfile(mineId: string): Promise<any> {
  return fetchJson<any>(`/api/environment/mines/${encodeURIComponent(mineId)}`);
}

export async function listEnvironmentalDomains(): Promise<{ domains: EnvironmentalDomain[] }> {
  return fetchJson<{ domains: EnvironmentalDomain[] }>("/api/environment/domains");
}

export async function listEnvironmentalParameters(
  domain?: string,
  applicableMineType?: string
): Promise<EnvironmentalParameter[]> {
  const params = new URLSearchParams();
  if (domain && domain !== "ALL") params.append("domain", domain);
  if (applicableMineType && applicableMineType !== "ALL") params.append("applicable_mine_type", applicableMineType);
  const q = params.toString() ? `?${params.toString()}` : "";
  return fetchJson<EnvironmentalParameter[]>(`/api/environment/parameters${q}`);
}

export async function listEnvironmentalThresholds(
  parameterId?: string,
  mineType?: string
): Promise<EnvironmentalThreshold[]> {
  const params = new URLSearchParams();
  if (parameterId) params.append("parameter_id", parameterId);
  if (mineType && mineType !== "ALL") params.append("mine_type", mineType);
  const q = params.toString() ? `?${params.toString()}` : "";
  return fetchJson<EnvironmentalThreshold[]>(`/api/environment/thresholds${q}`);
}

export async function createEnvironmentalThreshold(
  data: EnvironmentalThresholdCreate
): Promise<EnvironmentalThreshold> {
  return fetchJson<EnvironmentalThreshold>("/api/environment/thresholds", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function listEnvironmentalMeasurements(params?: {
  mine_id?: string;
  domain?: string;
  parameter_id?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
}): Promise<EnvironmentalMeasurement[]> {
  const qp = new URLSearchParams();
  if (params?.mine_id) qp.append("mine_id", params.mine_id);
  if (params?.domain && params.domain !== "ALL") qp.append("domain", params.domain);
  if (params?.parameter_id) qp.append("parameter_id", params.parameter_id);
  if (params?.status) qp.append("status", params.status);
  if (params?.start_date) qp.append("start_date", params.start_date);
  if (params?.end_date) qp.append("end_date", params.end_date);
  if (params?.limit) qp.append("limit", params.limit.toString());
  const q = qp.toString() ? `?${qp.toString()}` : "";
  return fetchJson<EnvironmentalMeasurement[]>(`/api/environment/measurements${q}`);
}

export async function recordEnvironmentalMeasurement(
  data: EnvironmentalMeasurementCreate
): Promise<{ measurement: EnvironmentalMeasurement; threshold_breach: boolean; violation_details?: any }> {
  return fetchJson<{ measurement: EnvironmentalMeasurement; threshold_breach: boolean; violation_details?: any }>(
    "/api/environment/measurements",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }
  );
}

export async function listEnvironmentalObligations(
  mineId?: string,
  domain?: string
): Promise<EnvironmentalObligation[]> {
  const params = new URLSearchParams();
  if (mineId) params.append("mine_id", mineId);
  if (domain && domain !== "ALL") params.append("domain", domain);
  const q = params.toString() ? `?${params.toString()}` : "";
  return fetchJson<EnvironmentalObligation[]>(`/api/environment/obligations${q}`);
}

export async function listEnvironmentalSchedules(params?: {
  mine_id?: string;
  domain?: string;
  status?: string;
  date?: string;
}): Promise<EnvironmentalSchedule[]> {
  const qp = new URLSearchParams();
  if (params?.mine_id) qp.append("mine_id", params.mine_id);
  if (params?.domain && params.domain !== "ALL") qp.append("domain", params.domain);
  if (params?.status) qp.append("status", params.status);
  if (params?.date) qp.append("date", params.date);
  const q = qp.toString() ? `?${qp.toString()}` : "";
  return fetchJson<EnvironmentalSchedule[]>(`/api/environment/schedules${q}`);
}

export async function listEnvironmentalViolations(
  mineId?: string,
  domain?: string
): Promise<any[]> {
  const params = new URLSearchParams();
  if (mineId) params.append("mine_id", mineId);
  if (domain && domain !== "ALL") params.append("domain", domain);
  const q = params.toString() ? `?${params.toString()}` : "";
  return fetchJson<any[]>(`/api/environment/violations${q}`);
}

export async function getEnvironmentalRisk(mineId: string): Promise<EnvironmentalRisk> {
  return fetchJson<EnvironmentalRisk>(`/api/environment/risk?mine_id=${encodeURIComponent(mineId)}`);
}

export async function listEnvironmentalCases(
  mineId?: string,
  domain?: string,
  status?: string
): Promise<any[]> {
  const params = new URLSearchParams();
  if (mineId) params.append("mine_id", mineId);
  if (domain && domain !== "ALL") params.append("domain", domain);
  if (status) params.append("status", status);
  const q = params.toString() ? `?${params.toString()}` : "";
  return fetchJson<any[]>(`/api/environment/cases${q}`);
}

export async function listEnvironmentalReports(
  mineId?: string,
  limit?: number
): Promise<EnvironmentalReport[]> {
  const params = new URLSearchParams();
  if (mineId) params.append("mine_id", mineId);
  if (limit) params.append("limit", limit.toString());
  const q = params.toString() ? `?${params.toString()}` : "";
  return fetchJson<EnvironmentalReport[]>(`/api/environment/reports${q}`);
}

export async function generateEnvironmentalReport(
  data: EnvironmentalReportGenerateRequest
): Promise<EnvironmentalReport> {
  return fetchJson<EnvironmentalReport>("/api/environment/reports/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function finalizeEnvironmentalReport(reportId: string): Promise<EnvironmentalReport> {
  return fetchJson<EnvironmentalReport>(
    `/api/environment/reports/${encodeURIComponent(reportId)}/finalize`,
    {
      method: "POST",
    }
  );
}

export async function getEnvironmentalReport(reportId: string): Promise<EnvironmentalReport> {
  return fetchJson<EnvironmentalReport>(`/api/environment/reports/${encodeURIComponent(reportId)}`);
}
