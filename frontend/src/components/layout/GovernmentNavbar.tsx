import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Home, Menu, X, Shield, Activity, Globe, LogOut, ArrowRight, UserCheck } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { useLanguage } from "../../i18n/LanguageContext";
import { ROLE_NAVIGATION, PUBLIC_NAVIGATION } from "../../auth/navigation";

export const GovernmentNavbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { session, logout } = useAuth();
  const { t } = useLanguage();
  const [mobileOpen, setMobileOpen] = useState(false);

  const role = session?.role;
  const navItems = role ? ROLE_NAVIGATION[role] : PUBLIC_NAVIGATION;

  const isCurrentActive = (item: { path: string }) => {
    if (item.path === "/") {
      return location.pathname === "/" || location.pathname === "/landing" || location.pathname === "/overview";
    }
    if (item.path === "/manager") {
      return location.pathname === "/manager" || location.pathname === "/compliance";
    }
    return location.pathname === item.path || (item.path !== "/" && location.pathname.startsWith(`${item.path}/`));
  };

  const handleLogout = () => {
    logout();
    navigate("/", { replace: true });
  };

  return (
    <nav className="gov-navbar" aria-label="Main Navigation">
      <div className="gov-nav-container">
        {/* Left: Home Icon Button & Nav Links */}
        <div className="gov-nav-left">
          <Link
            to="/"
            className={`gov-nav-home-btn ${location.pathname === "/" || location.pathname === "/landing" ? "active" : ""}`}
            title="PRITHVI Public Home"
            aria-label="PRITHVI Public Home"
          >
            <Home size={16} />
            <span className="gov-nav-home-text">{t("nav.home", "HOME")}</span>
          </Link>

          {/* Desktop Nav Items */}
          <ul className="gov-nav-list" role="menubar">
            {navItems
              .filter((item) => item.label !== "PORTAL HOME" && item.label !== "HOME")
              .map((item) => {
                const active = isCurrentActive(item);
                return (
                  <li key={item.path} role="none">
                    <Link
                      to={item.path}
                      role="menuitem"
                      className={`gov-nav-item ${active ? "active" : ""}`}
                      aria-current={active ? "page" : undefined}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
          </ul>
        </div>

        {/* Right: Role Context / Workspace Selector & Logout */}
        <div className="gov-nav-right">
          {role ? (
            <>
              <div className="gov-nav-role-badge" title={`Active Authorized Workspace: ${role.replace(/_/g, " ")}`}>
                <Shield size={13} className="gov-nav-role-icon" />
                <span className="gov-nav-role-name">
                  {role.replace(/_/g, " ")}
                </span>
              </div>

              <div className="gov-nav-status-badge" title="Real-Time SCADA Telemetry Engine Online (Simulated)">
                <Activity size={12} className="gov-pulse-dot" />
                <span>SCADA ONLINE</span>
              </div>

              <Link
                to="/workspace"
                className="gov-nav-switch-role-link"
                style={{
                  fontSize: "11px",
                  color: "#fef08a",
                  textDecoration: "none",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  border: "1px solid rgba(254, 240, 138, 0.4)",
                  background: "rgba(0, 0, 0, 0.25)",
                  fontWeight: 600,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                }}
                title="Switch Operational Role"
              >
                <UserCheck size={12} />
                <span>Switch Role</span>
              </Link>

              <button
                type="button"
                onClick={handleLogout}
                style={{
                  background: "rgba(255, 255, 255, 0.15)",
                  border: "1px solid rgba(255, 255, 255, 0.3)",
                  color: "#ffffff",
                  borderRadius: "4px",
                  padding: "4px 8px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                }}
                title="Log out and return to Public Portal"
              >
                <LogOut size={12} />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <>
              <div
                className="gov-nav-role-badge"
                style={{
                  background: "rgba(255, 255, 255, 0.15)",
                  border: "1px solid rgba(255, 255, 255, 0.25)",
                }}
                title="Public Information Portal (No role active)"
              >
                <Globe size={13} style={{ color: "#93c5fd" }} />
                <span>PUBLIC PORTAL</span>
              </div>

              <Link
                to="/workspace"
                style={{
                  background: "#b45309",
                  color: "#ffffff",
                  textDecoration: "none",
                  padding: "5px 12px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  fontWeight: 700,
                  letterSpacing: "0.03em",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
                }}
                title="Enter PRITHVI Role-Based Workspace"
              >
                <span>CHOOSE WORKSPACE</span>
                <ArrowRight size={13} />
              </Link>
            </>
          )}

          <button
            type="button"
            className="gov-mobile-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle navigation menu"
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileOpen && (
        <div className="gov-nav-mobile-drawer" role="menu">
          <Link
            to="/"
            role="menuitem"
            className={`gov-nav-mobile-item ${location.pathname === "/" ? "active" : ""}`}
            onClick={() => setMobileOpen(false)}
          >
            <Home size={16} />
            <span>{t("nav.home", "HOME")}</span>
          </Link>
          {navItems.map((item) => {
            const active = isCurrentActive(item);
            return (
              <Link
                key={item.path}
                to={item.path}
                role="menuitem"
                className={`gov-nav-mobile-item ${active ? "active" : ""}`}
                onClick={() => setMobileOpen(false)}
              >
                {item.label}
              </Link>
            );
          })}
          {role ? (
            <button
              type="button"
              className="gov-nav-mobile-item"
              onClick={() => {
                setMobileOpen(false);
                handleLogout();
              }}
              style={{ color: "#fca5a5", background: "none", border: "none", width: "100%", textAlign: "left", cursor: "pointer" }}
            >
              <LogOut size={16} style={{ display: "inline", marginRight: "8px" }} />
              <span>Logout ({role.replace(/_/g, " ")})</span>
            </button>
          ) : (
            <Link
              to="/workspace"
              role="menuitem"
              className="gov-nav-mobile-item"
              onClick={() => setMobileOpen(false)}
              style={{ color: "#fef08a", fontWeight: 700 }}
            >
              <ArrowRight size={16} style={{ display: "inline", marginRight: "8px" }} />
              <span>Choose Workspace</span>
            </Link>
          )}
        </div>
      )}
    </nav>
  );
};

export default GovernmentNavbar;
