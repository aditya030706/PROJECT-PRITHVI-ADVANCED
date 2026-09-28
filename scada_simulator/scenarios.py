"""
Scenario profiles for PRITHVI SCADA Telemetry Simulator.
Provides deterministic, repeatable readings for demonstration and compliance verification.
All scenarios are clearly marked as SIMULATED.
"""

from typing import Dict, List, Any
from datetime import datetime, timezone

SCENARIOS = {
    "normal": {
        "description": "All telemetry within statutory safe limits (CMR 2017 compliant)",
        "values": {
            "METHANE": 0.28,              # % (< 0.75% Warning, < 1.25% Critical)
            "AIRFLOW": 34.5,              # m3/s (> 20 Normal, < 15 Critical)
            "VENTILATION_FAN": 1480.0,    # RPM (> 1200 Normal, < 800 Critical)
            "DUST": 1.45,                 # mg/m3 (< 2.0 Normal, > 3.0 Critical)
            "SLOPE_DISPLACEMENT": 4.2,    # mm (< 25 Normal, > 50 Critical)
            "PORE_PRESSURE": 115.0,       # kPa (< 250 Normal, > 400 Critical)
            "RAINFALL": 2.5,              # mm/hr (< 15 Normal, > 40 Critical)
        }
    },
    "warning": {
        "description": "Elevated indicators approaching statutory thresholds (Advisory / Warning state)",
        "values": {
            "METHANE": 0.85,              # % Warning (>= 0.75%, < 1.25%)
            "AIRFLOW": 18.0,              # m3/s Warning (<= 20, > 15)
            "VENTILATION_FAN": 1100.0,    # RPM Warning (<= 1200, > 800)
            "DUST": 2.40,                 # mg/m3 Warning (>= 2.0, < 3.0)
            "SLOPE_DISPLACEMENT": 32.0,   # mm Warning (>= 25, < 50)
            "PORE_PRESSURE": 290.0,       # kPa Warning (>= 250, < 400)
            "RAINFALL": 22.0,             # mm/hr Warning (>= 15, < 40)
        }
    },
    "critical_methane": {
        "description": "CMR Reg 153 Methane Breach: Face concentration exceeds 1.25% statutory withdrawal limit",
        "values": {
            "METHANE": 1.68,              # CRITICAL (> 1.25% - Immediate evacuation trigger)
            "AIRFLOW": 17.5,              # Warning
            "VENTILATION_FAN": 1250.0,    # Normal
            "DUST": 1.90,                 # Normal
            "SLOPE_DISPLACEMENT": 6.0,    # Normal
            "PORE_PRESSURE": 120.0,       # Normal
            "RAINFALL": 4.0,              # Normal
        }
    },
    "critical_ventilation": {
        "description": "CMR Reg 154 Ventilation Failure: Main fan failure causing airflow collapse (< 15 m3/s)",
        "values": {
            "METHANE": 0.95,              # Warning
            "AIRFLOW": 9.2,               # CRITICAL (< 15 m3/s statutory minimum)
            "VENTILATION_FAN": 520.0,     # CRITICAL (< 800 RPM fan degradation)
            "DUST": 2.80,                 # Warning
            "SLOPE_DISPLACEMENT": 5.0,    # Normal
            "PORE_PRESSURE": 110.0,       # Normal
            "RAINFALL": 1.0,              # Normal
        }
    },
    "critical_slope": {
        "description": "Pit Highwall Instability: Slope displacement exceeds 50 mm geo-technical threshold",
        "values": {
            "METHANE": 0.15,              # Normal
            "AIRFLOW": 35.0,              # Normal
            "VENTILATION_FAN": 1450.0,    # Normal
            "DUST": 1.60,                 # Normal
            "SLOPE_DISPLACEMENT": 64.5,   # CRITICAL (> 50 mm bench failure threshold)
            "PORE_PRESSURE": 435.0,       # CRITICAL (> 400 kPa hydrostatic pressure)
            "RAINFALL": 48.0,             # CRITICAL (> 40 mm/hr cloudburst trigger)
        }
    },
    "critical_multi": {
        "description": "Compound Underground Emergency: Methane accumulation + Ventilation drop + Heavy dust",
        "values": {
            "METHANE": 1.82,              # CRITICAL
            "AIRFLOW": 8.5,               # CRITICAL
            "VENTILATION_FAN": 450.0,     # CRITICAL
            "DUST": 3.85,                 # CRITICAL
            "SLOPE_DISPLACEMENT": 8.0,    # Normal
            "PORE_PRESSURE": 130.0,       # Normal
            "RAINFALL": 3.0,              # Normal
        }
    },
    "recovery": {
        "description": "Safety restoration sequence: All sensors recovering safely to normal baseline",
        "values": {
            "METHANE": 0.32,              # Normal
            "AIRFLOW": 33.0,              # Normal
            "VENTILATION_FAN": 1460.0,    # Normal
            "DUST": 1.30,                 # Normal
            "SLOPE_DISPLACEMENT": 8.5,    # Normal (stabilized)
            "PORE_PRESSURE": 140.0,       # Normal
            "RAINFALL": 2.0,              # Normal
        }
    }
}


def build_scenario_payload(scenario_key: str, mine_id: str, sensors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Constructs a batch of simulated telemetry readings for the given scenario and mine sensors.
    """
    profile = SCENARIOS.get(scenario_key, SCENARIOS["normal"])
    values_map = profile["values"]
    now_iso = datetime.now(timezone.utc).isoformat()

    readings = []
    for s in sensors:
        stype = s["sensor_type"]
        val = values_map.get(stype, 0.0)
        readings.append({
            "sensor_id": s.get("id"),
            "sensor_code": s["sensor_code"],
            "mine_id": mine_id,
            "zone_id": s.get("zone_id"),
            "sensor_type": stype,
            "value": float(val),
            "unit": s["unit"],
            "quality": "GOOD",
            "simulated": True,
            "recorded_at": now_iso
        })
    return readings
