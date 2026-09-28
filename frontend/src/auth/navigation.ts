import type { UserRole } from "./types";

export type NavigationItem = {
    label: string;
    path: string;
};

export const ROLE_HOME_ROUTES: Record<UserRole, string> = {
    FIELD_INSPECTOR: "/inspections",
    MINE_SUPERVISOR: "/supervisor",
    MINE_MANAGER: "/manager",
    CORPORATE_MANAGEMENT: "/corporate",
};

export const PUBLIC_NAVIGATION: NavigationItem[] = [
    {
        label: "HOME",
        path: "/",
    },
    {
        label: "GOVERNANCE OVERVIEW",
        path: "/governance",
    },
    {
        label: "WORKSPACES",
        path: "/workspace",
    },
];

export const ROLE_NAVIGATION: Record<
    UserRole,
    NavigationItem[]
> = {

    FIELD_INSPECTOR: [
        {
            label: "PORTAL HOME",
            path: "/",
        },
        {
            label: "GPS ATTENDANCE",
            path: "/field",
        },
        {
            label: "MY INSPECTIONS",
            path: "/inspections",
        },
        {
            label: "INSPECTION PLAN",
            path: "/inspections/plan",
        },
        {
            label: "MY HISTORY",
            path: "/inspections/history",
        },
    ],
    MINE_SUPERVISOR: [
        {
            label: "PORTAL HOME",
            path: "/",
        },
        {
            label: "PRODUCTION",
            path: "/production",
        },
        {
            label: "ATTENDANCE",
            path: "/attendance/team",
        },
        {
            label: "SCADA SAFETY",
            path: "/safety",
        },
        {
            label: "MY TEAM",
            path: "/supervisor/team",
        },
    ],

    MINE_MANAGER: [
        {
            label: "PORTAL HOME",
            path: "/",
        },
        {
            label: "MINE COMMAND",
            path: "/manager",
        },
        {
            label: "GOVERNANCE",
            path: "/governance",
        },
        {
            label: "ENVIRONMENT",
            path: "/environment",
        },
        {
            label: "PRODUCTION",
            path: "/production",
        },
        {
            label: "SCADA SAFETY",
            path: "/safety",
        },
        {
            label: "MINES",
            path: "/mines",
        },
        {
            label: "VERIFICATION",
            path: "/verification",
        },
        {
            label: "ATTENDANCE",
            path: "/attendance/team",
        },
        {
            label: "REPORTS",
            path: "/manager/reports",
        },
    ],

    CORPORATE_MANAGEMENT: [
        {
            label: "PORTAL HOME",
            path: "/",
        },
        {
            label: "CORPORATE COMMAND",
            path: "/corporate",
        },
        {
            label: "GOVERNANCE MASTER",
            path: "/governance",
        },
        {
            label: "ENVIRONMENT",
            path: "/environment",
        },
        {
            label: "MASTER DATA ADMIN",
            path: "/admin/master-data",
        },
        {
            label: "PRODUCTION",
            path: "/production",
        },
        {
            label: "SCADA SAFETY",
            path: "/safety",
        },
        {
            label: "SUBSIDIARIES",
            path: "/corporate/subsidiaries",
        },
        {
            label: "MINES",
            path: "/corporate/mines",
        },
        {
            label: "RISK",
            path: "/corporate/risk",
        },
        {
            label: "TRENDS",
            path: "/corporate/trends",
        },
        {
            label: "REPORTS",
            path: "/corporate/reports",
        },
    ],
};