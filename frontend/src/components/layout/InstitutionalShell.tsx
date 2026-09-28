import React from "react";
import { GovernmentUtilityBar } from "./GovernmentUtilityBar";
import { GovernmentBrandHeader } from "./GovernmentBrandHeader";
import { GovernmentNavbar } from "./GovernmentNavbar";
import { GovernmentFooter } from "./GovernmentFooter";

interface InstitutionalShellProps {
  children: React.ReactNode;
}

export const InstitutionalShell: React.FC<InstitutionalShellProps> = ({ children }) => {
  return (
    <div className="institutional-shell">
      {/* 3-Tier Government Header */}
      <GovernmentUtilityBar />
      <GovernmentBrandHeader />
      <GovernmentNavbar />

      {/* Main Content Area with Accessibility ID */}
      <main id="main-content" className="institutional-main" tabIndex={-1}>
        {children}
      </main>

      {/* Standard Institutional Footer */}
      <GovernmentFooter />
    </div>
  );
};

export default InstitutionalShell;
