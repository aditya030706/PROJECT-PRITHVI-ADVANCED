import type { UserRole } from "./types";

export type Permission =
    // Field Inspector
    | "inspection.view_assigned"
    | "inspection.create"
    | "inspection.edit"
    | "inspection.submit"
    | "inspection.history_own"

    // Mine Supervisor
    | "attendance.create"
    | "attendance.view_team"
    | "safety.create"
    | "safety.view_team"

    // Mine Manager
    | "mine.view"
    | "mine.compliance.view"
    | "inspection.view_mine"
    | "verification.view"
    | "verification.review"
    | "report.approve"
    | "issue.escalate"
    | "schedule.view"

    // DGMS Officer
    | "region.view"
    | "mine.view_region"
    | "risk.view"
    | "verification.audit"
    | "attendance.audit"
    | "enforcement.create"
    | "statutory_report.view"

    // Corporate Management
    | "corporate.view"
    | "subsidiary.view"
    | "risk.trends"
    | "predictive_alerts.view"
    | "resource_allocation.view"
    | "corporate_reports.view"

    // Production & Operational Governance (Task 10)
    | "production.view"
    | "production.create"
    | "production.correct"
    | "production.reports"

    // Governance Master Hierarchy (Task 11)
    | "hierarchy.view"
    | "hierarchy.admin"

    // Environmental Governance & Monitoring (Task 13)
    | "environment.view"
    | "environment.manage";


export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {

    FIELD_INSPECTOR: [
        "inspection.view_assigned",
        "inspection.create",
        "inspection.edit",
        "inspection.submit",
        "inspection.history_own",
        "production.view",
        "hierarchy.view",
        "environment.view",
    ],

    MINE_SUPERVISOR: [
        "attendance.create",
        "attendance.view_team",
        "safety.create",
        "safety.view_team",
        "production.view",
        "production.create",
        "hierarchy.view",
        "environment.view",
    ],

    MINE_MANAGER: [
        "mine.view",
        "mine.compliance.view",
        "inspection.view_mine",
        "verification.view",
        "verification.review",
        "report.approve",
        "issue.escalate",
        "schedule.view",
        "production.view",
        "production.create",
        "production.correct",
        "production.reports",
        "hierarchy.view",
        "environment.view",
        "environment.manage",
    ],

    CORPORATE_MANAGEMENT: [
        "corporate.view",
        "subsidiary.view",
        "mine.view",
        "risk.trends",
        "predictive_alerts.view",
        "resource_allocation.view",
        "corporate_reports.view",
        "production.view",
        "production.reports",
        "hierarchy.view",
        "hierarchy.admin",
        "environment.view",
        "environment.manage",
    ],
};


export function hasPermission(
    role: UserRole,
    permission: Permission
): boolean {
    return ROLE_PERMISSIONS[role].includes(permission);
}