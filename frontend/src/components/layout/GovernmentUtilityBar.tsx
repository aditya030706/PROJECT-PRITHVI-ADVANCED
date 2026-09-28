import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Search, UserCheck, ChevronDown, Volume2, Globe, X, Loader2, Building, Layers, MapPin } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import type { UserRole } from "../../auth/types";
import { useRoleSwitch } from "../../context/RoleSwitchContext";
import { useLanguage } from "../../i18n/LanguageContext";
import { searchHierarchy, type SearchResultItem } from "../../api/hierarchy";

const FONT_STORAGE_KEY = "prithvi_font_scale";

export const GovernmentUtilityBar: React.FC = () => {
  const { session, logout } = useAuth();
  const { triggerRoleSwitch } = useRoleSwitch();
  const { lang, setLang, t } = useLanguage();
  const navigate = useNavigate();

  // Font resize state with persistence
  const [fontSize, setFontSize] = useState<"small" | "normal" | "large">(() => {
    try {
      const saved = localStorage.getItem(FONT_STORAGE_KEY);
      if (saved === "small" || saved === "normal" || saved === "large") return saved;
    } catch {
      // ignore
    }
    return "normal";
  });

  // Screen reader assistance feedback
  const [screenReaderActive, setScreenReaderActive] = useState<boolean>(false);
  const [srAnnouncement, setSrAnnouncement] = useState<string>("");

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Apply font size on mount and change
  useEffect(() => {
    const root = document.documentElement;
    if (fontSize === "small") root.style.fontSize = "14px";
    else if (fontSize === "large") root.style.fontSize = "18px";
    else root.style.fontSize = "16px";
    try {
      localStorage.setItem(FONT_STORAGE_KEY, fontSize);
    } catch {
      // ignore
    }
  }, [fontSize]);

  // Close search on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced live search
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setSearchResults([]);
      setSearchLoading(false);
      setSearchError(false);
      return;
    }

    setSearchLoading(true);
    setSearchError(false);
    const timer = setTimeout(async () => {
      try {
        const results = await searchHierarchy(searchQuery.trim(), 15);
        setSearchResults(results);
        setDropdownOpen(true);
      } catch (err) {
        console.error("Search failed:", err);
        setSearchError(true);
      } finally {
        setSearchLoading(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleFontSize = (size: "small" | "normal" | "large") => {
    setFontSize(size);
    const msg =
      size === "large"
        ? "Font size increased to large (18px)"
        : size === "small"
        ? "Font size decreased to small (14px)"
        : "Font size reset to normal standard (16px)";
    setSrAnnouncement(msg);
  };

  const handleRoleSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === "PUBLIC") {
      logout();
      navigate("/");
    } else if (val) {
      triggerRoleSwitch(val as UserRole);
    }
  };

  const handleToggleScreenReader = () => {
    const next = !screenReaderActive;
    setScreenReaderActive(next);
    const msg = next
      ? "Screen Reader optimization active: Accessible landmarks, semantic headers, and live aria regions enabled."
      : "Screen Reader optimization notification dismissed.";
    setSrAnnouncement(msg);
  };

  const handleSelectSearchResult = (item: SearchResultItem) => {
    setDropdownOpen(false);
    setSearchQuery("");
    navigate(item.link);
  };

  return (
    <div className="gov-utility-bar" role="region" aria-label="Government Utility Navigation">
      {/* Hidden Live Region for Screen Readers */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {srAnnouncement}
      </div>

      <div className="gov-utility-container">
        {/* Left: Indian National Flag & Government of India */}
        <div className="gov-utility-left">
          <div className="gov-flag-emblem" aria-hidden="true">
            <svg width="24" height="16" viewBox="0 0 24 16" fill="none" className="gov-flag-svg">
              <rect width="24" height="5.33" fill="#FF9933" />
              <rect y="5.33" width="24" height="5.34" fill="#FFFFFF" />
              <rect y="10.67" width="24" height="5.33" fill="#138808" />
              <circle cx="12" cy="8" r="2.2" stroke="#000080" strokeWidth="0.5" fill="none" />
            </svg>
          </div>
          <span className="gov-identity-text">
            <strong>{t("util.bharat_sarkar", "भारत सरकार")}</strong> | {t("util.gov_india", "Government of India")}
          </span>
          <span className="gov-badge-ministry">{t("util.ministry_of_coal", "Ministry of Coal")}</span>
        </div>

        {/* Right: Accessibility, Language, Search, Role Quick-Switch */}
        <div className="gov-utility-right">
          <a href="#main-content" className="gov-utility-link gov-skip-link">
            {t("util.skip_to_main", "Skip to main content")}
          </a>

          <span className="gov-utility-sep">|</span>

          {/* Screen Reader Access Toggle */}
          <button
            type="button"
            className={`gov-utility-tool ${screenReaderActive ? "gov-tool-active" : ""}`}
            onClick={handleToggleScreenReader}
            title={t("util.screen_reader", "Screen Reader Access")}
            aria-label={t("util.screen_reader", "Screen Reader Access")}
          >
            <Volume2 size={13} aria-hidden="true" />
            <span>{t("util.screen_reader", "Screen Reader Access")}</span>
          </button>

          <span className="gov-utility-sep">|</span>

          {/* Text Resize Controls */}
          <div className="gov-font-resizer" role="group" aria-label="Font size controls">
            <button
              type="button"
              className={`gov-font-btn ${fontSize === "small" ? "active" : ""}`}
              onClick={() => handleFontSize("small")}
              title={t("util.font_decrease", "Decrease font size")}
              aria-label={t("util.font_decrease", "Decrease font size")}
            >
              A-
            </button>
            <button
              type="button"
              className={`gov-font-btn ${fontSize === "normal" ? "active" : ""}`}
              onClick={() => handleFontSize("normal")}
              title={t("util.font_normal", "Normal font size")}
              aria-label={t("util.font_normal", "Normal font size")}
            >
              A
            </button>
            <button
              type="button"
              className={`gov-font-btn ${fontSize === "large" ? "active" : ""}`}
              onClick={() => handleFontSize("large")}
              title={t("util.font_increase", "Increase font size")}
              aria-label={t("util.font_increase", "Increase font size")}
            >
              A+
            </button>
          </div>

          <span className="gov-utility-sep">|</span>

          {/* Language Toggle */}
          <button
            type="button"
            className="gov-utility-tool gov-lang-btn"
            onClick={() => setLang(lang === "en" ? "hi" : "en")}
            title="Switch Language / भाषा बदलें"
            aria-label="Switch Language / भाषा बदलें"
          >
            <Globe size={13} aria-hidden="true" />
            <span className="font-semibold">{t("util.switch_lang", "हिंदी")}</span>
          </button>

          <span className="gov-utility-sep">|</span>

          {/* Role Switcher */}
          <div className="gov-role-selector" title="Switch Operational Role">
            <UserCheck size={13} className="gov-role-icon" aria-hidden="true" />
            <span className="gov-role-label">{t("util.role", "ROLE")}:</span>
            <div className="gov-role-select-box">
              <select
                id="gov-role-select"
                value={session?.role || "PUBLIC"}
                onChange={handleRoleSelect}
                aria-label="Select Operational Role"
              >
                <option value="PUBLIC">Public Portal</option>
                <option value="FIELD_INSPECTOR">Field Inspector</option>
                <option value="MINE_SUPERVISOR">Mine Supervisor</option>
                <option value="MINE_MANAGER">Mine Manager</option>
                <option value="CORPORATE_MANAGEMENT">Corporate Management</option>
              </select>
              <ChevronDown size={12} className="gov-role-arrow" aria-hidden="true" />
            </div>
          </div>

          {/* Search Box with Real Hierarchy Autocomplete */}
          <div className="gov-search-wrapper" ref={searchContainerRef}>
            <form
              className="gov-utility-search"
              onSubmit={(e) => {
                e.preventDefault();
                if (searchResults.length > 0) {
                  handleSelectSearchResult(searchResults[0]);
                } else if (searchQuery.trim()) {
                  navigate(`/governance?q=${encodeURIComponent(searchQuery.trim())}`);
                  setDropdownOpen(false);
                }
              }}
              role="search"
            >
              <input
                type="text"
                placeholder={t("util.search_placeholder", "Search mines, areas, subsidiaries...")}
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  if (e.target.value.trim().length >= 2) setDropdownOpen(true);
                }}
                onFocus={() => {
                  if (searchQuery.trim().length >= 2) setDropdownOpen(true);
                }}
                aria-label={t("util.search_placeholder", "Search mines, areas, subsidiaries...")}
              />
              {searchLoading ? (
                <div className="gov-search-spinner" aria-hidden="true">
                  <Loader2 size={13} className="animate-spin text-gray-500" />
                </div>
              ) : searchQuery ? (
                <button
                  type="button"
                  className="gov-search-clear-btn"
                  onClick={() => {
                    setSearchQuery("");
                    setSearchResults([]);
                    setDropdownOpen(false);
                  }}
                  aria-label="Clear search"
                >
                  <X size={12} />
                </button>
              ) : (
                <button type="submit" aria-label="Search">
                  <Search size={13} />
                </button>
              )}
            </form>

            {/* Dropdown Suggestions */}
            {dropdownOpen && searchQuery.trim().length >= 2 && (
              <div className="gov-search-dropdown" role="listbox">
                {searchLoading && searchResults.length === 0 && (
                  <div className="gov-search-status-item">
                    <Loader2 size={14} className="animate-spin" />
                    <span>Searching canonical hierarchy...</span>
                  </div>
                )}

                {searchError && (
                  <div className="gov-search-status-item text-red-600">
                    <span>{t("util.search_error", "Governance search is temporarily unavailable.")}</span>
                  </div>
                )}

                {!searchLoading && !searchError && searchResults.length === 0 && (
                  <div className="gov-search-status-item text-gray-500">
                    <span>{t("util.search_no_results", "No matching governance units found.")}</span>
                  </div>
                )}

                {searchResults.map((item) => (
                  <div
                    key={item.id}
                    className="gov-search-result-row"
                    onClick={() => handleSelectSearchResult(item)}
                    role="option"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSelectSearchResult(item);
                    }}
                  >
                    <div className="gov-search-res-icon">
                      {item.type === "MINE" ? (
                        <Building size={14} className="text-amber-700" />
                      ) : item.type === "OPERATIONAL_UNIT" ? (
                        <Layers size={14} className="text-blue-700" />
                      ) : (
                        <MapPin size={14} className="text-red-700" />
                      )}
                    </div>
                    <div className="gov-search-res-content">
                      <div className="gov-search-res-top">
                        <span className="gov-search-res-name">{item.name}</span>
                        <span className={`gov-search-res-badge badge-${item.type.toLowerCase()}`}>
                          {item.type === "MINE" && item.mine_type ? `${item.type} (${item.mine_type})` : item.type}
                        </span>
                      </div>
                      <div className="gov-search-res-path">
                        {item.hierarchy_path.join(" › ")}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
