import { apiGet } from "./client";

export function getDashboardSummary() {
    return apiGet("/api/dashboard/summary");
}