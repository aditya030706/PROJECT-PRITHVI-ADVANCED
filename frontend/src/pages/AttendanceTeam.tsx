import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import {
  getTeamAttendance,
  getAttendanceAnomalies,
  getMineZones,
  createMineZone,
  type TeamAttendanceSummary,
  type AnomalySignal,
  type MineZonesResponse,
} from "../api/attendance";
import {
  Users,
  Shield,
  AlertTriangle,
  RefreshCw,
  MapPin,
  X,
  Layers,
  Search,
} from "lucide-react";

export default function AttendanceTeam() {
  const { session } = useAuth();
  const navigate = useNavigate();

  const [selectedMineId, setSelectedMineId] = useState<string>("");
  const [data, setData] = useState<TeamAttendanceSummary | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalySignal[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  // Zone management modal state
  const [showZoneModal, setShowZoneModal] = useState<boolean>(false);
  const [zonesList, setZonesList] = useState<MineZonesResponse | null>(null);
  const [newZoneName, setNewZoneName] = useState<string>("");
  const [newZoneLat, setNewZoneLat] = useState<number>(23.7505);
  const [newZoneLon, setNewZoneLon] = useState<number>(86.4202);
  const [newZoneRadius, setNewZoneRadius] = useState<number>(150);
  const [newZoneDesc, setNewZoneDesc] = useState<string>("");
  const [creatingZone, setCreatingZone] = useState<boolean>(false);

  // Load team data & anomalies
  const loadData = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const [teamSummary, anomalySignals] = await Promise.all([
        getTeamAttendance(selectedMineId || undefined, session.user_id, session.role),
        getAttendanceAnomalies(selectedMineId || undefined, session.role),
      ]);
      setData(teamSummary);
      setAnomalies(anomalySignals);
    } catch (err) {
      console.error("Error loading team attendance data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedMineId, session?.user_id, session?.role]);

  // Load zones if modal opened
  const loadZones = async () => {
    const mineToQuery = selectedMineId || "MINE-BCCL-JHARIA-01";
    try {
      const zData = await getMineZones(mineToQuery);
      setZonesList(zData);
    } catch (err) {
      console.error("Error loading zones:", err);
    }
  };

  const handleOpenZoneModal = () => {
    setShowZoneModal(true);
    loadZones();
  };

  const handleCreateZone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session) return;
    setCreatingZone(true);
    try {
      await createMineZone(
        {
          mine_id: selectedMineId || "MINE-BCCL-JHARIA-01",
          name: newZoneName,
          latitude: newZoneLat,
          longitude: newZoneLon,
          geofence_radius_meters: newZoneRadius,
          description: newZoneDesc,
        },
        session.role
      );
      setNewZoneName("");
      setNewZoneDesc("");
      loadZones();
    } catch (err) {
      console.error("Error creating zone:", err);
    } finally {
      setCreatingZone(false);
    }
  };

  // Filter records
  const filteredRecords = (data?.records || []).filter((rec) => {
    const matchesSearch =
      rec.user_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rec.mine_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (rec.zone_id && rec.zone_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (rec.inspection_id && rec.inspection_id.toLowerCase().includes(searchTerm.toLowerCase()));

    if (!matchesSearch) return false;

    if (filterStatus === "VALID") return rec.status === "VALID";
    if (filterStatus === "OUTSIDE") return rec.geofence_status === "OUTSIDE_GEOFENCE";
    if (filterStatus === "FLAGGED") return rec.anomaly_status !== "NONE";
    return true;
  });

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "1.5rem 1rem" }}>
      {/* Header */}
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
            <Users size={24} color="#38bdf8" />
            <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700, color: "#f8fafc" }}>
              Field Team Attendance & Geo-Presence Console
            </h1>
          </div>
          <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.875rem" }}>
            Operational supervisor & manager live monitoring for satellite attendance, shift muster, and geofence integrity.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button
            onClick={() => navigate("/field")}
            style={{
              background: "#10b981",
              color: "#ffffff",
              border: "none",
              padding: "0.6rem 1rem",
              borderRadius: 8,
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.85rem",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            <MapPin size={16} />
            Check-In As Field User
          </button>
          <button
            onClick={handleOpenZoneModal}
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
            Manage Mine Zones
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            style={{
              background: "#1e293b",
              color: "#38bdf8",
              border: "1px solid #334155",
              padding: "0.6rem",
              borderRadius: 8,
              cursor: "pointer",
            }}
            title="Refresh Data"
          >
            <RefreshCw size={16} className={loading ? "spin" : ""} />
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "1.25rem" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.75rem", fontWeight: 600 }}>TOTAL CHECK-INS TODAY</div>
          <div style={{ color: "#f8fafc", fontSize: "1.8rem", fontWeight: 700, marginTop: "0.25rem" }}>
            {data?.total_records_today ?? 0}
          </div>
          <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.25rem" }}>
            Field inspectors & supervisors
          </div>
        </div>

        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "1.25rem" }}>
          <div style={{ color: "#10b981", fontSize: "0.75rem", fontWeight: 600 }}>VALID WITHIN GEOFENCE</div>
          <div style={{ color: "#34d399", fontSize: "1.8rem", fontWeight: 700, marginTop: "0.25rem" }}>
            {data?.valid_count ?? 0}
          </div>
          <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.25rem" }}>
            Verified on-site coordinates
          </div>
        </div>

        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "1.25rem" }}>
          <div style={{ color: "#f87171", fontSize: "0.75rem", fontWeight: 600 }}>OUTSIDE GEOFENCE BREACHES</div>
          <div style={{ color: "#ef4444", fontSize: "1.8rem", fontWeight: 700, marginTop: "0.25rem" }}>
            {data?.outside_geofence_count ?? 0}
          </div>
          <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.25rem" }}>
            Flagged for supervisor review
          </div>
        </div>

        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "1.25rem" }}>
          <div style={{ color: "#fbbf24", fontSize: "0.75rem", fontWeight: 600 }}>GEO-COMPLIANCE RATE</div>
          <div style={{ color: "#fbbf24", fontSize: "1.8rem", fontWeight: 700, marginTop: "0.25rem" }}>
            {data?.compliance_rate_pct ?? 100}%
          </div>
          <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.25rem" }}>
            Target: 100% statutory adherence
          </div>
        </div>
      </div>

      {/* Live Anomaly Alert Banner */}
      {anomalies.length > 0 && (
        <div
          style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid #ef4444",
            borderRadius: 10,
            padding: "1rem 1.25rem",
            marginBottom: "1.5rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <AlertTriangle size={18} color="#ef4444" />
            <span style={{ fontWeight: 700, color: "#fca5a5", fontSize: "0.95rem" }}>
              Active Anomaly Signals ({anomalies.length})
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {anomalies.slice(0, 4).map((a, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontSize: "0.825rem",
                  color: "#cbd5e1",
                  background: "rgba(15, 23, 42, 0.6)",
                  padding: "0.4rem 0.75rem",
                  borderRadius: 6,
                }}
              >
                <div>
                  <strong style={{ color: "#f87171" }}>{a.anomaly_label}</strong> · User:{" "}
                  <code style={{ color: "#38bdf8" }}>{a.user_id}</code> ({a.mine_id})
                </div>
                <div style={{ color: "#94a3b8", fontSize: "0.75rem" }}>
                  {a.distance_meters !== null && `${Math.round(a.distance_meters)}m off `}·{" "}
                  {new Date(a.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters and Search Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flex: 1, minWidth: 280 }}>
          <div style={{ position: "relative", flex: 1 }}>
            <Search size={16} color="#64748b" style={{ position: "absolute", left: 10, top: 11 }} />
            <input
              type="text"
              placeholder="Search by worker ID, mine, zone, or inspection..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: "100%",
                padding: "0.6rem 0.6rem 0.6rem 2.2rem",
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 8,
                color: "#f8fafc",
                fontSize: "0.85rem",
              }}
            />
          </div>

          <select
            value={selectedMineId}
            onChange={(e) => setSelectedMineId(e.target.value)}
            style={{
              padding: "0.6rem",
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#f8fafc",
              fontSize: "0.85rem",
            }}
          >
            <option value="">All Demonstrator Mines</option>
            <option value="MINE-BCCL-JHARIA-01">Jharia Underground (BCCL)</option>
            <option value="MINE-ECL-RANIGANJ-01">Raniganj Underground (ECL)</option>
            <option value="MINE-MCL-TALCHER-01">Talcher Opencast (MCL)</option>
          </select>
        </div>

        {/* Filter Badges */}
        <div style={{ display: "flex", gap: "0.4rem" }}>
          {["ALL", "VALID", "OUTSIDE", "FLAGGED"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              style={{
                background: filterStatus === st ? "#0284c7" : "#1e293b",
                color: filterStatus === st ? "#fff" : "#94a3b8",
                border: "1px solid #334155",
                padding: "0.45rem 0.75rem",
                borderRadius: 6,
                fontSize: "0.75rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Attendance Roster Table */}
      <div
        style={{
          background: "#0f172a",
          border: "1px solid #1e293b",
          borderRadius: 12,
          overflow: "hidden",
        }}
      >
        <div style={{ padding: "1rem 1.25rem", borderBottom: "1px solid #1e293b" }}>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 600, color: "#f8fafc" }}>
            Operational Personnel Attendance Log ({filteredRecords.length})
          </h3>
        </div>

        {filteredRecords.length === 0 ? (
          <div style={{ textAlign: "center", padding: "3rem", color: "#64748b" }}>
            No attendance records match the current criteria.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.825rem", color: "#cbd5e1" }}>
              <thead>
                <tr style={{ background: "#0b1329", borderBottom: "1px solid #334155", color: "#94a3b8", textAlign: "left" }}>
                  <th style={{ padding: "0.75rem 1rem" }}>Worker Identity</th>
                  <th style={{ padding: "0.75rem 1rem" }}>Mine Location</th>
                  <th style={{ padding: "0.75rem 1rem" }}>Zone</th>
                  <th style={{ padding: "0.75rem 1rem" }}>Recorded GPS</th>
                  <th style={{ padding: "0.75rem 1rem" }}>Distance</th>
                  <th style={{ padding: "0.75rem 1rem" }}>Time</th>
                  <th style={{ padding: "0.75rem 1rem" }}>Status</th>
                  <th style={{ padding: "0.75rem 1rem" }}>Inspection Link</th>
                  <th style={{ padding: "0.75rem 1rem" }}>Evidence Hash</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((rec) => (
                  <tr key={rec.attendance_id} style={{ borderBottom: "1px solid #1e293b" }}>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      <div style={{ fontWeight: 600, color: "#f8fafc" }}>{rec.user_id}</div>
                      <div style={{ fontSize: "0.7rem", color: "#64748b" }}>{rec.user_role}</div>
                    </td>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      <span style={{ color: "#38bdf8", fontWeight: 500 }}>{rec.mine_id}</span>
                    </td>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      {rec.zone_id ? (
                        <span style={{ color: "#e2e8f0" }}>{rec.zone_id}</span>
                      ) : (
                        <span style={{ color: "#64748b" }}>General Mine</span>
                      )}
                    </td>
                    <td style={{ padding: "0.75rem 1rem", fontFamily: "monospace" }}>
                      {rec.latitude?.toFixed(4)}, {rec.longitude?.toFixed(4)}
                      {rec.accuracy_meters && (
                        <span style={{ color: "#64748b", fontSize: "0.7rem" }}> (±{Math.round(rec.accuracy_meters)}m)</span>
                      )}
                    </td>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      <span
                        style={{
                          fontWeight: 600,
                          color: rec.geofence_status === "INSIDE_GEOFENCE" ? "#34d399" : "#f87171",
                        }}
                      >
                        {rec.distance_from_reference_meters !== null ? `${Math.round(rec.distance_from_reference_meters)}m` : "—"}
                      </span>
                    </td>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      <div>{new Date(rec.server_recorded_at).toLocaleTimeString()}</div>
                      <div style={{ fontSize: "0.7rem", color: "#64748b" }}>
                        {new Date(rec.server_recorded_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                        <span
                          style={{
                            display: "inline-block",
                            padding: "0.2rem 0.5rem",
                            borderRadius: 4,
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            textAlign: "center",
                            background: rec.status === "VALID" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                            color: rec.status === "VALID" ? "#34d399" : "#f87171",
                          }}
                        >
                          {rec.status}
                        </span>
                        {rec.anomaly_status !== "NONE" && (
                          <span style={{ fontSize: "0.65rem", color: "#ef4444", fontWeight: 600 }}>
                            {rec.anomaly_status}
                          </span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      {rec.inspection_id ? (
                        <span style={{ color: "#38bdf8", fontSize: "0.75rem", fontFamily: "monospace" }}>
                          {rec.inspection_id}
                        </span>
                      ) : (
                        <span style={{ color: "#475569" }}>—</span>
                      )}
                    </td>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      {rec.evidence_id ? (
                        <button
                          onClick={() => navigate(`/audit-chain/evidence/${rec.evidence_id}`)}
                          style={{
                            background: "transparent",
                            border: "none",
                            color: "#38bdf8",
                            cursor: "pointer",
                            fontSize: "0.75rem",
                            display: "flex",
                            alignItems: "center",
                            gap: "0.3rem",
                            textDecoration: "underline",
                          }}
                        >
                          <Shield size={12} />
                          Anchor
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

      {/* Zone Management Modal */}
      {showZoneModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
        >
          <div
            style={{
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 12,
              width: "100%",
              maxWidth: 640,
              maxHeight: "90vh",
              overflowY: "auto",
              padding: "1.5rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Layers size={20} color="#38bdf8" />
                <h3 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700, color: "#f8fafc" }}>
                  Geofenced Mine Zones
                </h3>
              </div>
              <button
                onClick={() => setShowZoneModal(false)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer" }}
              >
                <X size={20} />
              </button>
            </div>

            <p style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: 0 }}>
              Registered micro-fenced operational areas for <strong>{selectedMineId || "MINE-BCCL-JHARIA-01"}</strong>.
            </p>

            {/* List existing zones */}
            <div style={{ marginBottom: "1.5rem" }}>
              <h4 style={{ fontSize: "0.9rem", color: "#e2e8f0", marginBottom: "0.5rem" }}>Configured Zones</h4>
              {zonesList?.zones && zonesList.zones.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {zonesList.zones.map((z) => (
                    <div
                      key={z.mine_zone_id}
                      style={{
                        background: "#1e293b",
                        border: "1px solid #334155",
                        borderRadius: 6,
                        padding: "0.6rem 0.8rem",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: "0.825rem",
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, color: "#f8fafc" }}>{z.name}</div>
                        <div style={{ color: "#94a3b8", fontSize: "0.75rem" }}>{z.description}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ color: "#38bdf8", fontWeight: 600 }}>Radius: {z.geofence_radius_meters}m</div>
                        <div style={{ color: "#64748b", fontSize: "0.7rem", fontFamily: "monospace" }}>
                          {z.latitude.toFixed(4)}, {z.longitude.toFixed(4)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: "#64748b", fontSize: "0.8rem" }}>No micro-zones registered for this mine.</div>
              )}
            </div>

            {/* Form to add a new zone */}
            <form onSubmit={handleCreateZone} style={{ borderTop: "1px solid #334155", paddingTop: "1rem" }}>
              <h4 style={{ fontSize: "0.9rem", color: "#e2e8f0", marginBottom: "0.75rem" }}>
                Add New Micro-Geofence Zone
              </h4>

              <div style={{ marginBottom: "0.75rem" }}>
                <label style={{ fontSize: "0.75rem", color: "#94a3b8", display: "block", marginBottom: "0.25rem" }}>
                  ZONE NAME
                </label>
                <input
                  type="text"
                  required
                  value={newZoneName}
                  onChange={(e) => setNewZoneName(e.target.value)}
                  placeholder="e.g. South Ventilation Portal"
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

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem", marginBottom: "0.75rem" }}>
                <div>
                  <label style={{ fontSize: "0.7rem", color: "#64748b" }}>LATITUDE</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={newZoneLat}
                    onChange={(e) => setNewZoneLat(parseFloat(e.target.value))}
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
                    required
                    value={newZoneLon}
                    onChange={(e) => setNewZoneLon(parseFloat(e.target.value))}
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
                  <label style={{ fontSize: "0.7rem", color: "#64748b" }}>RADIUS (M)</label>
                  <input
                    type="number"
                    step="10"
                    required
                    value={newZoneRadius}
                    onChange={(e) => setNewZoneRadius(parseFloat(e.target.value))}
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

              <div style={{ marginBottom: "1rem" }}>
                <label style={{ fontSize: "0.75rem", color: "#94a3b8", display: "block", marginBottom: "0.25rem" }}>
                  OPERATIONAL DESCRIPTION
                </label>
                <input
                  type="text"
                  value={newZoneDesc}
                  onChange={(e) => setNewZoneDesc(e.target.value)}
                  placeholder="Safety purpose or equipment location..."
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

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
                <button
                  type="button"
                  onClick={() => setShowZoneModal(false)}
                  style={{
                    background: "#334155",
                    color: "#cbd5e1",
                    border: "none",
                    padding: "0.5rem 1rem",
                    borderRadius: 6,
                    cursor: "pointer",
                    fontSize: "0.85rem",
                  }}
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={creatingZone}
                  style={{
                    background: "#0284c7",
                    color: "#fff",
                    border: "none",
                    padding: "0.5rem 1rem",
                    borderRadius: 6,
                    cursor: "pointer",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                  }}
                >
                  {creatingZone ? "Registering..." : "Add Zone"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
