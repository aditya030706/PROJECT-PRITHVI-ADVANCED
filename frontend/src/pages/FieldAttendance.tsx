import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import {
  submitCheckIn,
  getMyAttendance,
  getMineZones,
  type AttendanceRecord,
  type CheckInResponse,
  type MineZonesResponse,
} from "../api/attendance";
import {
  MapPin,
  Shield,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Radio,
  Crosshair,
  ChevronRight,
  RefreshCw,
  Layers,
} from "lucide-react";

// Demonstration presets for rapid judging / testing
const DEMO_PRESETS = [
  {
    name: "Inside Mine Perimeter (Jharia HQ)",
    lat: 23.7503,
    lon: 86.4203,
    acc: 12.0,
    tag: "INSIDE",
  },
  {
    name: "Inside Zone: Pit Head & Incline 1",
    lat: 23.7505,
    lon: 86.4202,
    acc: 8.0,
    tag: "ZONE_INSIDE",
  },
  {
    name: "Outside Geofence (~1.2 km away)",
    lat: 23.7635,
    lon: 86.4320,
    acc: 15.0,
    tag: "OUTSIDE",
  },
  {
    name: "Weak GPS Signal (Low Accuracy)",
    lat: 23.7502,
    lon: 86.4201,
    acc: 165.0,
    tag: "LOW_ACC",
  },
];

export default function FieldAttendance() {
  const { session } = useAuth();
  const navigate = useNavigate();

  const [selectedMineId, setSelectedMineId] = useState("MINE-BCCL-JHARIA-01");
  const [mineZonesData, setMineZonesData] = useState<MineZonesResponse | null>(null);
  const [selectedZoneId, setSelectedZoneId] = useState<string>("");

  // GPS State
  const [userLat, setUserLat] = useState<number | null>(23.7503);
  const [userLon, setUserLon] = useState<number | null>(86.4203);
  const [accuracyM, setAccuracyM] = useState<number | null>(12.0);
  const [gpsAcquiring, setGpsAcquiring] = useState<boolean>(false);
  const [gpsError, setGpsError] = useState<string | null>(null);

  // Optional fields
  const [notes, setNotes] = useState<string>("");
  const [scheduleInstanceId, setScheduleInstanceId] = useState<string>("");
  const [inspectionId, setInspectionId] = useState<string>("");

  // Submission State
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [checkInResult, setCheckInResult] = useState<CheckInResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // History State
  const [history, setHistory] = useState<AttendanceRecord[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // 1. Fetch mine zones when mine selection changes
  useEffect(() => {
    let isMounted = true;
    getMineZones(selectedMineId)
      .then((data) => {
        if (isMounted) {
          setMineZonesData(data);
          setSelectedZoneId(""); // reset zone
        }
      })
      .catch((err) => console.error("Error loading mine zones:", err));
    return () => {
      isMounted = false;
    };
  }, [selectedMineId]);

  // 2. Fetch user attendance history
  const loadHistory = () => {
    if (!session) return;
    setLoadingHistory(true);
    getMyAttendance(session.user_id, session.role)
      .then((data) => setHistory(data))
      .catch((err) => console.error("Error loading history:", err))
      .finally(() => setLoadingHistory(false));
  };

  useEffect(() => {
    loadHistory();
  }, [session?.user_id, session?.role]);

  // Handle live browser geolocation
  const handleAcquireGPS = () => {
    setGpsAcquiring(true);
    setGpsError(null);
    if (!navigator.geolocation) {
      setGpsError("Geolocation is not supported by your browser.");
      setGpsAcquiring(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLat(pos.coords.latitude);
        setUserLon(pos.coords.longitude);
        setAccuracyM(pos.coords.accuracy);
        setGpsAcquiring(false);
      },
      (err) => {
        setGpsError(`GPS acquisition failed: ${err.message}. Use demo presets below.`);
        setGpsAcquiring(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  // Set demo preset
  const handlePreset = (p: typeof DEMO_PRESETS[0]) => {
    setUserLat(p.lat);
    setUserLon(p.lon);
    setAccuracyM(p.acc);
    setGpsError(null);
  };

  // Compute live client-side estimated distance for radar visualization
  const referenceCoords = useMemo(() => {
    if (selectedZoneId && mineZonesData?.zones) {
      const z = mineZonesData.zones.find((zn) => zn.mine_zone_id === selectedZoneId);
      if (z) {
        return {
          lat: z.latitude,
          lon: z.longitude,
          radius: z.geofence_radius_meters,
          name: z.name,
        };
      }
    }
    return {
      lat: mineZonesData?.mine_latitude ?? 23.75,
      lon: mineZonesData?.mine_longitude ?? 86.42,
      radius: mineZonesData?.mine_geofence_radius_meters ?? 500,
      name: "Mine Perimeter",
    };
  }, [selectedZoneId, mineZonesData]);

  // Client approximate Haversine for live radar view
  const liveEstDistance = useMemo(() => {
    if (userLat === null || userLon === null || referenceCoords.lat === null || referenceCoords.lon === null) {
      return null;
    }
    const R = 6371000;
    const dLat = ((userLat - referenceCoords.lat) * Math.PI) / 180;
    const dLon = ((userLon - referenceCoords.lon) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((referenceCoords.lat * Math.PI) / 180) *
        Math.cos((userLat * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c * 10) / 10;
  }, [userLat, userLon, referenceCoords]);

  const isLiveInside = liveEstDistance !== null && liveEstDistance <= referenceCoords.radius;

  // Handle Check-in submit
  const handleCheckIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session) return;
    setSubmitting(true);
    setSubmitError(null);
    setCheckInResult(null);

    try {
      const resp = await submitCheckIn(
        {
          mine_id: selectedMineId,
          zone_id: selectedZoneId || null,
          latitude: userLat,
          longitude: userLon,
          accuracy_meters: accuracyM,
          schedule_instance_id: scheduleInstanceId || null,
          inspection_id: inspectionId || null,
          device_info: `${navigator.userAgent.slice(0, 80)}`,
          notes: notes || null,
        },
        session.user_id,
        session.role
      );
      setCheckInResult(resp);
      loadHistory(); // refresh history table
    } catch (err: any) {
      setSubmitError(err.message || "Failed to submit attendance.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "1.5rem 1rem" }}>
      {/* Header Banner */}
      <div
        style={{
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
          border: "1px solid #334155",
          borderRadius: 12,
          padding: "1.5rem",
          marginBottom: "1.5rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
            <MapPin size={24} color="#10b981" />
            <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700, color: "#f8fafc" }}>
              GIS Field Attendance & Geo-Fenced Operations
            </h1>
          </div>
          <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.875rem" }}>
            Cryptographically anchored satellite check-in with authoritative server-side Haversine geofence validation.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <div
            style={{
              background: "#1e293b",
              border: "1px solid #475569",
              padding: "0.5rem 1rem",
              borderRadius: 8,
              fontSize: "0.8125rem",
            }}
          >
            <div style={{ color: "#64748b", fontSize: "0.7rem", textTransform: "uppercase", fontWeight: 600 }}>
              Active Identity
            </div>
            <div style={{ color: "#38bdf8", fontWeight: 600 }}>{session?.user_id || "ANONYMOUS"}</div>
            <div style={{ color: "#cbd5e1", fontSize: "0.75rem" }}>{session?.role || "GUEST"}</div>
          </div>
          <button
            onClick={() => navigate("/attendance/team")}
            style={{
              background: "#334155",
              color: "#e2e8f0",
              border: "1px solid #475569",
              padding: "0.6rem 1rem",
              borderRadius: 8,
              cursor: "pointer",
              fontWeight: 500,
              fontSize: "0.85rem",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            <Layers size={16} />
            Supervisor Roster
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))", gap: "1.5rem" }}>
        {/* Left Column: Form & Coordinates */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div
            style={{
              background: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: 12,
              padding: "1.5rem",
            }}
          >
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, color: "#f1f5f9", marginTop: 0, marginBottom: "1rem" }}>
              1. Select Assigned Mine & Zone
            </h2>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.35rem" }}>
                Target Mine Location
              </label>
              <select
                value={selectedMineId}
                onChange={(e) => setSelectedMineId(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.65rem",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 6,
                  color: "#f8fafc",
                  fontSize: "0.9rem",
                }}
              >
                <option value="MINE-BCCL-JHARIA-01">MINE-BCCL-JHARIA-01 · Jharia Underground Mine (BCCL)</option>
                <option value="MINE-ECL-RANIGANJ-01">MINE-ECL-RANIGANJ-01 · Raniganj Underground Mine (ECL)</option>
                <option value="MINE-MCL-TALCHER-01">MINE-MCL-TALCHER-01 · Talcher Opencast Mine (MCL)</option>
              </select>
            </div>

            <div style={{ marginBottom: "1.25rem" }}>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.35rem" }}>
                Designated Mine Zone (Optional)
              </label>
              <select
                value={selectedZoneId}
                onChange={(e) => setSelectedZoneId(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.65rem",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 6,
                  color: "#f8fafc",
                  fontSize: "0.9rem",
                }}
              >
                <option value="">-- Entire Mine Boundary ({referenceCoords.radius}m fence) --</option>
                {mineZonesData?.zones?.map((z) => (
                  <option key={z.mine_zone_id} value={z.mine_zone_id}>
                    {z.name} (Radius: {z.geofence_radius_meters}m)
                  </option>
                ))}
              </select>
            </div>

            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, color: "#f1f5f9", marginBottom: "1rem" }}>
              2. Capture Satellite GPS Coordinates
            </h2>

            <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem", flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={handleAcquireGPS}
                disabled={gpsAcquiring}
                style={{
                  flex: 1,
                  background: "#0284c7",
                  color: "#fff",
                  border: "none",
                  padding: "0.65rem 1rem",
                  borderRadius: 6,
                  cursor: "pointer",
                  fontWeight: 600,
                  fontSize: "0.85rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.5rem",
                }}
              >
                {gpsAcquiring ? <RefreshCw size={16} className="spin" /> : <Crosshair size={16} />}
                {gpsAcquiring ? "Acquiring Fix..." : "Acquire Device GPS"}
              </button>
            </div>

            {/* Demonstration Test Presets */}
            <div style={{ marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: "0.4rem", fontWeight: 600 }}>
                RAPID DEMO SIMULATION PRESETS
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem" }}>
                {DEMO_PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handlePreset(p)}
                    style={{
                      background: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: 6,
                      padding: "0.5rem",
                      color: "#cbd5e1",
                      fontSize: "0.75rem",
                      textAlign: "left",
                      cursor: "pointer",
                      transition: "border 0.2s",
                    }}
                  >
                    <div style={{ fontWeight: 600, color: p.tag === "INSIDE" || p.tag === "ZONE_INSIDE" ? "#34d399" : "#f87171" }}>
                      {p.tag}
                    </div>
                    <div>{p.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Coordinate display / inputs */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ fontSize: "0.7rem", color: "#64748b" }}>LATITUDE</label>
                <input
                  type="number"
                  step="0.0001"
                  value={userLat ?? ""}
                  onChange={(e) => setUserLat(e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="23.7500"
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 4,
                    color: "#f8fafc",
                    fontSize: "0.85rem",
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.7rem", color: "#64748b" }}>LONGITUDE</label>
                <input
                  type="number"
                  step="0.0001"
                  value={userLon ?? ""}
                  onChange={(e) => setUserLon(e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="86.4200"
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 4,
                    color: "#f8fafc",
                    fontSize: "0.85rem",
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.7rem", color: "#64748b" }}>ACCURACY (M)</label>
                <input
                  type="number"
                  step="1"
                  value={accuracyM ?? ""}
                  onChange={(e) => setAccuracyM(e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="10"
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 4,
                    color: "#f8fafc",
                    fontSize: "0.85rem",
                  }}
                />
              </div>
            </div>

            {gpsError && (
              <div
                style={{
                  background: "rgba(239, 68, 68, 0.1)",
                  border: "1px solid #ef4444",
                  padding: "0.6rem",
                  borderRadius: 6,
                  color: "#fca5a5",
                  fontSize: "0.75rem",
                  marginBottom: "1rem",
                }}
              >
                {gpsError}
              </div>
            )}

            {/* Optional Links */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ fontSize: "0.7rem", color: "#64748b" }}>INSPECTION ID (OPTIONAL)</label>
                <input
                  type="text"
                  value={inspectionId}
                  onChange={(e) => setInspectionId(e.target.value)}
                  placeholder="e.g. INSP-2026-001"
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 4,
                    color: "#f8fafc",
                    fontSize: "0.85rem",
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.7rem", color: "#64748b" }}>SCHEDULE INSTANCE (OPTIONAL)</label>
                <input
                  type="text"
                  value={scheduleInstanceId}
                  onChange={(e) => setScheduleInstanceId(e.target.value)}
                  placeholder="e.g. SCHED-JHARIA-VENT"
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 4,
                    color: "#f8fafc",
                    fontSize: "0.85rem",
                  }}
                />
              </div>
            </div>

            <div style={{ marginBottom: "1.25rem" }}>
              <label style={{ fontSize: "0.7rem", color: "#64748b" }}>FIELD NOTES / OBSERVATIONS</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Operational notes, shift muster, or weather remarks..."
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 4,
                  color: "#f8fafc",
                  fontSize: "0.85rem",
                  resize: "vertical",
                }}
              />
            </div>

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleCheckIn}
              disabled={submitting || userLat === null || userLon === null}
              style={{
                width: "100%",
                padding: "0.85rem",
                background: isLiveInside ? "linear-gradient(135deg, #059669 0%, #10b981 100%)" : "linear-gradient(135deg, #d97706 0%, #f59e0b 100%)",
                color: "#ffffff",
                border: "none",
                borderRadius: 8,
                fontWeight: 700,
                fontSize: "1rem",
                cursor: submitting ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.5rem",
                boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
              }}
            >
              <Shield size={20} />
              {submitting ? "Anchoring Record to Server..." : isLiveInside ? "Submit Authoritative Check-In" : "Submit Outside-Geofence Check-In"}
            </button>
          </div>
        </div>

        {/* Right Column: Interactive SVG GIS Radar & Verdict */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Radar Card */}
          <div
            style={{
              background: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: 12,
              padding: "1.5rem",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div style={{ width: "100%", display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <Radio size={18} color="#38bdf8" />
                <span style={{ fontWeight: 600, color: "#f8fafc", fontSize: "0.95rem" }}>
                  GIS Geofence Vector Radar
                </span>
              </div>
              <span
                style={{
                  fontSize: "0.75rem",
                  padding: "0.2rem 0.6rem",
                  borderRadius: 999,
                  fontWeight: 600,
                  background: isLiveInside ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                  color: isLiveInside ? "#34d399" : "#f87171",
                  border: `1px solid ${isLiveInside ? "#10b981" : "#ef4444"}`,
                }}
              >
                {isLiveInside ? "INSIDE GEOFENCE" : "OUTSIDE BOUNDARY"}
              </span>
            </div>

            {/* SVG Radar Graphic */}
            <div style={{ position: "relative", width: 280, height: 280, margin: "0.5rem 0" }}>
              <svg width="280" height="280" viewBox="0 0 280 280" style={{ overflow: "visible" }}>
                {/* Background Grid */}
                <rect width="280" height="280" rx="140" fill="#0b1329" stroke="#1e293b" strokeWidth="2" />
                
                {/* Concentric rings */}
                <circle cx="140" cy="140" r="120" fill="none" stroke="#1e3a5f" strokeWidth="1" strokeDasharray="3 3" />
                <circle cx="140" cy="140" r="85" fill="none" stroke="#1e3a5f" strokeWidth="1" />
                <circle cx="140" cy="140" r="50" fill="none" stroke="#1e3a5f" strokeWidth="1" strokeDasharray="2 2" />

                {/* Crosshairs */}
                <line x1="140" y1="10" x2="140" y2="270" stroke="#1e293b" strokeWidth="1" />
                <line x1="10" y1="140" x2="270" y2="140" stroke="#1e293b" strokeWidth="1" />

                {/* Mine Reference Geofence Ring (Scale: 100px = radius) */}
                <circle
                  cx="140"
                  cy="140"
                  r="85"
                  fill="rgba(14, 165, 233, 0.06)"
                  stroke="#0ea5e9"
                  strokeWidth="2"
                />
                <text x="145" y="60" fill="#38bdf8" fontSize="10" fontWeight="600">
                  {referenceCoords.name} ({referenceCoords.radius}m)
                </text>

                {/* Center Mine / Zone Marker */}
                <circle cx="140" cy="140" r="5" fill="#38bdf8" />
                <text x="140" y="155" fill="#94a3b8" fontSize="9" textAnchor="middle">
                  Ref Center
                </text>

                {/* User position calculation relative to center */}
                {liveEstDistance !== null && (
                  (() => {
                    // Scaled offset: 85px = referenceCoords.radius
                    const scale = 85 / Math.max(referenceCoords.radius, 100);
                    const angle = 0.8; // synthetic polar angle for demo visualization
                    const distScaled = Math.min(liveEstDistance * scale, 125);
                    const userX = 140 + distScaled * Math.cos(angle);
                    const userY = 140 - distScaled * Math.sin(angle);

                    return (
                      <g>
                        {/* Connecting line */}
                        <line
                          x1="140"
                          y1="140"
                          x2={userX}
                          y2={userY}
                          stroke={isLiveInside ? "#10b981" : "#ef4444"}
                          strokeWidth="1.5"
                          strokeDasharray="2 2"
                        />
                        {/* Pulsing ring */}
                        <circle
                          cx={userX}
                          cy={userY}
                          r="10"
                          fill="none"
                          stroke={isLiveInside ? "#10b981" : "#ef4444"}
                          strokeWidth="1"
                          opacity="0.6"
                        />
                        {/* User dot */}
                        <circle
                          cx={userX}
                          cy={userY}
                          r="6"
                          fill={isLiveInside ? "#10b981" : "#ef4444"}
                        />
                        {/* Accuracy circle */}
                        {accuracyM && (
                          <circle
                            cx={userX}
                            cy={userY}
                            r={Math.min(accuracyM * scale, 35)}
                            fill={accuracyM > 100 ? "rgba(234, 179, 8, 0.15)" : "rgba(16, 185, 129, 0.1)"}
                            stroke={accuracyM > 100 ? "#eab308" : "#10b981"}
                            strokeWidth="1"
                            strokeDasharray="2 2"
                          />
                        )}
                        <text
                          x={userX + 8}
                          y={userY - 8}
                          fill={isLiveInside ? "#34d399" : "#fca5a5"}
                          fontSize="10"
                          fontWeight="700"
                        >
                          You ({liveEstDistance}m)
                        </text>
                      </g>
                    );
                  })()
                )}
              </svg>
            </div>

            {/* Metrics Row */}
            <div
              style={{
                width: "100%",
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: "0.5rem",
                marginTop: "0.5rem",
                padding: "0.75rem",
                background: "#1e293b",
                borderRadius: 8,
                textAlign: "center",
              }}
            >
              <div>
                <div style={{ color: "#64748b", fontSize: "0.7rem", fontWeight: 600 }}>CALCULATED DISTANCE</div>
                <div style={{ color: isLiveInside ? "#34d399" : "#f87171", fontWeight: 700, fontSize: "1.1rem" }}>
                  {liveEstDistance !== null ? `${liveEstDistance} m` : "—"}
                </div>
              </div>
              <div>
                <div style={{ color: "#64748b", fontSize: "0.7rem", fontWeight: 600 }}>GEOFENCE RADIUS</div>
                <div style={{ color: "#38bdf8", fontWeight: 700, fontSize: "1.1rem" }}>
                  {referenceCoords.radius} m
                </div>
              </div>
              <div>
                <div style={{ color: "#64748b", fontSize: "0.7rem", fontWeight: 600 }}>GPS ACCURACY</div>
                <div
                  style={{
                    color: (accuracyM ?? 0) > 100 ? "#fbbf24" : "#94a3b8",
                    fontWeight: 700,
                    fontSize: "1.1rem",
                  }}
                >
                  {accuracyM !== null ? `±${Math.round(accuracyM)} m` : "—"}
                </div>
              </div>
            </div>
          </div>

          {/* Submission Verdict Card */}
          {checkInResult && (
            <div
              style={{
                background:
                  checkInResult.status === "VALID"
                    ? "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%)"
                    : "linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%)",
                border: `1px solid ${checkInResult.status === "VALID" ? "#059669" : "#dc2626"}`,
                borderRadius: 12,
                padding: "1.25rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
                {checkInResult.status === "VALID" ? (
                  <CheckCircle2 size={24} color="#10b981" />
                ) : (
                  <AlertTriangle size={24} color="#ef4444" />
                )}
                <div>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc" }}>
                    {checkInResult.status_label}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                    Attendance ID: <code style={{ color: "#38bdf8" }}>{checkInResult.attendance_id}</code>
                  </div>
                </div>
              </div>

              <p style={{ margin: "0.5rem 0", fontSize: "0.85rem", color: "#cbd5e1" }}>
                {checkInResult.message}
              </p>

              {checkInResult.anomaly_detected && (
                <div
                  style={{
                    background: "rgba(239, 68, 68, 0.2)",
                    border: "1px solid #ef4444",
                    borderRadius: 6,
                    padding: "0.5rem",
                    margin: "0.5rem 0",
                    fontSize: "0.8rem",
                    color: "#fca5a5",
                  }}
                >
                  <strong>Anomaly Signal Flagged:</strong> {checkInResult.anomaly_label} (Severity:{" "}
                  {checkInResult.anomaly_severity})
                </div>
              )}

              {/* Field Operations Action Bar */}
              <div
                style={{
                  marginTop: "1rem",
                  paddingTop: "0.75rem",
                  borderTop: "1px solid #334155",
                  display: "flex",
                  gap: "0.5rem",
                  flexWrap: "wrap",
                }}
              >
                <button
                  onClick={() => navigate("/inspections")}
                  style={{
                    flex: 1,
                    background: "#0284c7",
                    color: "#fff",
                    border: "none",
                    padding: "0.5rem 0.75rem",
                    borderRadius: 6,
                    cursor: "pointer",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.3rem",
                  }}
                >
                  <ChevronRight size={16} />
                  Proceed to Inspection
                </button>
                {checkInResult.evidence_id && (
                  <button
                    onClick={() => navigate(`/audit-chain/evidence/${checkInResult.evidence_id}`)}
                    style={{
                      background: "#334155",
                      color: "#93c5fd",
                      border: "1px solid #475569",
                      padding: "0.5rem 0.75rem",
                      borderRadius: 6,
                      cursor: "pointer",
                      fontSize: "0.8rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.3rem",
                    }}
                  >
                    <Shield size={14} />
                    View Hash Proof
                  </button>
                )}
              </div>
            </div>
          )}

          {submitError && (
            <div
              style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid #ef4444",
                borderRadius: 12,
                padding: "1rem",
                color: "#fca5a5",
                fontSize: "0.85rem",
              }}
            >
              <strong>Check-In Submission Error:</strong> {submitError}
            </div>
          )}
        </div>
      </div>

      {/* Recent Personal Attendance Log */}
      <div
        style={{
          marginTop: "2rem",
          background: "#0f172a",
          border: "1px solid #1e293b",
          borderRadius: 12,
          padding: "1.5rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Clock size={18} color="#94a3b8" />
            <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 600, color: "#f8fafc" }}>
              My Attendance History (Active User Log)
            </h3>
          </div>
          <button
            onClick={loadHistory}
            disabled={loadingHistory}
            style={{
              background: "transparent",
              border: "none",
              color: "#38bdf8",
              cursor: "pointer",
              fontSize: "0.8rem",
              display: "flex",
              alignItems: "center",
              gap: "0.3rem",
            }}
          >
            <RefreshCw size={14} className={loadingHistory ? "spin" : ""} />
            Refresh
          </button>
        </div>

        {history.length === 0 ? (
          <div style={{ textAlign: "center", padding: "2rem", color: "#64748b", fontSize: "0.875rem" }}>
            No check-in records found for this session identity yet. Submit a check-in above to start logging.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.825rem", color: "#cbd5e1" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8", textAlign: "left" }}>
                  <th style={{ padding: "0.6rem" }}>Timestamp</th>
                  <th style={{ padding: "0.6rem" }}>Mine / Zone</th>
                  <th style={{ padding: "0.6rem" }}>Coordinates</th>
                  <th style={{ padding: "0.6rem" }}>Distance</th>
                  <th style={{ padding: "0.6rem" }}>Status</th>
                  <th style={{ padding: "0.6rem" }}>Anomaly</th>
                  <th style={{ padding: "0.6rem" }}>Evidence / Audit</th>
                </tr>
              </thead>
              <tbody>
                {history.map((rec) => (
                  <tr key={rec.attendance_id} style={{ borderBottom: "1px solid #1e293b" }}>
                    <td style={{ padding: "0.6rem" }}>
                      {rec.captured_at ? new Date(rec.captured_at).toLocaleTimeString() : new Date(rec.server_recorded_at).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: "0.6rem" }}>
                      <div style={{ fontWeight: 600, color: "#f1f5f9" }}>{rec.mine_id}</div>
                      {rec.zone_id && <div style={{ fontSize: "0.75rem", color: "#38bdf8" }}>{rec.zone_id}</div>}
                    </td>
                    <td style={{ padding: "0.6rem", fontFamily: "monospace" }}>
                      {rec.latitude?.toFixed(4)}, {rec.longitude?.toFixed(4)}
                      {rec.accuracy_meters && <span style={{ color: "#64748b", fontSize: "0.75rem" }}> (±{Math.round(rec.accuracy_meters)}m)</span>}
                    </td>
                    <td style={{ padding: "0.6rem" }}>
                      {rec.distance_from_reference_meters !== null ? `${Math.round(rec.distance_from_reference_meters)}m` : "N/A"}
                    </td>
                    <td style={{ padding: "0.6rem" }}>
                      <span
                        style={{
                          padding: "0.2rem 0.5rem",
                          borderRadius: 4,
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          background: rec.status === "VALID" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                          color: rec.status === "VALID" ? "#34d399" : "#f87171",
                        }}
                      >
                        {rec.status}
                      </span>
                    </td>
                    <td style={{ padding: "0.6rem" }}>
                      {rec.anomaly_status !== "NONE" ? (
                        <span style={{ color: "#f87171", fontWeight: 600 }}>{rec.anomaly_status}</span>
                      ) : (
                        <span style={{ color: "#64748b" }}>Clean</span>
                      )}
                    </td>
                    <td style={{ padding: "0.6rem" }}>
                      {rec.evidence_id ? (
                        <button
                          onClick={() => navigate(`/audit-chain/evidence/${rec.evidence_id}`)}
                          style={{
                            background: "transparent",
                            border: "none",
                            color: "#38bdf8",
                            cursor: "pointer",
                            fontSize: "0.75rem",
                            textDecoration: "underline",
                          }}
                        >
                          View Hash Proof
                        </button>
                      ) : (
                        <span style={{ color: "#475569" }}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
