"""
PRITHVI SCADA Telemetry Simulator CLI.
Independent process that generates deterministic simulated sensor streams and posts to PRITHVI API.
Explicitly simulated for compliance demonstration and testing.
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime, timezone
import urllib.request
import urllib.error

# Add parent directory to path to allow importing scada_simulator package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scada_simulator.config import DEFAULT_API_URL, DEFAULT_INTERVAL_SECONDS, MINES, MINE_ALIASES, SENSOR_CATALOG
from scada_simulator.scenarios import SCENARIOS, build_scenario_payload


def send_telemetry_batch(api_url: str, readings: list) -> dict:
    """Sends a batch of telemetry readings to the PRITHVI backend API."""
    payload = json.dumps({"readings": readings}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "PRITHVI-SCADA-Simulator/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return {"status": "error", "code": e.code, "detail": json.loads(err_body)}
        except Exception:
            return {"status": "error", "code": e.code, "detail": err_body}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="PRITHVI SCADA Telemetry Simulator (Explicitly Simulated IoT Layer)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="normal",
        choices=list(SCENARIOS.keys()),
        help=f"Telemetry scenario profile to simulate (choices: {', '.join(SCENARIOS.keys())})"
    )
    parser.add_argument(
        "--mine",
        type=str,
        default="MINE-JH-001",
        help="Target mine ID (or 'ALL' to broadcast across all seeded mines)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Broadcast interval in seconds (default: {DEFAULT_INTERVAL_SECONDS})"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=DEFAULT_API_URL,
        help=f"PRITHVI telemetry ingestion endpoint (default: {DEFAULT_API_URL})"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Send a single batch of readings and exit immediately"
    )

    args = parser.parse_args()

    scenario_info = SCENARIOS.get(args.scenario, SCENARIOS["normal"])
    if args.mine.upper() == "ALL":
        target_mines = list(MINES.keys())
    else:
        resolved_mine = MINE_ALIASES.get(args.mine, MINE_ALIASES.get(args.mine.upper(), args.mine))
        target_mines = [resolved_mine]

    print("=" * 72)
    print("  PRITHVI MINE INTELLIGENCE — SCADA TELEMETRY SIMULATOR")
    print("  [DISCLAIMER: EXPLICITLY SIMULATED TELEMETRY FOR COMPLIANCE EVALUATION]")
    print("=" * 72)
    print(f"  Target API Endpoint : {args.api_url}")
    print(f"  Selected Scenario   : [{args.scenario.upper()}] {scenario_info['description']}")
    print(f"  Target Mine(s)      : {', '.join(target_mines)}")
    print(f"  Broadcast Mode      : {'Single Pulse (--once)' if args.once else f'Continuous Loop ({args.interval}s interval)'}")
    print("=" * 72)

    iteration = 1
    try:
        while True:
            total_readings = []
            for mine_id in target_mines:
                sensors = SENSOR_CATALOG.get(mine_id, [])
                if not sensors:
                    print(f"[WARN] No sensor definitions found for {mine_id}")
                    continue
                readings = build_scenario_payload(args.scenario, mine_id, sensors)
                total_readings.extend(readings)

            ts_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"\n[{ts_str}] Batch #{iteration}: Dispatching {len(total_readings)} simulated readings...")

            for r in total_readings:
                print(f"   -> [{r['mine_id']}] {r['sensor_code']} ({r['sensor_type']}): {r['value']} {r['unit']}")

            result = send_telemetry_batch(args.api_url, total_readings)

            if result.get("success") is True or result.get("status") == "success":
                accepted = result.get("ingested_count", 0)
                eval_count = result.get("evaluated_signals_count", 0)
                critical_count = result.get("critical_signals_count", 0)
                cases = result.get("new_cases_created", 0)
                print(f"   [OK] Ingested: {accepted} readings | Evaluated: {eval_count} | Critical Signals: {critical_count} | Cases Created: {cases}")
            else:
                print(f"   [ERROR] Ingestion failed: {result}")

            if args.once:
                print("\n[INFO] Single pulse complete. Exiting.")
                break

            iteration += 1
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n[INFO] SCADA Telemetry Simulator terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
