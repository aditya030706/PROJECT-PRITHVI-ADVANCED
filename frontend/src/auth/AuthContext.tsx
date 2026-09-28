import {
    createContext,
    useContext,
    useMemo,
    useState,
    type ReactNode,
} from "react";

import type {
    UserRole,
    UserSession,
} from "./types";


type AuthContextValue = {
    session: UserSession | null;
    role: UserRole | null;
    isAuthenticated: boolean;
    setRole: (role: UserRole | null) => void;
    logout: () => void;
    isHydrated: boolean;
};

const ROLE_STORAGE_KEY = "prithvi_active_role";

function getInitialRole(): UserRole | null {
    if (typeof window === "undefined") {
        return null;
    }
    try {
        const stored =
            localStorage.getItem(ROLE_STORAGE_KEY) ||
            sessionStorage.getItem(ROLE_STORAGE_KEY);
        if (stored && stored in DEMO_SESSIONS) {
            return stored as UserRole;
        }
    } catch {
        // storage disabled or unavailable
    }
    return null;
}

const DEMO_SESSIONS: Record<UserRole, UserSession> = {

    FIELD_INSPECTOR: {
        user_id: "INSPECTOR-WEB-001",
        name: "Field Inspector",
        role: "FIELD_INSPECTOR",
        mine_id: "MINE-DEMO-001",
    },

    MINE_SUPERVISOR: {
        user_id: "SUPERVISOR-WEB-001",
        name: "Mine Supervisor",
        role: "MINE_SUPERVISOR",
        mine_id: "MINE-DEMO-001",
    },

    MINE_MANAGER: {
        user_id: "MANAGER-WEB-001",
        name: "Mine Manager",
        role: "MINE_MANAGER",
        mine_id: "MINE-DEMO-001",
    },

    CORPORATE_MANAGEMENT: {
        user_id: "CORPORATE-WEB-001",
        name: "Corporate Management",
        role: "CORPORATE_MANAGEMENT",
        subsidiary: "COAL INDIA",
    },
};


const AuthContext =
    createContext<AuthContextValue | null>(null);


export function AuthProvider({
    children,
}: {
    children: ReactNode;
}) {

    const [role, setRoleState] =
        useState<UserRole | null>(getInitialRole);

    const [isHydrated] =
        useState<boolean>(true);

    const setRole = (newRole: UserRole | null) => {
        setRoleState(newRole);
        try {
            if (newRole) {
                localStorage.setItem(ROLE_STORAGE_KEY, newRole);
                sessionStorage.setItem(ROLE_STORAGE_KEY, newRole);
            } else {
                localStorage.removeItem(ROLE_STORAGE_KEY);
                sessionStorage.removeItem(ROLE_STORAGE_KEY);
            }
        } catch {
            // storage error handling
        }
    };

    const logout = () => {
        setRoleState(null);
        try {
            localStorage.removeItem(ROLE_STORAGE_KEY);
            sessionStorage.removeItem(ROLE_STORAGE_KEY);
        } catch {
            // storage error handling
        }
    };

    const session = useMemo(
        () => (role ? DEMO_SESSIONS[role] : null),
        [role]
    );

    const value = useMemo(
        () => ({
            session,
            role,
            isAuthenticated: role !== null,
            setRole,
            logout,
            isHydrated,
        }),
        [session, role, isHydrated]
    );

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}


export function useAuth(): AuthContextValue {

    const context = useContext(AuthContext);

    if (!context) {
        throw new Error(
            "useAuth must be used inside AuthProvider"
        );
    }

    return context;
}