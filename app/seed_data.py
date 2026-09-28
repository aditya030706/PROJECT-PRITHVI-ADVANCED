"""
PRITHVI Feature 1 — Authoritative Regulatory / Inspection Seed Data.

Contains the 13 statutory inspection templates, regulatory obligations,
schedule rules, and mine profiles for the Jharia Underground Demonstration Mine
under the Coal Mines Regulations, 2017.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from .models import (
    ChecklistItem,
    EvidenceRequirement,
    EvidenceType,
    InspectionTemplate,
    MeasurementDefinition,
    Mine,
    MineType,
    GassyDegree,
    RegulatoryObligation,
    RegulatorySource,
    RegulatoryScheduleRule,
    ScheduleFrequencyType,
    ScheduleUnit,
    ProductionRecord,
    ProductionTarget,
    ProductionSource,
    ContractType,
    ProductionOperationType,
    ProductionRecordStatus,
    OrganizationUnit,
    OrganizationUnitType,
    OperationalUnit,
    OperationalUnitType,
    ContractorMaster,
    ContractorType,
    ContractMaster,
    WorkerMaster,
    WorkerType,
    EnvironmentalDomain,
    EnvironmentalSourceType,
    DataQualityStatus,
    EnvironmentalParameter,
    EnvironmentalMeasurement,
    EnvironmentalThreshold,
    EnvironmentalObligation,
    EnvironmentalSchedule,
    EnvironmentalReport,
    Finding,
    ComplianceCase,
    CaseSourceType,
    CaseStatus,
    CorrectiveAction,
)
from . import database as db
from .production_service import record_production_event
from .schemas import ProductionRecordCreate


def load_mine_seed() -> None:
    """
    Load realistic demonstration mine profiles for the PRITHVI prototype.
    """
    mines = [
        Mine(
            mine_id="MINE-BCCL-JHARIA-01",
            name="Jharia Underground Demonstration Mine",
            subsidiary="BCCL",
            state="Jharkhand",
            district="Dhanbad",
            mine_type=MineType.UNDERGROUND_COAL,
            mining_method="Underground bord and pillar",
            gassy_degree=GassyDegree.DEGREE_II,
            mechanised=True,
            uses_hemm=True,
            has_winding_installation=True,
            blasting_operation=True,
            active=True,
            organization_unit_id="ORG-MINE-BCCL-JHARIA-UG",
        ),
        Mine(
            mine_id="MINE-ECL-RANIGANJ-01",
            name="Raniganj Underground Demonstration Mine",
            subsidiary="ECL",
            state="West Bengal",
            district="Paschim Bardhaman",
            mine_type=MineType.UNDERGROUND_COAL,
            mining_method="Underground mechanised mining",
            gassy_degree=GassyDegree.DEGREE_I,
            mechanised=True,
            uses_hemm=False,
            has_winding_installation=True,
            blasting_operation=True,
            active=True,
            organization_unit_id="ORG-MINE-ECL-RANIGANJ-UG",
        ),
        Mine(
            mine_id="MINE-MCL-TALCHER-01",
            name="Talcher Opencast Demonstration Mine",
            subsidiary="MCL",
            state="Odisha",
            district="Angul",
            mine_type=MineType.OPENCAST_COAL,
            mining_method="Opencast mechanised mining",
            gassy_degree=GassyDegree.NOT_APPLICABLE,
            mechanised=True,
            uses_hemm=True,
            has_winding_installation=False,
            blasting_operation=True,
            active=True,
            organization_unit_id="ORG-MINE-MCL-TALCHER-OC",
        ),
        Mine(
            mine_id="MINE-SECL-GEVRA-01",
            name="Gevra Opencast Demonstration Mine",
            subsidiary="SECL",
            state="Chhattisgarh",
            district="Korba",
            mine_type=MineType.OPENCAST_COAL,
            mining_method="Opencast mechanised continuous mining",
            gassy_degree=GassyDegree.NOT_APPLICABLE,
            mechanised=True,
            uses_hemm=True,
            has_winding_installation=False,
            blasting_operation=True,
            active=True,
            organization_unit_id="ORG-MINE-SECL-GEVRA-OC",
        ),
    ]

    for mine in mines:
        db.save_mine(mine)
        if "JHARIA" in mine.mine_id:
            db.update_mine_hierarchy_info(mine.mine_id, "AREA-BCCL-JHARIA", "Jharia Area")
        elif "RANIGANJ" in mine.mine_id:
            db.update_mine_hierarchy_info(mine.mine_id, "AREA-ECL-RANIGANJ", "Raniganj Area")
        elif "TALCHER" in mine.mine_id:
            db.update_mine_hierarchy_info(mine.mine_id, "AREA-MCL-TALCHER", "Talcher Area")
        elif "GEVRA" in mine.mine_id:
            db.update_mine_hierarchy_info(mine.mine_id, "AREA-SECL-GEVRA", "Gevra Area")


def load_regulatory_seed() -> None:
    """
    Load the regulatory source, obligations, and the 13 statutory inspection templates.
    """
    # Deactivate obsolete prototype template and rules if previously inserted
    conn = db._connect()
    conn.execute("UPDATE inspection_templates SET active = 0 WHERE template_id = 'INS-VENT-GAS-001'")
    conn.execute("UPDATE regulatory_schedule_rules SET active = 0 WHERE template_id = 'INS-VENT-GAS-001'")
    conn.execute("UPDATE mine_inspection_schedules SET active = 0 WHERE schedule_id NOT IN (SELECT schedule_id FROM regulatory_schedule_rules WHERE active = 1)")
    conn.commit()
    conn.close()

    cmr_source = RegulatorySource(
        source_id="SRC-CMR-2017",
        title="Coal Mines Regulations, 2017",
        regulation_number=None,
        chapter=None,
        description="Coal Mines Regulations, 2017 issued under the Mines Act, 1952.",
        source_document="Coal Mines Regulations, 2017",
        source_reference="Gazette of India, Extraordinary, Part II, Section 3, Sub-section (i)",
    )
    db.save_regulatory_source(cmr_source)

    # ----------------------------------------------------
    # OBLIGATIONS
    # ----------------------------------------------------
    obligations = [
        RegulatoryObligation(
            obligation_id="CMR-119",
            regulation=cmr_source,
            title="Pre-Shift Examinations of Workings",
            requirement_type="Periodic examination",
            requirement="Competent person shall examine every part of the mine in which persons have to work or pass before commencement of work in a shift.",
            applicability="Underground coal workings",
            frequency_or_trigger="Within 2 hours before commencement of each shift",
            responsible_role="Overman / Deputy",
            required_record_or_evidence="Pre-shift gas and ventilation examination report",
        ),
        RegulatoryObligation(
            obligation_id="CMR-156",
            regulation=cmr_source,
            title="Ventilation Surveys and Measurements",
            requirement_type="Measurement / survey",
            requirement="Ventilation officer shall measure air quantity, velocity, humidity, and gas concentrations at designated stations.",
            applicability="Underground ventilating districts",
            frequency_or_trigger="Weekly measurements and monthly complete survey",
            responsible_role="Ventilation Officer",
            required_record_or_evidence="Ventilation survey book and ventilation district plans",
        ),
        RegulatoryObligation(
            obligation_id="CMR-75",
            regulation=cmr_source,
            title="Examination of Shafts and Guides",
            requirement_type="Examination",
            requirement="Shaft guides, headgear, conductors, and shaft walls shall be examined at least once in every seven days.",
            applicability="Shafts in use for raising/lowering persons or material",
            frequency_or_trigger="Once at least in every seven days",
            responsible_role="Winding Engineer + Overman",
            required_record_or_evidence="Shaft examination statutory register",
        ),
        RegulatoryObligation(
            obligation_id="CMR-76-80",
            regulation=cmr_source,
            title="Winding Installations, Safety Catches and Brakes",
            requirement_type="Mechanical testing",
            requirement="Examine and test winding ropes, brakes, depth indicators, automatic contrivances, and overwind preventers.",
            applicability="Winding installations",
            frequency_or_trigger="Monthly thorough examination and testing",
            responsible_role="Winding Engineer + Electrical Engineer",
            required_record_or_evidence="Winding installation test and examination record",
        ),
        RegulatoryObligation(
            obligation_id="CMR-160-170",
            regulation=cmr_source,
            title="Electrical Apparatus, Flameproof Enclosures and Earthing",
            requirement_type="Electrical safety",
            requirement="All apparatus, conductors, earthing systems, and flameproof enclosures must be tested and inspected.",
            applicability="All underground electrical installations and machinery",
            frequency_or_trigger="Weekly continuity/earth test and monthly thorough inspection",
            responsible_role="Electrical Engineer",
            required_record_or_evidence="Electrical statutory inspection log and insulation tests",
        ),
        RegulatoryObligation(
            obligation_id="CMR-135",
            regulation=cmr_source,
            title="Heavy Earth Moving Machinery & Mechanised Equipment",
            requirement_type="Pre-start and periodic inspection",
            requirement="Pre-shift walkaround and functional check of HEMM safety devices, plus weekly mechanical examination.",
            applicability="Mechanised coal mines using HEMM",
            frequency_or_trigger="Every shift prior to operation; weekly mechanical inspection",
            responsible_role="HEMM Operator / Mechanical Engineer",
            required_record_or_evidence="HEMM pre-start log sheet and maintenance register",
        ),
        RegulatoryObligation(
            obligation_id="CMR-155-158",
            regulation=cmr_source,
            title="Drilling, Charging, Blasting and Post-Shot Inspection",
            requirement_type="Safety procedure",
            requirement="Pre-blast methane check, danger zone evacuation, post-blast waiting period, misfire examination, and smoke clearance.",
            applicability="Mines with blasting operations",
            frequency_or_trigger="Before and immediately after every blasting round",
            responsible_role="Blasting Supervisor / Safety Officer",
            required_record_or_evidence="Blasting log, shot-firer register, misfire log",
        ),
        RegulatoryObligation(
            obligation_id="CMR-85-95",
            regulation=cmr_source,
            title="Support and Strata Control (SCAMP)",
            requirement_type="Strata monitoring",
            requirement="Sounding of roof and sides, tell-tale monitoring, support installation check according to Strata Control and Monitoring Plan.",
            applicability="Underground roof and sides in active workings",
            frequency_or_trigger="Every shift by supervisory official",
            responsible_role="Overman / Deputy",
            required_record_or_evidence="Daily roof examination record book",
        ),
        RegulatoryObligation(
            obligation_id="CMR-145",
            regulation=cmr_source,
            title="Mine Drainage and Pumping Stations",
            requirement_type="Water safety",
            requirement="Inspect main sump, water inflow, pumping machinery, pipeline integrity, and flood prevention measures.",
            applicability="Mines with underground water inflow / main sump stations",
            frequency_or_trigger="At least once every seven days",
            responsible_role="Mechanical Engineer + Pump Operator",
            required_record_or_evidence="Mine pumping station logbook and water level records",
        ),
    ]

    for ob in obligations:
        db.save_obligation(ob)

    # ----------------------------------------------------
    # THE 13 STATUTORY INSPECTION TEMPLATES
    # ----------------------------------------------------

    templates = [
        # ====================================================
        # 1. Pre-Shift Methane Check (Ventilation & Gas)
        # ====================================================
        InspectionTemplate(
            template_id="PRE-SHIFT-METHANE-CHECK",
            name="Pre-Shift Methane Check",
            inspection_family="Ventilation & Gas",
            description="Statutory pre-shift examination of working faces and airways for inflammable gas, airflow, and environmental parameters prior to shift entry.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-119"],
            frequency_or_trigger="3 times/day",
            frequency_label="Required every shift (3 times/day)",
            responsible_role="Overman / Deputy",
            regulation_reference="Coal Mines Regulations 2017, Regulation 119",
            measurements=[
                MeasurementDefinition(
                    measurement_id="PSM-01",
                    name="Methane at Working Face",
                    unit="%",
                    required=True,
                    description="Measured methane (CH4) concentration at the active coal production face.",
                    max_value=1.25,
                    threshold_label="< 1.25%",
                ),
                MeasurementDefinition(
                    measurement_id="PSM-02",
                    name="Methane at Return Airway",
                    unit="%",
                    required=True,
                    description="Measured methane (CH4) concentration in the district return airway.",
                    max_value=2.0,
                    threshold_label="< 2.0%",
                ),
                MeasurementDefinition(
                    measurement_id="PSM-03",
                    name="Air Velocity",
                    unit="m/s",
                    required=True,
                    description="Airflow speed through the working district face area.",
                    min_value=0.5,
                    threshold_label="> 0.5 m/s",
                ),
                MeasurementDefinition(
                    measurement_id="PSM-04",
                    name="Carbon Monoxide (CO)",
                    unit="%",
                    required=True,
                    description="Concentration of carbon monoxide in parts or percentage.",
                    max_value=0.005,
                    threshold_label="< 0.005%",
                ),
                MeasurementDefinition(
                    measurement_id="PSM-05",
                    name="Air Temperature",
                    unit="°C",
                    required=True,
                    description="Ambient air dry-bulb temperature at the face.",
                    max_value=30.0,
                    threshold_label="< 30°C",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="PSM-CHK-01",
                    question="Gas detector calibrated, battery verified, and operational before descent",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="PSM-CHK-02",
                    question="Working face thoroughly inspected for gas accumulation in roof cavities",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="PSM-CHK-03",
                    question="District return airway inspected for adequate ventilation dilution",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="PSM-CHK-04",
                    question="Auxiliary ventilation ducting intact, undamaged, and delivering required air volume",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="PSM-CHK-05",
                    question="Multi-gas detector readings logged and verified against statutory limits",
                    required=True,
                    severity_if_failed="HIGH",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="PSM-EV-01",
                    evidence_type=EvidenceType.PHOTO,
                    name="Working Face Photograph",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="PSM-EV-02",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="Gas Multi-Detector Reading Log",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 2. Weekly Ventilation Survey (Ventilation & Gas)
        # ====================================================
        InspectionTemplate(
            template_id="WEEKLY-VENTILATION-SURVEY",
            name="Weekly Ventilation Survey",
            inspection_family="Ventilation & Gas",
            description="Weekly statutory determination of air quantities, fan pressure, and relative humidity across mine ventilation measuring stations.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-156"],
            frequency_or_trigger="Weekly",
            frequency_label="Weekly",
            responsible_role="Ventilation Officer",
            regulation_reference="Coal Mines Regulations 2017, Regulation 156",
            measurements=[
                MeasurementDefinition(
                    measurement_id="WVS-01",
                    name="Total Intake Air Quantity",
                    unit="m³/min",
                    required=True,
                    description="Total volume of fresh intake air entering the mine district.",
                    min_value=3000.0,
                    threshold_label="> 3000 m³/min",
                ),
                MeasurementDefinition(
                    measurement_id="WVS-02",
                    name="Total Return Air Quantity",
                    unit="m³/min",
                    required=True,
                    description="Total volume of return air discharged from the mine district.",
                    min_value=3000.0,
                    threshold_label="> 3000 m³/min",
                ),
                MeasurementDefinition(
                    measurement_id="WVS-03",
                    name="Main Fan Water Gauge Pressure",
                    unit="mm wg",
                    required=True,
                    description="Negative pressure generated by main mechanical ventilator.",
                    min_value=50.0,
                    max_value=150.0,
                    threshold_label="50–150 mm wg",
                ),
                MeasurementDefinition(
                    measurement_id="WVS-04",
                    name="Relative Humidity",
                    unit="%",
                    required=True,
                    description="Relative humidity in the return airway.",
                    max_value=90.0,
                    threshold_label="< 90%",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="WVS-CHK-01",
                    question="Air measurements taken at all designated statutory ventilation measuring stations",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WVS-CHK-02",
                    question="Air crossings, doors, and stoppings inspected for leakage and structural seal",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WVS-CHK-03",
                    question="Main mechanical ventilator operating parameters, RPM, and motor amps recorded",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WVS-CHK-04",
                    question="Ventilation district air distribution verified against approved mine ventilation plan",
                    required=True,
                    severity_if_failed="MEDIUM",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="WVS-EV-01",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="Anemometer Traverse Reading Record",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="WVS-EV-02",
                    evidence_type=EvidenceType.PHOTO,
                    name="Ventilation Measurement Station Photograph",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 3. Monthly Ventilation Inspection (Ventilation & Gas)
        # ====================================================
        InspectionTemplate(
            template_id="MONTHLY-VENTILATION-INSPECTION",
            name="Monthly Ventilation Inspection",
            inspection_family="Ventilation & Gas",
            description="Comprehensive monthly statutory audit of overall mine ventilation system, leakage indices, and isolation stoppings.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-156"],
            frequency_or_trigger="Monthly",
            frequency_label="Monthly",
            responsible_role="Ventilation Officer + Mine Manager",
            regulation_reference="Coal Mines Regulations 2017, Regulation 156",
            measurements=[
                MeasurementDefinition(
                    measurement_id="MVI-01",
                    name="Overall Mine Air Quantity",
                    unit="m³/min",
                    required=True,
                    description="Total air circulating through the entire underground mine.",
                    min_value=6000.0,
                    threshold_label="> 6000 m³/min",
                ),
                MeasurementDefinition(
                    measurement_id="MVI-02",
                    name="Air Leakage Coefficient",
                    unit="%",
                    required=True,
                    description="Calculated air volumetric leakage across shaft bottom stoppings.",
                    max_value=15.0,
                    threshold_label="< 15%",
                ),
                MeasurementDefinition(
                    measurement_id="MVI-03",
                    name="Wet Bulb Temperature at Deepest Face",
                    unit="°C",
                    required=True,
                    description="Statutory wet bulb temperature at deepest active underground face.",
                    max_value=30.5,
                    threshold_label="< 30.5°C",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="MVI-CHK-01",
                    question="Complete monthly ventilation survey plotted on statutory ventilation plan",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="MVI-CHK-02",
                    question="Booster and auxiliary fan installations examined for mechanical alignment and earthing",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="MVI-CHK-03",
                    question="Isolation stoppings and sealed fire districts inspected for gas emission and differential pressure",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="MVI-CHK-04",
                    question="Monthly statutory ventilation report countersigned by Mine Manager for submission",
                    required=True,
                    severity_if_failed="HIGH",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="MVI-EV-01",
                    evidence_type=EvidenceType.DOCUMENT,
                    name="Monthly Ventilation Survey Report / Plan",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="MVI-EV-02",
                    evidence_type=EvidenceType.PHOTO,
                    name="Deepest Face Hygrometer Photo",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 4. Weekly Shaft Examination (Shaft & Winding)
        # ====================================================
        InspectionTemplate(
            template_id="WEEKLY-SHAFT-EXAMINATION",
            name="Weekly Shaft Examination",
            inspection_family="Shaft & Winding",
            description="Weekly statutory descent examination of shaft guides, wall lining, cable brackets, insets, and sump water accumulation.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-75"],
            frequency_or_trigger="Weekly",
            frequency_label="Weekly",
            responsible_role="Winding Engineer + Overman",
            regulation_reference="Coal Mines Regulations 2017, Regulation 75",
            measurements=[
                MeasurementDefinition(
                    measurement_id="WSE-01",
                    name="Shaft Guide Clearance",
                    unit="mm",
                    required=True,
                    description="Clearance gap between cage shoes and shaft guide rails.",
                    min_value=15.0,
                    max_value=35.0,
                    threshold_label="15–35 mm",
                ),
                MeasurementDefinition(
                    measurement_id="WSE-02",
                    name="Shaft Sump Water Level",
                    unit="m",
                    required=True,
                    description="Standing water depth in the shaft bottom sump.",
                    max_value=2.0,
                    threshold_label="< 2.0 m",
                ),
                MeasurementDefinition(
                    measurement_id="WSE-03",
                    name="Shaft Wall Inset Inflow",
                    unit="l/min",
                    required=True,
                    description="Water infiltration rate through shaft concrete lining joints.",
                    max_value=50.0,
                    threshold_label="< 50 l/min",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="WSE-CHK-01",
                    question="Shaft lining, brickwork/concrete walling, and intermediate insets examined throughout full depth",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WSE-CHK-02",
                    question="Rigid guide rails and rope guides inspected for wear, verticality, and tension weights",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WSE-CHK-03",
                    question="Shaft electrical signalling, pull-wire bells, and emergency telephone tested from all levels",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="WSE-CHK-04",
                    question="Shaft sump drainage pump operational and protective cage landing baulks intact",
                    required=True,
                    severity_if_failed="HIGH",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="WSE-EV-01",
                    evidence_type=EvidenceType.PHOTO,
                    name="Shaft Inset / Guide Examination Photo",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="WSE-EV-02",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="Shaft Sump Level Measurement Log",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 5. Monthly Winding Installation Inspection (Shaft & Winding)
        # ====================================================
        InspectionTemplate(
            template_id="MONTHLY-WINDING-INSTALLATION",
            name="Monthly Winding Installation Inspection",
            inspection_family="Shaft & Winding",
            description="Monthly statutory testing of winding engine mechanical brakes, overwind/overspeed contrivances, and rope diameter reduction.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-76-80"],
            frequency_or_trigger="Monthly",
            frequency_label="Monthly",
            responsible_role="Winding Engineer + Electrical Engineer",
            regulation_reference="Coal Mines Regulations 2017, Regulations 76–80",
            measurements=[
                MeasurementDefinition(
                    measurement_id="MWI-01",
                    name="Brake Holding Torque",
                    unit="kN·m",
                    required=True,
                    description="Holding torque of mechanical winding brakes under static load test.",
                    min_value=120.0,
                    threshold_label="> 120 kN·m",
                ),
                MeasurementDefinition(
                    measurement_id="MWI-02",
                    name="Winding Rope Wear Reduction",
                    unit="%",
                    required=True,
                    description="Percentage wear reduction in outer wires of the winding rope.",
                    max_value=10.0,
                    threshold_label="< 10%",
                ),
                MeasurementDefinition(
                    measurement_id="MWI-03",
                    name="Over-Speed Trip Governor Setting",
                    unit="m/s",
                    required=True,
                    description="Trigger speed of automatic electrical overspeed governor trip.",
                    max_value=8.0,
                    threshold_label="< 8.0 m/s",
                ),
                MeasurementDefinition(
                    measurement_id="MWI-04",
                    name="Rope Diameter Reduction",
                    unit="%",
                    required=True,
                    description="Measured rope diameter decrease compared to nominal factory diameter.",
                    max_value=6.0,
                    threshold_label="< 6%",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="MWI-CHK-01",
                    question="Automatic overwind and overspeed prevention devices functionally tripped and tested",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="MWI-CHK-02",
                    question="Emergency and service brakes tested under full unbalanced load condition",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="MWI-CHK-03",
                    question="Headgear sheaves, pulleys, king-bolts, and fleet angles measured for groove wear",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="MWI-CHK-04",
                    question="Cage suspension gear (D-shackles, bridle chains, safety hooks) magnaflux/visually tested",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="MWI-EV-01",
                    evidence_type=EvidenceType.DOCUMENT,
                    name="Winding Engine Brake Test Certificate",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="MWI-EV-02",
                    evidence_type=EvidenceType.PHOTO,
                    name="Winding Rope Gauge Measurement Photo",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 6. Weekly Electrical Inspection (Electrical)
        # ====================================================
        InspectionTemplate(
            template_id="WEEKLY-ELECTRICAL-INSPECTION",
            name="Weekly Electrical Inspection",
            inspection_family="Electrical",
            description="Weekly statutory testing of underground electrical earthing resistance, FLP enclosures, gate end boxes, and trailing cables.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-160-170"],
            frequency_or_trigger="Weekly",
            frequency_label="Weekly",
            responsible_role="Electrical Engineer",
            regulation_reference="Coal Mines Regulations 2017, Regulations 160–170",
            measurements=[
                MeasurementDefinition(
                    measurement_id="WEI-01",
                    name="Earth Resistance",
                    unit="ohm",
                    required=True,
                    description="Individual apparatus earth continuity loop resistance.",
                    max_value=1.0,
                    threshold_label="< 1.0 ohm",
                ),
                MeasurementDefinition(
                    measurement_id="WEI-02",
                    name="Insulation Resistance (Substation to Face)",
                    unit="megaohm",
                    required=True,
                    description="Megger insulation resistance test between conductors and earth.",
                    min_value=5.0,
                    threshold_label="> 5.0 MΩ",
                ),
                MeasurementDefinition(
                    measurement_id="WEI-03",
                    name="Neutral Voltage to Earth",
                    unit="V",
                    required=True,
                    description="Measured potential between neutral conductor and general mass of earth.",
                    max_value=5.0,
                    threshold_label="< 5.0 V",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="WEI-CHK-01",
                    question="Earth continuity conductors verified across all underground working districts",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="WEI-CHK-02",
                    question="Flameproof electrical enclosures (FLP) examined for missing bolts, damaged seals, or flame gaps",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="WEI-CHK-03",
                    question="Gate end boxes, pilot control circuits, and earth leakage trips tested with test push buttons",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WEI-CHK-04",
                    question="Flexible trailing cables to shearers/drills checked for physical cuts, punctures, or joint integrity",
                    required=True,
                    severity_if_failed="HIGH",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="WEI-EV-01",
                    evidence_type=EvidenceType.PHOTO,
                    name="Earth Resistance Meter Reading Photo",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="WEI-EV-02",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="FLP Enclosure Examination Record",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 7. Monthly Electrical Installation Inspection (Electrical)
        # ====================================================
        InspectionTemplate(
            template_id="MONTHLY-ELECTRICAL-INSTALLATION",
            name="Monthly Electrical Installation Inspection",
            inspection_family="Electrical",
            description="Monthly statutory audit of main underground substation, transformer oil dielectric strength, and earth leakage relay timing.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-160-170"],
            frequency_or_trigger="Monthly",
            frequency_label="Monthly",
            responsible_role="Electrical Engineer + Mine Manager",
            regulation_reference="Coal Mines Regulations 2017, Regulations 160–170",
            measurements=[
                MeasurementDefinition(
                    measurement_id="MEI-01",
                    name="Main Substation Earth Grid Resistance",
                    unit="ohm",
                    required=True,
                    description="Overall resistance to earth of the main mine substation grounding grid.",
                    max_value=0.5,
                    threshold_label="< 0.5 ohm",
                ),
                MeasurementDefinition(
                    measurement_id="MEI-02",
                    name="Underground Transformer Oil Breakdown Voltage",
                    unit="kV",
                    required=True,
                    description="Dielectric strength breakdown test value of cooling insulating oil.",
                    min_value=40.0,
                    threshold_label="> 40.0 kV",
                ),
                MeasurementDefinition(
                    measurement_id="MEI-03",
                    name="Earth Leakage Relay Trip Time",
                    unit="ms",
                    required=True,
                    description="Calibrated trip response time of main high-voltage circuit breaker.",
                    max_value=100.0,
                    threshold_label="< 100 ms",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="MEI-CHK-01",
                    question="High voltage switchgear, protection relays, and overcurrent releases tested and calibrated",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="MEI-CHK-02",
                    question="Statutory register of flameproof apparatus verified and updated with apparatus locations",
                    required=True,
                    severity_if_failed="MEDIUM",
                ),
                ChecklistItem(
                    item_id="MEI-CHK-03",
                    question="Substation battery charger banks, emergency lighting, and fire extinguishers examined",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="MEI-CHK-04",
                    question="Insulated rubber safety mats, danger caution boards, and CPR diagrams verified in place",
                    required=True,
                    severity_if_failed="MEDIUM",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="MEI-EV-01",
                    evidence_type=EvidenceType.DOCUMENT,
                    name="Substation Earth Grid Test Certificate",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="MEI-EV-02",
                    evidence_type=EvidenceType.PHOTO,
                    name="Earth Leakage Relay Calibration Photo",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 8. Daily HEMM Pre-Start Check (HEMM)
        # ====================================================
        InspectionTemplate(
            template_id="DAILY-HEMM-PRESTART",
            name="Daily HEMM Pre-Start Check",
            inspection_family="HEMM",
            description="Daily shift-wise pre-start mechanical and safety check conducted on heavy earth moving machinery before operation.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-135"],
            frequency_or_trigger="Every shift",
            frequency_label="Every shift",
            responsible_role="HEMM Operator",
            regulation_reference="Coal Mines Regulations 2017, Regulation 135",
            measurements=[
                MeasurementDefinition(
                    measurement_id="DHP-01",
                    name="Engine Oil Pressure",
                    unit="bar",
                    required=True,
                    description="Engine oil pressure reading after warmup idle.",
                    min_value=2.5,
                    max_value=5.0,
                    threshold_label="2.5–5.0 bar",
                ),
                MeasurementDefinition(
                    measurement_id="DHP-02",
                    name="Hydraulic Fluid Pressure",
                    unit="psi",
                    required=True,
                    description="System hydraulic circuit operating pressure.",
                    min_value=2000.0,
                    max_value=3200.0,
                    threshold_label="2000–3200 psi",
                ),
                MeasurementDefinition(
                    measurement_id="DHP-03",
                    name="Brake Air Pressure",
                    unit="bar",
                    required=True,
                    description="Pneumatic brake reservoir tank pressure.",
                    min_value=6.5,
                    threshold_label="> 6.5 bar",
                ),
                MeasurementDefinition(
                    measurement_id="DHP-04",
                    name="Battery Voltage",
                    unit="V",
                    required=True,
                    description="Heavy equipment starting battery terminal voltage.",
                    min_value=24.0,
                    threshold_label="> 24.0 V",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="DHP-CHK-01",
                    question="Service brake, emergency brake, and secondary steering tested and functioning properly",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="DHP-CHK-02",
                    question="Audio-visual reverse backup alarm (AVLA) tested and sounding clearly",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="DHP-CHK-03",
                    question="Automatic/manual fire suppression system (AFSS) pressure gauge in green operating band",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="DHP-CHK-04",
                    question="Operator seat belt, cabin ROPS/FOPS structural frame, and rear-view mirrors intact",
                    required=True,
                    severity_if_failed="HIGH",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="DHP-EV-01",
                    evidence_type=EvidenceType.PHOTO,
                    name="HEMM Equipment Dashboard / Gauge Photo",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="DHP-EV-02",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="Operator Pre-Start Checklist Sign-off",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 9. Weekly HEMM Inspection (HEMM)
        # ====================================================
        InspectionTemplate(
            template_id="WEEKLY-HEMM-INSPECTION",
            name="Weekly HEMM Inspection",
            inspection_family="HEMM",
            description="Weekly mechanical engineering inspection of heavy earth moving machinery brake efficiency, tyre tread, and exhaust cooling.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-135"],
            frequency_or_trigger="Weekly",
            frequency_label="Weekly",
            responsible_role="Mechanical Engineer + HEMM Supervisor",
            regulation_reference="Coal Mines Regulations 2017, Regulation 135",
            measurements=[
                MeasurementDefinition(
                    measurement_id="WHI-01",
                    name="Brake Stopping Distance at 15 km/h",
                    unit="m",
                    required=True,
                    description="Measured full emergency braking stopping distance on dry level grade.",
                    max_value=8.0,
                    threshold_label="< 8.0 m",
                ),
                MeasurementDefinition(
                    measurement_id="WHI-02",
                    name="Tyre Tread Depth / Track Tension Sag",
                    unit="mm",
                    required=True,
                    description="Remaining tyre tread depth or crawler track sag deflection.",
                    min_value=20.0,
                    threshold_label="> 20.0 mm",
                ),
                MeasurementDefinition(
                    measurement_id="WHI-03",
                    name="Exhaust Gas Temperature",
                    unit="°C",
                    required=True,
                    description="Diesel exhaust surface and flame-trap temperature.",
                    max_value=450.0,
                    threshold_label="< 450°C",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="WHI-CHK-01",
                    question="Dynamic brake retarder, dual-circuit hydraulic valves, and fail-safe parking brake tested",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="WHI-CHK-02",
                    question="Hydraulic high-pressure hoses, cylinders, and swivel joints examined for weeping/leaks",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WHI-CHK-03",
                    question="Chassis main frame, articulation pins, and dump body mechanical locks inspected for cracks",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WHI-CHK-04",
                    question="Thermal detection wiring, fire suppression nozzles, and engine shut-off solenoids serviced",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="WHI-EV-01",
                    evidence_type=EvidenceType.DOCUMENT,
                    name="HEMM Weekly Mechanical Inspection Log",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="WHI-EV-02",
                    evidence_type=EvidenceType.PHOTO,
                    name="Brake Test Distance Verification Photo",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 10. Pre-Blasting Inspection (Blasting)
        # ====================================================
        InspectionTemplate(
            template_id="PRE-BLASTING-INSPECTION",
            name="Pre-Blasting Inspection",
            inspection_family="Blasting",
            description="Mandatory statutory safety examination conducted immediately before shot-firing to check methane, drill holes, and clear danger zones.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-155-158"],
            frequency_or_trigger="Before every blast",
            frequency_label="Before every blasting operation",
            responsible_role="Blasting Supervisor + Safety Officer",
            regulation_reference="Coal Mines Regulations 2017, Regulations 155–158",
            measurements=[
                MeasurementDefinition(
                    measurement_id="PBI-01",
                    name="Pre-Blast Face Methane Concentration",
                    unit="%",
                    required=True,
                    description="Inflammable gas percentage within 20 metres of the face prior to charging.",
                    max_value=0.5,
                    threshold_label="< 0.5%",
                ),
                MeasurementDefinition(
                    measurement_id="PBI-02",
                    name="Number of Shot-Holes Drilled",
                    unit="holes",
                    required=True,
                    description="Total count of drilled shot-holes in the face pattern.",
                    min_value=1.0,
                    threshold_label="> 0",
                ),
                MeasurementDefinition(
                    measurement_id="PBI-03",
                    name="Maximum Charge Per Delay",
                    unit="kg",
                    required=True,
                    description="Explosive charge weight in single millisecond delay interval.",
                    max_value=2.5,
                    threshold_label="< 2.5 kg",
                ),
                MeasurementDefinition(
                    measurement_id="PBI-04",
                    name="Danger Zone Clearance Radius",
                    unit="m",
                    required=True,
                    description="Clearance cordon radius evacuated and guarded by sentries.",
                    min_value=300.0,
                    threshold_label="≥ 300 m",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="PBI-CHK-01",
                    question="All shot-holes scraped and tested for inflammable gas presence prior to charging",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="PBI-CHK-02",
                    question="Permitted explosives and approved delay detonators verified against explosive magazine issue voucher",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="PBI-CHK-03",
                    question="Danger zone cleared of all personnel; sentries posted with red flags at all approach roadways",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="PBI-CHK-04",
                    question="Approved blast shelter occupied; warning sirens/whistles sounded before connection to exploder",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="PBI-EV-01",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="Face Gas Test and Hole Charging Record",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="PBI-EV-02",
                    evidence_type=EvidenceType.PHOTO,
                    name="Sentries Placement / Danger Zone Photo",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 11. Post-Blasting Inspection (Blasting)
        # ====================================================
        InspectionTemplate(
            template_id="POST-BLASTING-INSPECTION",
            name="Post-Blasting Inspection",
            inspection_family="Blasting",
            description="Statutory inspection of the blasted face following the mandatory cooling period to detect misfires, fumes, and loose roof strata.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-155-158"],
            frequency_or_trigger="After every blast",
            frequency_label="After every blasting operation",
            responsible_role="Blasting Supervisor + Ventilation Officer",
            regulation_reference="Coal Mines Regulations 2017, Regulation 158",
            measurements=[
                MeasurementDefinition(
                    measurement_id="POST-01",
                    name="Re-entry Wait Time Observed",
                    unit="min",
                    required=True,
                    description="Elapsed waiting time between blast detonation and official re-entry.",
                    min_value=30.0,
                    threshold_label="≥ 30 min",
                ),
                MeasurementDefinition(
                    measurement_id="POST-02",
                    name="Post-Blast Methane at Blasted Face",
                    unit="%",
                    required=True,
                    description="CH4 concentration after smoke clearance at the blasted coal heap.",
                    max_value=0.8,
                    threshold_label="< 0.8%",
                ),
                MeasurementDefinition(
                    measurement_id="POST-03",
                    name="Post-Blast Carbon Monoxide (CO)",
                    unit="%",
                    required=True,
                    description="Residual toxic carbon monoxide concentration before allowing workers entry.",
                    max_value=0.003,
                    threshold_label="< 0.003%",
                ),
                MeasurementDefinition(
                    measurement_id="POST-04",
                    name="Misfire Holes Detected",
                    unit="holes",
                    required=True,
                    description="Number of unexploded or partially exploded holes discovered.",
                    max_value=0.0,
                    threshold_label="0 holes",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="POST-CHK-01",
                    question="Statutory waiting period (minimum 30 min for electric blasting) strictly observed before re-entry",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="POST-CHK-02",
                    question="Blasted face thoroughly examined for misfires, sockets, and unexploded explosive cartridges",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="POST-CHK-03",
                    question="Roof and side strata tested with sounding rod and all loose stones dressed down safely",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="POST-CHK-04",
                    question="Fumes completely cleared and auxiliary ventilation restored to the working face",
                    required=True,
                    severity_if_failed="HIGH",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="POST-EV-01",
                    evidence_type=EvidenceType.PHOTO,
                    name="Post-Blast Face Examination Photo",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="POST-EV-02",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="Misfire Clearance Sign-off Sheet",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 12. Daily Roof Inspection (Roof / Strata)
        # ====================================================
        InspectionTemplate(
            template_id="DAILY-ROOF-INSPECTION",
            name="Daily Roof Inspection",
            inspection_family="Roof / Strata",
            description="Shift-wise strata inspection of underground roof support compliance, tell-tale extensometers, and roof bolt anchorage torque.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-85-95"],
            frequency_or_trigger="Every shift",
            frequency_label="Every shift",
            responsible_role="Overman / Deputy",
            regulation_reference="Coal Mines Regulations 2017, Regulations 85–95",
            measurements=[
                MeasurementDefinition(
                    measurement_id="DRI-01",
                    name="Maximum Unsupported Roof Span",
                    unit="m",
                    required=True,
                    description="Distance between last row of permanent supports and newly exposed face.",
                    max_value=1.5,
                    threshold_label="< 1.5 m",
                ),
                MeasurementDefinition(
                    measurement_id="DRI-02",
                    name="Tell-Tale Strata Extensometer Displacement",
                    unit="mm",
                    required=True,
                    description="Bed separation displacement indicated by dual-height tell-tale.",
                    max_value=6.0,
                    threshold_label="< 6.0 mm",
                ),
                MeasurementDefinition(
                    measurement_id="DRI-03",
                    name="Roof Bolt Torque Anchorage Test",
                    unit="N·m",
                    required=True,
                    description="Tightening torque measured with calibrated torque wrench on resin bolts.",
                    min_value=150.0,
                    threshold_label="> 150 N·m",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="DRI-CHK-01",
                    question="Sounding of roof and sides conducted along whole working face, roadways, and junctions",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="DRI-CHK-02",
                    question="Support plan compliance verified against approved Strata Control and Monitoring Plan (SCAMP)",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="DRI-CHK-03",
                    question="Roof bolts, steel bearing plates, and temporary props inspected for tightness and load deflection",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="DRI-CHK-04",
                    question="Geological slips, faults, water dripping, or roof micro-fissures logged and reported",
                    required=True,
                    severity_if_failed="MEDIUM",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="DRI-EV-01",
                    evidence_type=EvidenceType.PHOTO,
                    name="Tell-Tale Indicator / Roof Bolt Reading Photo",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="DRI-EV-02",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="Roof Sounding and Dressing Log",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),

        # ====================================================
        # 13. Weekly Pumping Station Inspection (Water / Drainage)
        # ====================================================
        InspectionTemplate(
            template_id="WEEKLY-PUMPING-STATION",
            name="Weekly Pumping Station Inspection",
            inspection_family="Water / Drainage",
            description="Weekly statutory inspection of main underground drainage sumps, pump discharge pressures, and flood prevention barriers.",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            regulatory_obligation_ids=["CMR-145"],
            frequency_or_trigger="Weekly",
            frequency_label="Weekly",
            responsible_role="Mechanical Engineer + Pump Operator",
            regulation_reference="Coal Mines Regulations 2017, Regulation 145",
            measurements=[
                MeasurementDefinition(
                    measurement_id="WPS-01",
                    name="Main Sump Water Level",
                    unit="m",
                    required=True,
                    description="Current water depth above sump floor.",
                    max_value=3.5,
                    threshold_label="< 3.5 m",
                ),
                MeasurementDefinition(
                    measurement_id="WPS-02",
                    name="Sump Inflow Rate",
                    unit="m³/hr",
                    required=True,
                    description="Rate of ground water seepage entering the main underground sump.",
                    max_value=120.0,
                    threshold_label="< 120 m³/hr",
                ),
                MeasurementDefinition(
                    measurement_id="WPS-03",
                    name="Pump Discharge Pressure",
                    unit="kg/cm²",
                    required=True,
                    description="Operating head discharge pressure of main dewatering pump.",
                    min_value=8.0,
                    max_value=18.0,
                    threshold_label="8–18 kg/cm²",
                ),
                MeasurementDefinition(
                    measurement_id="WPS-04",
                    name="Pump Motor Bearing Temperature",
                    unit="°C",
                    required=True,
                    description="Operating temperature of main dewatering pump drive bearing.",
                    max_value=75.0,
                    threshold_label="< 75°C",
                ),
            ],
            checklist=[
                ChecklistItem(
                    item_id="WPS-CHK-01",
                    question="Standby main dewatering pump tested and confirmed ready for emergency immediate start",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
                ChecklistItem(
                    item_id="WPS-CHK-02",
                    question="Delivery water column pipes, non-return valves, and expansion joints inspected for leaks",
                    required=True,
                    severity_if_failed="HIGH",
                ),
                ChecklistItem(
                    item_id="WPS-CHK-03",
                    question="Sump siltation level inspected and silt clearing schedule verified",
                    required=True,
                    severity_if_failed="MEDIUM",
                ),
                ChecklistItem(
                    item_id="WPS-CHK-04",
                    question="Water barrier boundary pillars and dams inspected for dampness, seepage, or spalling",
                    required=True,
                    severity_if_failed="CRITICAL",
                ),
            ],
            evidence_requirements=[
                EvidenceRequirement(
                    evidence_id="WPS-EV-01",
                    evidence_type=EvidenceType.PHOTO,
                    name="Sump Water Level Gauge Photo",
                    required=True,
                    minimum_count=1,
                ),
                EvidenceRequirement(
                    evidence_id="WPS-EV-02",
                    evidence_type=EvidenceType.MANUAL_READING,
                    name="Pump Operating Pressure & Temperature Log",
                    required=True,
                    minimum_count=1,
                ),
            ],
            active=True,
        ),
    ]

    for tmpl in templates:
        db.save_inspection_template(tmpl)


def load_schedule_seed() -> None:
    """
    Load schedule rules for all 13 statutory inspection types.
    """
    rules = [
        # --- SHIFT-BASED (Due Today) ---
        RegulatoryScheduleRule(
            schedule_id="SCH-PRE-SHIFT-METHANE",
            obligation_id="CMR-119",
            template_id="PRE-SHIFT-METHANE-CHECK",
            name="Pre-Shift Methane Check",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=8,
            interval_unit=ScheduleUnit.HOURS,
            trigger_type="shift",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[GassyDegree.DEGREE_I, GassyDegree.DEGREE_II, GassyDegree.DEGREE_III],
            condition_description="Required every shift before worker entry.",
            responsible_role="Overman / Deputy",
            regulation_reference="CMR 2017 Regulation 119",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulation 119",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-DAILY-HEMM-PRESTART",
            obligation_id="CMR-135",
            template_id="DAILY-HEMM-PRESTART",
            name="Daily HEMM Pre-Start Check",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=8,
            interval_unit=ScheduleUnit.HOURS,
            trigger_type="shift",
            applicable_mine_types=[MineType.UNDERGROUND_COAL, MineType.OPENCAST_COAL],
            applicable_gassy_degrees=[],
            condition_description="Required every shift prior to machine operation.",
            responsible_role="HEMM Operator",
            regulation_reference="CMR 2017 Regulation 135",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulation 135",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-DAILY-ROOF",
            obligation_id="CMR-85-95",
            template_id="DAILY-ROOF-INSPECTION",
            name="Daily Roof Inspection",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=8,
            interval_unit=ScheduleUnit.HOURS,
            trigger_type="shift",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[],
            condition_description="Required every shift for underground workings.",
            responsible_role="Overman / Deputy",
            regulation_reference="CMR 2017 Regulations 85–95",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulations 85–95",
            validation_status="VALIDATED",
            active=True,
        ),

        # --- BLASTING (Conditional / Event-based) ---
        RegulatoryScheduleRule(
            schedule_id="SCH-PRE-BLASTING",
            obligation_id="CMR-155-158",
            template_id="PRE-BLASTING-INSPECTION",
            name="Pre-Blasting Inspection",
            frequency_type=ScheduleFrequencyType.CONDITIONAL,
            interval_value=None,
            interval_unit=None,
            trigger_type="pre_blast",
            applicable_mine_types=[MineType.UNDERGROUND_COAL, MineType.OPENCAST_COAL],
            applicable_gassy_degrees=[],
            condition_description="Required prior to every blasting round.",
            responsible_role="Blasting Supervisor + Safety Officer",
            regulation_reference="CMR 2017 Regulations 155–158",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulations 155–158",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-POST-BLASTING",
            obligation_id="CMR-155-158",
            template_id="POST-BLASTING-INSPECTION",
            name="Post-Blasting Inspection",
            frequency_type=ScheduleFrequencyType.CONDITIONAL,
            interval_value=None,
            interval_unit=None,
            trigger_type="post_blast",
            applicable_mine_types=[MineType.UNDERGROUND_COAL, MineType.OPENCAST_COAL],
            applicable_gassy_degrees=[],
            condition_description="Required after every blasting round.",
            responsible_role="Blasting Supervisor + Ventilation Officer",
            regulation_reference="CMR 2017 Regulation 158",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulation 158",
            validation_status="VALIDATED",
            active=True,
        ),

        # --- WEEKLY (Due Soon) ---
        RegulatoryScheduleRule(
            schedule_id="SCH-WEEKLY-VENT-SURVEY",
            obligation_id="CMR-156",
            template_id="WEEKLY-VENTILATION-SURVEY",
            name="Weekly Ventilation Survey",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=7,
            interval_unit=ScheduleUnit.DAYS,
            trigger_type="weekly",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[],
            condition_description="Weekly statutory ventilation survey.",
            responsible_role="Ventilation Officer",
            regulation_reference="CMR 2017 Regulation 156",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulation 156",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-WEEKLY-SHAFT-EXAM",
            obligation_id="CMR-75",
            template_id="WEEKLY-SHAFT-EXAMINATION",
            name="Weekly Shaft Examination",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=7,
            interval_unit=ScheduleUnit.DAYS,
            trigger_type="weekly",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[],
            condition_description="Weekly shaft and guides examination.",
            responsible_role="Winding Engineer + Overman",
            regulation_reference="CMR 2017 Regulation 75",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulation 75",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-WEEKLY-ELEC-INSP",
            obligation_id="CMR-160-170",
            template_id="WEEKLY-ELECTRICAL-INSPECTION",
            name="Weekly Electrical Inspection",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=7,
            interval_unit=ScheduleUnit.DAYS,
            trigger_type="weekly",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[],
            condition_description="Weekly electrical inspection and earthing check.",
            responsible_role="Electrical Engineer",
            regulation_reference="CMR 2017 Regulations 160–170",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulations 160–170",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-WEEKLY-HEMM-INSP",
            obligation_id="CMR-135",
            template_id="WEEKLY-HEMM-INSPECTION",
            name="Weekly HEMM Inspection",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=7,
            interval_unit=ScheduleUnit.DAYS,
            trigger_type="weekly",
            applicable_mine_types=[MineType.UNDERGROUND_COAL, MineType.OPENCAST_COAL],
            applicable_gassy_degrees=[],
            condition_description="Weekly heavy earth moving machinery mechanical inspection.",
            responsible_role="Mechanical Engineer + HEMM Supervisor",
            regulation_reference="CMR 2017 Regulation 135",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulation 135",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-WEEKLY-PUMP-STATION",
            obligation_id="CMR-145",
            template_id="WEEKLY-PUMPING-STATION",
            name="Weekly Pumping Station Inspection",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=7,
            interval_unit=ScheduleUnit.DAYS,
            trigger_type="weekly",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[],
            condition_description="Weekly pumping station examination.",
            responsible_role="Mechanical Engineer + Pump Operator",
            regulation_reference="CMR 2017 Regulation 145",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulation 145",
            validation_status="VALIDATED",
            active=True,
        ),

        # --- MONTHLY (Upcoming) ---
        RegulatoryScheduleRule(
            schedule_id="SCH-MONTHLY-VENT-INSP",
            obligation_id="CMR-156",
            template_id="MONTHLY-VENTILATION-INSPECTION",
            name="Monthly Ventilation Inspection",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=30,
            interval_unit=ScheduleUnit.DAYS,
            trigger_type="monthly",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[],
            condition_description="Monthly comprehensive ventilation inspection.",
            responsible_role="Ventilation Officer + Mine Manager",
            regulation_reference="CMR 2017 Regulation 156",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulation 156",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-MONTHLY-WIND-INSTALL",
            obligation_id="CMR-76-80",
            template_id="MONTHLY-WINDING-INSTALLATION",
            name="Monthly Winding Installation Inspection",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=30,
            interval_unit=ScheduleUnit.DAYS,
            trigger_type="monthly",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[],
            condition_description="Monthly winding installation testing.",
            responsible_role="Winding Engineer + Electrical Engineer",
            regulation_reference="CMR 2017 Regulations 76–80",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulations 76–80",
            validation_status="VALIDATED",
            active=True,
        ),
        RegulatoryScheduleRule(
            schedule_id="SCH-MONTHLY-ELEC-INSTALL",
            obligation_id="CMR-160-170",
            template_id="MONTHLY-ELECTRICAL-INSTALLATION",
            name="Monthly Electrical Installation Inspection",
            frequency_type=ScheduleFrequencyType.INTERVAL,
            interval_value=30,
            interval_unit=ScheduleUnit.DAYS,
            trigger_type="monthly",
            applicable_mine_types=[MineType.UNDERGROUND_COAL],
            applicable_gassy_degrees=[],
            condition_description="Monthly electrical substation and transformer inspection.",
            responsible_role="Electrical Engineer + Mine Manager",
            regulation_reference="CMR 2017 Regulations 160–170",
            source_document="Coal Mines Regulations, 2017",
            source_reference="CMR 2017 Regulations 160–170",
            validation_status="VALIDATED",
            active=True,
        ),
    ]

    for rule in rules:
        db.save_schedule_rule(rule)


def load_mine_zones_and_coordinates_seed() -> None:
    """
    Seed realistic demonstration coordinates and zones for the 3 demo mines (Task 8).
    """
    coords = [
        ("MINE-BCCL-JHARIA-01", 23.7500, 86.4200, 600.0),
        ("MINE-ECL-RANIGANJ-01", 23.6200, 87.1300, 800.0),
        ("MINE-MCL-TALCHER-01", 20.9500, 85.2200, 1200.0),
    ]
    for mine_id, lat, lon, radius in coords:
        db.update_mine_coordinates(mine_id, lat, lon, radius)

    demo_zones = [
        {
            "mine_zone_id": "ZONE-JHARIA-PITHEAD",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "name": "Main Pit Head & Incline 1",
            "latitude": 23.7505,
            "longitude": 86.4202,
            "geofence_radius_meters": 150.0,
            "description": "Primary personnel muster and shaft entrance point.",
            "active": True,
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "mine_zone_id": "ZONE-JHARIA-VENT-EAST",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "name": "Main Exhaust Fan House (East)",
            "latitude": 23.7512,
            "longitude": 86.4215,
            "geofence_radius_meters": 100.0,
            "description": "Surface ventilation monitoring station and fan installations.",
            "active": True,
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "mine_zone_id": "ZONE-JHARIA-SUBSTATION",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "name": "Surface Main Substation",
            "latitude": 23.7492,
            "longitude": 86.4190,
            "geofence_radius_meters": 120.0,
            "description": "High-voltage distribution yard and flameproof switchgear bay.",
            "active": True,
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "mine_zone_id": "ZONE-RANIGANJ-SHAFT",
            "mine_id": "MINE-ECL-RANIGANJ-01",
            "name": "No. 3 Winding Shaft",
            "latitude": 23.6205,
            "longitude": 87.1305,
            "geofence_radius_meters": 150.0,
            "description": "Cage winding installation and headgear inspection area.",
            "active": True,
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "mine_zone_id": "ZONE-TALCHER-BENCH4",
            "mine_id": "MINE-MCL-TALCHER-01",
            "name": "Dragline Bench No. 4",
            "latitude": 20.9510,
            "longitude": 85.2210,
            "geofence_radius_meters": 300.0,
            "description": "Active opencast excavation bench and highwall zone.",
            "active": True,
            "created_at": "2026-01-01T00:00:00Z",
        },
    ]
    for z in demo_zones:
        db.upsert_mine_zone(z)


def load_sensor_seed() -> None:
    """
    Seed industrial telemetry sensors and baseline normal readings (Phase 2 Task 9).
    Covers all 7 sensor types for Jharia, Raniganj, and Talcher mines.
    """
    from .telemetry_service import ingest_telemetry_reading

    sensors = [
        # --- Jharia Underground Demonstration Mine (MINE-BCCL-JHARIA-01) ---
        {
            "sensor_id": "SN-JHARIA-CH4-01",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "zone_id": "ZONE-JHARIA-PITHEAD",
            "sensor_code": "CH4-JHARIA-01",
            "sensor_type": "METHANE",
            "unit": "%",
            "display_name": "Incline 1 Methane Optical Sensor",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 0.35,
        },
        {
            "sensor_id": "SN-JHARIA-AIR-01",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "zone_id": "ZONE-JHARIA-PITHEAD",
            "sensor_code": "AIR-JHARIA-01",
            "sensor_type": "AIRFLOW",
            "unit": "m³/s",
            "display_name": "Main Intake Airway Anemometer",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 22.5,
        },
        {
            "sensor_id": "SN-JHARIA-FAN-01",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "zone_id": "ZONE-JHARIA-VENT-EAST",
            "sensor_code": "FAN-JHARIA-01",
            "sensor_type": "VENTILATION_FAN",
            "unit": "RPM",
            "display_name": "Main Exhaust Fan Tachometer & Vibration",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 745.0,
        },
        {
            "sensor_id": "SN-JHARIA-DUST-01",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "zone_id": "ZONE-JHARIA-SUBSTATION",
            "sensor_code": "DUST-JHARIA-01",
            "sensor_type": "DUST",
            "unit": "mg/m³",
            "display_name": "Conveyor Transfer Respirable Dust Monitor",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 1.15,
        },
        {
            "sensor_id": "SN-JHARIA-SLP-01",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "zone_id": "ZONE-JHARIA-PITHEAD",
            "sensor_code": "SLP-JHARIA-01",
            "sensor_type": "SLOPE_DISPLACEMENT",
            "unit": "mm",
            "display_name": "Incline Portal Extensometer",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 2.4,
        },
        {
            "sensor_id": "SN-JHARIA-POR-01",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "zone_id": "ZONE-JHARIA-SUBSTATION",
            "sensor_code": "POR-JHARIA-01",
            "sensor_type": "PORE_PRESSURE",
            "unit": "kPa",
            "display_name": "Barrier Strata Piezometer",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 65.0,
        },
        {
            "sensor_id": "SN-JHARIA-RAIN-01",
            "mine_id": "MINE-BCCL-JHARIA-01",
            "zone_id": "ZONE-JHARIA-PITHEAD",
            "sensor_code": "RAIN-JHARIA-01",
            "sensor_type": "RAINFALL",
            "unit": "mm/hr",
            "display_name": "Surface Pluviometer Station",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 2.0,
        },

        # --- Raniganj Underground Demonstration Mine (MINE-ECL-RANIGANJ-01) ---
        {
            "sensor_id": "SN-RANIGANJ-CH4-01",
            "mine_id": "MINE-ECL-RANIGANJ-01",
            "zone_id": "ZONE-RANIGANJ-SHAFT",
            "sensor_code": "CH4-RANI-01",
            "sensor_type": "METHANE",
            "unit": "%",
            "display_name": "Shaft Return Methane Monitor",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 0.28,
        },
        {
            "sensor_id": "SN-RANIGANJ-AIR-01",
            "mine_id": "MINE-ECL-RANIGANJ-01",
            "zone_id": "ZONE-RANIGANJ-SHAFT",
            "sensor_code": "AIR-RANI-01",
            "sensor_type": "AIRFLOW",
            "unit": "m³/s",
            "display_name": "Downcast Shaft Velocity Sensor",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 18.2,
        },

        # --- Talcher Opencast Demonstration Mine (MINE-MCL-TALCHER-01) ---
        {
            "sensor_id": "SN-TALCHER-SLP-01",
            "mine_id": "MINE-MCL-TALCHER-01",
            "zone_id": "ZONE-TALCHER-BENCH4",
            "sensor_code": "SLP-TALC-01",
            "sensor_type": "SLOPE_DISPLACEMENT",
            "unit": "mm",
            "display_name": "Dragline Bench 4 Radar Prism",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 4.1,
        },
        {
            "sensor_id": "SN-TALCHER-POR-01",
            "mine_id": "MINE-MCL-TALCHER-01",
            "zone_id": "ZONE-TALCHER-BENCH4",
            "sensor_code": "POR-TALC-01",
            "sensor_type": "PORE_PRESSURE",
            "unit": "kPa",
            "display_name": "Overburden Dump Piezometer No. 2",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 82.0,
        },
        {
            "sensor_id": "SN-TALCHER-RAIN-01",
            "mine_id": "MINE-MCL-TALCHER-01",
            "zone_id": "ZONE-TALCHER-BENCH4",
            "sensor_code": "RAIN-TALC-01",
            "sensor_type": "RAINFALL",
            "unit": "mm/hr",
            "display_name": "Pit Weather Station Tipping Bucket",
            "status": "ACTIVE",
            "simulated": True,
            "created_at": "2026-01-01T00:00:00Z",
            "base_val": 0.0,
        },
    ]

    for s in sensors:
        base_val = s.pop("base_val")
        db.upsert_sensor(s)
        existing_readings = db.list_telemetry_history(s["mine_id"], limit=1, sensor_type=s["sensor_type"])
        if not existing_readings:
            try:
                ingest_telemetry_reading({
                    "sensor_id": s["sensor_id"],
                    "mine_id": s["mine_id"],
                    "zone_id": s.get("zone_id"),
                    "sensor_type": s["sensor_type"],
                    "value": base_val,
                    "unit": s["unit"],
                    "quality_status": "GOOD",
                    "source": "SCADA_SIMULATOR",
                    "simulated": True,
                })
            except Exception:
                pass


def load_production_seed() -> None:
    """
    Seed initial operational production targets and realistic shift records
    for demonstration mines. All marked explicitly as simulated.
    """
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    today_str = now_utc.strftime("%Y-%m-%d")

    # 1. Targets
    targets = [
        ProductionTarget(
            target_id=f"TGT-MINE-BCCL-JHARIA-01-{today_str}",
            mine_id="MINE-BCCL-JHARIA-01",
            target_date=today_str,
            daily_target_tonnes=4500.0,
            monthly_target_tonnes=135000.0,
            dispatch_target_tonnes=4300.0,
            set_by="BCCL Corporate Planning",
            created_at=now_utc,
        ),
        ProductionTarget(
            target_id=f"TGT-MINE-MCL-TALCHER-01-{today_str}",
            mine_id="MINE-MCL-TALCHER-01",
            target_date=today_str,
            daily_target_tonnes=12000.0,
            monthly_target_tonnes=360000.0,
            dispatch_target_tonnes=11500.0,
            set_by="MCL Operational Directorate",
            created_at=now_utc,
        ),
        ProductionTarget(
            target_id=f"TGT-MINE-ECL-RANIGANJ-01-{today_str}",
            mine_id="MINE-ECL-RANIGANJ-01",
            target_date=today_str,
            daily_target_tonnes=3200.0,
            monthly_target_tonnes=96000.0,
            dispatch_target_tonnes=3000.0,
            set_by="ECL Planning Department",
            created_at=now_utc,
        ),
    ]
    for t in targets:
        db.save_production_target(t)

    # 2. Check if records already exist for today
    existing = db.list_production_records(mine_id="MINE-BCCL-JHARIA-01", production_date=today_str, limit=1)
    if existing:
        return

    # 3. Jharia Underground Demonstration Mine Records
    jharia_records = [
        ProductionRecordCreate(
            mine_id="MINE-BCCL-JHARIA-01",
            shift_name="Shift A",
            production_date=today_str,
            production_quantity=1480.0,
            production_unit="TONNES",
            dispatch_quantity=1420.0,
            production_source="WEIGHBRIDGE",
            operation_type="UNDERGROUND_EXTRACTION",
            district_section="Seam XI Panel 4",
            face_panel="Face 4A",
            contractor_id="DEPT-BCCL",
            contractor_name="BCCL Departmental Mining",
            contract_type="DEPARTMENTAL",
            target_quantity=1500.0,
            downtime_minutes=20,
            delay_reason="Conveyor belt alignment check",
            entered_by="MANAGER_DESK",
            simulated=True,
            notes="Morning shift baseline extraction",
        ),
        ProductionRecordCreate(
            mine_id="MINE-BCCL-JHARIA-01",
            shift_name="Shift B",
            production_date=today_str,
            production_quantity=1620.0,
            production_unit="TONNES",
            dispatch_quantity=1580.0,
            production_source="SHIFT_REPORT",
            operation_type="UNDERGROUND_EXTRACTION",
            district_section="Seam XI Panel 4",
            face_panel="Face 4B",
            contractor_id="DEPT-BCCL",
            contractor_name="BCCL Departmental Mining",
            contract_type="DEPARTMENTAL",
            target_quantity=1500.0,
            downtime_minutes=0,
            entered_by="SUPERVISOR_DESK",
            simulated=True,
            notes="General production shift",
        ),
        ProductionRecordCreate(
            mine_id="MINE-BCCL-JHARIA-01",
            shift_name="Shift C",
            production_date=today_str,
            production_quantity=1320.0,
            production_unit="TONNES",
            dispatch_quantity=1290.0,
            production_source="WEIGHBRIDGE",
            operation_type="UNDERGROUND_EXTRACTION",
            district_section="Seam X East",
            face_panel="Panel East 2",
            contractor_id="MDO-EASTERN",
            contractor_name="Eastern Mining & Infra MDO",
            contract_type="MDO",
            target_quantity=1500.0,
            downtime_minutes=40,
            delay_reason="Auxiliary fan inspection and cable test",
            entered_by="MDO_SUPERVISOR",
            simulated=True,
            notes="Night shift extraction under MDO agreement",
        ),
    ]
    for r in jharia_records:
        record_production_event(r, actor_id="SEED_LOADER")

    # 4. Talcher Opencast Demonstration Mine Records
    talcher_records = [
        ProductionRecordCreate(
            mine_id="MINE-MCL-TALCHER-01",
            shift_name="Shift A",
            production_date=today_str,
            production_quantity=4100.0,
            production_unit="TONNES",
            dispatch_quantity=4050.0,
            production_source="WEIGHBRIDGE",
            operation_type="OPENCAST_MINING",
            overburden_quantity=12500.0,
            overburden_unit="BCM",
            contractor_id="CONT-TML",
            contractor_name="Talcher Mining Logistics",
            contract_type="WORK_ORDER",
            target_quantity=4000.0,
            downtime_minutes=15,
            delay_reason="Haul truck tire replacement",
            hemm_context="8 Komatsu HD785 Dumpers · 2 Excavators",
            entered_by="MCL_WEIGHBRIDGE_OP",
            simulated=True,
        ),
        ProductionRecordCreate(
            mine_id="MINE-MCL-TALCHER-01",
            shift_name="Shift B",
            production_date=today_str,
            production_quantity=4350.0,
            production_unit="TONNES",
            dispatch_quantity=4300.0,
            production_source="CHP",
            operation_type="OPENCAST_MINING",
            overburden_quantity=13800.0,
            overburden_unit="BCM",
            contractor_id="DEPT-MCL",
            contractor_name="MCL Departmental Fleet",
            contract_type="DEPARTMENTAL",
            target_quantity=4000.0,
            downtime_minutes=0,
            hemm_context="10 Dumpers · 2 Excavators",
            entered_by="MCL_DISPATCHER",
            simulated=True,
        ),
        ProductionRecordCreate(
            mine_id="MINE-MCL-TALCHER-01",
            shift_name="Shift C",
            production_date=today_str,
            production_quantity=3450.0,
            production_unit="TONNES",
            dispatch_quantity=3400.0,
            production_source="WEIGHBRIDGE",
            operation_type="OPENCAST_MINING",
            overburden_quantity=11200.0,
            overburden_unit="BCM",
            contractor_id="CONT-TML",
            contractor_name="Talcher Mining Logistics",
            contract_type="WORK_ORDER",
            target_quantity=4000.0,
            downtime_minutes=55,
            delay_reason="Haul road grading and dust suppression watering",
            hemm_context="6 Dumpers · 1 Excavator · 55m delay",
            entered_by="MCL_WEIGHBRIDGE_OP",
            simulated=True,
        ),
    ]
    for r in talcher_records:
        record_production_event(r, actor_id="SEED_LOADER")

    # 5. Raniganj Underground Demonstration Mine Records
    raniganj_records = [
        ProductionRecordCreate(
            mine_id="MINE-ECL-RANIGANJ-01",
            shift_name="Shift A",
            production_date=today_str,
            production_quantity=1050.0,
            production_unit="TONNES",
            dispatch_quantity=1000.0,
            production_source="SURVEYOR",
            operation_type="UNDERGROUND_EXTRACTION",
            contractor_id="DEPT-ECL",
            contractor_name="ECL Departmental Workforce",
            contract_type="DEPARTMENTAL",
            target_quantity=1066.0,
            downtime_minutes=10,
            entered_by="ECL_SURVEYOR",
            simulated=True,
        ),
        ProductionRecordCreate(
            mine_id="MINE-ECL-RANIGANJ-01",
            shift_name="Shift B",
            production_date=today_str,
            production_quantity=1120.0,
            production_unit="TONNES",
            dispatch_quantity=1100.0,
            production_source="SHIFT_REPORT",
            operation_type="UNDERGROUND_EXTRACTION",
            contractor_id="DEPT-ECL",
            contractor_name="ECL Departmental Workforce",
            contract_type="DEPARTMENTAL",
            target_quantity=1067.0,
            downtime_minutes=0,
            entered_by="ECL_SUPERVISOR",
            simulated=True,
        ),
        ProductionRecordCreate(
            mine_id="MINE-ECL-RANIGANJ-01",
            shift_name="Shift C",
            production_date=today_str,
            production_quantity=980.0,
            production_unit="TONNES",
            dispatch_quantity=950.0,
            production_source="WEIGHBRIDGE",
            operation_type="UNDERGROUND_EXTRACTION",
            contractor_id="DEPT-ECL",
            contractor_name="ECL Departmental Workforce",
            contract_type="DEPARTMENTAL",
            target_quantity=1067.0,
            downtime_minutes=30,
            delay_reason="Shaft winder safety brake test",
            entered_by="ECL_WINDER_ENG",
            simulated=True,
        ),
    ]
    for r in raniganj_records:
        record_production_event(r, actor_id="SEED_LOADER")


def load_governance_hierarchy_seed() -> None:
    """
    Authoritative Governance Hierarchy, Master Organizations & Scope Engine Seed (Phase 2 Task 11).
    Establishes the canonical organizational & operational backbone:
    MINISTRY OF COAL -> CIL -> SUBSIDIARY/ENTITY -> AREA -> MINE -> OPERATIONAL UNITS.
    Also seeds representative contractors, contracts, and workers [DEMO / SIMULATED].
    """
    now = datetime.now(timezone.utc)

    # 1. ORGANIZATIONAL UNITS
    # Ministry of Coal
    db.save_organization_unit(OrganizationUnit(
        id="ORG-MINISTRY-MOC",
        parent_id=None,
        unit_type=OrganizationUnitType.MINISTRY,
        code="MOC",
        name="Ministry of Coal",
        legal_name="Ministry of Coal, Government of India",
        status="ACTIVE",
        state="Delhi",
        district="New Delhi",
        headquarters="Shastri Bhawan, Dr. Rajendra Prasad Road, New Delhi",
        effective_from="1973-01-01",
        created_at=now,
        updated_at=now,
    ))

    # Coal India Limited (CIL)
    db.save_organization_unit(OrganizationUnit(
        id="ORG-CIL-CIL",
        parent_id="ORG-MINISTRY-MOC",
        unit_type=OrganizationUnitType.CIL,
        code="CIL",
        name="Coal India Limited",
        legal_name="Coal India Limited (Maharatna PSU)",
        status="ACTIVE",
        state="West Bengal",
        district="Kolkata",
        headquarters="Coal Bhawan, Premise No-04 MAR, Action Area-1A, Newtown, Rajarhat, Kolkata",
        effective_from="1975-11-01",
        created_at=now,
        updated_at=now,
    ))

    # Subsidiaries & Entities
    subsidiaries_data = [
        ("ORG-SUBSIDIARY-BCCL", "BCCL", "Bharat Coking Coal Limited", "Bharat Coking Coal Limited", "Jharkhand", "Dhanbad", "Koyla Bhawan, Koyla Nagar, Dhanbad, Jharkhand", "1972-01-01", None),
        ("ORG-SUBSIDIARY-ECL", "ECL", "Eastern Coalfields Limited", "Eastern Coalfields Limited", "West Bengal", "Paschim Bardhaman", "Sanctoria, Dishergarh, West Bengal", "1975-11-01", None),
        ("ORG-SUBSIDIARY-MCL", "MCL", "Mahanadi Coalfields Limited", "Mahanadi Coalfields Limited", "Odisha", "Sambalpur", "Jagriti Vihar, Burla, Sambalpur, Odisha", "1992-04-03", None),
        ("ORG-SUBSIDIARY-SECL", "SECL", "South Eastern Coalfields Limited", "South Eastern Coalfields Limited", "Chhattisgarh", "Bilaspur", "Seepat Road, Bilaspur, Chhattisgarh", "1985-11-28", None),
        ("ORG-SUBSIDIARY-CCL", "CCL", "Central Coalfields Limited", "Central Coalfields Limited", "Jharkhand", "Ranchi", "Darbhanga House, Ranchi, Jharkhand", "1975-11-01", None),
        ("ORG-SUBSIDIARY-NCL", "NCL", "Northern Coalfields Limited", "Northern Coalfields Limited", "Madhya Pradesh", "Singrauli", "Singrauli, Madhya Pradesh", "1985-11-28", None),
        ("ORG-SUBSIDIARY-WCL", "WCL", "Western Coalfields Limited", "Western Coalfields Limited", "Maharashtra", "Nagpur", "Coal Estate, Civil Lines, Nagpur, Maharashtra", "1975-11-01", None),
        ("ORG-SUBSIDIARY-CMPDI", "CMPDI", "Central Mine Planning & Design Institute", "Central Mine Planning & Design Institute Limited", "Jharkhand", "Ranchi", "Gondwana Place, Kanke Road, Ranchi, Jharkhand", "1975-11-01", "Planning & Design Consultancy (Non-Coal-Producing)"),
        ("ORG-SUBSIDIARY-NEC", "NEC", "North Eastern Coalfields", "North Eastern Coalfields (Direct CIL Administration)", "Assam", "Tinsukia", "Margherita, Tinsukia, Assam", "1975-11-01", "Directly Administered Unit"),
    ]

    for sid, code, name, legal_name, state, district, hq, eff_from, meta in subsidiaries_data:
        db.save_organization_unit(OrganizationUnit(
            id=sid,
            parent_id="ORG-CIL-CIL",
            unit_type=OrganizationUnitType.SUBSIDIARY,
            code=code,
            name=name,
            legal_name=legal_name,
            status="ACTIVE",
            state=state,
            district=district,
            headquarters=hq,
            effective_from=eff_from,
            metadata=meta,
            created_at=now,
            updated_at=now,
        ))

    # Operational Areas
    areas_data = [
        ("ORG-AREA-BCCL-JHARIA", "ORG-SUBSIDIARY-BCCL", "AREA-JHARIA", "Jharia Area", "Jharkhand", "Dhanbad", "Dhanbad"),
        ("ORG-AREA-ECL-RANIGANJ", "ORG-SUBSIDIARY-ECL", "AREA-RANIGANJ", "Raniganj Area", "West Bengal", "Paschim Bardhaman", "Asansol"),
        ("ORG-AREA-MCL-TALCHER", "ORG-SUBSIDIARY-MCL", "AREA-TALCHER", "Talcher Area", "Odisha", "Angul", "Talcher"),
        ("ORG-AREA-SECL-GEVRA", "ORG-SUBSIDIARY-SECL", "AREA-GEVRA", "Gevra Area", "Chhattisgarh", "Korba", "Gevra Project, Korba"),
    ]

    for aid, pid, code, name, state, district, hq in areas_data:
        db.save_organization_unit(OrganizationUnit(
            id=aid,
            parent_id=pid,
            unit_type=OrganizationUnitType.AREA,
            code=code,
            name=name,
            legal_name=f"{name}, {pid.split('-')[-1]}",
            status="ACTIVE",
            state=state,
            district=district,
            headquarters=hq,
            effective_from="1980-01-01",
            created_at=now,
            updated_at=now,
        ))

    # Mines (Canonical OrganizationUnit representation)
    mines_data = [
        ("ORG-MINE-BCCL-JHARIA-UG", "ORG-AREA-BCCL-JHARIA", "MINE-BCCL-JHARIA-01", "Jharia Underground Demonstration Mine", "Jharkhand", "Dhanbad"),
        ("ORG-MINE-ECL-RANIGANJ-UG", "ORG-AREA-ECL-RANIGANJ", "MINE-ECL-RANIGANJ-01", "Raniganj Underground Demonstration Mine", "West Bengal", "Paschim Bardhaman"),
        ("ORG-MINE-MCL-TALCHER-OC", "ORG-AREA-MCL-TALCHER", "MINE-MCL-TALCHER-01", "Talcher Opencast Demonstration Mine", "Odisha", "Angul"),
        ("ORG-MINE-SECL-GEVRA-OC", "ORG-AREA-SECL-GEVRA", "MINE-SECL-GEVRA-01", "Gevra Opencast Demonstration Mine", "Chhattisgarh", "Korba"),
    ]

    for mid, pid, code, name, state, district in mines_data:
        db.save_organization_unit(OrganizationUnit(
            id=mid,
            parent_id=pid,
            unit_type=OrganizationUnitType.MINE,
            code=code,
            name=name,
            legal_name=name,
            status="ACTIVE",
            state=state,
            district=district,
            effective_from="1990-01-01",
            created_at=now,
            updated_at=now,
        ))

    # 2. OPERATIONAL UNITS
    # Jharia Underground Mine (Underground hierarchy: Shaft -> District -> Panel -> Section -> Face)
    jharia_op = [
        ("OP-SHAFT-JHARIA-01", "MINE-BCCL-JHARIA-01", None, OperationalUnitType.SHAFT_INCLINE, "SH-02", "Shaft No. 2 Pit Incline"),
        ("OP-DIST-JHARIA-01", "MINE-BCCL-JHARIA-01", "OP-SHAFT-JHARIA-01", OperationalUnitType.VENTILATION_DISTRICT, "VD-S1", "Ventilation District South-1"),
        ("OP-PANEL-JHARIA-01", "MINE-BCCL-JHARIA-01", "OP-DIST-JHARIA-01", OperationalUnitType.PANEL, "PN-4E", "Panel 4-East Depillaring"),
        ("OP-SEC-JHARIA-01", "MINE-BCCL-JHARIA-01", "OP-PANEL-JHARIA-01", OperationalUnitType.SECTION, "SC-A", "Section A Bord & Pillar"),
        ("OP-FACE-JHARIA-01", "MINE-BCCL-JHARIA-01", "OP-SEC-JHARIA-01", OperationalUnitType.WORKING_FACE, "WF-14", "Working Face 14 Continuous Extraction"),
    ]
    for oid, mid, parent_op, utype, code, name in jharia_op:
        db.save_operational_unit(OperationalUnit(
            id=oid,
            mine_id=mid,
            parent_operational_unit_id=parent_op,
            unit_type=utype,
            code=code,
            name=name,
            active=True,
            created_at=now,
            updated_at=now,
        ))

    # Talcher Opencast Mine (Opencast hierarchy: Pit -> Bench / Haul Road / Dump / HEMM Park)
    talcher_op = [
        ("OP-PIT-TALCHER-01", "MINE-MCL-TALCHER-01", None, OperationalUnitType.PIT, "PIT-01S", "Pit No. 1 South"),
        ("OP-BENCH-TALCHER-01", "MINE-MCL-TALCHER-01", "OP-PIT-TALCHER-01", OperationalUnitType.BENCH, "BN-C3", "Coal Bench Level 3"),
        ("OP-ROAD-TALCHER-01", "MINE-MCL-TALCHER-01", "OP-PIT-TALCHER-01", OperationalUnitType.HAUL_ROAD, "HR-W1", "Main Haul Road West"),
        ("OP-DUMP-TALCHER-01", "MINE-MCL-TALCHER-01", "OP-PIT-TALCHER-01", OperationalUnitType.DUMP_STOCK, "OB-D1", "Overburden Dump Yard North"),
        ("OP-HEMM-TALCHER-01", "MINE-MCL-TALCHER-01", "OP-PIT-TALCHER-01", OperationalUnitType.HEMM_PARK, "HP-01", "HEMM Maintenance & Parking Bay"),
    ]
    for oid, mid, parent_op, utype, code, name in talcher_op:
        db.save_operational_unit(OperationalUnit(
            id=oid,
            mine_id=mid,
            parent_operational_unit_id=parent_op,
            unit_type=utype,
            code=code,
            name=name,
            active=True,
            created_at=now,
            updated_at=now,
        ))

    # Gevra Opencast Mine
    gevra_op = [
        ("OP-PIT-GEVRA-01", "MINE-SECL-GEVRA-01", None, OperationalUnitType.PIT, "PIT-MEGA", "Mega Pit Block A"),
        ("OP-BENCH-GEVRA-01", "MINE-SECL-GEVRA-01", "OP-PIT-GEVRA-01", OperationalUnitType.BENCH, "BN-OB1", "Overburden Bench Level 1"),
        ("OP-ROAD-GEVRA-01", "MINE-SECL-GEVRA-01", "OP-PIT-GEVRA-01", OperationalUnitType.HAUL_ROAD, "HR-CH1", "Central Heavy Haul Road"),
        ("OP-DUMP-GEVRA-01", "MINE-SECL-GEVRA-01", "OP-PIT-GEVRA-01", OperationalUnitType.DUMP_STOCK, "OB-D2", "External Waste Dump Yard 02"),
        ("OP-HEMM-GEVRA-01", "MINE-SECL-GEVRA-01", "OP-PIT-GEVRA-01", OperationalUnitType.HEMM_PARK, "HP-240T", "240T Dumper Park & Dispatch Bay"),
    ]
    for oid, mid, parent_op, utype, code, name in gevra_op:
        db.save_operational_unit(OperationalUnit(
            id=oid,
            mine_id=mid,
            parent_operational_unit_id=parent_op,
            unit_type=utype,
            code=code,
            name=name,
            active=True,
            created_at=now,
            updated_at=now,
        ))

    # 3. CONTRACTOR MASTER
    contractors_data = [
        ("CONT-BCCL-DEPT", "BCCL Departmental Operations", "BCCL Departmental Workforce", "REG-DEPT-BCCL-01", ContractorType.DEPARTMENTAL),
        ("CONT-ECL-DEPT", "ECL Departmental Operations", "ECL Departmental Workforce", "REG-DEPT-ECL-01", ContractorType.DEPARTMENTAL),
        ("CONT-MCL-DEPT", "MCL Departmental Operations", "MCL Departmental Workforce", "REG-DEPT-MCL-01", ContractorType.DEPARTMENTAL),
        ("CONT-SECL-DEPT", "SECL Departmental Operations", "SECL Departmental Workforce", "REG-DEPT-SECL-01", ContractorType.DEPARTMENTAL),
        ("CONT-TML", "Tata Mining Logistics Limited", "TML Logistics", "CIN-U10100WB2005PLC102938", ContractorType.WORK_ORDER),
        ("CONT-EMD-MDO", "Eastern Mining Developers Limited", "EMD Mining MDO", "CIN-U10100JH2012PLC049581", ContractorType.MDO),
        ("CONT-SGS-SRV", "SGS Mineral Quality Services Ltd", "SGS Quality Assurance", "CIN-U74140MH2001PLC132910", ContractorType.SERVICE),
    ]

    for cid, legal_name, display_name, reg_ref, ctype in contractors_data:
        db.save_contractor(ContractorMaster(
            id=cid,
            legal_name=legal_name,
            display_name=display_name,
            registration_reference=reg_ref,
            status="ACTIVE",
            contractor_type=ctype,
            created_at=now,
            updated_at=now,
        ))

    # 4. CONTRACT MASTER
    contracts_data = [
        ("CNTR-BCCL-JHARIA-01", "CONT-BCCL-DEPT", "MINE-BCCL-JHARIA-01", "ORG-AREA-BCCL-JHARIA", "ORG-SUBSIDIARY-BCCL", ContractorType.DEPARTMENTAL, "DEPT-BCCL-JHA-2024", "Statutory Departmental Coal Extraction", "2024-01-01", "2027-12-31", 350),
        ("CNTR-BCCL-JHARIA-02", "CONT-TML", "MINE-BCCL-JHARIA-01", "ORG-AREA-BCCL-JHARIA", "ORG-SUBSIDIARY-BCCL", ContractorType.WORK_ORDER, "WO-TML-JHA-2024-09", "Overburden Removal & Pit Head Haulage", "2024-04-01", "2026-03-31", 120),
        ("CNTR-MCL-TALCHER-01", "CONT-MCL-DEPT", "MINE-MCL-TALCHER-01", "ORG-AREA-MCL-TALCHER", "ORG-SUBSIDIARY-MCL", ContractorType.DEPARTMENTAL, "DEPT-MCL-TAL-2024", "Opencast Highwall Mining Operations", "2024-01-01", "2027-12-31", 400),
        ("CNTR-SECL-GEVRA-01", "CONT-EMD-MDO", "MINE-SECL-GEVRA-01", "ORG-AREA-SECL-GEVRA", "ORG-SUBSIDIARY-SECL", ContractorType.MDO, "MDO-SECL-GEV-2023-01", "Full Mine Developer & Operator (MDO) Package", "2023-04-01", "2033-03-31", 600),
    ]

    for cid, contractor_id, mine_id, area_id, sub_id, ctype, cnum, scope, sdate, edate, limit in contracts_data:
        db.save_contract(ContractMaster(
            id=cid,
            contractor_id=contractor_id,
            mine_id=mine_id,
            area_id=area_id,
            subsidiary_id=sub_id,
            contract_type=ctype,
            contract_number=cnum,
            scope=scope,
            start_date=sdate,
            end_date=edate,
            workforce_limit=limit,
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        ))

    # 5. WORKER MASTER [DEMO / SIMULATED]
    workers_data = [
        ("WRK-EMP-001", "BCCL-EMP-10492", "Rajesh Kumar Sharma [DEMO / SIMULATED]", WorkerType.DEPARTMENTAL, "CONT-BCCL-DEPT", "CNTR-BCCL-JHARIA-01", "MINE-BCCL-JHARIA-01", "SKILLED", "MINING", "2018-05-10", "VALID", "GOV-ID-91823"),
        ("WRK-TML-002", "TML-WRK-8291", "Suresh Bauri [DEMO / SIMULATED]", WorkerType.CONTRACTOR, "CONT-TML", "CNTR-BCCL-JHARIA-02", "MINE-BCCL-JHARIA-01", "HEAVY_OPERATOR", "HAULAGE", "2024-04-15", "VALID", "AADHAAR-XXXX-1928"),
        ("WRK-TML-003", "TML-WRK-8292", "Ramesh Hembram [DEMO / SIMULATED]", WorkerType.CONTRACTOR, "CONT-TML", "CNTR-BCCL-JHARIA-02", "MINE-BCCL-JHARIA-01", "SEMI_SKILLED", "VENTILATION", "2024-04-20", "VALID", "AADHAAR-XXXX-3819"),
        ("WRK-MCL-004", "MCL-EMP-40192", "Dilip Mahato [DEMO / SIMULATED]", WorkerType.DEPARTMENTAL, "CONT-MCL-DEPT", "CNTR-MCL-TALCHER-01", "MINE-MCL-TALCHER-01", "SUPERVISORY", "BLASTING", "2015-08-01", "VALID", "GOV-ID-88291"),
        ("WRK-MDO-005", "EMD-MDO-0193", "Vikas Singh [DEMO / SIMULATED]", WorkerType.MDO, "CONT-EMD-MDO", "CNTR-SECL-GEVRA-01", "MINE-SECL-GEVRA-01", "HEMM_OPERATOR", "EXCAVATION", "2023-05-01", "VALID", "AADHAAR-XXXX-9912"),
    ]

    for wid, wcode, name, wtype, contractor_id, contract_id, mine_id, skill, dept, ondate, trn_status, ident in workers_data:
        db.save_worker(WorkerMaster(
            id=wid,
            worker_code=wcode,
            name=name,
            worker_type=wtype,
            contractor_id=contractor_id,
            contract_id=contract_id,
            mine_id=mine_id,
            skill_category=skill,
            department=dept,
            active=True,
            onboarding_date=ondate,
            training_status=trn_status,
            identity_reference=ident,
            created_at=now,
            updated_at=now,
        ))


def load_environmental_governance_seed() -> None:
    """
    Seed idempotent demonstration parameters, configurable thresholds,
    statutory obligations, schedules, and representative measurements for PRITHVI Task 13.
    """
    now = datetime.now(timezone.utc)

    # 1. Environmental Parameters Master
    parameters_data = [
        ("PARAM-AIR-PM10", "ENV-AIR-PM10", "Respirable Particulate Matter (PM10)", EnvironmentalDomain.AIR, "µg/m³", "Ambient air PM10 concentration in mining and leasehold zone.", "ALL"),
        ("PARAM-AIR-PM25", "ENV-AIR-PM25", "Fine Particulate Matter (PM2.5)", EnvironmentalDomain.AIR, "µg/m³", "Fine airborne respirable particulate matter.", "ALL"),
        ("PARAM-AIR-DUST", "ENV-AIR-DUST", "Workplace Dust Concentration", EnvironmentalDomain.AIR, "mg/m³", "Active haul road and transfer point workplace dust.", "ALL"),
        ("PARAM-WATER-PH", "ENV-WATER-PH", "Mine Water Discharge pH", EnvironmentalDomain.WATER, "pH", "Acidity/alkalinity of treated mine effluent discharge.", "ALL"),
        ("PARAM-WATER-TDS", "ENV-WATER-TDS", "Total Dissolved Solids (TDS)", EnvironmentalDomain.WATER, "mg/l", "Total dissolved mineral solids in mine sump discharge.", "ALL"),
        ("PARAM-WATER-TSS", "ENV-WATER-TSS", "Total Suspended Solids (TSS)", EnvironmentalDomain.WATER, "mg/l", "Suspended sediment concentration in settling ponds.", "ALL"),
        ("PARAM-NOISE-DAY", "ENV-NOISE-DAY", "Ambient Noise Level (Daytime)", EnvironmentalDomain.NOISE, "dB(A)", "Daytime equivalent continuous sound level (Leq).", "ALL"),
        ("PARAM-NOISE-NIGHT", "ENV-NOISE-NIGHT", "Ambient Noise Level (Night-time)", EnvironmentalDomain.NOISE, "dB(A)", "Night-time ambient noise at industrial boundary.", "ALL"),
        ("PARAM-VIB-PPV", "ENV-VIB-PPV", "Blasting Ground Vibration (PPV)", EnvironmentalDomain.VIBRATION, "mm/s", "Peak Particle Velocity recorded at nearest structural station.", "OPENCAST"),
        ("PARAM-LAND-SLOPE", "ENV-LAND-SLOPE", "Overburden Dump Slope Angle", EnvironmentalDomain.LAND, "degrees", "Overall slope angle of active overburden dumps.", "OPENCAST"),
        ("PARAM-REC-SURV", "ENV-REC-SURV", "Plantation Survival Rate", EnvironmentalDomain.RECLAMATION, "%", "Survival percentage of afforestation green belt saplings.", "ALL"),
        ("PARAM-WASTE-OIL", "ENV-WASTE-OIL", "Used Oil Storage Compliance", EnvironmentalDomain.WASTE, "KL", "Hazardous used lubricant containment and licensed disposal.", "ALL"),
        ("PARAM-AIR-VENT-CH4", "ENV-AIR-VENT-CH4", "Ventilation Exhaust Methane", EnvironmentalDomain.AIR, "%", "Underground main return airway methane concentration.", "UNDERGROUND"),
    ]

    for pid, code, name, domain, unit, desc, app_type in parameters_data:
        db.save_environmental_parameter(EnvironmentalParameter(
            id=pid,
            code=code,
            name=name,
            domain=domain,
            unit=unit,
            description=desc,
            mine_type_applicability=app_type,
            active=True,
            created_at=now,
            updated_at=now,
        ))

    # 2. Configurable Threshold Rules [DEMO / CONFIGURED RULE]
    thresholds_data = [
        ("TH-AIR-PM10-OC", "PARAM-AIR-PM10", "OPENCAST", "MAX_LIMIT", None, 300.0, "µg/m³", "HIGH", "DEMO / CONFIGURED RULE (National Ambient Air Quality Standard - Mining Zone)"),
        ("TH-AIR-PM10-UG", "PARAM-AIR-PM10", "UNDERGROUND", "MAX_LIMIT", None, 100.0, "µg/m³", "HIGH", "DEMO / CONFIGURED RULE (Surface Buffer Ambient Limit)"),
        ("TH-AIR-PM25-ALL", "PARAM-AIR-PM25", "ALL", "MAX_LIMIT", None, 120.0, "µg/m³", "HIGH", "DEMO / CONFIGURED RULE (CPCB 24-hr Mining Area Standard)"),
        ("TH-WATER-PH-ALL", "PARAM-WATER-PH", "ALL", "RANGE", 6.5, 8.5, "pH", "HIGH", "DEMO / CONFIGURED RULE (Effluent Discharge General Standards)"),
        ("TH-WATER-TSS-ALL", "PARAM-WATER-TSS", "ALL", "MAX_LIMIT", None, 100.0, "mg/l", "MEDIUM", "DEMO / CONFIGURED RULE (EPA Schedule VI Discharge Standard)"),
        ("TH-NOISE-DAY-ALL", "PARAM-NOISE-DAY", "ALL", "MAX_LIMIT", None, 75.0, "dB(A)", "MEDIUM", "DEMO / CONFIGURED RULE (Industrial Ambient Noise Norm)"),
        ("TH-VIB-PPV-OC", "PARAM-VIB-PPV", "OPENCAST", "MAX_LIMIT", None, 10.0, "mm/s", "CRITICAL", "DEMO / CONFIGURED RULE (DGMS Tech Circular 1997 Permissible PPV)"),
        ("TH-LAND-SLOPE-OC", "PARAM-LAND-SLOPE", "OPENCAST", "MAX_LIMIT", None, 28.0, "degrees", "HIGH", "DEMO / CONFIGURED RULE (DGMS Circular Overburden Stability Limit)"),
        ("TH-REC-SURV-ALL", "PARAM-REC-SURV", "ALL", "MIN_LIMIT", 70.0, None, "%", "MEDIUM", "DEMO / CONFIGURED RULE (MoEFCC Green Belt Survival Stipulation)"),
    ]

    for tid, param_id, mtype, ttype, lower, upper, unit, sev, sref in thresholds_data:
        db.save_environmental_threshold(EnvironmentalThreshold(
            id=tid,
            parameter_id=param_id,
            mine_type=mtype,
            threshold_type=ttype,
            lower_limit=lower,
            upper_limit=upper,
            unit=unit,
            severity=sev,
            source_reference=sref,
            is_demo_rule=True,
            active=True,
            created_at=now,
        ))

    # 3. Environmental Statutory Obligations
    obligations_data = [
        ("ENV-OB-JHA-01", "MINE-BCCL-JHARIA-01", "CTO-JHA-WAT-01", "Consent to Operate (CTO) Mine Water Discharge Quality Monitoring", "Monthly laboratory testing of treated mine water discharge from main sump.", EnvironmentalDomain.WATER, "UNDERGROUND", "MONTHLY", "ENVIRONMENTAL_OFFICER", "MoEFCC / JSPCB Consent to Operate Order 2023", "NABL Lab Test Report"),
        ("ENV-OB-JHA-02", "MINE-BCCL-JHARIA-01", "EC-JHA-AIR-02", "Ambient Air & Surface Shaft Exhaust Dust Monitoring", "Fortnightly measurement of PM10 and PM2.5 at surface fan house and pit-head.", EnvironmentalDomain.AIR, "UNDERGROUND", "FORTNIGHTLY", "ENVIRONMENTAL_OFFICER", "MoEFCC Environmental Clearance Specific Condition IV", "CAAQMS Log & Filter Paper"),
        ("ENV-OB-TAL-01", "MINE-MCL-TALCHER-01", "EC-TAL-AIR-01", "Haul Road Particulate & Ambient Dust Monitoring", "Continuous and mobile monitoring of respirable dust on coal transportation corridor.", EnvironmentalDomain.AIR, "OPENCAST", "DAILY", "ENVIRONMENTAL_OFFICER", "MoEFCC Clearance Condition (Haul Road Suppression)", "Dustrak / High Volume Sampler"),
        ("ENV-OB-TAL-02", "MINE-MCL-TALCHER-01", "DGMS-TAL-VIB-01", "Statutory Blasting Ground Vibration (PPV) Recording", "Seismograph recording of blast-induced ground vibration at nearest lease boundary.", EnvironmentalDomain.VIBRATION, "OPENCAST", "EVENT_TRIGGERED", "SURVEYOR", "DGMS Technical Circular 7 of 1997", "Minimate Seismograph Chart"),
        ("ENV-OB-TAL-03", "MINE-MCL-TALCHER-01", "EC-TAL-DUMP-01", "Overburden Dump Slope Stability Inspection", "Geotechnical survey and visual inspection of internal & external overburden dumps.", EnvironmentalDomain.LAND, "OPENCAST", "MONTHLY", "MINE_MANAGER", "DGMS Guidelines for Scientific Dump Design", "Total Station Slope Profile"),
        ("ENV-OB-GEV-01", "MINE-SECL-GEVRA-01", "EC-GEV-NOISE-01", "Heavy Earthmoving Machinery Acoustic Boundary Compliance", "Day and night noise level monitoring around active extraction face and workshops.", EnvironmentalDomain.NOISE, "OPENCAST", "MONTHLY", "ENVIRONMENTAL_OFFICER", "MoEFCC EC Specific Condition (Noise Suppression)", "Class 1 Sound Level Meter Log"),
    ]

    for oid, mid, code, title, desc, dom, mtype, freq, role, sref, reqs in obligations_data:
        db.save_environmental_obligation(EnvironmentalObligation(
            obligation_id=oid,
            mine_id=mid,
            code=code,
            title=title,
            description=desc,
            domain=dom,
            applicable_mine_type=mtype,
            frequency=freq,
            responsible_role=role,
            regulatory_source=sref,
            evidence_requirements=reqs,
            active=True,
            start_date="2024-01-01",
            created_at=now,
        ))

    # 4. Monitoring Schedules
    today_str = now.strftime("%Y-%m-%d")
    schedules_data = [
        ("SCH-JHA-01", "ENV-OB-JHA-01", "MINE-BCCL-JHARIA-01", "PARAM-WATER-PH", None, EnvironmentalDomain.WATER, today_str, "ENVIRONMENTAL_OFFICER", "VERIFIED", "2026-09-14T10:00:00Z"),
        ("SCH-JHA-02", "ENV-OB-JHA-02", "MINE-BCCL-JHARIA-01", "PARAM-AIR-PM10", None, EnvironmentalDomain.AIR, today_str, "ENVIRONMENTAL_OFFICER", "SCHEDULED", None),
        ("SCH-TAL-01", "ENV-OB-TAL-01", "MINE-MCL-TALCHER-01", "PARAM-AIR-PM10", "OP-ROAD-TALCHER-01", EnvironmentalDomain.AIR, today_str, "ENVIRONMENTAL_OFFICER", "NON_COMPLIANT", None),
        ("SCH-TAL-02", "ENV-OB-TAL-02", "MINE-MCL-TALCHER-01", "PARAM-VIB-PPV", "OP-PIT-TALCHER-01", EnvironmentalDomain.VIBRATION, today_str, "SURVEYOR", "VERIFIED", "2026-09-15T08:30:00Z"),
        ("SCH-TAL-03", "ENV-OB-TAL-03", "MINE-MCL-TALCHER-01", "PARAM-LAND-SLOPE", "OP-DUMP-TALCHER-01", EnvironmentalDomain.LAND, "2026-09-20", "MINE_MANAGER", "SCHEDULED", None),
        ("SCH-GEV-01", "ENV-OB-GEV-01", "MINE-SECL-GEVRA-01", "PARAM-NOISE-DAY", "OP-PIT-GEVRA-01", EnvironmentalDomain.NOISE, today_str, "ENVIRONMENTAL_OFFICER", "SCHEDULED", None),
    ]

    for sid, oid, mid, pid, op_id, dom, ddate, role, stat, comp in schedules_data:
        db.save_environmental_schedule(EnvironmentalSchedule(
            schedule_id=sid,
            obligation_id=oid,
            mine_id=mid,
            parameter_id=pid,
            operational_unit_id=op_id,
            domain=dom,
            due_date=ddate,
            responsible_role=role,
            status=stat,
            completed_at=comp,
            created_at=now,
        ))

    # 5. Representative Measurements [SIMULATED]
    measurements_data = [
        ("ENV-MEAS-JHA-001", "MINE-BCCL-JHARIA-01", None, "PARAM-WATER-PH", 7.3, "pH", "2026-09-14T09:30:00Z", EnvironmentalSourceType.FIELD_OBSERVATION, "Discharge Weirs Sump 4", "RECORDED", DataQualityStatus.VALID, False),
        ("ENV-MEAS-JHA-002", "MINE-BCCL-JHARIA-01", None, "PARAM-AIR-PM10", 78.4, "µg/m³", "2026-09-14T14:15:00Z", EnvironmentalSourceType.SIMULATED, "Surface Pit Head Monitor", "RECORDED", DataQualityStatus.VALID, True),
        ("ENV-MEAS-JHA-003", "MINE-BCCL-JHARIA-01", None, "PARAM-NOISE-DAY", 64.2, "dB(A)", "2026-09-14T11:00:00Z", EnvironmentalSourceType.SIMULATED, "Colliery Boundary North", "RECORDED", DataQualityStatus.VALID, True),
        # Talcher Opencast - VIOLATION (342.5 µg/m³ vs 300.0 threshold)
        ("ENV-MEAS-TAL-001", "MINE-MCL-TALCHER-01", "OP-ROAD-TALCHER-01", "PARAM-AIR-PM10", 342.5, "µg/m³", "2026-09-15T08:45:00Z", EnvironmentalSourceType.FIELD_OBSERVATION, "Mobile Monitor Station West", "FLAGGED_ANOMALY", DataQualityStatus.VALID, True),
        ("ENV-MEAS-TAL-002", "MINE-MCL-TALCHER-01", "OP-PIT-TALCHER-01", "PARAM-VIB-PPV", 6.8, "mm/s", "2026-09-15T08:30:00Z", EnvironmentalSourceType.FIELD_OBSERVATION, "Seismograph Station B", "RECORDED", DataQualityStatus.VALID, True),
        ("ENV-MEAS-TAL-003", "MINE-MCL-TALCHER-01", "OP-DUMP-TALCHER-01", "PARAM-LAND-SLOPE", 24.5, "degrees", "2026-09-13T16:00:00Z", EnvironmentalSourceType.MANUAL_ENTRY, "Surveyor Clinometer Check", "RECORDED", DataQualityStatus.VALID, True),
        ("ENV-MEAS-GEV-001", "MINE-SECL-GEVRA-01", "OP-PIT-GEVRA-01", "PARAM-NOISE-DAY", 71.8, "dB(A)", "2026-09-15T10:00:00Z", EnvironmentalSourceType.SIMULATED, "Active Face Zone A", "RECORDED", DataQualityStatus.VALID, True),
    ]

    for mid, mine_id, op_id, pid, val, unit, mtime, stype, sref, stat, dq_stat, sim in measurements_data:
        m_dt = datetime.fromisoformat(mtime.replace("Z", "+00:00"))
        db.save_environmental_measurement(EnvironmentalMeasurement(
            id=mid,
            mine_id=mine_id,
            operational_unit_id=op_id,
            parameter_id=pid,
            value=val,
            unit=unit,
            measured_at=m_dt,
            source_type=stype,
            source_reference=sref,
            entered_by="ENV_INSPECTOR_DEMO",
            status=stat,
            data_quality_status=dq_stat,
            simulated=sim,
            created_at=now,
            updated_at=now,
        ))

    # 6. Seed Compliance Case and Corrective Action for the Talcher violation
    case_id = "CASE-ENV-TALCHER-01"
    db.save_compliance_case(ComplianceCase(
        case_id=case_id,
        mine_id="MINE-MCL-TALCHER-01",
        inspection_id=None,
        finding_id=None,
        category="AIR",
        regulation_reference="MoEFCC / CPCB Ambient Air Quality Standards",
        title="Environmental Violation: PM10 Exceeded on Haul Road",
        description="Statutory PM10 breach recorded at Talcher Opencast Mine. Observed: 342.5 µg/m³ (Limit: 300.0 µg/m³). Inadequate water sprinkling identified.",
        severity="HIGH",
        risk_level="HIGH",
        status=CaseStatus.ACTION_REQUIRED,
        source_type=CaseSourceType.ENVIRONMENTAL_VIOLATION,
        source_id="ENV-MEAS-TAL-001",
        created_at=now,
        updated_at=now,
    ))

    db.save_corrective_action(CorrectiveAction(
        action_id="ACT-ENV-TALCHER-01",
        case_id=case_id,
        finding_id=None,
        mine_id="MINE-MCL-TALCHER-01",
        title="Deploy Additional Water Tanker on Haul Road West",
        description="Increase water tanker suppression frequency from 2 to 4 runs per shift on Main Haul Road West.",
        assigned_role="ENVIRONMENTAL_OFFICER",
        assigned_to="Dilip Mahato",
        priority="HIGH",
        status="OPEN",
        created_at=now,
        updated_at=now,
    ))

    # 7. Sample Traceable Regulatory Report
    report_id = "ENV-REP-TALCHER-202609"
    lineage = {
        "mine": {"id": "MINE-MCL-TALCHER-01", "name": "Talcher Opencast Demonstration Mine"},
        "area": {"id": "ORG-AREA-MCL-TALCHER", "name": "Talcher Area"},
        "subsidiary": {"id": "ORG-SUBSIDIARY-MCL", "name": "Mahanadi Coalfields Limited"},
        "holding_company": {"id": "ORG-CIL-CIL", "name": "Coal India Limited"},
        "ministry": {"id": "ORG-MINISTRY-MOC", "name": "Ministry of Coal"},
    }
    summary_info = {
        "mine_name": "Talcher Opencast Demonstration Mine",
        "mine_type": "opencast_coal",
        "total_measurements": 3,
        "violations_count": 1,
        "open_cases_count": 1,
        "reporting_period": "2026-09-01 to 2026-09-15",
        "governance_note": "Generated from authoritative PRITHVI database records. Traceable to Ministry of Coal.",
    }
    content_hash = "8f3b26c04e3895e84a7e390c883e4c4ef1e976c66cf1c7de29f3458e0a15b3c4"
    ipfs_cid = "bafkreiavw26h77l2sqcswm6nypld4v47o6q7f33k6z5mhy3x33r57qgeea"

    db.save_environmental_report(EnvironmentalReport(
        report_id=report_id,
        mine_id="MINE-MCL-TALCHER-01",
        reporting_period_start="2026-09-01",
        reporting_period_end="2026-09-15",
        title="Statutory Environmental Governance Report: Talcher Opencast (Fortnightly)",
        report_type="MONITORING_SUMMARY",
        status="FINALIZED",
        summary=json.dumps(summary_info),
        measurements_count=3,
        violations_count=1,
        open_cases_count=1,
        corrective_actions_count=1,
        lineage_snapshot=json.dumps(lineage),
        content_hash=content_hash,
        ipfs_cid=ipfs_cid,
        generated_by="ENVIRONMENTAL_OFFICER",
        generated_at=now,
        finalized_at=now,
        finalized_by="REGULATORY_OFFICER",
    ))


def seed_initial_data() -> None:
    """
    Entry point for initial PRITHVI seed loading.
    """
    load_mine_seed()
    load_regulatory_seed()
    load_schedule_seed()
    load_mine_zones_and_coordinates_seed()
    load_sensor_seed()
    load_production_seed()
    load_governance_hierarchy_seed()
    load_environmental_governance_seed()