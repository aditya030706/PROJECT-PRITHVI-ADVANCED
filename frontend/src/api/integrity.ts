/**
 * PRITHVI — Evidence Integrity API Client (Phase 2 Task 7)
 *
 * Provides typed access to the evidence integrity endpoints:
 *  GET  /api/evidence/{id}/integrity
 *  POST /api/evidence/{id}/anchor
 *  POST /api/evidence/{id}/verify-integrity
 *  GET  /api/inspections/{id}/audit-integrity
 *  GET  /api/cases/{id}/audit-integrity
 *  GET  /api/integrity/status
 */

import { apiGet, apiPost } from './client';

// ============================================================
// TYPES
// ============================================================

export interface EvidenceIntegrityRecord {
  integrity_id: string;
  evidence_id: string;
  content_hash: string;
  hash_algorithm: string;
  ipfs_cid: string | null;
  ipfs_status: 'PENDING' | 'STORED' | 'IPFS_NOT_CONFIGURED' | 'FAILED';
  blockchain_network: string | null;
  transaction_ref: string | null;
  block_ref: string | null;
  anchored_at: string | null;
  anchor_mode: 'DEMO_AUDIT_MODE' | 'LIVE_BLOCKCHAIN';
  status: 'PENDING' | 'ANCHORED' | 'VERIFIED' | 'FAILED';
  verified_at: string | null;
  verification_result: string | null;
  created_at: string;
  integrity_label: string | null;
  mode_label: string | null;
}

export interface EvidenceAnchorRequest {
  actor_id?: string;
  reference_type?: string;
  notes?: string;
}

export interface EvidenceAnchorResponse {
  evidence_id: string;
  anchored: boolean;
  integrity: EvidenceIntegrityRecord;
  message: string;
}

export interface EvidenceIntegrityStatusResponse {
  evidence_id: string;
  status: string;
  integrity: EvidenceIntegrityRecord | null;
  message?: string;
}

export interface EvidenceVerifyResponse {
  evidence_id: string;
  matches: boolean;
  verification_status: string;
  mode: string;
  details: string;
  integrity: EvidenceIntegrityRecord | null;
}

export interface EvidenceWithIntegrity {
  evidence_id: string;
  evidence_type: string;
  filename: string | null;
  captured_at: string | null;
  sha256: string | null;
  integrity: EvidenceIntegrityRecord | null;
}

export interface InspectionAuditIntegrityResponse {
  inspection_id: string;
  mine_id: string | null;
  total_evidence: number;
  anchored_count: number;
  verified_count: number;
  pending_count: number;
  integrity_coverage: 'FULL' | 'PARTIAL' | 'NONE';
  evidence_integrity: EvidenceWithIntegrity[];
  ipfs_service_status: {
    configured: boolean;
    mode: string;
    message: string;
  };
  blockchain_service_status: {
    configured: boolean;
    mode: string;
    network: string;
    ledger_standard: string;
    message: string;
  };
}

export interface CaseAuditIntegrityResponse {
  case_id: string;
  mine_id: string | null;
  total_correction_evidence: number;
  anchored_count: number;
  verified_count: number;
  integrity_coverage: 'FULL' | 'PARTIAL' | 'NONE';
  evidence_integrity: EvidenceWithIntegrity[];
  ipfs_service_status: Record<string, unknown>;
  blockchain_service_status: Record<string, unknown>;
}

export interface IntegrityServiceStatus {
  ipfs: {
    configured: boolean;
    mode: string;
    endpoint: string | null;
    message: string;
  };
  blockchain: {
    configured: boolean;
    mode: string;
    network: string;
    ledger_standard: string;
    rpc_endpoint: string | null;
    message: string;
  };
  note: string;
}

// ============================================================
// API CALLS
// ============================================================

export async function anchorEvidence(
  evidenceId: string,
  payload: EvidenceAnchorRequest = {}
): Promise<EvidenceAnchorResponse> {
  return apiPost<EvidenceAnchorResponse>(
    `/api/evidence/${evidenceId}/anchor`,
    payload
  );
}

export async function getEvidenceIntegrity(
  evidenceId: string
): Promise<EvidenceIntegrityStatusResponse> {
  return apiGet<EvidenceIntegrityStatusResponse>(
    `/api/evidence/${evidenceId}/integrity`
  );
}

export async function verifyEvidenceIntegrity(
  evidenceId: string
): Promise<EvidenceVerifyResponse> {
  return apiPost<EvidenceVerifyResponse>(
    `/api/evidence/${evidenceId}/verify-integrity`,
    {}
  );
}

export async function getInspectionAuditIntegrity(
  inspectionId: string
): Promise<InspectionAuditIntegrityResponse> {
  return apiGet<InspectionAuditIntegrityResponse>(
    `/api/inspections/${inspectionId}/audit-integrity`
  );
}

export async function getCaseAuditIntegrity(
  caseId: string
): Promise<CaseAuditIntegrityResponse> {
  return apiGet<CaseAuditIntegrityResponse>(
    `/api/cases/${caseId}/audit-integrity`
  );
}

export async function getIntegrityServiceStatus(): Promise<IntegrityServiceStatus> {
  return apiGet<IntegrityServiceStatus>('/api/integrity/status');
}
