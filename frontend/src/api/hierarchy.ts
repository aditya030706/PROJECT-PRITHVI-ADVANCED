/**
 * PRITHVI Canonical Governance Master Hierarchy API Client (Phase 2 Task 11)
 */

import { apiGet, apiPost } from "./client";

const API_BASE_URL = "http://127.0.0.1:8000";

export type OrganizationUnitType = "MINISTRY" | "CIL" | "SUBSIDIARY" | "AREA" | "MINE";

export type OperationalUnitType =
  | "PIT"
  | "BENCH"
  | "HAUL_ROAD"
  | "DUMP_STOCK"
  | "HEMM_PARK"
  | "SHAFT_INCLINE"
  | "VENTILATION_DISTRICT"
  | "PANEL"
  | "SECTION"
  | "WORKING_FACE";

export type ContractorType = "DEPARTMENTAL" | "WORK_ORDER" | "MDO" | "SERVICE";
export type WorkerType = "DEPARTMENTAL" | "CONTRACTOR" | "MDO" | "OTHER";

export interface MineProfile {
  mine_id: string;
  mine_type: string;
  gassy_degree: string;
  mechanised: boolean;
  uses_hemm: boolean;
  has_winding_installation: boolean;
  blasting_operation: boolean;
}

export interface HierarchyTreeNode {
  id: string;
  parent_id?: string | null;
  unit_type: OrganizationUnitType;
  code: string;
  name: string;
  legal_name?: string | null;
  status: string;
  state?: string | null;
  district?: string | null;
  headquarters?: string | null;
  mine_profile?: MineProfile | null;
  children: HierarchyTreeNode[];
}

export interface OrganizationUnit {
  id: string;
  parent_id?: string | null;
  unit_type: OrganizationUnitType;
  code: string;
  name: string;
  legal_name?: string | null;
  status: string;
  state?: string | null;
  district?: string | null;
  headquarters?: string | null;
  effective_from: string;
  effective_to?: string | null;
  metadata?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OperationalUnit {
  id: string;
  mine_id: string;
  parent_operational_unit_id?: string | null;
  unit_type: OperationalUnitType;
  code: string;
  name: string;
  active: boolean;
  latitude?: number | null;
  longitude?: number | null;
  geofence_radius?: number | null;
  metadata?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContractorMaster {
  id: string;
  legal_name: string;
  display_name: string;
  registration_reference?: string | null;
  status: string;
  contractor_type: ContractorType;
  created_at: string;
  updated_at: string;
}

export interface ContractMaster {
  id: string;
  contractor_id: string;
  contractor_name?: string | null;
  mine_id: string;
  mine_name?: string | null;
  area_id?: string | null;
  subsidiary_id?: string | null;
  contract_type: ContractorType;
  contract_number: string;
  scope?: string | null;
  start_date: string;
  end_date?: string | null;
  workforce_limit?: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface WorkerMaster {
  id: string;
  worker_code: string;
  name: string;
  worker_type: WorkerType;
  contractor_id?: string | null;
  contractor_name?: string | null;
  contract_id?: string | null;
  contract_number?: string | null;
  mine_id: string;
  mine_name?: string | null;
  skill_category?: string | null;
  department?: string | null;
  active: boolean;
  onboarding_date: string;
  training_status: string;
  identity_reference?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkerLineage {
  worker_id: string;
  worker_code: string;
  worker_name: string;
  worker_type: string;
  contract?: any;
  contractor?: any;
  mine: any;
  area: any;
  subsidiary: any;
  holding_company: any;
  ministry: any;
}

export interface HierarchyPath {
  target_unit_id: string;
  target_name: string;
  target_type: string;
  path: OrganizationUnit[];
}

export interface OrganizationAuditEvent {
  event_id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id: string;
  previous_state?: string | null;
  new_state?: string | null;
  reason?: string | null;
  timestamp: string;
}

export async function fetchHierarchyTree(rootId?: string, depth = 5): Promise<HierarchyTreeNode[]> {
  const query = new URLSearchParams();
  if (rootId) query.append("root_id", rootId);
  query.append("depth", depth.toString());
  return apiGet<HierarchyTreeNode[]>(`/api/hierarchy/tree?${query.toString()}`);
}

export async function fetchOrganizationUnits(params?: {
  unit_type?: string;
  parent_id?: string;
  status?: string;
}): Promise<OrganizationUnit[]> {
  const query = new URLSearchParams();
  if (params?.unit_type) query.append("unit_type", params.unit_type);
  if (params?.parent_id) query.append("parent_id", params.parent_id);
  if (params?.status) query.append("status", params.status);
  return apiGet<OrganizationUnit[]>(`/api/hierarchy?${query.toString()}`);
}

export async function fetchSubsidiaries(): Promise<OrganizationUnit[]> {
  return apiGet<OrganizationUnit[]>("/api/hierarchy/subsidiaries");
}

export async function fetchSubsidiaryDetail(id: string): Promise<{ subsidiary: OrganizationUnit; areas: OrganizationUnit[] }> {
  return apiGet<{ subsidiary: OrganizationUnit; areas: OrganizationUnit[] }>(`/api/hierarchy/subsidiaries/${encodeURIComponent(id)}`);
}

export async function fetchAreaDetail(id: string): Promise<{ area: OrganizationUnit; mines: OrganizationUnit[] }> {
  return apiGet<{ area: OrganizationUnit; mines: OrganizationUnit[] }>(`/api/hierarchy/areas/${encodeURIComponent(id)}`);
}

export async function fetchMineHierarchy(id: string): Promise<{
  mine: any;
  area: any;
  subsidiary: any;
  holding_company: any;
  ministry: any;
}> {
  return apiGet<{
    mine: any;
    area: any;
    subsidiary: any;
    holding_company: any;
    ministry: any;
  }>(`/api/hierarchy/mines/${encodeURIComponent(id)}`);
}

export async function fetchMineZones(mineId: string): Promise<OperationalUnit[]> {
  return apiGet<OperationalUnit[]>(`/api/hierarchy/mines/${encodeURIComponent(mineId)}/zones`);
}

export async function fetchMineContracts(mineId: string): Promise<ContractMaster[]> {
  return apiGet<ContractMaster[]>(`/api/hierarchy/mines/${encodeURIComponent(mineId)}/contracts`);
}

export async function fetchMineWorkforce(mineId: string, activeOnly = false): Promise<WorkerMaster[]> {
  return apiGet<WorkerMaster[]>(`/api/hierarchy/mines/${encodeURIComponent(mineId)}/workforce?active_only=${activeOnly}`);
}

export async function fetchHierarchyPath(unitId: string): Promise<HierarchyPath> {
  return apiGet<HierarchyPath>(`/api/hierarchy/path/${encodeURIComponent(unitId)}`);
}

export interface SearchResultItem {
  id: string;
  name: string;
  code: string;
  type: string;
  unit_type: string;
  mine_type?: string | null;
  status: string;
  state?: string | null;
  district?: string | null;
  hierarchy_path: string[];
  link: string;
}

export async function searchHierarchy(query: string, limit = 20): Promise<SearchResultItem[]> {
  if (!query || !query.trim()) return [];
  const q = new URLSearchParams({ q: query.trim(), limit: limit.toString() });
  return apiGet<SearchResultItem[]>(`/api/hierarchy/search?${q.toString()}`);
}

export async function createOrganizationUnit(data: any): Promise<OrganizationUnit> {

  return apiPost<OrganizationUnit>("/api/hierarchy/units", data);
}

export async function updateOrganizationUnit(id: string, data: any): Promise<OrganizationUnit> {
  const response = await fetch(`${API_BASE_URL}/api/hierarchy/units/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", "X-User-Role": "ADMIN" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || "Failed to update unit");
  }
  return response.json();
}

export async function createOperationalUnit(data: any): Promise<OperationalUnit> {
  return apiPost<OperationalUnit>("/api/hierarchy/operational-units", data);
}

export async function fetchWorkerLineage(workerId: string): Promise<WorkerLineage> {
  return apiGet<WorkerLineage>(`/api/hierarchy/workers/${encodeURIComponent(workerId)}/lineage`);
}

export async function fetchWorkers(params?: {
  mine_id?: string;
  contract_id?: string;
  active_only?: boolean;
}): Promise<WorkerMaster[]> {
  const query = new URLSearchParams();
  if (params?.mine_id) query.append("mine_id", params.mine_id);
  if (params?.contract_id) query.append("contract_id", params.contract_id);
  if (params?.active_only) query.append("active_only", "true");
  return apiGet<WorkerMaster[]>(`/api/hierarchy/workers?${query.toString()}`);
}

export async function createWorker(data: any): Promise<WorkerMaster> {
  return apiPost<WorkerMaster>("/api/hierarchy/workers", data);
}

export async function fetchContractors(params?: {
  contractor_type?: string;
  status?: string;
}): Promise<ContractorMaster[]> {
  const query = new URLSearchParams();
  if (params?.contractor_type) query.append("contractor_type", params.contractor_type);
  if (params?.status) query.append("status", params.status);
  return apiGet<ContractorMaster[]>(`/api/hierarchy/contractors?${query.toString()}`);
}

export async function createContractor(data: any): Promise<ContractorMaster> {
  return apiPost<ContractorMaster>("/api/hierarchy/contractors", data);
}

export async function fetchContracts(params?: {
  mine_id?: string;
  contractor_id?: string;
  status?: string;
}): Promise<ContractMaster[]> {
  const query = new URLSearchParams();
  if (params?.mine_id) query.append("mine_id", params.mine_id);
  if (params?.contractor_id) query.append("contractor_id", params.contractor_id);
  if (params?.status) query.append("status", params.status);
  return apiGet<ContractMaster[]>(`/api/hierarchy/contracts?${query.toString()}`);
}

export async function createContract(data: any): Promise<ContractMaster> {
  return apiPost<ContractMaster>("/api/hierarchy/contracts", data);
}

export async function fetchOrganizationAuditEvents(entityId?: string, limit = 100): Promise<OrganizationAuditEvent[]> {
  const query = new URLSearchParams();
  if (entityId) query.append("entity_id", entityId);
  query.append("limit", limit.toString());
  return apiGet<OrganizationAuditEvent[]>(`/api/hierarchy/audit-events?${query.toString()}`);
}
