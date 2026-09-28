import { apiGet, apiPost } from "./client";

export interface TelemetryReading {
    reading_id: string;
    sensor_id: string;
    mine_id: string;
    zone_id?: string | null;
    sensor_type: string;
    value: number;
    unit: string;
    recorded_at: string;
    received_at: string;
    quality_status: string;
    threshold_status: "NORMAL" | "WARNING" | "CRITICAL";
    source: string;
    simulated: boolean;
    display_name?: string | null;
    sensor_code?: string | null;
}

export interface SafetySignal {
    signal_id: string;
    mine_id: string;
    sensor_id: string;
    sensor_type: string;
    severity: "WARNING" | "CRITICAL";
    status: "ACTIVE" | "RECOVERED" | "ACKNOWLEDGED";
    observed_value: number;
    unit: string;
    threshold_definition: string;
    explanation: string;
    first_detected_at: string;
    last_detected_at: string;
    recovered_at?: string | null;
    consecutive_readings: number;
    linked_case_id?: string | null;
    evidence_id?: string | null;
    simulated: boolean;
    display_name?: string | null;
    sensor_code?: string | null;
}

export interface SensorInfo {
    sensor_id: string;
    mine_id: string;
    zone_id?: string | null;
    sensor_code: string;
    sensor_type: string;
    unit: string;
    display_name: string;
    status: string;
    simulated: boolean;
    created_at: string;
}

export interface TelemetryHealth {
    source: string;
    total_sensors_configured: number;
    total_readings_stored: number;
    sensors_reporting_live: number;
    active_safety_signals: number;
    last_telemetry_timestamp?: string | null;
    status: string;
}

export interface TelemetryBatchResponse {
    success: boolean;
    ingested_count: number;
    evaluated_signals_count: number;
    critical_signals_count: number;
    new_cases_created: number;
    server_timestamp: string;
    readings: TelemetryReading[];
}

export async function fetchLatestMineTelemetry(mineId: string): Promise<TelemetryReading[]> {
    return apiGet<TelemetryReading[]>(`/api/telemetry/mine/${mineId}/latest`);
}

export async function fetchMineTelemetryHistory(
    mineId: string,
    limit: number = 50,
    sensorType?: string
): Promise<TelemetryReading[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (sensorType) params.append("sensor_type", sensorType);
    return apiGet<TelemetryReading[]>(`/api/telemetry/mine/${mineId}?${params.toString()}`);
}

export async function fetchMineSafetySignals(
    mineId: string,
    activeOnly: boolean = false
): Promise<SafetySignal[]> {
    const params = new URLSearchParams({ active_only: String(activeOnly) });
    return apiGet<SafetySignal[]>(`/api/telemetry/mine/${mineId}/signals?${params.toString()}`);
}

export async function fetchAllSensors(mineId?: string): Promise<SensorInfo[]> {
    const path = mineId ? `/api/telemetry/sensors?mine_id=${encodeURIComponent(mineId)}` : `/api/telemetry/sensors`;
    return apiGet<SensorInfo[]>(path);
}

export async function fetchTelemetryHealth(): Promise<TelemetryHealth> {
    return apiGet<TelemetryHealth>("/api/telemetry/health");
}

export async function postTelemetryBatch(readings: any[]): Promise<TelemetryBatchResponse> {
    return apiPost<TelemetryBatchResponse>("/api/telemetry/readings", {
        readings,
        source: "SCADA_SIMULATOR",
        simulated: true,
    });
}
