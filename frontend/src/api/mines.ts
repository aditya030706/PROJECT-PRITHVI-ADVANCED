import { apiGet } from "./client";

export function getMines() {
    return apiGet("/api/mines");
}

export function getMine(mineId: string) {
    return apiGet(`/api/mines/${mineId}`);
}

export function getMineApplicability(mineId: string) {
    return apiGet(`/api/mines/${mineId}/applicability`);
}

export function getMineInspections(mineId: string) {
    return apiGet(`/api/mines/${mineId}/inspections`);
}