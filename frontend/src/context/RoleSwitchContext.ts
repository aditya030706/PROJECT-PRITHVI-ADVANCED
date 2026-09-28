import { createContext, useContext } from "react";
import type { UserRole } from "../auth/types";

/* =============================================================
   ROLE SWITCH CONTEXT
   Allows any component inside Layout to trigger the existing
   cinematic role-switch transition without prop drilling.
   Provided by Layout; consumed by PrithviLanding and any
   other component that needs to initiate a role switch.
============================================================= */

export type RoleSwitchContextValue = {
  /** Trigger the full role-switch transition for a given role. */
  triggerRoleSwitch: (role: UserRole) => void;
};

export const RoleSwitchContext =
  createContext<RoleSwitchContextValue | null>(null);

export function useRoleSwitch(): RoleSwitchContextValue {
  const ctx = useContext(RoleSwitchContext);
  if (!ctx) {
    throw new Error(
      "useRoleSwitch must be used inside RoleSwitchContext.Provider (within Layout)"
    );
  }
  return ctx;
}
