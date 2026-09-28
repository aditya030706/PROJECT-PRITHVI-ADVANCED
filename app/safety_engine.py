"""
PRITHVI — Safety Threshold Engine (Phase 2 Task 9)
==================================================

Evaluates incoming SCADA / IoT telemetry readings against transparent,
explainable safety limits.

Distinguishes explicitly between:
- Statutory regulations (CMR 2017) where an established statutory limit exists
- "Demo safety threshold" for demonstrative geotechnical & environmental sensors

Returns deterministic threshold classifications: NORMAL, WARNING, CRITICAL.
"""

from __future__ import annotations
from typing import NamedTuple, Optional
from .models import SensorType, ThresholdStatus


class SafetyEvaluationResult(NamedTuple):
    status: ThresholdStatus
    status_label: str
    threshold_definition: str
    explanation: str
    is_statutory: bool
    regulation_reference: Optional[str] = None


# Authoritative, transparent threshold configurations
THRESHOLD_RULES = {
    SensorType.METHANE.value: {
        "label": "Methane Concentration",
        "unit": "%",
        "warning_threshold": 0.8,
        "critical_threshold": 1.25,
        "is_statutory": True,
        "regulation": "CMR 2017 Regulation 119 & 156 (Permissible Inflammable Gas Concentration)",
        "warn_def": "Methane concentration > 0.8% (approaching statutory limit)",
        "crit_def": "Methane concentration ≥ 1.25% (statutory withdrawal & power isolation limit)",
        "safe_def": "Methane concentration < 0.8% (within normal atmospheric range)",
        "min_bound": 0.0,
        "max_bound": 100.0,
    },
    SensorType.AIRFLOW.value: {
        "label": "Airflow",
        "unit": "m³/s",
        "warning_threshold": 15.0,
        "critical_threshold": 8.0,
        "is_statutory": True,
        "regulation": "CMR 2017 Regulation 119 (Adequate Underground Airway Dilution)",
        "warn_def": "Airflow < 15.0 m³/s (reduced ventilation velocity)",
        "crit_def": "Airflow < 8.0 m³/s (severe stagnation, statutory dilution failure)",
        "safe_def": "Airflow ≥ 15.0 m³/s (normal ventilation velocity)",
        "min_bound": 0.0,
        "max_bound": 300.0,
    },
    SensorType.VENTILATION_FAN.value: {
        "label": "Ventilation Fan",
        "unit": "RPM",
        "warning_threshold": 800.0,
        "critical_threshold": 500.0,
        "is_statutory": True,
        "regulation": "CMR 2017 Regulation 119 (Continuous Mechanical Ventilator Operation)",
        "warn_def": "Main fan speed < 800 RPM (reduced ventilation extraction capacity)",
        "crit_def": "Main fan speed < 500 RPM (critical degradation / fan stall hazard)",
        "safe_def": "Main fan operating at rated nominal speed (≥ 800 RPM)",
        "min_bound": 0.0,
        "max_bound": 3000.0,
    },
    SensorType.DUST.value: {
        "label": "Dust Concentration",
        "unit": "mg/m³",
        "warning_threshold": 2.0,
        "critical_threshold": 3.0,
        "is_statutory": True,
        "regulation": "CMR 2017 Regulation 124 (Permissible Limit of Respirable Dust)",
        "warn_def": "Dust concentration > 2.0 mg/m³ (elevated particulate concentration)",
        "crit_def": "Dust concentration ≥ 3.0 mg/m³ (statutory respirable dust limit exceeded)",
        "safe_def": "Dust concentration ≤ 2.0 mg/m³ (within statutory occupational limits)",
        "min_bound": 0.0,
        "max_bound": 150.0,
    },
    SensorType.SLOPE_DISPLACEMENT.value: {
        "label": "Slope Displacement",
        "unit": "mm",
        "warning_threshold": 25.0,
        "critical_threshold": 50.0,
        "is_statutory": False,
        "regulation": "Demo safety threshold (Geotechnical Highwall & Bench Monitoring)",
        "warn_def": "Highwall displacement > 25.0 mm (accelerating tension crack velocity)",
        "crit_def": "Highwall displacement > 50.0 mm (imminent bench instability alert)",
        "safe_def": "Highwall displacement ≤ 25.0 mm (stable geological bench profile)",
        "min_bound": 0.0,
        "max_bound": 500.0,
    },
    SensorType.PORE_PRESSURE.value: {
        "label": "Pore Pressure",
        "unit": "kPa",
        "warning_threshold": 180.0,
        "critical_threshold": 250.0,
        "is_statutory": False,
        "regulation": "Demo safety threshold (Spoil Dump & Overburden Saturation Stability)",
        "warn_def": "Pore pressure > 180.0 kPa (elevated phreatic surface in spoil dump)",
        "crit_def": "Pore pressure > 250.0 kPa (critical saturation, liquefaction risk)",
        "safe_def": "Pore pressure ≤ 180.0 kPa (normal dump drainage equilibrium)",
        "min_bound": 0.0,
        "max_bound": 1000.0,
    },
    SensorType.RAINFALL.value: {
        "label": "Rainfall",
        "unit": "mm/hr",
        "warning_threshold": 25.0,
        "critical_threshold": 50.0,
        "is_statutory": False,
        "regulation": "Demo safety threshold (CMR 2017 Reg 145 Danger Protocol Reference)",
        "warn_def": "Precipitation rate > 25.0 mm/hr (heavy rainfall surface runoff warning)",
        "crit_def": "Precipitation rate > 50.0 mm/hr (torrential deluge, pit inundation hazard)",
        "safe_def": "Precipitation rate ≤ 25.0 mm/hr (normal precipitation rate)",
        "min_bound": 0.0,
        "max_bound": 300.0,
    },
}


def validate_reading_bounds(sensor_type: str, value: float, unit: str) -> tuple[bool, str | None]:
    """
    Validate that telemetry is physically plausible and matches configured units.
    Rejects NaNs, infinities, impossible ranges, and unit mismatches.
    """
    import math
    if math.isnan(value) or math.isinf(value):
        return False, "Telemetry value cannot be NaN or Infinite."

    rule = THRESHOLD_RULES.get(sensor_type)
    if not rule:
        return False, f"Unsupported sensor type: '{sensor_type}'."

    # Validate unit (normalize superscripts)
    expected_unit = rule["unit"]
    norm_u = unit.strip().lower().replace("3", "³")
    norm_exp = expected_unit.strip().lower().replace("3", "³")
    if norm_u != norm_exp:
        return False, f"Unit mismatch for {sensor_type}: expected '{expected_unit}', got '{unit}'."

    # Validate numeric physical bounds
    min_b = rule["min_bound"]
    max_b = rule["max_bound"]
    if value < min_b or value > max_b:
        return False, f"Value {value} out of physical sensor bounds [{min_b}, {max_b}] for {sensor_type}."

    return True, None


def evaluate_sensor_reading(sensor_type: str, value: float) -> SafetyEvaluationResult:
    """
    Evaluate a sensor reading against centralized, explainable threshold definitions.
    Returns structured evaluation with severity, explainability, and regulatory basis.
    """
    rule = THRESHOLD_RULES.get(sensor_type)
    if not rule:
        return SafetyEvaluationResult(
            status=ThresholdStatus.NORMAL,
            status_label="Normal",
            threshold_definition="Unclassified sensor",
            explanation=f"Sensor reading of {value} received without specific threshold rule.",
            is_statutory=False,
            regulation_reference=None,
        )

    is_statutory = rule["is_statutory"]
    reg_ref = rule["regulation"]
    prefix = f"[{reg_ref}] " if is_statutory else f"[Demo safety threshold] "

    # Check for lower-is-worse sensors (Airflow and Fan speed)
    if sensor_type in (SensorType.AIRFLOW.value, SensorType.VENTILATION_FAN.value):
        if value < rule["critical_threshold"]:
            explanation = (
                f"{prefix}Critical low {rule['label']} of {value} {rule['unit']} recorded. "
                f"Deficit exceeds safe threshold of {rule['critical_threshold']} {rule['unit']}. "
                f"{rule['crit_def']}."
            )
            return SafetyEvaluationResult(
                status=ThresholdStatus.CRITICAL,
                status_label="Critical",
                threshold_definition=rule["crit_def"],
                explanation=explanation,
                is_statutory=is_statutory,
                regulation_reference=reg_ref if is_statutory else None,
            )
        elif value < rule["warning_threshold"]:
            explanation = (
                f"{prefix}Warning: {rule['label']} of {value} {rule['unit']} is below standard operating minimum "
                f"of {rule['warning_threshold']} {rule['unit']}. {rule['warn_def']}."
            )
            return SafetyEvaluationResult(
                status=ThresholdStatus.WARNING,
                status_label="Warning",
                threshold_definition=rule["warn_def"],
                explanation=explanation,
                is_statutory=is_statutory,
                regulation_reference=reg_ref if is_statutory else None,
            )
        else:
            explanation = f"{prefix}{rule['label']} reading of {value} {rule['unit']} is within safe operational limits."
            return SafetyEvaluationResult(
                status=ThresholdStatus.NORMAL,
                status_label="Normal",
                threshold_definition=rule["safe_def"],
                explanation=explanation,
                is_statutory=is_statutory,
                regulation_reference=reg_ref if is_statutory else None,
            )

    # Upper-is-worse sensors (Methane, Dust, Slope, Pore Pressure, Rainfall)
    if value >= rule["critical_threshold"]:
        explanation = (
            f"{prefix}Critical level of {value} {rule['unit']} detected for {rule['label']}. "
            f"Exceeds safety limit of {rule['critical_threshold']} {rule['unit']}. {rule['crit_def']}."
        )
        return SafetyEvaluationResult(
            status=ThresholdStatus.CRITICAL,
            status_label="Critical",
            threshold_definition=rule["crit_def"],
            explanation=explanation,
            is_statutory=is_statutory,
            regulation_reference=reg_ref if is_statutory else None,
        )
    elif value > rule["warning_threshold"]:
        explanation = (
            f"{prefix}Warning: {rule['label']} of {value} {rule['unit']} is elevated above warning threshold "
            f"of {rule['warning_threshold']} {rule['unit']}. {rule['warn_def']}."
        )
        return SafetyEvaluationResult(
            status=ThresholdStatus.WARNING,
            status_label="Warning",
            threshold_definition=rule["warn_def"],
            explanation=explanation,
            is_statutory=is_statutory,
            regulation_reference=reg_ref if is_statutory else None,
        )
    else:
        explanation = f"{prefix}{rule['label']} reading of {value} {rule['unit']} is within safe operational limits."
        return SafetyEvaluationResult(
            status=ThresholdStatus.NORMAL,
            status_label="Normal",
            threshold_definition=rule["safe_def"],
            explanation=explanation,
            is_statutory=is_statutory,
            regulation_reference=reg_ref if is_statutory else None,
        )
