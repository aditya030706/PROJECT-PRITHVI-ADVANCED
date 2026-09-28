import { apiGet, apiPost } from "./client";

export type CreateInspectionRequest = {
    mine_id: string;
    template_id: string;
    obligation_id?: string;
    inspector_id: string;
    inspection_date?: string;
    latitude?: number;
    longitude?: number;
    gps_accuracy_m?: number;
};

export type Inspection = {
    inspection_id: string;
    mine_id: string;
    template_id: string;
    obligation_id: string | null;
    inspector_id: string;
    started_at: string;
    submitted_at: string | null;
    inspection_date: string;
    status: string;

    latitude: number | null;
    longitude: number | null;
    gps_accuracy_m: number | null;

    inspection_name: string;
    inspection_family: string;
};

export type MineInspectionHistory = {
    mine_id: string;
    inspections: Inspection[];
};

export type VerificationSignal = {
    signal_id: string;
    category: string;
    name: string;
    status: string;
    severity: string;
    score: number | null;
    explanation: string;
};

export type VerificationResult = {
    verification_id: string;
    inspection_id: string;
    status: string;
    confidence: number;
    signals: VerificationSignal[];
    source_anomalies: string[];
    evidence_conflicts: string[];
    recommendation: string;
    human_decision_required: boolean;
};

export async function createInspection(
    payload: CreateInspectionRequest
): Promise<Inspection> {
    return apiPost<Inspection>(
        "/api/inspections",
        payload
    );
}

export async function getMineInspections(
    mineId: string
): Promise<MineInspectionHistory> {
    return apiGet<MineInspectionHistory>(
        `/api/mines/${encodeURIComponent(mineId)}/inspections`
    );
}

export async function getVerification(
    inspectionId: string
): Promise<VerificationResult> {
    return apiGet<VerificationResult>(
        `/api/verifications/${encodeURIComponent(inspectionId)}`
    );
}