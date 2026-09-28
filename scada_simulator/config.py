"""
Configuration for PRITHVI SCADA Telemetry Simulator.
Explicitly simulated telemetry for PRITHVI compliance intelligence platform.
"""

import os

# Target PRITHVI backend API URL
DEFAULT_API_URL = os.getenv("PRITHVI_API_URL", "http://localhost:8000/api/telemetry/readings")
DEFAULT_INTERVAL_SECONDS = 5.0

# Supported Mine IDs in PRITHVI
MINES = {
    "MINE-BCCL-JHARIA-01": "Jharia Underground Demonstration Mine (BCCL)",
    "MINE-ECL-RANIGANJ-01": "Raniganj Underground Demonstration Mine (ECL)",
    "MINE-MCL-TALCHER-01": "Talcher Opencast Demonstration Mine (MCL)",
}

MINE_ALIASES = {
    "MINE-JH-001": "MINE-BCCL-JHARIA-01",
    "JHARIA": "MINE-BCCL-JHARIA-01",
    "MINE-WB-002": "MINE-ECL-RANIGANJ-01",
    "RANIGANJ": "MINE-ECL-RANIGANJ-01",
    "MINE-OR-003": "MINE-MCL-TALCHER-01",
    "TALCHER": "MINE-MCL-TALCHER-01",
}

# Sensor definitions per mine matching seed database
SENSOR_CATALOG = {
    "MINE-BCCL-JHARIA-01": [
        {"sensor_id": "SN-JHARIA-CH4-01", "sensor_code": "CH4-JHARIA-01", "sensor_type": "METHANE", "unit": "%", "zone_id": "ZONE-JHARIA-PITHEAD"},
        {"sensor_id": "SN-JHARIA-AIR-01", "sensor_code": "AIR-JHARIA-01", "sensor_type": "AIRFLOW", "unit": "m³/s", "zone_id": "ZONE-JHARIA-PITHEAD"},
        {"sensor_id": "SN-JHARIA-FAN-01", "sensor_code": "FAN-JHARIA-01", "sensor_type": "VENTILATION_FAN", "unit": "RPM", "zone_id": "ZONE-JHARIA-VENT-EAST"},
        {"sensor_id": "SN-JHARIA-DUST-01", "sensor_code": "DUST-JHARIA-01", "sensor_type": "DUST", "unit": "mg/m³", "zone_id": "ZONE-JHARIA-SUBSTATION"},
        {"sensor_id": "SN-JHARIA-SLP-01", "sensor_code": "SLP-JHARIA-01", "sensor_type": "SLOPE_DISPLACEMENT", "unit": "mm", "zone_id": "ZONE-JHARIA-PITHEAD"},
        {"sensor_id": "SN-JHARIA-POR-01", "sensor_code": "POR-JHARIA-01", "sensor_type": "PORE_PRESSURE", "unit": "kPa", "zone_id": "ZONE-JHARIA-SUBSTATION"},
        {"sensor_id": "SN-JHARIA-RAIN-01", "sensor_code": "RAIN-JHARIA-01", "sensor_type": "RAINFALL", "unit": "mm/hr", "zone_id": "ZONE-JHARIA-PITHEAD"},
    ],
    "MINE-ECL-RANIGANJ-01": [
        {"sensor_id": "SN-RANIGANJ-CH4-01", "sensor_code": "CH4-RANI-01", "sensor_type": "METHANE", "unit": "%", "zone_id": "ZONE-RANIGANJ-SHAFT"},
        {"sensor_id": "SN-RANIGANJ-AIR-01", "sensor_code": "AIR-RANI-01", "sensor_type": "AIRFLOW", "unit": "m³/s", "zone_id": "ZONE-RANIGANJ-SHAFT"},
    ],
    "MINE-MCL-TALCHER-01": [
        {"sensor_id": "SN-TALCHER-SLP-01", "sensor_code": "SLP-TALC-01", "sensor_type": "SLOPE_DISPLACEMENT", "unit": "mm", "zone_id": "ZONE-TALCHER-BENCH4"},
        {"sensor_id": "SN-TALCHER-POR-01", "sensor_code": "POR-TALC-01", "sensor_type": "PORE_PRESSURE", "unit": "kPa", "zone_id": "ZONE-TALCHER-BENCH4"},
        {"sensor_id": "SN-TALCHER-RAIN-01", "sensor_code": "RAIN-TALC-01", "sensor_type": "RAINFALL", "unit": "mm/hr", "zone_id": "ZONE-TALCHER-BENCH4"},
    ],
}
