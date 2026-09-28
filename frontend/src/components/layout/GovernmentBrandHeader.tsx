import React from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "../../i18n/LanguageContext";

export const GovernmentBrandHeader: React.FC = () => {
  const { lang, t } = useLanguage();

  return (
    <header className="gov-brand-header" role="banner">
      <div className="gov-brand-container">
        {/* Left: Ministry of Coal / Government of India Emblem */}
        <div className="gov-brand-left">
          <Link to="/landing" className="gov-emblem-link" title="Ministry of Coal, Government of India">
            <img
              src="/ministry-of-coal-official.png"
              alt="Ministry of Coal, Government of India - Ashoka Stambh"
              className="gov-ministry-emblem-img"
            />
          </Link>
        </div>

        {/* Center: PROJECT PRITHVI - 100% Crisp Native Vector Typography */}
        <div className="gov-brand-center">
          <Link to="/landing" className="gov-prithvi-brand" title="Project PRITHVI Home">
            <div className="gov-prithvi-title-cluster">
              <div className="gov-prithvi-header-top-row">
                <img
                  src="/prithvi-mountain.svg"
                  alt="PRITHVI Crest"
                  className="gov-mountain-mark-img"
                />
                <h1 className="gov-prithvi-main-title">
                  <span className="gov-prithvi-prefix">{lang === "hi" ? "परियोजना" : "PROJECT"}</span>
                  <span className="gov-prithvi-highlight">{lang === "hi" ? "पृथ्वी" : "PRITHVI"}</span>
                </h1>
              </div>
              <p className="gov-prithvi-tagline">
                {lang === "hi"
                  ? "कोयला खदानों के लिए एआई-आधारित स्मार्ट गवर्नेंस और अनुपालन निगरानी प्रणाली"
                  : "AI-BASED SMART GOVERNANCE AND COMPLIANCE MONITORING SYSTEM FOR COAL MINES"}
              </p>
            </div>
          </Link>
        </div>

        {/* Right: Government Initiatives Cluster (Crisp Infinite-Resolution Vector SVGs) */}
        <div className="gov-brand-right">
          <div className="gov-initiatives-cluster">
            <a
              href="https://swachhbharatmission.ddws.gov.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="gov-initiative-link gov-swachh-bharat-wrapper"
              title="Swachh Bharat Mission"
            >
              <img
                src="/swachh-bharat.svg"
                alt={t("header.swachh_bharat_alt", "Swachh Bharat - Ek Kadam Swachhata Ki Ore")}
                className="gov-initiative-img gov-swachh-bharat-img"
              />
            </a>
            <a
              href="https://pmgatishakti.gov.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="gov-initiative-link gov-gatishakti-wrapper"
              title="PM GatiShakti National Master Plan"
            >
              <img
                src="/pm-gatishakti.svg"
                alt={t("header.pm_gatishakti_alt", "PM GatiShakti National Master Plan")}
                className="gov-initiative-img gov-gatishakti-img"
              />
            </a>
            <a
              href="https://www.digitalindia.gov.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="gov-initiative-link gov-digital-india-wrapper"
              title="Digital India - Power To Empower"
            >
              <img
                src="/digital-india.svg"
                alt={t("header.digital_india_alt", "Digital India - Power To Empower")}
                className="gov-initiative-img gov-digital-india-img"
              />
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};

export default GovernmentBrandHeader;
