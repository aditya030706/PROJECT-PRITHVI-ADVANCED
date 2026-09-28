import { apiGet, apiPost } from "./client";

export type MeasurementCreate = {
    measurement_type: string;
    value: number;
    unit?: string | null;
    source?: string;
    captured_at?: string | null;
};

export type ChecklistResultCreate = {
    item_id: string;
    passed: boolean;
    observation?: string | null;
};

export type FindingCreate = {
    title: string;
    description: string;
    severity: string;
    corrective_action_required?: boolean;
    evidence_ids?: string[];
};

export type EvidenceCreate = {
    evidence_type:
    | "photo"
    | "document"
    | "video"
    | "voice"
    | "sensor"
    | "manual_reading";
    filename?: string | null;
    storage_reference?: string | null;
    captured_at?: string | null;
    latitude?: number | null;
    longitude?: number | null;
};

export type UploadedEvidence = {
    evidence_id: string;
    inspection_id: string;
    evidence_type: string;
    filename: string;
    storage_reference: string;
    sha256: string;
    captured_at: string;
};

export type DemoDocument = {
    filename: string;
    size_bytes: number;
    mine_hint: string | null;
};

export type Inspection = {
    inspection_id: string;
    mine_id: string;
    template_id: string;
    obligation_id: string | null;
    inspector_id: string;
    inspection_date: string;
    started_at: string | null;
    submitted_at: string | null;
    status: string;
    latitude: number | null;
    longitude: number | null;
    gps_accuracy_m: number | null;
};

export type InspectionTemplate = {
    template_id: string;
    name: string;
    inspection_family: string;
    description: string | null;
    applicable_mine_types: string[];
    regulatory_obligation_ids: string[];
    frequency_or_trigger: string | null;
    frequency_label?: string | null;
    responsible_role?: string | null;
    regulation_reference?: string | null;
    measurements: Array<{
        measurement_id?: string;
        name: string;
        unit?: string | null;
        required?: boolean;
        description?: string;
        min_value?: number | null;
        max_value?: number | null;
        threshold_label?: string | null;
        options?: string[] | null;
    }>;
    checklist: Array<{
        item_id: string;
        question: string;
        required?: boolean;
        severity_if_failed?: string;
    }>;
    evidence_requirements: Array<{
        evidence_id: string;
        evidence_type: string;
        name: string;
        required?: boolean;
        minimum_count?: number;
    }>;
    active: boolean;
};

export async function getInspection(inspectionId: string) {
    return apiGet<Inspection>(`/api/inspections/${inspectionId}`);
}

export async function getInspectionTemplates() {
    return apiGet<InspectionTemplate[]>("/api/inspection-templates");
}

export async function getMineTemplates(mineId: string) {
    return apiGet<InspectionTemplate[]>(`/api/mines/${mineId}/templates`);
}

export async function addMeasurement(inspectionId: string, payload: MeasurementCreate) {
    return apiPost(`/api/inspections/${inspectionId}/measurements`, payload);
}

export async function addChecklistResult(inspectionId: string, payload: ChecklistResultCreate) {
    return apiPost(`/api/inspections/${inspectionId}/checklist`, payload);
}

export async function addFinding(inspectionId: string, payload: FindingCreate) {
    return apiPost(`/api/inspections/${inspectionId}/findings`, payload);
}

export async function addEvidence(inspectionId: string, payload: EvidenceCreate) {
    return apiPost<UploadedEvidence>(`/api/inspections/${inspectionId}/evidence`, payload);
}

export async function listInspectionEvidence(inspectionId: string): Promise<UploadedEvidence[]> {
    return apiGet<UploadedEvidence[]>(`/api/inspections/${inspectionId}/evidence`);
}

export async function uploadEvidence(
    inspectionId: string,
    file: File
): Promise<UploadedEvidence> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(
        `http://127.0.0.1:8000/api/inspections/${inspectionId}/upload-evidence`,
        { method: "POST", body: formData }
    );
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload failed: ${response.status} — ${errorText}`);
    }
    return response.json();
}

export async function listDemoDocuments(): Promise<DemoDocument[]> {
    return apiGet<DemoDocument[]>("/api/demo-documents");
}

export async function attachDemoDocument(
    inspectionId: string,
    filename: string
): Promise<UploadedEvidence> {
    return apiPost<UploadedEvidence>(
        `/api/inspections/${inspectionId}/attach-demo`,
        { filename }
    );
}

export async function submitInspection(
    inspectionId: string,
    payload: {
        inspection_id: string;
        measurements?: MeasurementCreate[];
        checklist_results?: ChecklistResultCreate[];
        findings?: FindingCreate[];
        observation?: string | null;
    }
) {
    return apiPost(`/api/inspections/${inspectionId}/submit`, payload);
}

