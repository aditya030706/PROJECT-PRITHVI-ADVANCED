import React, { createContext, useContext, useState, useEffect } from "react";

export type Language = "en" | "hi";

interface LanguageContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string, fallback?: string) => string;
}

const STORAGE_KEY = "prithvi_language";

export const TRANSLATIONS: Record<Language, Record<string, string>> = {
  en: {
    // Utility Bar
    "util.gov_india": "Government of India",
    "util.bharat_sarkar": "भारत सरकार",
    "util.ministry_of_coal": "Ministry of Coal",
    "util.skip_to_main": "Skip to main content",
    "util.screen_reader": "Screen Reader Access",
    "util.font_decrease": "Decrease font size",
    "util.font_normal": "Normal font size",
    "util.font_increase": "Increase font size",
    "util.switch_lang": "हिंदी",
    "util.search_placeholder": "Search mines, areas, subsidiaries...",
    "util.role": "ROLE",
    "util.search_no_results": "No matching governance units found.",
    "util.search_error": "Governance search is temporarily unavailable.",
    "util.search_enter_hint": "Type at least 2 characters to search canonical hierarchy...",

    // Brand Header
    "header.ministry_hi": "कोयला मंत्रालय",
    "header.ministry_en": "Ministry of Coal",
    "header.gov_india": "Government of India",
    "header.project_prefix": "PROJECT",
    "header.project_name": "PRITHVI",
    "header.flagship_title": "AI-BASED SMART GOVERNANCE AND COMPLIANCE MONITORING SYSTEM FOR COAL MINES",
    "header.sih_title": "SMART INDIA HACKATHON 2026",
    "header.sih_code": "SIH26024 · COAL MONITORING",
    "header.swachh_bharat_alt": "Swachh Bharat - Ek Kadam Swachhata Ki Ore",
    "header.pm_gatishakti_alt": "PM GatiShakti National Master Plan",
    "header.digital_india_alt": "Digital India - Power To Empower",

    // Navigation Bar
    "nav.home": "HOME",
    "nav.governance": "GOVERNANCE",
    "nav.compliance": "COMPLIANCE",
    "nav.safety_risk": "SAFETY / RISK",
    "nav.inspections": "INSPECTIONS",
    "nav.production": "PRODUCTION",
    "nav.attendance": "ATTENDANCE",
    "nav.about": "ABOUT PRITHVI",
    "nav.evidence_chain": "EVIDENCE AUDIT CHAIN",
    "nav.system_overview": "SYSTEM OVERVIEW",
    "nav.scada_online": "SCADA SIMULATION ONLINE",

    // Hero Section
    "hero.eyebrow": "SUSTAINABLE MINING | SAFE OPERATION | COMPLIANT TOMORROW",
    "hero.title_part1": "AI-Powered",
    "hero.title_part2": "Mine Compliance & Governance",
    "hero.description":
      "Project PRITHVI provides an integrated platform for monitoring mine inspections, safety compliance, field evidence and regulatory requirements across coal mining operations in India.",
    "hero.cta_compliance": "View Compliance Dashboard",
    "hero.cta_explore": "Explore Mines",
    "hero.image_caption": "Heavy Earth Moving Machinery at Indian Opencast Coal Mine",

    // Value Propositions
    "vp.safe_mines_title": "Safe Mines",
    "vp.safe_mines_sub": "For a Brighter India",
    "vp.transparent_gov_title": "Transparent Governance",
    "vp.transparent_gov_sub": "Through Technology",
    "vp.sustainable_growth_title": "Sustainable Growth",
    "vp.sustainable_growth_sub": "For Future Generations",

    // Radial Intelligence Section
    "radial.center_title": "PRITHVI",
    "radial.center_sub": "SAFE MINES STRONGER INDIA",
    "radial.field_title": "FIELD",
    "radial.field_desc": "Real-time field & operations",
    "radial.inspection_title": "INSPECTION",
    "radial.inspection_desc": "Schedules, reports & observations",
    "radial.evidence_title": "EVIDENCE",
    "radial.evidence_desc": "Images, documents & geo-tagged data",
    "radial.verification_title": "VERIFICATION",
    "radial.verification_desc": "Validation & approval",
    "radial.risk_title": "RISK",
    "radial.risk_desc": "Risk assessment & mitigation",
    "radial.compliance_title": "COMPLIANCE",
    "radial.compliance_desc": "Monitoring & corrective actions",
    "radial.management_title": "MANAGEMENT",
    "radial.management_desc": "Planning, resources & oversight",
    "radial.regulatory_title": "REGULATORY",
    "radial.regulatory_desc": "Acts, rules & statutory compliance",

    // Operational Architecture
    "arch.eyebrow": "OPERATIONAL ARCHITECTURE",
    "arch.title": "From Field Observation to Governance Intelligence",
    "arch.subtitle":
      "A continuous, reliable chain linking on-site measurements to executive decision-making for safer and more compliant coal mining operations.",
    "arch.step1_title": "FIELD OBSERVATION",
    "arch.step1_desc": "Direct sensor & on-site environmental assessment.",
    "arch.step2_title": "INSPECTION",
    "arch.step2_desc": "Structured statutory checklist execution.",
    "arch.step3_title": "EVIDENCE",
    "arch.step3_desc": "Immutable geo-tagged photos & measurement logs.",
    "arch.step4_title": "VERIFICATION",
    "arch.step4_desc": "Multi-signal anomaly & discrepancy detection.",
    "arch.step5_title": "COMPLIANCE INTELLIGENCE",
    "arch.step5_desc": "Risk aggregation & automated audit prioritization.",
    "arch.step6_title": "MANAGEMENT / REGULATORY ACTION",
    "arch.step6_desc": "Corrective work orders, inspections & statutory notices.",

    // 3 Layer Architecture
    "layer.input_title": "INPUT LAYER",
    "layer.input_heading": "FIELD DATA",
    "layer.input_measurements_title": "Measurements",
    "layer.input_measurements_desc": "Sensor telemetry, gas level, ventilation, vibrations",
    "layer.input_checklists_title": "Checklists",
    "layer.input_checklists_desc": "Statutory Coal Mines Regulations compliance items",
    "layer.input_evidence_title": "Evidence",
    "layer.input_evidence_desc": "Geo-tagged imagery, audio notes, equipment logs",
    "layer.input_findings_title": "Findings",
    "layer.input_findings_desc": "On-site observations & inspector hazard ratings",

    "layer.intelligence_eyebrow": "THE PRITHVI INTELLIGENCE LAYER",
    "layer.intelligence_heading": "AI - Assisted. Human - Controlled.",
    "layer.intelligence_sub":
      "PRITHVI augments regulatory review with machine intelligence without removing statutory authority. No automated penalties: all findings escalate to certified human decision-makers.",
    "layer.intelligence_box_title": "PRITHVI MINE COMPLIANCE INTELLIGENCE",
    "layer.intelligence_sig_title": "Verification Signals",
    "layer.intelligence_sig_desc": "Authenticates observations & tamper detection",
    "layer.intelligence_risk_title": "Risk Indicators",
    "layer.intelligence_risk_desc": "Dynamic hazard probability & occurrence weighting",
    "layer.intelligence_ctx_title": "Compliance Context",
    "layer.intelligence_ctx_desc": "Historical correlation against DGMS statutory benchmarks",
    "layer.intelligence_trend_title": "Trend Intelligence",
    "layer.intelligence_trend_desc": "Predicts safety vectors across mines and regions",

    "layer.output_title": "OUTPUT LAYER",
    "layer.output_heading": "HUMAN DECISION",
    "layer.output_review_title": "Review",
    "layer.output_review_desc": "Mandatory supervisor and manager case sign-off",
    "layer.output_action_title": "Corrective Action",
    "layer.output_action_desc": "Binding operational modification directives",
    "layer.output_reinspect_title": "Reinspection",
    "layer.output_reinspect_desc": "Targeted physical verification of remediated hazards",
    "layer.output_escalation_title": "Escalation",
    "layer.output_escalation_desc": "Formal DGMS statutory notice & enforcement path",

    // Multi-Level Governance
    "mlg.eyebrow": "MULTI-LEVEL GOVERNANCE",
    "mlg.title": "Designed for Multi-Level Governance",
    "mlg.subtitle": "Segmented role authority delivering unified enterprise and regulatory visibility.",
    "mlg.card1_badge": "LEVEL 01",
    "mlg.card1_title": "FIELD",
    "mlg.card1_sub": "Operational Data Capture",
    "mlg.card1_desc":
      "Direct operational data capture, inspections, geo-tagged evidence, observations and attendance.",
    "mlg.card2_badge": "LEVEL 02",
    "mlg.card2_title": "MINE",
    "mlg.card2_sub": "Compliance Management",
    "mlg.card2_desc":
      "Compliance management, inspection tracking, safety monitoring, corrective action and operational governance.",
    "mlg.card3_badge": "LEVEL 03",
    "mlg.card3_title": "CORPORATE",
    "mlg.card3_sub": "Enterprise Risk Visibility",
    "mlg.card3_desc":
      "Multi-mine/subsidiary performance, risk aggregation, compliance trends, production governance and strategic oversight.",
    "mlg.card4_badge": "LEVEL 04",
    "mlg.card4_title": "REGULATORY",
    "mlg.card4_sub": "Audit & Enforcement",
    "mlg.card4_desc":
      "Statutory audit oversight, safety standard compliance, and regulatory enforcement tracking.",
    "mlg.learn_more": "Learn More →",

    // Governance Hierarchy (Mandatory Addition)
    "hierarchy.eyebrow": "GOVERNANCE HIERARCHY",
    "hierarchy.title": "From National Governance to Mine-Level Operations",
    "hierarchy.subtitle":
      "PRITHVI connects regulatory oversight, corporate governance, mine operations, workforce and field activities through a single traceable organizational structure.",
    "hierarchy.cta_explore": "Explore Governance Hierarchy →",
    "hierarchy.chain_title": "Authoritative Organizational Backbone",
    "hierarchy.level_ministry": "MINISTRY OF COAL",
    "hierarchy.level_cil": "COAL INDIA LIMITED",
    "hierarchy.level_subsidiary": "CIL ENTITY / SUBSIDIARY",
    "hierarchy.level_area": "AREA",
    "hierarchy.level_mine": "MINE / PROJECT",
    "hierarchy.level_operational_unit": "OPERATIONAL UNIT",
    "hierarchy.mine_type_notice":
      "Mine Type (Underground / Opencast) is an intrinsic property of the Mine, determining its statutory operational structure:",
    "hierarchy.underground_title": "UNDERGROUND OPERATIONAL STRUCTURE",
    "hierarchy.underground_flow": "Shaft / Incline → Ventilation District → Panel → Section → Working Face",
    "hierarchy.opencast_title": "OPENCAST OPERATIONAL STRUCTURE",
    "hierarchy.opencast_flow": "Pit → Bench → (Haul Road · Dump / Stock · HEMM Park)",
    "hierarchy.relations_title": "Relational Governance Bindings",
    "hierarchy.relations_desc":
      "Commercial contracts, contractors, and workforce rosters attach relationally to the Mine node rather than forming organizational levels:",
    "hierarchy.rel_contracts": "Commercial & MDO Contracts",
    "hierarchy.rel_workforce": "Supervisors, Operators & Mining Sirdars",
    "hierarchy.rel_activities": "Shift Muster & GPS Field Operations",
    "hierarchy.rel_inspections": "Statutory CMR Checklists & Evidence",
    "hierarchy.rel_telemetry": "IoT Atmospheric & Mechanical Telemetry",
    "hierarchy.rel_cases": "Discrepancy Cases & Corrective Actions",
    "hierarchy.rel_dgms": "DGMS Regional Directives & S.22 Prohibition Gates",
    "hierarchy.live_drilldown_title": "Interactive Live Hierarchy Drill-Down",
    "hierarchy.live_drilldown_desc":
      "Querying canonical Task 11 API records. Select an administrative node to inspect structural lineage and operational subdivisions:",
    "hierarchy.loading": "Loading canonical governance hierarchy from master...",
    "hierarchy.error": "Governance hierarchy data is temporarily unavailable.",
    "hierarchy.retry": "Retry",
    "hierarchy.empty": "No governance units are currently available for this scope.",
    "hierarchy.selected_unit": "Selected Governance Node",
    "hierarchy.statutory_code": "Statutory Code",
    "hierarchy.type": "Type",
    "hierarchy.status": "Status",
    "hierarchy.lineage_path": "Traceable Governance Lineage",

    // Role Architecture
    "roles.eyebrow": "ROLE ARCHITECTURE",
    "roles.heading": "ENTER OPERATIONAL CONTEXT",
    "roles.subtitle": "Enter PRITHVI through the workspace corresponding to your operational responsibility.",
    "roles.field_inspector": "FIELD INSPECTOR",
    "roles.field_inspector_desc":
      "Conduct on-site inspections, capture field measurements and evidence, record findings and submit inspection reports.",
    "roles.mine_supervisor": "MINE SUPERVISOR",
    "roles.mine_supervisor_desc":
      "Manage workforce, ensure safety compliance, track inspections and oversee operational activities.",
    "roles.mine_manager": "MINE MANAGER",
    "roles.mine_manager_desc":
      "Monitor mine compliance, inspection status, corrective actions and management reports.",
    "roles.dgms_officer": "DGMS OFFICER",
    "roles.dgms_officer_desc":
      "Audit mine compliance, assess regional risk, review notifications and statutory enforcement.",
    "roles.corporate_management": "CORPORATE MANAGEMENT",
    "roles.corporate_management_desc":
      "Monitor subsidiary performance, analyse risk trends, and drive strategic decisions across mines.",
    "roles.enter_workspace": "ENTER WORKSPACE →",

    // Footer
    "footer.moc_hi": "कोयला मंत्रालय",
    "footer.moc_en": "MINISTRY OF COAL",
    "footer.gov_hi": "भारत सरकार",
    "footer.gov_en": "GOVERNMENT OF INDIA",
    "footer.important_links": "Important Links",
    "footer.privacy_policy": "Privacy Policy",
    "footer.terms_of_use": "Terms of Use",
    "footer.accessibility": "Accessibility",
    "footer.sitemap": "Sitemap",
    "footer.help": "Help",
    "footer.copyright": "© 2026 Ministry of Coal, Government of India. Project PRITHVI.",
    "footer.disclaimer":
      "AI-Assisted Decision Support System designed for Smart India Hackathon 2026 (SIH26024). All statutory authority resides with authorized human officials under Mines Act 1952.",
  },
  hi: {
    // Utility Bar
    "util.gov_india": "भारत सरकार",
    "util.bharat_sarkar": "भारत सरकार",
    "util.ministry_of_coal": "कोयला मंत्रालय",
    "util.skip_to_main": "मुख्य सामग्री पर जाएं",
    "util.screen_reader": "स्क्रीन रीडर एक्सेस",
    "util.font_decrease": "फ़ॉन्ट का आकार घटाएं",
    "util.font_normal": "सामान्य फ़ॉन्ट आकार",
    "util.font_increase": "फ़ॉन्ट का आकार बढ़ाएं",
    "util.switch_lang": "English",
    "util.search_placeholder": "खदानें, क्षेत्र, सहायक कंपनियां खोजें...",
    "util.role": "भूमिका",
    "util.search_no_results": "कोई मेल खाने वाली अभिशासन इकाई नहीं मिली।",
    "util.search_error": "अभिशासन खोज वर्तमान में अनुपलब्ध है।",
    "util.search_enter_hint": "प्रामाणिक पदानुक्रम में खोजने के लिए कम से कम 2 अक्षर टाइप करें...",

    // Brand Header
    "header.ministry_hi": "कोयला मंत्रालय",
    "header.ministry_en": "Ministry of Coal",
    "header.gov_india": "भारत सरकार",
    "header.project_prefix": "परियोजना",
    "header.project_name": "पृथ्वी",
    "header.flagship_title": "कोयला खदानों के लिए एआई-आधारित स्मार्ट अभिशासन एवं अनुपालन निगरानी प्रणाली",
    "header.sih_title": "स्मार्ट इंडिया हैकथॉन 2026",
    "header.sih_code": "SIH26024 · कोयला निगरानी",
    "header.swachh_bharat_alt": "स्वच्छ भारत - एक कदम स्वच्छता की ओर",
    "header.pm_gatishakti_alt": "पीएम गतिशक्ति - राष्ट्रीय मास्टर प्लान",
    "header.digital_india_alt": "डिजिटल इंडिया - सशक्तिकरण की शक्ति",

    // Navigation Bar
    "nav.home": "मुख्य पृष्ठ",
    "nav.governance": "अभिशासन",
    "nav.compliance": "अनुपालन",
    "nav.safety_risk": "सुरक्षा एवं जोखिम",
    "nav.inspections": "निरीक्षण",
    "nav.production": "उत्पादन",
    "nav.attendance": "उपस्थिति",
    "nav.about": "पृथ्वी के बारे में",
    "nav.evidence_chain": "साक्ष्य ऑडिट श्रृंखला",
    "nav.system_overview": "प्रणाली अवलोकन",
    "nav.scada_online": "स्काडा सिमुलेशन ऑनलाइन",

    // Hero Section
    "hero.eyebrow": "सतत खनन | सुरक्षित संचालन | अनुपालनशील कल",
    "hero.title_part1": "एआई-संचालित",
    "hero.title_part2": "खान अनुपालन एवं अभिशासन",
    "hero.description":
      "परियोजना पृथ्वी भारत में कोयला खनन कार्यों में खान निरीक्षण, सुरक्षा अनुपालन, फील्ड साक्ष्य और विनियामक आवश्यकताओं की निगरानी के लिए एक एकीकृत मंच प्रदान करती है।",
    "hero.cta_compliance": "अनुपालन डैशबोर्ड देखें",
    "hero.cta_explore": "खदानें देखें",
    "hero.image_caption": "भारतीय ओपनकास्ट कोयला खदान में भारी अर्थ मूविंग मशीनरी (HEMM)",

    // Value Propositions
    "vp.safe_mines_title": "सुरक्षित खदानें",
    "vp.safe_mines_sub": "उज्ज्वल भारत के लिए",
    "vp.transparent_gov_title": "पारदर्शी अभिशासन",
    "vp.transparent_gov_sub": "प्रौद्योगिकी के माध्यम से",
    "vp.sustainable_growth_title": "सतत विकास",
    "vp.sustainable_growth_sub": "भावी पीढ़ियों के लिए",

    // Radial Intelligence Section
    "radial.center_title": "पृथ्वी",
    "radial.center_sub": "सुरक्षित खदानें मजबूत भारत",
    "radial.field_title": "फ़ील्ड",
    "radial.field_desc": "वास्तविक समय फील्ड संचालन",
    "radial.inspection_title": "निरीक्षण",
    "radial.inspection_desc": "अनुसूचियां, रिपोर्ट एवं प्रेक्षण",
    "radial.evidence_title": "साक्ष्य",
    "radial.evidence_desc": "छवियां, दस्तावेज एवं जियो-टैग डेटा",
    "radial.verification_title": "सत्यापन",
    "radial.verification_desc": "सत्यापन एवं अनुमोदन",
    "radial.risk_title": "जोखिम",
    "radial.risk_desc": "जोखिम मूल्यांकन एवं शमन",
    "radial.compliance_title": "अनुपालन",
    "radial.compliance_desc": "निगरानी एवं सुधारात्मक कार्रवाई",
    "radial.management_title": "प्रबंधन",
    "radial.management_desc": "योजना, संसाधन एवं पर्यवेक्षण",
    "radial.regulatory_title": "विनियामक",
    "radial.regulatory_desc": "अधिनियम, नियम एवं वैधानिक अनुपालन",

    // Operational Architecture
    "arch.eyebrow": "परिचालन वास्तुकला",
    "arch.title": "फील्ड प्रेक्षण से अभिशासन आसूचना तक",
    "arch.subtitle":
      "सुरक्षित और अधिक अनुपालनशील कोयला खनन कार्यों के लिए ऑन-साइट मापों को कार्यकारी निर्णय लेने से जोड़ने वाली एक सतत, विश्वसनीय श्रृंखला।",
    "arch.step1_title": "फ़ील्ड प्रेक्षण",
    "arch.step1_desc": "प्रत्यक्ष सेंसर एवं ऑन-साइट पर्यावरणीय मूल्यांकन।",
    "arch.step2_title": "निरीक्षण",
    "arch.step2_desc": "संरचित वैधानिक चेकलिस्ट निष्पादन।",
    "arch.step3_title": "साक्ष्य",
    "arch.step3_desc": "अपरिवर्तनीय जियो-टैग्ड तस्वीरें और माप लॉग।",
    "arch.step4_title": "सत्यापन",
    "arch.step4_desc": "बहु-संकेत विसंगति एवं विचलन पहचान।",
    "arch.step5_title": "अनुपालन आसूचना",
    "arch.step5_desc": "जोखिम एकत्रीकरण एवं स्वचालित ऑडिट प्राथमिकता।",
    "arch.step6_title": "प्रबंधन / विनियामक कार्रवाई",
    "arch.step6_desc": "सुधारात्मक कार्य आदेश, निरीक्षण एवं वैधानिक नोटिस।",

    // 3 Layer Architecture
    "layer.input_title": "इनपुट लेयर",
    "layer.input_heading": "फ़ील्ड डेटा",
    "layer.input_measurements_title": "माप",
    "layer.input_measurements_desc": "सेंसर टेलीमेट्री, गैस स्तर, वेंटिलेशन, कंपन",
    "layer.input_checklists_title": "चेकलिस्ट",
    "layer.input_checklists_desc": "वैधानिक कोयला खान विनियम अनुपालन मदें",
    "layer.input_evidence_title": "साक्ष्य",
    "layer.input_evidence_desc": "जियो-टैग्ड इमेजरी, ऑडियो नोट्स, उपकरण लॉग",
    "layer.input_findings_title": "निष्कर्ष",
    "layer.input_findings_desc": "ऑन-साइट प्रेक्षण और निरीक्षक खतरा रेटिंग",

    "layer.intelligence_eyebrow": "पृथ्वी आसूचना लेयर",
    "layer.intelligence_heading": "एआई-सहायता प्राप्त। मानव-नियंत्रित।",
    "layer.intelligence_sub":
      "पृथ्वी वैधानिक अधिकार को हटाए बिना मशीन आसूचना के साथ विनियामक समीक्षा को सुदृढ़ करती है। कोई स्वचालित दंड नहीं: सभी निष्कर्ष प्रमाणित मानव निर्णयकर्ताओं को अग्रेषित होते हैं।",
    "layer.intelligence_box_title": "पृथ्वी खान अनुपालन आसूचना",
    "layer.intelligence_sig_title": "सत्यापन संकेत",
    "layer.intelligence_sig_desc": "प्रेक्षणों एवं छेड़छाड़ पहचान का प्रमाणीकरण",
    "layer.intelligence_risk_title": "जोखिम संकेतक",
    "layer.intelligence_risk_desc": "गतिशील खतरा संभावना एवं आवृत्ति भारांक",
    "layer.intelligence_ctx_title": "अनुपालन संदर्भ",
    "layer.intelligence_ctx_desc": "डीजीएमएस वैधानिक मानकों के विरुद्ध ऐतिहासिक सहसंबंध",
    "layer.intelligence_trend_title": "प्रवृत्ति आसूचना",
    "layer.intelligence_trend_desc": "खदानों और क्षेत्रों में सुरक्षा रुझानों का पूर्वानुमान",

    "layer.output_title": "आउटपुट लेयर",
    "layer.output_heading": "मानव निर्णय",
    "layer.output_review_title": "समीक्षा",
    "layer.output_review_desc": "अनिवार्य पर्यवेक्षक एवं प्रबंधक प्रकरण अनुमोदन",
    "layer.output_action_title": "सुधारात्मक कार्रवाई",
    "layer.output_action_desc": "बाध्यकारी परिचालन संशोधन निर्देश",
    "layer.output_reinspect_title": "पुनः निरीक्षण",
    "layer.output_reinspect_desc": "सुधारे गए खतरों का लक्षित भौतिक सत्यापन",
    "layer.output_escalation_title": "अग्रसारण",
    "layer.output_escalation_desc": "औपचारिक डीजीएमएस वैधानिक नोटिस एवं प्रवर्तन मार्ग",

    // Multi-Level Governance
    "mlg.eyebrow": "बहु-स्तरीय अभिशासन",
    "mlg.title": "बहु-स्तरीय अभिशासन के लिए अभिकल्पित",
    "mlg.subtitle": "एकीकृत उद्यम और विनियामक दृश्यता प्रदान करने वाला खंडित भूमिका अधिकार।",
    "mlg.card1_badge": "स्तर 01",
    "mlg.card1_title": "फ़ील्ड",
    "mlg.card1_sub": "परिचालन डेटा संग्रह",
    "mlg.card1_desc":
      "प्रत्यक्ष परिचालन डेटा संग्रह, निरीक्षण, जियो-टैग साक्ष्य, प्रेक्षण और उपस्थिति।",
    "mlg.card2_badge": "स्तर 02",
    "mlg.card2_title": "खान",
    "mlg.card2_sub": "अनुपालन प्रबंधन",
    "mlg.card2_desc":
      "अनुपालन प्रबंधन, निरीक्षण ट्रैकिंग, सुरक्षा निगरानी, सुधारात्मक कार्रवाई और परिचालन अभिशासन।",
    "mlg.card3_badge": "स्तर 03",
    "mlg.card3_title": "कॉर्पोरेट",
    "mlg.card3_sub": "उद्यम जोखिम दृश्यता",
    "mlg.card3_desc":
      "बहु-खान/सहायक कंपनी प्रदर्शन, जोखिम एकत्रीकरण, अनुपालन रुझान, उत्पादन अभिशासन और रणनीतिक पर्यवेक्षण।",
    "mlg.card4_badge": "स्तर 04",
    "mlg.card4_title": "विनियामक",
    "mlg.card4_sub": "ऑडिट एवं प्रवर्तन",
    "mlg.card4_desc":
      "वैधानिक पर्यवेक्षण, सुरक्षा मानक अनुपालन, और विनियामक प्रवर्तन ट्रैकिंग।",
    "mlg.learn_more": "और जानें →",

    // Governance Hierarchy (Mandatory Addition)
    "hierarchy.eyebrow": "अभिशासन पदानुक्रम",
    "hierarchy.title": "राष्ट्रीय अभिशासन से खान-स्तरीय संचालन तक",
    "hierarchy.subtitle":
      "पृथ्वी विनियामक पर्यवेक्षण, कॉर्पोरेट अभिशासन, खान संचालन, कार्यबल और फील्ड गतिविधियों को एक एकल अनुरेखणीय संगठनात्मक संरचना के माध्यम से जोड़ती है।",
    "hierarchy.cta_explore": "अभिशासन पदानुक्रम देखें →",
    "hierarchy.chain_title": "प्रामाणिक संगठनात्मक रीढ़",
    "hierarchy.level_ministry": "कोयला मंत्रालय",
    "hierarchy.level_cil": "कोल इंडिया लिमिटेड",
    "hierarchy.level_subsidiary": "सीआईएल अनुषंगी कंपनी / इकाई",
    "hierarchy.level_area": "क्षेत्र (Area)",
    "hierarchy.level_mine": "खान / परियोजना",
    "hierarchy.level_operational_unit": "परिचालन इकाई",
    "hierarchy.mine_type_notice":
      "खान का प्रकार (भूमिगत / ओपनकास्ट) खान की एक आंतरिक विशेषता है, जो इसकी वैधानिक परिचालन संरचना निर्धारित करती है:",
    "hierarchy.underground_title": "भूमिगत परिचालन संरचना",
    "hierarchy.underground_flow": "शाफ्ट / इनक्लाइन → वेंटिलेशन डिस्ट्रिक्ट → पैनल → सेक्शन → वर्किंग फेस",
    "hierarchy.opencast_title": "ओपनकास्ट परिचालन संरचना",
    "hierarchy.opencast_flow": "पिट → बेंच → (ढुलाई मार्ग · डंप / स्टॉक · एचईएमएम पार्क)",
    "hierarchy.relations_title": "संबंधित अभिशासन संबंध",
    "hierarchy.relations_desc":
      "वाणिज्यिक अनुबंध, संविदाकार और कार्यबल संगठनात्मक स्तर बनने के बजाय खान नोड से संबंधात्मक रूप से जुड़े होते हैं:",
    "hierarchy.rel_contracts": "वाणिज्यिक एवं एमडीओ अनुबंध",
    "hierarchy.rel_workforce": "पर्यवेक्षक, ऑपरेटर एवं माइनिंग सरदार",
    "hierarchy.rel_activities": "शिफ्ट मस्टर एवं जीपीएस फील्ड संचालन",
    "hierarchy.rel_inspections": "वैधानिक सीएमआर चेकलिस्ट एवं साक्ष्य",
    "hierarchy.rel_telemetry": "आईओटी वायुमंडलीय एवं यांत्रिक टेलीमेट्री",
    "hierarchy.rel_cases": "विसंगति प्रकरण एवं सुधारात्मक कार्रवाइयां",
    "hierarchy.rel_dgms": "डीजीएमएस क्षेत्रीय निर्देश एवं धारा 22 निषेध आदेश",
    "hierarchy.live_drilldown_title": "इंटरैक्टिव लाइव पदानुक्रम अन्वेषण",
    "hierarchy.live_drilldown_desc":
      "टास्क 11 एपीआई रिकॉर्ड से प्रामाणिक डेटा। संरचनात्मक वंशावली और परिचालन उप-विभाजनों का निरीक्षण करने के लिए एक नोड चुनें:",
    "hierarchy.loading": "मास्टर डेटाबेस से प्रामाणिक अभिशासन पदानुक्रम लोड हो रहा है...",
    "hierarchy.error": "अभिशासन पदानुक्रम डेटा वर्तमान में अनुपलब्ध है।",
    "hierarchy.retry": "पुनः प्रयास करें",
    "hierarchy.empty": "इस दायरे के लिए वर्तमान में कोई अभिशासन इकाइयां उपलब्ध नहीं हैं।",
    "hierarchy.selected_unit": "चयनित अभिशासन नोड",
    "hierarchy.statutory_code": "वैधानिक कोड",
    "hierarchy.type": "प्रकार",
    "hierarchy.status": "स्थिति",
    "hierarchy.lineage_path": "अनुरेखणीय अभिशासन वंशावली",

    // Role Architecture
    "roles.eyebrow": "भूमिका वास्तुकला",
    "roles.heading": "परिचालन संदर्भ में प्रवेश करें",
    "roles.subtitle": "अपनी परिचालन जिम्मेदारी के अनुरूप कार्यक्षेत्र के माध्यम से पृथ्वी में प्रवेश करें।",
    "roles.field_inspector": "फ़ील्ड इंस्पेक्टर",
    "roles.field_inspector_desc":
      "ऑन-साइट निरीक्षण करें, फ़ील्ड माप और साक्ष्य कैप्चर करें, निष्कर्ष दर्ज करें और निरीक्षण रिपोर्ट जमा करें।",
    "roles.mine_supervisor": "माइन सुपरवाइजर",
    "roles.mine_supervisor_desc":
      "कार्यबल का प्रबंधन करें, सुरक्षा अनुपालन सुनिश्चित करें, निरीक्षणों को ट्रैक करें और परिचालन गतिविधियों की देखरेख करें।",
    "roles.mine_manager": "माइन मैनेजर",
    "roles.mine_manager_desc":
      "खान अनुपालन, निरीक्षण स्थिति, सुधारात्मक कार्रवाइयों और प्रबंधन रिपोर्टों की निगरानी करें।",
    "roles.dgms_officer": "डीजीएमएस अधिकारी",
    "roles.dgms_officer_desc":
      "खान अनुपालन का ऑडिट करें, क्षेत्रीय जोखिम का आकलन करें, अधिसूचनाओं और वैधानिक प्रवर्तन की समीक्षा करें।",
    "roles.corporate_management": "कॉर्पोरेट प्रबंधन",
    "roles.corporate_management_desc":
      "सहायक कंपनियों के प्रदर्शन की निगरानी करें, जोखिम प्रवृत्तियों का विश्लेषण करें, और खदानों में रणनीतिक निर्णय लें।",
    "roles.enter_workspace": "कार्यक्षेत्र में प्रवेश करें →",

    // Footer
    "footer.moc_hi": "कोयला मंत्रालय",
    "footer.moc_en": "MINISTRY OF COAL",
    "footer.gov_hi": "भारत सरकार",
    "footer.gov_en": "GOVERNMENT OF INDIA",
    "footer.important_links": "महत्वपूर्ण कड़ियाँ",
    "footer.privacy_policy": "गोपनीयता नीति",
    "footer.terms_of_use": "उपयोग की शर्तें",
    "footer.accessibility": "सुगमता (Accessibility)",
    "footer.sitemap": "साइटमैप",
    "footer.help": "सहायता",
    "footer.copyright": "© 2026 कोयला मंत्रालय, भारत सरकार। परियोजना पृथ्वी।",
    "footer.disclaimer":
      "स्मार्ट इंडिया हैकथॉन 2026 (SIH26024) के लिए अभिकल्पित एआई-सहायता प्राप्त निर्णय समर्थन प्रणाली। खान अधिनियम 1952 के तहत सभी वैधानिक अधिकार अधिकृत मानव अधिकारियों के पास सुरक्षित हैं।",
  },
};

const LanguageContext = createContext<LanguageContextType>({
  lang: "en",
  setLang: () => {},
  t: (key: string, fallback?: string) => fallback || key,
});

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Language>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "hi" || saved === "en") return saved;
    } catch {
      // ignore
    }
    return "en";
  });

  const setLang = (nextLang: Language) => {
    setLangState(nextLang);
    try {
      localStorage.setItem(STORAGE_KEY, nextLang);
      document.documentElement.lang = nextLang;
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const t = (key: string, fallback?: string): string => {
    const dict = TRANSLATIONS[lang];
    if (dict && dict[key]) {
      return dict[key];
    }
    const enDict = TRANSLATIONS["en"];
    if (enDict && enDict[key]) {
      return enDict[key];
    }
    return fallback || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
export default LanguageContext;
