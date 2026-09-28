# PRITHVI SCADA Telemetry Simulator

## Overview
The **PRITHVI SCADA Simulator** is an independent service component that generates deterministic simulated sensor streams and transmits them over HTTP to PRITHVI's Telemetry Ingestion API (`/api/telemetry/readings`).

> [!IMPORTANT]
> **SIMULATION NOTICE**: All data produced by this tool is strictly simulated for demonstration, scenario validation, and statutory compliance workflow testing. PRITHVI makes no claim of direct connection to physical underground hardware, operational PLCs, or actual mine SCADA networks.

---

## Sensor Categories & Thresholds

| Sensor Category | Sensor Type | Unit | Statutory / Safety Threshold (CMR 2017) |
|---|---|---|---|
| **Methane Concentration** | `METHANE` | `%` | Normal < 0.75% \| Warning 0.75–1.25% \| Critical > 1.25% (Reg 153 Withdrawal) |
| **Airflow Velocity** | `AIRFLOW` | `m³/s` | Normal > 20 m³/s \| Warning 15–20 m³/s \| Critical < 15 m³/s (Reg 154 Colliery Minimum) |
| **Ventilation Fan Speed**| `VENTILATION_FAN` | `RPM` | Normal > 1200 RPM \| Warning 800–1200 RPM \| Critical < 800 RPM |
| **Dust Concentration** | `DUST` | `mg/m³`| Normal < 2.0 mg/m³ \| Warning 2.0–3.0 mg/m³ \| Critical > 3.0 mg/m³ (Reg 124 Respirable Dust) |
| **Slope Displacement** | `SLOPE_DISPLACEMENT`| `mm` | Normal < 25 mm \| Warning 25–50 mm \| Critical > 50 mm (Highwall Stability) |
| **Pore Pressure** | `PORE_PRESSURE` | `kPa` | Normal < 250 kPa \| Warning 250–400 kPa \| Critical > 400 kPa (Hydrostatic Burden) |
| **Rainfall Rate** | `RAINFALL` | `mm/hr`| Normal < 15 mm/hr \| Warning 15–40 mm/hr \| Critical > 40 mm/hr (Pit Inundation Risk) |

---

## Available Scenarios

- `normal`: All sensors within statutory bounds.
- `warning`: Approaching statutory thresholds (triggers Warning signals).
- `critical_methane`: Methane jumps to 1.68% (> 1.25%), triggering CRITICAL signal and operational case synthesis.
- `critical_ventilation`: Fan speed drops to 520 RPM, airflow drops to 9.2 m³/s (< 15 m³/s statutory minimum).
- `critical_slope`: Slope displacement hits 64.5 mm, pore pressure hits 435 kPa, rainfall hits 48 mm/hr.
- `critical_multi`: Combined high methane + ventilation failure + heavy dust.
- `recovery`: Sensors return to safe baseline values. Signals mark as `RECOVERED` (compliance cases remain open for human review).

---

## Execution Commands

### 1. Send a single batch of normal readings (default: Jharia `MINE-JH-001`)
```bash
python scada_simulator/simulator.py --scenario normal --once
```

### 2. Simulate Methane Statutory Breach on Jharia
```bash
python scada_simulator/simulator.py --scenario critical_methane --mine MINE-JH-001 --once
```

### 3. Simulate Highwall Instability on Talcher Opencast
```bash
python scada_simulator/simulator.py --scenario critical_slope --mine MINE-OR-003 --once
```

### 4. Broadcast Continuous Stream Across All Mines (every 5 seconds)
```bash
python scada_simulator/simulator.py --scenario normal --mine ALL --interval 5.0
```

### 5. Simulate Safety Recovery
```bash
python scada_simulator/simulator.py --scenario recovery --mine MINE-JH-001 --once
```
