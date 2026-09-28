import { useState } from "react";
import { X, ExternalLink } from "lucide-react";
import { useLanguage } from "../../i18n/LanguageContext";

export const GovernmentFooter: React.FC = () => {
  const { t } = useLanguage();
  const [activeModal, setActiveModal] = useState<string | null>(null);

  const legalContent: Record<string, { title: string; content: string[] }> = {
    "important-links": {
      title: "Important Links & Statutory Portals",
      content: [
        "Ministry of Coal (MoC): https://coal.gov.in",
        "Directorate General of Mines Safety (DGMS): https://dgms.gov.in",
        "Coal India Limited (CIL): https://www.coalindia.in",
        "Digital India Platform: https://www.digitalindia.gov.in",
        "PARIVESH Environmental Clearance Portal: https://parivesh.nic.in",
        "Smart India Hackathon 2026: Problem Statement SIH26024",
      ],
    },
    privacy: {
      title: "Privacy Policy",
      content: [
        "Project PRITHVI is dedicated to ensuring the highest standards of data integrity and privacy.",
        "All telemetry, inspection, and verification data are cryptographically signed using SHA-256 hashes.",
        "Personal biometric records are processed strictly within authorized statutory scopes under Mines Rules 1955.",
        "No non-operational telemetry is shared with unauthorized external entities.",
      ],
    },
    terms: {
      title: "Terms of Use",
      content: [
        "Project PRITHVI is an AI-assisted decision support system deployed under the mandate of Ministry of Coal mandates for SIH 2026.",
        "All final statutory enforcement actions, prohibition notices under Section 22, and inspection closures remain with authorized human officials.",
        "Unauthorized attempts to tamper with cryptographically verified records constitute a violation of statutory safety mandates.",
      ],
    },
    accessibility: {
      title: "Accessibility Statement",
      content: [
        "Project PRITHVI complies with the Guidelines for Indian Government Websites (GIGW) and WCAG 2.1 Level AA standards.",
        "Semantic HTML5 landmarks, visible focus states, responsive text scaling (A-, A, A+), and high-contrast color standards are implemented across all consoles.",
        "Full screen reader compatibility is supported via standard ARIA attributes.",
      ],
    },
    sitemap: {
      title: "Portal Sitemap",
      content: [
        "• Home / System Overview (/landing, /overview)",
        "• Canonical Governance Master Hierarchy (/governance)",
        "• Mine Compliance Command Center (/)",
        "• Field Operations & Inspector Console (/inspections)",
        "• SCADA Telemetry & Environmental Safety (/safety)",
        "• Workforce Attendance & Muster Roll (/attendance/team)",
        "• Production & Operational Governance (/production)",
        "• DGMS Regulatory Intelligence & Audits (/dgms)",
        "• Evidence Chain & Tamper-Evident Ledger (/evidence)",
      ],
    },
    help: {
      title: "Help & Operational Support",
      content: [
        "For technical inquiries regarding the PRITHVI platform, refer to the System Architecture documentation.",
        "For statutory inspection issues, contact your designated Area Safety Officer or DGMS Regional Inspector.",
        "SCADA and atmospheric gas sensor telemetry in this deployment are driven by the PRITHVI simulated SCADA engine.",
      ],
    },
  };

  return (
    <footer className="gov-footer-official" role="contentinfo">
      <div className="gov-footer-inner-container">
        {/* Left: Ministry Branding with Ashoka Stambh */}
        <div className="gov-footer-left-brand">
          <img
            src="/ministry-of-coal-official.png"
            alt="Ministry of Coal Government of India Emblem"
            className="gov-footer-emblem-img"
          />
        </div>

        {/* Right: Institutional Navigation Links */}
        <div className="gov-footer-links-group" role="navigation" aria-label="Footer Links">
          <button
            type="button"
            className="gov-footer-link-btn"
            onClick={() => setActiveModal("important-links")}
          >
            {t("footer.important_links", "Important Links")}
          </button>
          <span className="gov-footer-sep">|</span>

          <button
            type="button"
            className="gov-footer-link-btn"
            onClick={() => setActiveModal("privacy")}
          >
            {t("footer.privacy_policy", "Privacy Policy")}
          </button>
          <span className="gov-footer-sep">|</span>

          <button
            type="button"
            className="gov-footer-link-btn"
            onClick={() => setActiveModal("terms")}
          >
            {t("footer.terms_of_use", "Terms of Use")}
          </button>
          <span className="gov-footer-sep">|</span>

          <button
            type="button"
            className="gov-footer-link-btn"
            onClick={() => setActiveModal("accessibility")}
          >
            {t("footer.accessibility", "Accessibility")}
          </button>
          <span className="gov-footer-sep">|</span>

          <button
            type="button"
            className="gov-footer-link-btn"
            onClick={() => setActiveModal("sitemap")}
          >
            {t("footer.sitemap", "Sitemap")}
          </button>
          <span className="gov-footer-sep">|</span>

          <button
            type="button"
            className="gov-footer-link-btn"
            onClick={() => setActiveModal("help")}
          >
            {t("footer.help", "Help")}
          </button>
        </div>
      </div>

      {/* Institutional Disclaimer Strip */}
      <div className="gov-footer-sub-bar">
        <div className="gov-footer-sub-container">
          <p className="gov-footer-disclaimer-text">
            {t(
              "footer.disclaimer",
              "AI-Assisted Decision Support System designed for Smart India Hackathon 2026 (SIH26024). All statutory authority resides with authorized human officials under Mines Act 1952."
            )}
          </p>
          <p className="gov-footer-copy-text">
            {t("footer.copyright", "© 2026 Ministry of Coal, Government of India. Project PRITHVI.")}
          </p>
        </div>
      </div>

      {/* Accessible Informational Modal */}
      {activeModal && legalContent[activeModal] && (
        <div className="gov-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div className="gov-modal-box">
            <div className="gov-modal-header">
              <h3 id="modal-title" className="gov-modal-title">
                {legalContent[activeModal].title}
              </h3>
              <button
                type="button"
                className="gov-modal-close-btn"
                onClick={() => setActiveModal(null)}
                aria-label="Close dialog"
              >
                <X size={18} />
              </button>
            </div>
            <div className="gov-modal-body">
              <ul className="gov-modal-list">
                {legalContent[activeModal].content.map((line, idx) => (
                  <li key={idx} className="gov-modal-item">
                    {line.startsWith("• ") || line.includes("https://") ? (
                      line.includes("https://") ? (
                        <a
                          href={line.split(": ")[1]}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="gov-modal-link"
                        >
                          {line} <ExternalLink size={12} className="inline ml-1" />
                        </a>
                      ) : (
                        <span>{line}</span>
                      )
                    ) : (
                      <span>{line}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
            <div className="gov-modal-footer">
              <button
                type="button"
                className="gov-modal-dismiss-btn"
                onClick={() => setActiveModal(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </footer>
  );
};

export default GovernmentFooter;
