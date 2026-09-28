/**
 * PRITHVI — Phase 2 Task 10: Production & Operational Governance API Client
 * =========================================================================
 * Provides typed access to mine, area, subsidiary, corporate aggregation,
 * shift-level reporting, anomaly detection, record correction, and statutory report generation.
 */

const API_BASE_URL = "http://127.0.0.1:8000";

export interface ShiftProductionItem {
  shift_name: string;
  production_tonnes: number;
  dispatch_tonnes: number;
  downtime_minutes: number;
  sources: string[];
  delays: string[];
}

export interface ContractorProductionItem {
  contractor_id?: string;
  contractor_name: string;
  contract_type: string;
  production_tonnes: number;
  percentage_share: number;
}

export interface ProductionAnomaly {
  anomaly_id: string;
  mine_id: string;
  mine_name?: string;
  anomaly_type: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  what: string;
  why: string;
  source: string;
  time: string;
  affected_record_ids: string[];
  recommended_review: string;
  resolved: boolean;
}

export interface MineProductionSummary {
  mine_id: string;
  mine_name: string;
  subsidiary: string;
  area_name?: string;
  mine_type: string;
  date: string;
  production_actual_tonnes: number;
  production_target_tonnes?: number;
  target_status: "CONFIGURED" | "TARGET_NOT_CONFIGURED";
  variance_tonnes?: number;
  achievement_percentage?: number;
  dispatch_actual_tonnes: number;
  dispatch_variance_tonnes?: number;
  overburden_actual_bcm?: number;
  total_downtime_minutes: number;
  shifts: ShiftProductionItem[];
  contractor_contributions: ContractorProductionItem[];
  hemm_context_summary?: string;
  delay_reasons: string[];
  sources_used: string[];
  anomalies: ProductionAnomaly[];
  active_safety_stoppage: boolean;
  safety_stoppage_notes?: string;
  compliance_status: "COMPLIANT" | "REVIEW_REQUIRED" | "ACTION_REQUIRED";
  simulated: boolean;
}

export interface AreaMineItem {
  mine_id: string;
  mine_name: string;
  mine_type: string;
  production_tonnes: number;
  target_tonnes?: number;
  achievement_percentage?: number;
  active_anomalies_count: number;
  active_safety_stoppage: boolean;
  compliance_status: string;
}

export interface AreaProductionSummary {
  area_id: string;
  area_name: string;
  subsidiary: string;
  date: string;
  total_production_tonnes: number;
  total_target_tonnes?: number;
  overall_achievement_percentage?: number;
  total_dispatch_tonnes: number;
  mines_reporting: number;
  total_mines: number;
  unresolved_anomalies_count: number;
  mines: AreaMineItem[];
}

export interface SubsidiaryAreaItem {
  area_id: string;
  area_name: string;
  total_production_tonnes: number;
  total_target_tonnes?: number;
  achievement_percentage?: number;
  mines_reporting: number;
  total_mines: number;
  unresolved_anomalies_count: number;
  critical_safety_signals: number;
}

export interface SubsidiaryProductionSummary {
  subsidiary_id: string;
  subsidiary_name: string;
  date: string;
  total_production_tonnes: number;
  total_target_tonnes?: number;
  overall_achievement_percentage?: number;
  total_dispatch_tonnes: number;
  areas_count: number;
  total_mines_count: number;
  mines_reporting_count: number;
  total_anomalies_count: number;
  critical_safety_signals_count: number;
  areas: SubsidiaryAreaItem[];
}

export interface CorporateSubsidiaryItem {
  subsidiary_id: string;
  subsidiary_name: string;
  production_tonnes: number;
  target_tonnes?: number;
  achievement_percentage?: number;
  mines_reporting: number;
  total_mines: number;
  critical_signals_count: number;
  anomalies_count: number;
}

export interface CorporateProductionSummary {
  organization: string;
  date: string;
  pan_india_production_tonnes: number;
  pan_india_target_tonnes?: number;
  pan_india_achievement_percentage?: number;
  pan_india_dispatch_tonnes: number;
  total_subsidiaries: number;
  total_mines_operating: number;
  total_mines_reporting: number;
  critical_operational_signals_count: number;
  total_anomalies_count: number;
  subsidiaries: CorporateSubsidiaryItem[];
}

export interface DailyProductionReport {
  report_title: string;
  mine_id: string;
  mine_name: string;
  subsidiary: string;
  area_name?: string;
  date: string;
  generated_at: string;
  records_included_count: number;
  source_types: string[];
  shifts_reported: ShiftProductionItem[];
  production_actual_tonnes: number;
  production_target_tonnes?: number;
  variance_tonnes?: number;
  achievement_percentage?: number;
  dispatch_actual_tonnes: number;
  dispatch_variance_tonnes?: number;
  total_downtime_minutes: number;
  delay_reasons: string[];
  anomalies_count: number;
  anomalies: ProductionAnomaly[];
  compliance_status: string;
  integrity_verification_hash: string;
  integrity_mode: string;
}

export interface ProductionRecordCreatePayload {
  mine_id: string;
  shift_name: string;
  production_date: string;
  production_quantity: number;
  production_unit?: string;
  dispatch_quantity?: number;
  production_source: string;
  operation_type?: string;
  zone_id?: string;
  district_section?: string;
  face_panel?: string;
  overburden_quantity?: number;
  overburden_unit?: string;
  contractor_id?: string;
  contractor_name?: string;
  contract_type?: string;
  target_quantity?: number;
  downtime_minutes?: number;
  delay_reason?: string;
  hemm_context?: string;
  entered_by?: string;
  source_reference?: string;
  notes?: string;
  simulated?: boolean;
}

export interface ProductionCorrectionPayload {
  corrected_quantity: number;
  corrected_dispatch?: number;
  reason: string;
  corrected_by?: string;
  notes?: string;
}

export async function getMineProductionSummary(mineId: string, date?: string): Promise<MineProductionSummary> {
  const url = `${API_BASE_URL}/api/production/mine/${mineId}/summary${date ? `?date=${date}` : ""}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load mine summary: ${resp.statusText}`);
  return resp.json();
}

export async function getAreaProductionSummary(areaId: string, date?: string): Promise<AreaProductionSummary> {
  const url = `${API_BASE_URL}/api/production/area/${areaId}/summary${date ? `?date=${date}` : ""}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load area summary: ${resp.statusText}`);
  return resp.json();
}

export async function getSubsidiaryProductionSummary(subsidiaryId: string, date?: string): Promise<SubsidiaryProductionSummary> {
  const url = `${API_BASE_URL}/api/production/subsidiary/${subsidiaryId}/summary${date ? `?date=${date}` : ""}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load subsidiary summary: ${resp.statusText}`);
  return resp.json();
}

export async function getCorporateProductionSummary(date?: string): Promise<CorporateProductionSummary> {
  const url = `${API_BASE_URL}/api/production/corporate/summary${date ? `?date=${date}` : ""}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load corporate summary: ${resp.statusText}`);
  return resp.json();
}

export async function getDailyProductionReport(mineId: string, date?: string): Promise<DailyProductionReport> {
  const url = `${API_BASE_URL}/api/production/report/daily?mine_id=${mineId}${date ? `&date=${date}` : ""}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to generate daily report: ${resp.statusText}`);
  return resp.json();
}

export async function createProductionRecord(payload: ProductionRecordCreatePayload, userRole?: string): Promise<any> {
  const resp = await fetch(`${API_BASE_URL}/api/production/records`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(userRole ? { "X-User-Role": userRole } : {}),
    },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `Failed to create production record: ${resp.statusText}`);
  }
  return resp.json();
}

export async function correctProductionRecord(
  recordId: string,
  payload: ProductionCorrectionPayload,
  userRole?: string
): Promise<any> {
  const resp = await fetch(`${API_BASE_URL}/api/production/records/${recordId}/correct`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(userRole ? { "X-User-Role": userRole } : {}),
    },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `Failed to submit record correction: ${resp.statusText}`);
  }
  return resp.json();
}

export async function getProductionAnomalies(mineId: string): Promise<ProductionAnomaly[]> {
  const resp = await fetch(`${API_BASE_URL}/api/production/anomalies/${mineId}`);
  if (!resp.ok) throw new Error(`Failed to load anomalies: ${resp.statusText}`);
  return resp.json();
}
