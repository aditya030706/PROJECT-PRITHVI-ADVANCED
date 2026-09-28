import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ShieldCheck,
  Leaf,
  ClipboardList,
  FileCheck2,
  BarChart3,
  Building2,
  Users,
  Activity,
  Layers,
  Search,
  AlertTriangle,
  Settings,
  FileText,
  Radio,
  FileSpreadsheet,
  Gavel,
  RefreshCw,
  GitCommit,
  GitBranch,
  HardHat,
  Briefcase,
  UserCheck,
  Compass,
  Cpu,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useRoleSwitch } from "../context/RoleSwitchContext";
import { useLanguage } from "../i18n/LanguageContext";
import {
  fetchHierarchyTree,
  type HierarchyTreeNode,
  type OperationalUnit,
  fetchMineZones,
} from "../api/hierarchy";

export default function PrithviLanding() {
  const { triggerRoleSwitch } = useRoleSwitch();
  const { t } = useLanguage();

  // Dynamic hierarchy state for the Governance Hierarchy section
  const [hierarchyTree, setHierarchyTree] = useState<HierarchyTreeNode[]>([]);
  const [treeLoading, setTreeLoading] = useState<boolean>(true);
  const [treeError, setTreeError] = useState<boolean>(false);

  // Selected nodes for interactive demonstration drill-down
  const [selectedSubsidiary, setSelectedSubsidiary] = useState<HierarchyTreeNode | null>(null);
  const [selectedArea, setSelectedArea] = useState<HierarchyTreeNode | null>(null);
  const [selectedMine, setSelectedMine] = useState<HierarchyTreeNode | null>(null);
  const [selectedMineZones, setSelectedMineZones] = useState<OperationalUnit[]>([]);
  const [zonesLoading, setZonesLoading] = useState<boolean>(false);

  // Hero Visual Slideshow (PM Narendra Modi & Coal Minister G. Kishan Reddy)
  const heroSlides = [
    {
      id: "pm-modi",
      type: "dignitary" as const,
      image: "/pm-narendra-modi.jpg",
      alt: "Hon'ble Prime Minister of India Shri Narendra Modi",
      title: "Shri Narendra Modi",
      role: "Hon'ble Prime Minister of India",
      govHeader: "भारत सरकार | Government of India",
      deptHeader: "Vision for Sustainable Mineral Governance",
      quote: "Technologically empowered, transparent and sustainable mining for an Atmanirbhar Bharat.",
      tagline: "Atmanirbhar Bharat · Sustainable Mining",
      tagColor: "#D97706",
    },
    {
      id: "minister-reddy",
      type: "dignitary" as const,
      image: "/minister-kishan-reddy.jpg",
      alt: "Hon'ble Union Minister of Coal and Mines Shri G. Kishan Reddy",
      title: "Shri G. Kishan Reddy",
      role: "Hon'ble Union Minister of Coal & Mines",
      govHeader: "कोयला मंत्रालय | Ministry of Coal",
      deptHeader: "Government of India",
      quote: "Accelerating digital compliance, mine worker safety, and environmental excellence across all operations.",
      tagline: "Mission PRITHVI · Safe Coal Operations",
      tagColor: "#0284C7",
    },
    {
      id: "minister-dubey",
      type: "dignitary" as const,
      image: "/minister-satish-dubey.jpg",
      alt: "Hon'ble Minister of State for Coal and Mines Shri Satish Chandra Dubey",
      title: "Shri Satish Chandra Dubey",
      role: "Hon'ble Minister of State for Coal & Mines",
      govHeader: "कोयला मंत्रालय | Ministry of Coal",
      deptHeader: "Government of India",
      quote: "Ensuring zero-harm mining environments, workforce welfare, and technologically resilient mineral operations nationwide.",
      tagline: "Safety Standards · Worker Welfare · Sustainable Mines",
      tagColor: "#16A34A",
    },
  ];

  const [currentSlide, setCurrentSlide] = useState<number>(0);

  // Auto-scroll slideshow every 4 seconds as requested by user
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [heroSlides.length]);

  // Load canonical hierarchy from backend on mount
  useEffect(() => {
    loadHierarchy();
  }, []);

  const loadHierarchy = async () => {
    setTreeLoading(true);
    setTreeError(false);
    try {
      const data = await fetchHierarchyTree(undefined, 6);
      setHierarchyTree(data);

      if (data.length > 0) {
        // Find CIL node or top node
        const topNode = data[0];
        const cilNode = topNode.children?.find((c) => c.unit_type === "CIL") || topNode;
        const subs = cilNode.children?.filter((c) => c.unit_type === "SUBSIDIARY") || [];
        
        // Pick BCCL if present, else first subsidiary
        const defaultSub = subs.find((s) => s.code.includes("BCCL")) || subs[0] || null;
        if (defaultSub) {
          setSelectedSubsidiary(defaultSub);
          const areas = defaultSub.children || [];
          const defaultArea = areas[0] || null;
          if (defaultArea) {
            setSelectedArea(defaultArea);
            const mines = defaultArea.children || [];
            const defaultMine = mines[0] || null;
            if (defaultMine) {
              setSelectedMine(defaultMine);
              loadMineZones(defaultMine.code);
            }
          }
        }
      }
    } catch (err) {
      console.error("Failed to load canonical hierarchy tree:", err);
      setTreeError(true);
    } finally {
      setTreeLoading(false);
    }
  };

  const loadMineZones = async (mineCode: string) => {
    setZonesLoading(true);
    try {
      const zones = await fetchMineZones(mineCode);
      setSelectedMineZones(zones);
    } catch (err) {
      console.error("Failed to load mine operational zones:", err);
      setSelectedMineZones([]);
    } finally {
      setZonesLoading(false);
    }
  };

  const handleSelectSubsidiary = (sub: HierarchyTreeNode) => {
    setSelectedSubsidiary(sub);
    const areas = sub.children || [];
    const firstArea = areas[0] || null;
    setSelectedArea(firstArea);
    if (firstArea) {
      const mines = firstArea.children || [];
      const firstMine = mines[0] || null;
      setSelectedMine(firstMine);
      if (firstMine) loadMineZones(firstMine.code);
      else setSelectedMineZones([]);
    } else {
      setSelectedMine(null);
      setSelectedMineZones([]);
    }
  };

  const handleSelectArea = (area: HierarchyTreeNode) => {
    setSelectedArea(area);
    const mines = area.children || [];
    const firstMine = mines[0] || null;
    setSelectedMine(firstMine);
    if (firstMine) loadMineZones(firstMine.code);
    else setSelectedMineZones([]);
  };

  const handleSelectMine = (mine: HierarchyTreeNode) => {
    setSelectedMine(mine);
    loadMineZones(mine.code);
  };

  // Find all available subsidiaries from the tree
  const allSubsidiaries: HierarchyTreeNode[] = [];
  if (hierarchyTree.length > 0) {
    const topNode = hierarchyTree[0];
    const cilNode = topNode.children?.find((c) => c.unit_type === "CIL") || topNode;
    if (cilNode.children) {
      allSubsidiaries.push(...cilNode.children.filter((c) => c.unit_type === "SUBSIDIARY"));
    }
  }

  // 8 Spokes definition matching visual reference slice 2
  const radialSpokes = [
    {
      key: "field",
      title: t("radial.field_title", "FIELD"),
      desc: t("radial.field_desc", "Real-time field & operations"),
      icon: Compass,
      color: "spoke-green",
      positionClass: "spoke-pos-top",
    },
    {
      key: "inspection",
      title: t("radial.inspection_title", "INSPECTION"),
      desc: t("radial.inspection_desc", "Schedules, reports & observations"),
      icon: Search,
      color: "spoke-orange",
      positionClass: "spoke-pos-top-right",
    },
    {
      key: "evidence",
      title: t("radial.evidence_title", "EVIDENCE"),
      desc: t("radial.evidence_desc", "Images, documents & geo-tagged data"),
      icon: BarChart3,
      color: "spoke-darkgreen",
      positionClass: "spoke-pos-right",
    },
    {
      key: "verification",
      title: t("radial.verification_title", "VERIFICATION"),
      desc: t("radial.verification_desc", "Validation & approval"),
      icon: ShieldCheck,
      color: "spoke-purple",
      positionClass: "spoke-pos-bottom-right",
    },
    {
      key: "risk",
      title: t("radial.risk_title", "RISK"),
      desc: t("radial.risk_desc", "Risk assessment & mitigation"),
      icon: AlertTriangle,
      color: "spoke-red",
      positionClass: "spoke-pos-bottom",
    },
    {
      key: "compliance",
      title: t("radial.compliance_title", "COMPLIANCE"),
      desc: t("radial.compliance_desc", "Monitoring & corrective actions"),
      icon: Settings,
      color: "spoke-blue",
      positionClass: "spoke-pos-bottom-left",
    },
    {
      key: "management",
      title: t("radial.management_title", "MANAGEMENT"),
      desc: t("radial.management_desc", "Planning, resources & oversight"),
      icon: Users,
      color: "spoke-amber",
      positionClass: "spoke-pos-left",
    },
    {
      key: "regulatory",
      title: t("radial.regulatory_title", "REGULATORY"),
      desc: t("radial.regulatory_desc", "Acts, rules & statutory compliance"),
      icon: FileText,
      color: "spoke-indigo",
      positionClass: "spoke-pos-top-left",
    },
  ];

  return (
    <div className="landing-gov-page">
      {/* =========================================================
          1. HERO SECTION — EXACT MATCH TO REFERENCE SLICE 1
      ========================================================= */}
      <section className="hero-section-gov" aria-labelledby="hero-title">
        <div className="hero-gov-container">
          {/* Left Column: Eyebrow, Title, Description, Buttons, 3 Badges */}
          <div className="hero-content-left">
            <div className="hero-gov-eyebrow">
              {t("hero.eyebrow", "SUSTAINABLE MINING | SAFE OPERATION | COMPLIANT TOMORROW")}
            </div>

            <h1 id="hero-title" className="hero-gov-title">
              <span>{t("hero.title_part1", "AI-Powered")}</span>
              <span>{t("hero.title_part2", "Mine Compliance & Governance")}</span>
            </h1>

            <p className="hero-gov-desc">
              {t(
                "hero.description",
                "Project PRITHVI provides an integrated platform for monitoring mine inspections, safety compliance, field evidence and regulatory requirements across coal mining operations in India."
              )}
            </p>

            {/* Action Buttons */}
            <div className="hero-gov-actions">
              <Link
                to="/compliance"
                className="hero-btn-red"
                aria-label={t("hero.cta_compliance", "View Compliance Dashboard")}
              >
                <span>{t("hero.cta_compliance", "View Compliance Dashboard")}</span>
                <ArrowRight size={16} />
              </Link>

              <Link
                to="/governance"
                className="hero-btn-outline"
                aria-label={t("hero.cta_explore", "Explore Mines")}
              >
                <span>{t("hero.cta_explore", "Explore Mines")}</span>
                <ArrowRight size={16} />
              </Link>
            </div>

            {/* 3 Circular Badges Row */}
            <div className="hero-badges-row">
              {/* Badge 1: Safer Mines */}
              <div className="hero-badge-circle-item">
                <div className="hero-badge-circle-icon badge-green" aria-hidden="true">
                  <Leaf size={20} />
                </div>
                <div className="hero-badge-circle-texts">
                  <span className="hero-badge-label">{t("vp.safe_mines_title", "Safer Mines")}</span>
                  <span className="hero-badge-sub">{t("vp.safe_mines_sub", "for a Brighter India")}</span>
                </div>
              </div>

              {/* Badge 2: Transparent Governance */}
              <div className="hero-badge-circle-item">
                <div className="hero-badge-circle-icon badge-orange" aria-hidden="true">
                  <Users size={20} />
                </div>
                <div className="hero-badge-circle-texts">
                  <span className="hero-badge-label">{t("vp.transparent_gov_title", "Transparent Governance")}</span>
                  <span className="hero-badge-sub">{t("vp.transparent_gov_sub", "Through Technology")}</span>
                </div>
              </div>

              {/* Badge 3: Sustainable Growth */}
              <div className="hero-badge-circle-item">
                <div className="hero-badge-circle-icon badge-blue" aria-hidden="true">
                  <Settings size={20} />
                </div>
                <div className="hero-badge-circle-texts">
                  <span className="hero-badge-label">{t("vp.sustainable_growth_title", "Sustainable Growth")}</span>
                  <span className="hero-badge-sub">{t("vp.sustainable_growth_sub", "For Future Generations")}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Institutional Leadership & Operations Carousel */}
          <div
            className="hero-visual-right hero-gov-showcase-card"
            aria-label="Government of India Leadership and Active Mining Operations"
            role="region"
          >
            {/* Top Indian Tricolor Strip */}
            <div className="hero-gov-tricolor-strip" aria-hidden="true">
              <span className="strip-saffron" />
              <span className="strip-white" />
              <span className="strip-green" />
            </div>

            <div className="hero-slideshow-container">
              {heroSlides.map((slide, idx) => {
                const isActive = idx === currentSlide;
                return (
                  <div
                    key={slide.id}
                    className={`hero-slide-item ${isActive ? "active" : ""}`}
                    aria-hidden={!isActive}
                  >
                    {slide.type === "dignitary" ? (
                      <div className="hero-gov-dignitary-card">
                        {/* Left Info Column */}
                        <div className="hero-gov-card-info">
                          <div className="hero-gov-card-crest-row">
                            <img
                              src="/ministry-of-coal-official.png"
                              alt="National Emblem of India"
                              className="hero-gov-card-emblem"
                            />
                            <div className="hero-gov-card-crest-text">
                              <span className="hero-gov-card-gov-label">{slide.govHeader}</span>
                              <span className="hero-gov-card-dept-label">{slide.deptHeader}</span>
                            </div>
                          </div>

                          <div className="hero-gov-card-dignitary-details">
                            <span className="hero-gov-card-role" style={{ color: slide.tagColor }}>
                              {slide.role}
                            </span>
                            <h2 className="hero-gov-card-name">
                              {slide.title}
                            </h2>
                            <blockquote className="hero-gov-card-quote">
                              "{slide.quote}"
                            </blockquote>
                          </div>

                          <div className="hero-gov-card-badge">
                            <span
                              className="hero-gov-card-badge-dot"
                              style={{ backgroundColor: slide.tagColor }}
                            />
                            <span>{slide.tagline}</span>
                          </div>
                        </div>

                        {/* Right Portrait Column */}
                        <div className="hero-gov-card-portrait-wrap">
                          <div className="hero-gov-card-portrait-inner">
                            <img
                              src={slide.image}
                              alt={slide.alt}
                              className="hero-gov-card-portrait-img"
                              loading={idx === 0 ? "eager" : "lazy"}
                            />
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* Active Mining Operations Slide */
                      <div className="hero-gov-operations-slide">
                        <img
                          src={slide.image}
                          alt={slide.alt}
                          className="hero-gov-operations-img"
                          loading="lazy"
                        />
                        <div className="hero-gov-operations-overlay">
                          <div className="hero-gov-operations-badge">
                            <Activity size={13} className="gov-pulse-dot text-emerald-400" />
                            <span>LIVE TELEMETRY · KORBA BASIN</span>
                          </div>
                          <div className="hero-gov-operations-details">
                            <h3 className="hero-gov-operations-title">
                              {slide.title}
                            </h3>
                            <p className="hero-gov-operations-sub">
                              {slide.role}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Bottom Controls Bar: Dots + Counter + Arrows */}
            <div className="hero-gov-controls-bar">
              <div className="hero-gov-slide-indicator">
                <span className="hero-gov-slide-num">0{currentSlide + 1}</span>
                <span className="hero-gov-slide-divider">/</span>
                <span className="hero-gov-slide-total">0{heroSlides.length}</span>
              </div>

              <div className="hero-slideshow-dots" role="tablist" aria-label="Slideshow controls">
                {heroSlides.map((slide, idx) => (
                  <button
                    key={slide.id}
                    type="button"
                    className={`hero-slide-dot ${idx === currentSlide ? "active" : ""}`}
                    onClick={() => setCurrentSlide(idx)}
                    aria-label={`Go to slide ${idx + 1}: ${slide.title}`}
                    aria-selected={idx === currentSlide}
                    role="tab"
                  />
                ))}
              </div>

              <div className="hero-gov-nav-arrows">
                <button
                  type="button"
                  className="hero-gov-nav-btn"
                  onClick={() => setCurrentSlide((prev) => (prev - 1 + heroSlides.length) % heroSlides.length)}
                  aria-label="Previous slide"
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  type="button"
                  className="hero-gov-nav-btn"
                  onClick={() => setCurrentSlide((prev) => (prev + 1) % heroSlides.length)}
                  aria-label="Next slide"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          2. CENTRAL RADIAL PRITHVI INTELLIGENCE SECTION — SLICE 2
      ========================================================= */}
      <section className="gov-radial-section" aria-label="PRITHVI Governance Architecture Hub">
        <div className="gov-radial-bg-overlay" />
        <div className="gov-radial-container">
          <div className="gov-radial-wheel-box">
            {/* Center Core Emblem */}
            <div className="gov-radial-center-emblem">
              <div className="gov-radial-emblem-inner">
                <div className="gov-radial-mountain-art" aria-hidden="true">
                  <svg width="60" height="34" viewBox="0 0 60 34" fill="none">
                    <path d="M0 34L18 4L32 26L42 12L60 34H0Z" fill="#FFFFFF" opacity="0.95" />
                    <circle cx="48" cy="28" r="4" fill="#E2E8F0" />
                    <circle cx="54" cy="28" r="3" fill="#E2E8F0" />
                  </svg>
                </div>
                <div className="gov-radial-center-text">
                  <span className="gov-radial-brand-label">SAFE MINES</span>
                  <span className="gov-radial-brand-strong">STRONGER INDIA</span>
                </div>
                {/* Indian Tricolor Underline */}
                <div className="gov-radial-tricolor-line" aria-hidden="true">
                  <span className="line-orange" />
                  <span className="line-white" />
                  <span className="line-green" />
                </div>
              </div>
            </div>

            {/* 8 Radial Spokes Cards */}
            <div className="gov-radial-spokes-grid">
              {radialSpokes.map((spoke) => {
                const Icon = spoke.icon;
                return (
                  <div
                    key={spoke.key}
                    className={`gov-radial-card ${spoke.positionClass}`}
                  >
                    <div className={`gov-radial-card-icon ${spoke.color}`}>
                      <Icon size={18} />
                    </div>
                    <div className="gov-radial-card-content">
                      <h3 className="gov-radial-card-title">{spoke.title}</h3>
                      <p className="gov-radial-card-desc">{spoke.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          3. OPERATIONAL ARCHITECTURE — SLICE 3
      ========================================================= */}
      <section className="gov-arch-section" aria-labelledby="arch-title">
        <div className="gov-arch-bg-overlay" />
        <div className="gov-container relative z-10">
          <div className="gov-section-eyebrow-box">
            <span className="gov-red-bar" />
            <span className="gov-eyebrow-text">{t("arch.eyebrow", "OPERATIONAL ARCHITECTURE")}</span>
          </div>

          <h2 id="arch-title" className="gov-section-main-heading">
            <span className="gov-title-red-bar" />
            {t("arch.title", "From Field Observation to Governance Intelligence")}
          </h2>
          <p className="gov-section-main-sub">
            {t(
              "arch.subtitle",
              "A continuous, reliable chain linking on-site measurements to executive decision-making for safer and more compliant coal mining operations."
            )}
          </p>

          {/* 6 Step Sequence Row (01 to 06) */}
          <div className="gov-six-steps-grid">
            {/* 01 Field Observation */}
            <div className="gov-step-box">
              <div className="gov-step-top">
                <span className="gov-step-number">01</span>
                <div className="gov-step-icon-circle icon-orange-tint">
                  <Compass size={18} />
                </div>
              </div>
              <h3 className="gov-step-label">{t("arch.step1_title", "FIELD OBSERVATION")}</h3>
              <p className="gov-step-desc">
                {t("arch.step1_desc", "Direct sensor & on-site environmental assessment.")}
              </p>
            </div>

            {/* 02 Inspection */}
            <div className="gov-step-box">
              <div className="gov-step-top">
                <span className="gov-step-number">02</span>
                <div className="gov-step-icon-circle icon-orange-tint">
                  <ClipboardList size={18} />
                </div>
              </div>
              <h3 className="gov-step-label">{t("arch.step2_title", "INSPECTION")}</h3>
              <p className="gov-step-desc">
                {t("arch.step2_desc", "Structured statutory checklist execution.")}
              </p>
            </div>

            {/* 03 Evidence */}
            <div className="gov-step-box">
              <div className="gov-step-top">
                <span className="gov-step-number">03</span>
                <div className="gov-step-icon-circle icon-orange-tint">
                  <FileCheck2 size={18} />
                </div>
              </div>
              <h3 className="gov-step-label">{t("arch.step3_title", "EVIDENCE")}</h3>
              <p className="gov-step-desc">
                {t("arch.step3_desc", "Immutable geo-tagged photos & measurement logs.")}
              </p>
            </div>

            {/* 04 Verification */}
            <div className="gov-step-box">
              <div className="gov-step-top">
                <span className="gov-step-number">04</span>
                <div className="gov-step-icon-circle icon-orange-tint">
                  <ShieldCheck size={18} />
                </div>
              </div>
              <h3 className="gov-step-label">{t("arch.step4_title", "VERIFICATION")}</h3>
              <p className="gov-step-desc">
                {t("arch.step4_desc", "Multi-signal anomaly & discrepancy detection.")}
              </p>
            </div>

            {/* 05 Compliance Intelligence */}
            <div className="gov-step-box">
              <div className="gov-step-top">
                <span className="gov-step-number">05</span>
                <div className="gov-step-icon-circle icon-orange-tint">
                  <BarChart3 size={18} />
                </div>
              </div>
              <h3 className="gov-step-label">{t("arch.step5_title", "COMPLIANCE INTELLIGENCE")}</h3>
              <p className="gov-step-desc">
                {t("arch.step5_desc", "Risk aggregation & automated audit prioritization.")}
              </p>
            </div>

            {/* 06 Management / Regulatory Action */}
            <div className="gov-step-box">
              <div className="gov-step-top">
                <span className="gov-step-number">06</span>
                <div className="gov-step-icon-circle icon-orange-tint">
                  <Gavel size={18} />
                </div>
              </div>
              <h3 className="gov-step-label">{t("arch.step6_title", "MANAGEMENT / REGULATORY ACTION")}</h3>
              <p className="gov-step-desc">
                {t("arch.step6_desc", "Corrective work orders, inspections & statutory notices.")}
              </p>
            </div>
          </div>

          {/* 3-Column Layer Architecture: Input Layer -> Intelligence Layer -> Output Layer */}
          <div className="gov-three-layer-layout">
            {/* 1. Input Layer */}
            <div className="gov-layer-card layer-card-input">
              <div className="gov-layer-card-header">
                <span className="gov-layer-kicker">{t("layer.input_title", "INPUT LAYER")}</span>
                <h3 className="gov-layer-title">{t("layer.input_heading", "FIELD DATA")}</h3>
              </div>
              <div className="gov-layer-items-list">
                <div className="gov-layer-item">
                  <div className="gov-layer-item-icon text-amber-600">
                    <Radio size={20} />
                  </div>
                  <div>
                    <h4 className="gov-layer-item-title">{t("layer.input_measurements_title", "Measurements")}</h4>
                    <p className="gov-layer-item-desc">{t("layer.input_measurements_desc", "Sensor telemetry, gas level, ventilation, vibrations")}</p>
                  </div>
                </div>

                <div className="gov-layer-item">
                  <div className="gov-layer-item-icon text-amber-600">
                    <ClipboardList size={20} />
                  </div>
                  <div>
                    <h4 className="gov-layer-item-title">{t("layer.input_checklists_title", "Checklists")}</h4>
                    <p className="gov-layer-item-desc">{t("layer.input_checklists_desc", "Statutory Coal Mines Regulations compliance items")}</p>
                  </div>
                </div>

                <div className="gov-layer-item">
                  <div className="gov-layer-item-icon text-amber-600">
                    <FileCheck2 size={20} />
                  </div>
                  <div>
                    <h4 className="gov-layer-item-title">{t("layer.input_evidence_title", "Evidence")}</h4>
                    <p className="gov-layer-item-desc">{t("layer.input_evidence_desc", "Geo-tagged imagery, audio notes, equipment logs")}</p>
                  </div>
                </div>

                <div className="gov-layer-item">
                  <div className="gov-layer-item-icon text-amber-600">
                    <BarChart3 size={20} />
                  </div>
                  <div>
                    <h4 className="gov-layer-item-title">{t("layer.input_findings_title", "Findings")}</h4>
                    <p className="gov-layer-item-desc">{t("layer.input_findings_desc", "On-site observations & inspector hazard ratings")}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Arrow 1 */}
            <div className="gov-layer-connector-arrow" aria-hidden="true">
              <ArrowRight size={28} className="text-red-700" />
            </div>

            {/* 2. PRITHVI Intelligence Layer */}
            <div className="gov-layer-card layer-card-intelligence">
              <div className="gov-layer-card-header text-center">
                <span className="gov-layer-kicker text-red-800">
                  {t("layer.intelligence_eyebrow", "THE PRITHVI INTELLIGENCE LAYER")}
                </span>
                <h3 className="gov-layer-title text-red-700 font-bold">
                  {t("layer.intelligence_heading", "AI - Assisted. Human - Controlled.")}
                </h3>
                <p className="gov-intelligence-subtext">
                  {t(
                    "layer.intelligence_sub",
                    "PRITHVI augments regulatory review with machine intelligence without removing statutory authority. No automated penalties: all findings escalate to certified human decision-makers."
                  )}
                </p>
              </div>

              <div className="gov-intelligence-inner-box">
                <div className="gov-intelligence-box-head">
                  <div className="gov-mountain-tiny" aria-hidden="true">
                    <svg width="24" height="14" viewBox="0 0 24 14" fill="none">
                      <path d="M0 14L8 1L14 10L18 4L24 14H0Z" fill="#7f1d1d" />
                    </svg>
                  </div>
                  <span className="gov-intelligence-brand-title">PRITHVI</span>
                  <span className="gov-intelligence-brand-sub">MINE COMPLIANCE INTELLIGENCE</span>
                </div>

                <div className="gov-intelligence-signals-list">
                  <div className="gov-intelligence-signal-row">
                    <GitBranch size={16} className="text-red-700 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong>{t("layer.intelligence_sig_title", "Verification Signals")}:</strong>{" "}
                      <span>{t("layer.intelligence_sig_desc", "Authenticates observations & tamper detection")}</span>
                    </div>
                  </div>

                  <div className="gov-intelligence-signal-row">
                    <AlertTriangle size={16} className="text-amber-700 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong>{t("layer.intelligence_risk_title", "Risk Indicators")}:</strong>{" "}
                      <span>{t("layer.intelligence_risk_desc", "Dynamic hazard probability & occurrence weighting")}</span>
                    </div>
                  </div>

                  <div className="gov-intelligence-signal-row">
                    <FileSpreadsheet size={16} className="text-red-700 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong>{t("layer.intelligence_ctx_title", "Compliance Context")}:</strong>{" "}
                      <span>{t("layer.intelligence_ctx_desc", "Historical correlation against DGMS statutory benchmarks")}</span>
                    </div>
                  </div>

                  <div className="gov-intelligence-signal-row">
                    <BarChart3 size={16} className="text-red-700 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong>{t("layer.intelligence_trend_title", "Trend Intelligence")}:</strong>{" "}
                      <span>{t("layer.intelligence_trend_desc", "Predicts safety vectors across mines and regions")}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Arrow 2 */}
            <div className="gov-layer-connector-arrow" aria-hidden="true">
              <ArrowRight size={28} className="text-red-700" />
            </div>

            {/* 3. Output Layer */}
            <div className="gov-layer-card layer-card-output">
              <div className="gov-layer-card-header">
                <span className="gov-layer-kicker">{t("layer.output_title", "OUTPUT LAYER")}</span>
                <h3 className="gov-layer-title">{t("layer.output_heading", "HUMAN DECISION")}</h3>
              </div>
              <div className="gov-layer-items-list">
                <div className="gov-layer-item">
                  <div className="gov-layer-item-icon text-amber-700">
                    <UserCheck size={20} />
                  </div>
                  <div>
                    <h4 className="gov-layer-item-title">{t("layer.output_review_title", "Review")}</h4>
                    <p className="gov-layer-item-desc">{t("layer.output_review_desc", "Mandatory supervisor and manager case sign-off")}</p>
                  </div>
                </div>

                <div className="gov-layer-item">
                  <div className="gov-layer-item-icon text-amber-700">
                    <Settings size={20} />
                  </div>
                  <div>
                    <h4 className="gov-layer-item-title">{t("layer.output_action_title", "Corrective Action")}</h4>
                    <p className="gov-layer-item-desc">{t("layer.output_action_desc", "Binding operational modification directives")}</p>
                  </div>
                </div>

                <div className="gov-layer-item">
                  <div className="gov-layer-item-icon text-amber-700">
                    <RefreshCw size={20} />
                  </div>
                  <div>
                    <h4 className="gov-layer-item-title">{t("layer.output_reinspect_title", "Reinspection")}</h4>
                    <p className="gov-layer-item-desc">{t("layer.output_reinspect_desc", "Targeted physical verification of remediated hazards")}</p>
                  </div>
                </div>

                <div className="gov-layer-item">
                  <div className="gov-layer-item-icon text-amber-700">
                    <FileText size={20} />
                  </div>
                  <div>
                    <h4 className="gov-layer-item-title">{t("layer.output_escalation_title", "Escalation")}</h4>
                    <p className="gov-layer-item-desc">{t("layer.output_escalation_desc", "Formal DGMS statutory notice & enforcement path")}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          4. MULTI-LEVEL GOVERNANCE — SLICE 4
      ========================================================= */}
      <section className="gov-mlg-section" aria-labelledby="mlg-title">
        <div className="gov-container">
          <div className="gov-section-eyebrow-box">
            <span className="gov-orange-dash">—</span>
            <span className="gov-eyebrow-text">{t("mlg.eyebrow", "MULTI-LEVEL GOVERNANCE")}</span>
          </div>

          <h2 id="mlg-title" className="gov-section-main-heading">
            <span className="gov-title-red-bar" />
            {t("mlg.title", "Designed for Multi-Level Governance")}
          </h2>
          <p className="gov-section-main-sub">
            {t("mlg.subtitle", "Segmented role authority delivering unified enterprise and regulatory visibility.")}
          </p>

          <div className="gov-mlg-cards-grid">
            {/* Level 01: Field */}
            <div className="gov-mlg-card">
              <div className="gov-mlg-card-top">
                <div className="gov-mlg-card-icon-box">
                  <HardHat size={28} className="text-amber-800" />
                </div>
                <div className="gov-mlg-card-badge-box">
                  <span className="gov-mlg-level-tag">{t("mlg.card1_badge", "LEVEL 01")}</span>
                  <h3 className="gov-mlg-card-title">{t("mlg.card1_title", "FIELD")}</h3>
                  <span className="gov-mlg-card-sub">{t("mlg.card1_sub", "Operational Data Capture")}</span>
                </div>
              </div>
              <p className="gov-mlg-card-desc">
                {t(
                  "mlg.card1_desc",
                  "Direct operational data capture, inspections, geo-tagged evidence, observations and attendance."
                )}
              </p>
              <div className="gov-mlg-card-action">
                <Link to="/inspections" className="gov-mlg-learn-btn">
                  <span>{t("mlg.learn_more", "Learn More →")}</span>
                </Link>
              </div>
              <div className="gov-mlg-card-progress progress-level-1" />
            </div>

            {/* Level 02: Mine */}
            <div className="gov-mlg-card">
              <div className="gov-mlg-card-top">
                <div className="gov-mlg-card-icon-box">
                  <Building2 size={28} className="text-amber-800" />
                </div>
                <div className="gov-mlg-card-badge-box">
                  <span className="gov-mlg-level-tag">{t("mlg.card2_badge", "LEVEL 02")}</span>
                  <h3 className="gov-mlg-card-title">{t("mlg.card2_title", "MINE")}</h3>
                  <span className="gov-mlg-card-sub">{t("mlg.card2_sub", "Compliance Management")}</span>
                </div>
              </div>
              <p className="gov-mlg-card-desc">
                {t(
                  "mlg.card2_desc",
                  "Compliance management, inspection tracking, safety monitoring, corrective action and operational governance."
                )}
              </p>
              <div className="gov-mlg-card-action">
                <button
                  type="button"
                  className="gov-mlg-learn-btn bg-transparent border-none p-0 cursor-pointer text-left"
                  onClick={() => triggerRoleSwitch("MINE_MANAGER")}
                >
                  <span>{t("mlg.learn_more", "Learn More →")}</span>
                </button>
              </div>
              <div className="gov-mlg-card-progress progress-level-2" />
            </div>

            {/* Level 03: Corporate */}
            <div className="gov-mlg-card">
              <div className="gov-mlg-card-top">
                <div className="gov-mlg-card-icon-box">
                  <Building2 size={28} className="text-amber-800" />
                </div>
                <div className="gov-mlg-card-badge-box">
                  <span className="gov-mlg-level-tag">{t("mlg.card3_badge", "LEVEL 03")}</span>
                  <h3 className="gov-mlg-card-title">{t("mlg.card3_title", "CORPORATE")}</h3>
                  <span className="gov-mlg-card-sub">{t("mlg.card3_sub", "Enterprise Risk Visibility")}</span>
                </div>
              </div>
              <p className="gov-mlg-card-desc">
                {t(
                  "mlg.card3_desc",
                  "Multi-mine/subsidiary performance, risk aggregation, compliance trends, production governance and strategic oversight."
                )}
              </p>
              <div className="gov-mlg-card-action">
                <Link to="/corporate" className="gov-mlg-learn-btn">
                  <span>{t("mlg.learn_more", "Learn More →")}</span>
                </Link>
              </div>
              <div className="gov-mlg-card-progress progress-level-3" />
            </div>

            {/* Level 04: Regulatory */}
            <div className="gov-mlg-card">
              <div className="gov-mlg-card-top">
                <div className="gov-mlg-card-icon-box">
                  <Gavel size={28} className="text-amber-800" />
                </div>
                <div className="gov-mlg-card-badge-box">
                  <span className="gov-mlg-level-tag">{t("mlg.card4_badge", "LEVEL 04")}</span>
                  <h3 className="gov-mlg-card-title">{t("mlg.card4_title", "REGULATORY")}</h3>
                  <span className="gov-mlg-card-sub">{t("mlg.card4_sub", "Audit & Enforcement")}</span>
                </div>
              </div>
              <p className="gov-mlg-card-desc">
                {t(
                  "mlg.card4_desc",
                  "Statutory audit oversight, safety standard compliance, and regulatory enforcement tracking."
                )}
              </p>
              <div className="gov-mlg-card-progress progress-level-4" />
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          5. NEW MANDATORY SECTION: GOVERNANCE HIERARCHY
          (From National Governance to Mine-Level Operations)
      ========================================================= */}
      <section className="gov-hierarchy-showcase-section" aria-labelledby="hierarchy-heading">
        <div className="gov-container">
          <div className="gov-section-eyebrow-box">
            <span className="gov-orange-dash">—</span>
            <span className="gov-eyebrow-text">{t("hierarchy.eyebrow", "GOVERNANCE HIERARCHY")}</span>
          </div>

          <div className="gov-hierarchy-header-flex">
            <div>
              <h2 id="hierarchy-heading" className="gov-section-main-heading">
                <span className="gov-title-red-bar" />
                {t("hierarchy.title", "From National Governance to Mine-Level Operations")}
              </h2>
              <p className="gov-section-main-sub">
                {t(
                  "hierarchy.subtitle",
                  "PRITHVI connects regulatory oversight, corporate governance, mine operations, workforce and field activities through a single traceable organizational structure."
                )}
              </p>
            </div>

            <div className="gov-hierarchy-header-cta">
              <Link to="/governance" className="gov-btn-hierarchy-cta">
                <span>{t("hierarchy.cta_explore", "Explore Governance Hierarchy →")}</span>
              </Link>
            </div>
          </div>

          {/* Canonical Hierarchy Diagram & Operational Branching */}
          <div className="gov-hierarchy-grid">
            {/* Left Box: The Canonical Vertical Spine + Underground vs Opencast Subdivision */}
            <div className="gov-hierarchy-spine-card">
              <div className="gov-hierarchy-card-header">
                <GitCommit size={18} className="text-red-700" />
                <h3 className="gov-hierarchy-card-title">
                  {t("hierarchy.chain_title", "Authoritative Organizational Backbone")}
                </h3>
              </div>

              {/* Vertical Traceable Spine */}
              <div className="gov-spine-flow">
                <div className="gov-spine-node node-ministry">
                  <span className="gov-node-badge">GOVERNMENT</span>
                  <span className="gov-node-name">{t("hierarchy.level_ministry", "MINISTRY OF COAL")}</span>
                </div>
                <div className="gov-spine-arrow">↓</div>

                <div className="gov-spine-node node-cil">
                  <span className="gov-node-badge">HOLDING CO</span>
                  <span className="gov-node-name">{t("hierarchy.level_cil", "COAL INDIA LIMITED")}</span>
                </div>
                <div className="gov-spine-arrow">↓</div>

                <div className="gov-spine-node node-subsidiary">
                  <span className="gov-node-badge">SUBSIDIARY</span>
                  <span className="gov-node-name">{t("hierarchy.level_subsidiary", "CIL ENTITY / SUBSIDIARY")}</span>
                </div>
                <div className="gov-spine-arrow">↓</div>

                <div className="gov-spine-node node-area">
                  <span className="gov-node-badge">OPERATIONAL AREA</span>
                  <span className="gov-node-name">{t("hierarchy.level_area", "AREA")}</span>
                </div>
                <div className="gov-spine-arrow">↓</div>

                <div className="gov-spine-node node-mine">
                  <span className="gov-node-badge">COLLIERY</span>
                  <span className="gov-node-name">{t("hierarchy.level_mine", "MINE / PROJECT")}</span>
                </div>
                <div className="gov-spine-arrow">↓</div>

                <div className="gov-spine-node node-opunit">
                  <span className="gov-node-badge">FIELD UNIT</span>
                  <span className="gov-node-name">{t("hierarchy.level_operational_unit", "OPERATIONAL UNIT")}</span>
                </div>
              </div>

              {/* Critical Rule Note: Mine Type is a property, not a node */}
              <div className="gov-mine-type-explainer">
                <p className="gov-explainer-note">
                  {t(
                    "hierarchy.mine_type_notice",
                    "Mine Type (Underground / Opencast) is an intrinsic property of the Mine, determining its statutory operational structure:"
                  )}
                </p>

                <div className="gov-branches-container">
                  {/* Underground Operational Structure */}
                  <div className="gov-branch-box branch-underground">
                    <div className="gov-branch-header">
                      <Layers size={15} className="text-amber-700" />
                      <h4 className="gov-branch-title">{t("hierarchy.underground_title", "UNDERGROUND OPERATIONAL STRUCTURE")}</h4>
                    </div>
                    <div className="gov-branch-tree">
                      <div className="gov-branch-level">Shaft / Incline</div>
                      <div className="gov-branch-sub">└── Ventilation District</div>
                      <div className="gov-branch-sub-2">└── Panel</div>
                      <div className="gov-branch-sub-3">└── Section</div>
                      <div className="gov-branch-sub-4">└── Working Face</div>
                    </div>
                  </div>

                  {/* Opencast Operational Structure */}
                  <div className="gov-branch-box branch-opencast">
                    <div className="gov-branch-header">
                      <HardHat size={15} className="text-blue-700" />
                      <h4 className="gov-branch-title">{t("hierarchy.opencast_title", "OPENCAST OPERATIONAL STRUCTURE")}</h4>
                    </div>
                    <div className="gov-branch-tree">
                      <div className="gov-branch-level">Pit</div>
                      <div className="gov-branch-sub">└── Bench</div>
                      <div className="gov-branch-sub-2">├── Haul Road</div>
                      <div className="gov-branch-sub-2">├── Dump / Stock</div>
                      <div className="gov-branch-sub-2">└── HEMM Park</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Box: Relational Governance Associations & Interactive Live Drill-Down */}
            <div className="gov-hierarchy-interactive-card">
              {/* Relational Governance Bindings Box */}
              <div className="gov-relational-bindings-card">
                <div className="gov-hierarchy-card-header">
                  <Briefcase size={18} className="text-red-700" />
                  <div>
                    <h3 className="gov-hierarchy-card-title">{t("hierarchy.relations_title", "Relational Governance Bindings")}</h3>
                    <p className="gov-hierarchy-card-subtitle">{t("hierarchy.relations_desc", "Commercial contracts, contractors, and workforce rosters attach relationally to the Mine node rather than forming organizational levels:")}</p>
                  </div>
                </div>

                <div className="gov-relational-tags-grid">
                  <div className="gov-rel-tag">
                    <Briefcase size={13} className="text-amber-700" />
                    <span>{t("hierarchy.rel_contracts", "Commercial & MDO Contracts")}</span>
                  </div>
                  <div className="gov-rel-tag">
                    <Users size={13} className="text-blue-700" />
                    <span>{t("hierarchy.rel_workforce", "Supervisors, Operators & Sirdars")}</span>
                  </div>
                  <div className="gov-rel-tag">
                    <Activity size={13} className="text-emerald-700" />
                    <span>{t("hierarchy.rel_activities", "Shift Muster & Field Operations")}</span>
                  </div>
                  <div className="gov-rel-tag">
                    <ClipboardList size={13} className="text-purple-700" />
                    <span>{t("hierarchy.rel_inspections", "Statutory CMR Checklists & Evidence")}</span>
                  </div>
                  <div className="gov-rel-tag">
                    <Radio size={13} className="text-indigo-700" />
                    <span>{t("hierarchy.rel_telemetry", "IoT Atmospheric & SCADA Telemetry")}</span>
                  </div>
                  <div className="gov-rel-tag">
                    <FileSpreadsheet size={13} className="text-rose-700" />
                    <span>{t("hierarchy.rel_cases", "Discrepancy Cases & Corrective Actions")}</span>
                  </div>
                  <div className="gov-rel-tag">
                    <Gavel size={13} className="text-red-700" />
                    <span>{t("hierarchy.rel_dgms", "DGMS Regional Directives & S.22 Gates")}</span>
                  </div>
                </div>
              </div>

              {/* Live Hierarchy Drill-Down Selector */}
              <div className="gov-live-drilldown-card">
                <div className="gov-hierarchy-card-header">
                  <Cpu size={18} className="text-red-700" />
                  <div>
                    <h3 className="gov-hierarchy-card-title">
                      {t("hierarchy.live_drilldown_title", "Interactive Live Hierarchy Drill-Down")}
                    </h3>
                    <p className="gov-hierarchy-card-subtitle">
                      {t(
                        "hierarchy.live_drilldown_desc",
                        "Querying canonical Task 11 API records. Select an administrative node to inspect structural lineage and operational subdivisions:"
                      )}
                    </p>
                  </div>
                </div>

                {treeLoading && (
                  <div className="gov-drilldown-loading">
                    <RefreshCw size={18} className="animate-spin text-red-700" />
                    <span>{t("hierarchy.loading", "Loading canonical governance hierarchy from master...")}</span>
                  </div>
                )}

                {treeError && (
                  <div className="gov-drilldown-error">
                    <AlertTriangle size={18} className="text-red-600" />
                    <span>{t("hierarchy.error", "Governance hierarchy data is temporarily unavailable.")}</span>
                    <button type="button" className="gov-btn-retry" onClick={loadHierarchy}>
                      {t("hierarchy.retry", "Retry")}
                    </button>
                  </div>
                )}

                {!treeLoading && !treeError && allSubsidiaries.length === 0 && (
                  <div className="gov-drilldown-empty">
                    <span>{t("hierarchy.empty", "No governance units are currently available for this scope.")}</span>
                  </div>
                )}

                {!treeLoading && !treeError && allSubsidiaries.length > 0 && (
                  <div className="gov-drilldown-content">
                    {/* Subsidiary Pills */}
                    <div className="gov-picker-row">
                      <span className="gov-picker-label">{t("hierarchy.level_subsidiary", "Subsidiary")}:</span>
                      <div className="gov-pills-list">
                        {allSubsidiaries.map((sub) => (
                          <button
                            key={sub.id}
                            type="button"
                            className={`gov-pill-btn ${selectedSubsidiary?.id === sub.id ? "active" : ""}`}
                            onClick={() => handleSelectSubsidiary(sub)}
                          >
                            {sub.code.replace("ORG-SUBSIDIARY-", "")}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Area Pills */}
                    {selectedSubsidiary && (
                      <div className="gov-picker-row">
                        <span className="gov-picker-label">{t("hierarchy.level_area", "Area")}:</span>
                        <div className="gov-pills-list">
                          {(selectedSubsidiary.children || []).map((area) => (
                            <button
                              key={area.id}
                              type="button"
                              className={`gov-pill-btn ${selectedArea?.id === area.id ? "active" : ""}`}
                              onClick={() => handleSelectArea(area)}
                            >
                              {area.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Mine Selector & Details */}
                    {selectedArea && (
                      <div className="gov-picker-row">
                        <span className="gov-picker-label">{t("hierarchy.level_mine", "Mine")}:</span>
                        <div className="gov-pills-list">
                          {(selectedArea.children || []).map((mine) => (
                            <button
                              key={mine.id}
                              type="button"
                              className={`gov-pill-btn ${selectedMine?.id === mine.id ? "active" : ""}`}
                              onClick={() => handleSelectMine(mine)}
                            >
                              {mine.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Selected Mine Detailed Lineage Card */}
                    {selectedMine && (
                      <div className="gov-selected-mine-dossier">
                        <div className="gov-mine-dossier-top">
                          <div>
                            <span className="gov-mine-stat-label">{t("hierarchy.selected_unit", "Selected Colliery")}:</span>
                            <h4 className="gov-mine-name-heading">{selectedMine.name}</h4>
                          </div>
                          <div className="gov-mine-badges-group">
                            <span className="gov-code-badge">
                              {selectedMine.code}
                            </span>
                            <span className={`gov-type-badge ${selectedMine.mine_profile?.mine_type === "UNDERGROUND" ? "badge-underground" : "badge-opencast"}`}>
                              {selectedMine.mine_profile?.mine_type || "UNDERGROUND"}
                            </span>
                          </div>
                        </div>

                        {/* Lineage Trail */}
                        <div className="gov-mine-lineage-trail">
                          <span className="gov-lineage-label">{t("hierarchy.lineage_path", "Lineage")}:</span>
                          <span className="gov-lineage-path">
                            Ministry of Coal › Coal India Limited › {selectedSubsidiary?.name} › {selectedArea?.name} › <strong>{selectedMine.name}</strong>
                          </span>
                        </div>

                        {/* Operational Subdivisions for this mine */}
                        <div className="gov-mine-zones-box">
                          <div className="gov-zones-header">
                            <span className="gov-zones-title">
                              {selectedMine.mine_profile?.mine_type === "UNDERGROUND"
                                ? "Underground Operational Subdivisions (Shafts, Ventilation Districts, Panels, Faces)"
                                : "Opencast Operational Subdivisions (Pits, Benches, Haul Roads, HEMM Parks)"}
                            </span>
                            {zonesLoading && <RefreshCw size={12} className="animate-spin text-gray-500" />}
                          </div>

                          <div className="gov-zones-tags-list">
                            {selectedMineZones.length > 0 ? (
                              selectedMineZones.map((zone) => (
                                <span key={zone.id} className="gov-zone-pill">
                                  <span className="zone-type">{zone.unit_type}:</span> {zone.name}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-gray-500 italic">
                                {zonesLoading ? "Loading operational subdivisions..." : "Standard operational units configured in canonical master."}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="gov-dossier-action-row">
                          <Link to="/governance" className="gov-btn-enter-hierarchy">
                            <span>Open in Governance Master Console →</span>
                          </Link>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          6. ROLE WORKSPACE GATEWAYS — SLICE 5
      ========================================================= */}
      <section className="gov-roles-section" aria-labelledby="roles-heading">
        <div className="gov-container">
          <div className="gov-section-eyebrow-box">
            <span className="gov-orange-dash">—</span>
            <span className="gov-eyebrow-text">{t("roles.eyebrow", "ROLE ARCHITECTURE")}</span>
          </div>

          <h2 id="roles-heading" className="gov-section-main-heading">
            <span className="gov-title-red-bar" />
            {t("roles.heading", "ENTER OPERATIONAL CONTEXT")}
          </h2>
          <p className="gov-section-main-sub">
            {t(
              "roles.subtitle",
              "Enter PRITHVI through the workspace corresponding to your operational responsibility."
            )}
          </p>

          <div className="gov-roles-cards-grid">
            {/* 1. Field Inspector */}
            <div className="gov-official-role-card">
              <div className="gov-role-card-top-icon text-amber-700">
                <ClipboardList size={26} />
              </div>
              <h3 className="gov-official-role-title">
                {t("roles.field_inspector", "FIELD INSPECTOR")}
              </h3>
              <p className="gov-official-role-desc">
                {t(
                  "roles.field_inspector_desc",
                  "Conduct on-site inspections, capture field measurements and evidence, record findings and submit inspection reports."
                )}
              </p>
              <div className="gov-official-role-footer">
                <button
                  type="button"
                  className="gov-btn-enter-workspace"
                  onClick={() => triggerRoleSwitch("FIELD_INSPECTOR")}
                  aria-label="Enter Field Inspector Workspace"
                >
                  <span>{t("roles.enter_workspace", "ENTER WORKSPACE →")}</span>
                </button>
              </div>
            </div>

            {/* 2. Mine Supervisor */}
            <div className="gov-official-role-card">
              <div className="gov-role-card-top-icon text-amber-700">
                <Users size={26} />
              </div>
              <h3 className="gov-official-role-title">
                {t("roles.mine_supervisor", "MINE SUPERVISOR")}
              </h3>
              <p className="gov-official-role-desc">
                {t(
                  "roles.mine_supervisor_desc",
                  "Manage workforce, ensure safety compliance, track inspections and oversee operational activities."
                )}
              </p>
              <div className="gov-official-role-footer">
                <button
                  type="button"
                  className="gov-btn-enter-workspace"
                  onClick={() => triggerRoleSwitch("MINE_SUPERVISOR")}
                  aria-label="Enter Mine Supervisor Workspace"
                >
                  <span>{t("roles.enter_workspace", "ENTER WORKSPACE →")}</span>
                </button>
              </div>
            </div>

            {/* 3. Mine Manager */}
            <div className="gov-official-role-card">
              <div className="gov-role-card-top-icon text-amber-700">
                <Building2 size={26} />
              </div>
              <h3 className="gov-official-role-title">
                {t("roles.mine_manager", "MINE MANAGER")}
              </h3>
              <p className="gov-official-role-desc">
                {t(
                  "roles.mine_manager_desc",
                  "Monitor mine compliance, inspection status, corrective actions and management reports."
                )}
              </p>
              <div className="gov-official-role-footer">
                <button
                  type="button"
                  className="gov-btn-enter-workspace"
                  onClick={() => triggerRoleSwitch("MINE_MANAGER")}
                  aria-label="Enter Mine Manager Workspace"
                >
                  <span>{t("roles.enter_workspace", "ENTER WORKSPACE →")}</span>
                </button>
              </div>
            </div>

            {/* 4. Corporate Management */}
            <div className="gov-official-role-card">
              <div className="gov-role-card-top-icon text-red-700">
                <BarChart3 size={26} />
              </div>
              <h3 className="gov-official-role-title">
                {t("roles.corporate_management", "CORPORATE MANAGEMENT")}
              </h3>
              <p className="gov-official-role-desc">
                {t(
                  "roles.corporate_management_desc",
                  "Monitor subsidiary performance, analyse risk trends, and drive strategic decisions across mines."
                )}
              </p>
              <div className="gov-official-role-footer">
                <button
                  type="button"
                  className="gov-btn-enter-workspace"
                  onClick={() => triggerRoleSwitch("CORPORATE_MANAGEMENT")}
                  aria-label="Enter Corporate Management Workspace"
                >
                  <span>{t("roles.enter_workspace", "ENTER WORKSPACE →")}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
