import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import type { Permission } from "./permissions";
import { hasPermission } from "./permissions";
import type { UserRole } from "./types";
import { ROLE_HOME_ROUTES } from "./navigation";
import { useAuth } from "./AuthContext";

type RoleGuardProps = {
    role?: UserRole | null;
    permission?: Permission;
    allowedRoles?: UserRole[];
    children: ReactNode;
};

export default function RoleGuard({
    role,
    permission,
    allowedRoles,
    children,
}: RoleGuardProps) {
    const { isHydrated } = useAuth();
    const location = useLocation();

    // Do not make permission decision while session is hydrating
    if (!isHydrated) {
        return null;
    }

    // If no role is selected, user must choose an authorized workspace
    if (!role) {
        return <Navigate to="/workspace" state={{ from: location.pathname }} replace />;
    }

    const homeRoute = ROLE_HOME_ROUTES[role] || "/";

    /*
     * Role-level protection
     */
    if (
        allowedRoles &&
        !allowedRoles.includes(role)
    ) {
        if (location.pathname === homeRoute) {
            return (
                <AccessDenied
                    role={role}
                />
            );
        }
        return <AccessDenied role={role} />;
    }

    /*
     * Permission-level protection
     */
    if (
        permission &&
        !hasPermission(role, permission)
    ) {
        if (location.pathname === homeRoute) {
            return (
                <AccessDenied
                    role={role}
                />
            );
        }
        return <AccessDenied role={role} />;
    }

    return <>{children}</>;
}


function AccessDenied({
    role,
}: {
    role: UserRole;
}) {
    return (
        <section
            style={{
                minHeight: "60vh",
                display: "grid",
                placeItems: "center",
                padding: "48px 24px",
            }}
        >
            <div
                style={{
                    maxWidth: "520px",
                    textAlign: "center",
                }}
            >
                <div
                    style={{
                        fontFamily: "DM Mono, monospace",
                        fontSize: "12px",
                        letterSpacing: "0.12em",
                        marginBottom: "16px",
                        color: "var(--copper)",
                    }}
                >
                    ACCESS CONTROL
                </div>

                <h1
                    style={{
                        margin: "0 0 12px",
                        fontFamily: "Playfair Display, serif",
                        fontSize: "36px",
                    }}
                >
                    Access restricted
                </h1>

                <p
                    style={{
                        margin: 0,
                        color: "var(--steel)",
                        lineHeight: 1.7,
                    }}
                >
                    Your current role (
                    <strong>{role}</strong>
                    ) does not have permission
                    to access this resource.
                </p>
            </div>
        </section>
    );
}