import React, { useState, useEffect } from "react";
import {
  fetchHierarchyTree,
  fetchMineZones,
  fetchMineContracts,
  fetchMineWorkforce,
  fetchSubsidiaryDetail,
  fetchAreaDetail,
} from "../api/hierarchy";
import type {
  HierarchyTreeNode,
  OperationalUnit,
  ContractMaster,
  WorkerMaster,
  OrganizationUnit,
} from "../api/hierarchy";
import HierarchyBreadcrumb from "../components/HierarchyBreadcrumb";

export const GovernanceMaster: React.FC = () => {
  const [tree, setTree] = useState<HierarchyTreeNode[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedNode, setSelectedNode] = useState<HierarchyTreeNode | null>(null);

  // Subsidiary drill-down details
  const [subsidiaryAreas, setSubsidiaryAreas] = useState<OrganizationUnit[]>([]);
  // Area drill-down details
  const [areaMines, setAreaMines] = useState<OrganizationUnit[]>([]);

  // Mine drill-down details
  const [mineZones, setMineZones] = useState<OperationalUnit[]>([]);
  const [mineContracts, setMineContracts] = useState<ContractMaster[]>([]);
  const [mineWorkforce, setMineWorkforce] = useState<WorkerMaster[]>([]);
  const [mineDetailLoading, setMineDetailLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"operational" | "contracts" | "workforce">("operational");

  // Expanded tree branches
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({
    "ORG-MINISTRY-MOC": true,
    "ORG-CIL-CIL": true,
    "ORG-SUBSIDIARY-BCCL": true,
    "ORG-AREA-BCCL-JHARIA": true,
  });

  useEffect(() => {
    loadTree();
  }, []);

  const loadTree = async () => {
    setLoading(true);
    try {
      const data = await fetchHierarchyTree(undefined, 6);
      setTree(data);
      if (data.length > 0) {
        // Select CIL or first top entity initially
        const topNode = data[0];
        const cilNode = topNode.children?.find((c) => c.unit_type === "CIL") || topNode;
        handleSelectNode(cilNode);
      }
    } catch (err) {
      console.error("Failed to load governance hierarchy tree:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (nodeId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedNodes((prev) => ({
      ...prev,
      [nodeId]: !prev[nodeId],
    }));
  };

  const handleSelectNode = async (node: HierarchyTreeNode) => {
    setSelectedNode(node);

    // Auto-expand this node
    setExpandedNodes((prev) => ({
      ...prev,
      [node.id]: true,
    }));

    if (node.unit_type === "SUBSIDIARY") {
      try {
        const res = await fetchSubsidiaryDetail(node.id);
        setSubsidiaryAreas(res.areas || []);
      } catch (err) {
        console.error("Failed to load subsidiary areas:", err);
      }
    } else if (node.unit_type === "AREA") {
      try {
        const res = await fetchAreaDetail(node.id);
        setAreaMines(res.mines || []);
      } catch (err) {
        console.error("Failed to load area mines:", err);
      }
    } else if (node.unit_type === "MINE") {
      setMineDetailLoading(true);
      try {
        const mineCode = node.code;
        const [zonesRes, contractsRes, workforceRes] = await Promise.all([
          fetchMineZones(mineCode).catch(() => []),
          fetchMineContracts(mineCode).catch(() => []),
          fetchMineWorkforce(mineCode).catch(() => []),
        ]);
        setMineZones(zonesRes);
        setMineContracts(contractsRes);
        setMineWorkforce(workforceRes);
      } catch (err) {
        console.error("Failed to load mine operational and workforce data:", err);
      } finally {
        setMineDetailLoading(false);
      }
    }
  };

  const renderTreeBranch = (node: HierarchyTreeNode, level = 0) => {
    const isExpanded = expandedNodes[node.id];
    const isSelected = selectedNode?.id === node.id;
    const hasChildren = node.children && node.children.length > 0;

    const getNodeBadge = (type: string) => {
      switch (type) {
        case "MINISTRY":
          return "bg-amber-100 text-amber-900 border-amber-300";
        case "CIL":
          return "bg-red-100 text-red-900 border-red-300 font-semibold";
        case "SUBSIDIARY":
          return "bg-blue-100 text-blue-900 border-blue-300";
        case "AREA":
          return "bg-purple-100 text-purple-900 border-purple-300";
        case "MINE":
          return "bg-emerald-100 text-emerald-900 border-emerald-300";
        default:
          return "bg-stone-100 text-stone-700 border-stone-300";
      }
    };

    return (
      <div key={node.id} className="select-none">
        <div
          onClick={() => handleSelectNode(node)}
          className={`flex items-center gap-1.5 py-1.5 px-2 rounded cursor-pointer transition-colors text-xs font-medium ${
            isSelected
              ? "bg-red-50 text-red-900 border-l-4 border-red-700 font-semibold shadow-xs"
              : "text-stone-700 hover:bg-stone-100"
          }`}
          style={{ paddingLeft: `${level * 14 + 8}px` }}
        >
          {hasChildren ? (
            <button
              type="button"
              onClick={(e) => toggleExpand(node.id, e)}
              className="w-4 h-4 flex items-center justify-center text-stone-400 hover:text-stone-700"
            >
              {isExpanded ? "▾" : "▸"}
            </button>
          ) : (
            <span className="w-4 inline-block text-center text-stone-300">•</span>
          )}
          <span className={`text-[9px] px-1 py-0.5 rounded border uppercase tracking-tight ${getNodeBadge(node.unit_type)}`}>
            {node.unit_type}
          </span>
          <span className="truncate flex-1">{node.name}</span>
          {node.mine_profile && (
            <span className="text-[9px] px-1.5 py-0.2 bg-stone-200 text-stone-700 rounded uppercase font-mono">
              {node.mine_profile.mine_type.includes("underground") ? "UG" : "OC"}
            </span>
          )}
        </div>

        {hasChildren && isExpanded && (
          <div className="border-l border-stone-200 ml-3.5 my-0.5">
            {node.children.map((child) => renderTreeBranch(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Institutional Top Header */}
      <div className="bg-white border-b-2 border-red-700 shadow-xs p-5 rounded">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-red-700 text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                CENTRAL GOVERNANCE MASTER
              </span>
              <span className="text-stone-400 text-xs font-mono">ISO 9001 / DGMS STATUTORY COMPLIANT</span>
            </div>
            <h1 className="text-2xl font-bold text-stone-900 mt-1">
              Authoritative Organizational & Operational Hierarchy
            </h1>
            <p className="text-stone-600 text-sm mt-0.5">
              Canonical governance backbone spanning Ministry of Coal, Coal India Limited, Subsidiaries, Operational Areas, and Mines.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="/admin/master-data"
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-stone-800 hover:bg-stone-900 text-white rounded text-xs font-semibold shadow-xs transition"
            >
              <span>⚙️</span> Master Data Administration
            </a>
          </div>
        </div>

        {/* Dynamic Breadcrumb Bar */}
        {selectedNode && (
          <div className="mt-4 pt-3 border-t border-stone-100">
            <HierarchyBreadcrumb unitId={selectedNode.id} />
          </div>
        )}
      </div>

      {/* Main Split Layout: Left Hierarchy Tree, Right Drill-Down View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Organization Tree (4 cols) */}
        <div className="lg:col-span-4 bg-white border border-stone-200 rounded p-4 shadow-xs flex flex-col h-[760px]">
          <div className="flex items-center justify-between pb-3 mb-2 border-b border-stone-200">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900">
                GOVERNANCE TREE
              </h2>
              <p className="text-[11px] text-stone-500">Ministry ➔ CIL ➔ Subsidiary ➔ Area ➔ Mine</p>
            </div>
            <button
              onClick={loadTree}
              className="text-xs text-stone-600 hover:text-red-700 underline font-medium"
            >
              Refresh
            </button>
          </div>

          <div className="overflow-y-auto flex-1 pr-1 space-y-1">
            {loading ? (
              <div className="p-4 text-center text-stone-400 text-xs">
                Loading canonical hierarchy...
              </div>
            ) : tree.length === 0 ? (
              <div className="p-4 text-center text-stone-400 text-xs">
                No organizational units found.
              </div>
            ) : (
              tree.map((node) => renderTreeBranch(node))
            )}
          </div>

          {/* Quick Filter / Legend */}
          <div className="pt-3 border-t border-stone-200 mt-2 text-[10px] text-stone-500 flex flex-wrap gap-2">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-amber-400 inline-block"></span> Ministry
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-red-600 inline-block"></span> CIL
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-blue-500 inline-block"></span> Subsidiary
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-purple-500 inline-block"></span> Area
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded bg-emerald-500 inline-block"></span> Mine
            </span>
          </div>
        </div>

        {/* Right Column: Node Details & Drill-Down (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {!selectedNode ? (
            <div className="bg-white border border-stone-200 rounded p-8 text-center text-stone-500">
              Select an organizational node from the hierarchy tree on the left to view governance details.
            </div>
          ) : (
            <>
              {/* Selected Node Summary Card */}
              <div className="bg-white border border-stone-200 rounded p-5 shadow-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-stone-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-stone-800 text-white uppercase tracking-wider font-mono">
                        {selectedNode.code}
                      </span>
                      <span className="text-xs text-stone-400 uppercase font-semibold">
                        {selectedNode.unit_type}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                        {selectedNode.status}
                      </span>
                    </div>
                    <h2 className="text-xl font-bold text-stone-900 mt-1">
                      {selectedNode.name}
                    </h2>
                    {selectedNode.legal_name && (
                      <p className="text-xs text-stone-500 italic mt-0.5">
                        {selectedNode.legal_name}
                      </p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 text-xs">
                  <div>
                    <span className="text-stone-400 block font-semibold text-[10px] uppercase">State</span>
                    <span className="text-stone-800 font-medium">{selectedNode.state || "National"}</span>
                  </div>
                  <div>
                    <span className="text-stone-400 block font-semibold text-[10px] uppercase">District</span>
                    <span className="text-stone-800 font-medium">{selectedNode.district || "—"}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-stone-400 block font-semibold text-[10px] uppercase">Headquarters / Location</span>
                    <span className="text-stone-800 font-medium truncate block">{selectedNode.headquarters || "—"}</span>
                  </div>
                </div>
              </div>

              {/* VIEW 1: CIL / MINISTRY OVERVIEW */}
              {(selectedNode.unit_type === "MINISTRY" || selectedNode.unit_type === "CIL") && (
                <div className="bg-white border border-stone-200 rounded p-5 shadow-xs space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-100 pb-2">
                    CIL OPERATING SUBSIDIARIES & ENTITIES
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {selectedNode.children?.map((sub) => (
                      <div
                        key={sub.id}
                        onClick={() => handleSelectNode(sub)}
                        className="border border-stone-200 hover:border-red-600 rounded p-3 bg-stone-50 hover:bg-red-50/20 cursor-pointer transition"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-stone-900">{sub.code}</span>
                          <span className="text-[9px] px-1.5 py-0.5 bg-blue-100 text-blue-900 rounded font-mono">
                            {sub.unit_type}
                          </span>
                        </div>
                        <p className="text-xs text-stone-700 font-medium mt-1 truncate">{sub.name}</p>
                        <p className="text-[11px] text-stone-500 mt-1">
                          {sub.state} · {sub.children?.length || 0} Areas
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* VIEW 2: SUBSIDIARY VIEW (Areas list) */}
              {selectedNode.unit_type === "SUBSIDIARY" && (
                <div className="bg-white border border-stone-200 rounded p-5 shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-stone-900">
                      OPERATIONAL AREAS IN {selectedNode.code}
                    </h3>
                    <span className="text-xs text-stone-500 font-mono">
                      {subsidiaryAreas.length} Areas Configured
                    </span>
                  </div>

                  {subsidiaryAreas.length === 0 ? (
                    <div className="p-6 text-center text-stone-400 text-xs">
                      No operational areas recorded under {selectedNode.name}.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {subsidiaryAreas.map((area) => (
                        <div
                          key={area.id}
                          onClick={() => {
                            const found = selectedNode.children?.find((c) => c.id === area.id);
                            if (found) handleSelectNode(found);
                          }}
                          className="border border-stone-200 hover:border-red-600 rounded p-3.5 bg-stone-50 hover:bg-red-50/20 cursor-pointer transition"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-stone-900">{area.name}</span>
                            <span className="text-[10px] text-stone-500 font-mono">{area.code}</span>
                          </div>
                          <p className="text-xs text-stone-600 mt-1">
                            HQ: {area.headquarters || area.district || area.state}
                          </p>
                          <span className="text-[10px] text-red-700 font-semibold mt-2 inline-block">
                            Drill down into Area Mines →
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* VIEW 3: AREA VIEW (Mines list) */}
              {selectedNode.unit_type === "AREA" && (
                <div className="bg-white border border-stone-200 rounded p-5 shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-stone-900">
                      MINES & PROJECTS IN {selectedNode.name}
                    </h3>
                    <span className="text-xs text-stone-500 font-mono">
                      {areaMines.length} Mines Operating
                    </span>
                  </div>

                  {areaMines.length === 0 ? (
                    <div className="p-6 text-center text-stone-400 text-xs">
                      No mines configured under {selectedNode.name}.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {areaMines.map((m) => (
                        <div
                          key={m.id}
                          onClick={() => {
                            const found = selectedNode.children?.find((c) => c.id === m.id);
                            if (found) handleSelectNode(found);
                          }}
                          className="border border-stone-200 hover:border-emerald-600 rounded p-3.5 bg-stone-50 hover:bg-emerald-50/20 cursor-pointer transition"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-stone-900">{m.name}</span>
                            <span className="text-[9px] px-1.5 py-0.5 bg-emerald-100 text-emerald-800 rounded font-mono">
                              MINE
                            </span>
                          </div>
                          <p className="text-xs text-stone-500 mt-1 font-mono">{m.code}</p>
                          <span className="text-[10px] text-emerald-800 font-semibold mt-2 inline-block">
                            View Operational Profile & Workforce →
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* VIEW 4: MINE VIEW (Operational Units, Contracts, Workforce) */}
              {selectedNode.unit_type === "MINE" && (
                <div className="bg-white border border-stone-200 rounded shadow-xs overflow-hidden">
                  {/* Mine Type & Operational Capability Header */}
                  <div className="bg-stone-50 border-b border-stone-200 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <span className="text-[10px] font-bold text-stone-400 uppercase tracking-wider block">
                          MINE TYPE PROPERTY (NOT HIERARCHY NODE)
                        </span>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-bold tracking-wide uppercase border ${
                              selectedNode.mine_profile?.mine_type.includes("underground")
                                ? "bg-purple-100 text-purple-900 border-purple-300"
                                : "bg-amber-100 text-amber-900 border-amber-300"
                            }`}
                          >
                            {selectedNode.mine_profile?.mine_type.includes("underground")
                              ? "UNDERGROUND COAL MINE"
                              : "OPENCAST COAL MINE"}
                          </span>
                          <span className="text-xs text-stone-600 font-medium">
                            Gassiness: {selectedNode.mine_profile?.gassy_degree || "NOT APPLICABLE"}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 text-xs">
                        {selectedNode.mine_profile?.mechanised && (
                          <span className="px-2 py-0.5 bg-stone-200 text-stone-800 rounded text-[11px] font-medium">
                            ⚙️ Mechanised
                          </span>
                        )}
                        {selectedNode.mine_profile?.uses_hemm && (
                          <span className="px-2 py-0.5 bg-stone-200 text-stone-800 rounded text-[11px] font-medium">
                            🚜 HEMM Enabled
                          </span>
                        )}
                        {selectedNode.mine_profile?.has_winding_installation && (
                          <span className="px-2 py-0.5 bg-stone-200 text-stone-800 rounded text-[11px] font-medium">
                            🏗️ Winding Engine
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Operational Tabs */}
                  <div className="border-b border-stone-200 flex px-4 gap-4 bg-white text-xs font-semibold">
                    <button
                      type="button"
                      onClick={() => setActiveTab("operational")}
                      className={`py-3 border-b-2 transition ${
                        activeTab === "operational"
                          ? "border-red-700 text-red-700"
                          : "border-transparent text-stone-500 hover:text-stone-800"
                      }`}
                    >
                      OPERATIONAL STRUCTURE ({mineZones.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveTab("contracts")}
                      className={`py-3 border-b-2 transition ${
                        activeTab === "contracts"
                          ? "border-red-700 text-red-700"
                          : "border-transparent text-stone-500 hover:text-stone-800"
                      }`}
                    >
                      CONTRACTS & MDO ({mineContracts.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveTab("workforce")}
                      className={`py-3 border-b-2 transition ${
                        activeTab === "workforce"
                          ? "border-red-700 text-red-700"
                          : "border-transparent text-stone-500 hover:text-stone-800"
                      }`}
                    >
                      WORKFORCE ROSTER ({mineWorkforce.length})
                    </button>
                  </div>

                  <div className="p-5">
                    {mineDetailLoading ? (
                      <div className="p-8 text-center text-stone-400 text-xs">
                        Loading operational structure and workforce bindings...
                      </div>
                    ) : (
                      <>
                        {/* TAB 1: OPERATIONAL STRUCTURE */}
                        {activeTab === "operational" && (
                          <div className="space-y-4">
                            <div className="flex items-center justify-between text-xs text-stone-500">
                              <span>
                                Operational Hierarchy:{" "}
                                {selectedNode.mine_profile?.mine_type.includes("underground")
                                  ? "Mine ➔ Shaft ➔ Ventilation District ➔ Panel ➔ Section ➔ Working Face"
                                  : "Mine ➔ Pit ➔ Bench ➔ Haul Road / Dump / HEMM Park"}
                              </span>
                            </div>

                            {mineZones.length === 0 ? (
                              <div className="p-6 text-center text-stone-400 text-xs border border-dashed rounded">
                                No operational units registered for this mine.
                              </div>
                            ) : (
                              <div className="overflow-x-auto">
                                <table className="w-full text-left text-xs border-collapse">
                                  <thead>
                                    <tr className="bg-stone-50 border-b border-stone-200 text-stone-600 font-semibold">
                                      <th className="py-2.5 px-3">Unit Code</th>
                                      <th className="py-2.5 px-3">Type</th>
                                      <th className="py-2.5 px-3">Operational Unit Name</th>
                                      <th className="py-2.5 px-3">Parent Operational Node</th>
                                      <th className="py-2.5 px-3">Status</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-stone-100">
                                    {mineZones.map((zone) => (
                                      <tr key={zone.id} className="hover:bg-stone-50/50">
                                        <td className="py-2.5 px-3 font-mono font-bold text-stone-900">
                                          {zone.code}
                                        </td>
                                        <td className="py-2.5 px-3">
                                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-stone-100 border border-stone-300 text-stone-800">
                                            {zone.unit_type}
                                          </span>
                                        </td>
                                        <td className="py-2.5 px-3 font-medium text-stone-800">{zone.name}</td>
                                        <td className="py-2.5 px-3 font-mono text-[11px] text-stone-500">
                                          {zone.parent_operational_unit_id || "Root (Mine Head)"}
                                        </td>
                                        <td className="py-2.5 px-3">
                                          <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200">
                                            ACTIVE
                                          </span>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        )}

                        {/* TAB 2: CONTRACTS & MDO */}
                        {activeTab === "contracts" && (
                          <div className="space-y-4">
                            <p className="text-xs text-stone-500">
                              Commercial and statutory work orders bound to this mine. Contracts derive Area and Subsidiary lineages from the canonical hierarchy.
                            </p>

                            {mineContracts.length === 0 ? (
                              <div className="p-6 text-center text-stone-400 text-xs border border-dashed rounded">
                                No contracts configured for this mine.
                              </div>
                            ) : (
                              <div className="space-y-3">
                                {mineContracts.map((c) => (
                                  <div
                                    key={c.id}
                                    className="border border-stone-200 rounded p-4 bg-stone-50/50 space-y-2"
                                  >
                                    <div className="flex flex-wrap items-center justify-between gap-2">
                                      <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold font-mono text-stone-900">
                                          {c.contract_number}
                                        </span>
                                        <span className="text-[10px] px-2 py-0.5 bg-blue-100 text-blue-900 rounded font-semibold uppercase">
                                          {c.contract_type}
                                        </span>
                                      </div>
                                      <span className="text-[10px] font-mono text-stone-500">
                                        Validity: {c.start_date} to {c.end_date || "Continuous"}
                                      </span>
                                    </div>
                                    <div className="text-xs">
                                      <span className="font-semibold text-stone-800">
                                        Contractor: {c.contractor_name || c.contractor_id}
                                      </span>
                                      <p className="text-stone-600 text-[11px] mt-0.5">Scope: {c.scope || "Operational Coal Extraction / Support"}</p>
                                    </div>
                                    <div className="text-[11px] text-stone-500 pt-1 border-t border-stone-100 flex items-center justify-between">
                                      <span>Max Workforce Limit: {c.workforce_limit || "Uncapped"}</span>
                                      <span className="text-emerald-700 font-semibold">Status: {c.status}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {/* TAB 3: WORKFORCE ROSTER */}
                        {activeTab === "workforce" && (
                          <div className="space-y-4">
                            <div className="flex items-center justify-between text-xs text-stone-500">
                              <span>
                                Worker Master: strictly segregated from application login accounts. Workers represent registered departmental and contractor personnel.
                              </span>
                            </div>

                            {mineWorkforce.length === 0 ? (
                              <div className="p-6 text-center text-stone-400 text-xs border border-dashed rounded">
                                No registered workers found for this mine.
                              </div>
                            ) : (
                              <div className="overflow-x-auto">
                                <table className="w-full text-left text-xs border-collapse">
                                  <thead>
                                    <tr className="bg-stone-50 border-b border-stone-200 text-stone-600 font-semibold">
                                      <th className="py-2.5 px-3">Worker Code</th>
                                      <th className="py-2.5 px-3">Name</th>
                                      <th className="py-2.5 px-3">Type</th>
                                      <th className="py-2.5 px-3">Contractor / Employer</th>
                                      <th className="py-2.5 px-3">Skill / Dept</th>
                                      <th className="py-2.5 px-3">Training</th>
                                      <th className="py-2.5 px-3">Status</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-stone-100">
                                    {mineWorkforce.map((w) => (
                                      <tr key={w.id} className="hover:bg-stone-50/50">
                                        <td className="py-2.5 px-3 font-mono font-bold text-stone-900">
                                          {w.worker_code}
                                        </td>
                                        <td className="py-2.5 px-3 font-medium text-stone-900">
                                          {w.name}
                                        </td>
                                        <td className="py-2.5 px-3">
                                          <span
                                            className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                                              w.worker_type === "DEPARTMENTAL"
                                                ? "bg-emerald-100 text-emerald-900"
                                                : w.worker_type === "MDO"
                                                ? "bg-purple-100 text-purple-900"
                                                : "bg-blue-100 text-blue-900"
                                            }`}
                                          >
                                            {w.worker_type}
                                          </span>
                                        </td>
                                        <td className="py-2.5 px-3 text-stone-700">
                                          {w.contractor_name || "Departmental"}
                                        </td>
                                        <td className="py-2.5 px-3 text-stone-600">
                                          {w.skill_category || "General"} · {w.department || "Operations"}
                                        </td>
                                        <td className="py-2.5 px-3">
                                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-stone-100 text-stone-700 font-medium">
                                            {w.training_status}
                                          </span>
                                        </td>
                                        <td className="py-2.5 px-3">
                                          <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200">
                                            {w.active ? "ACTIVE" : "INACTIVE"}
                                          </span>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default GovernanceMaster;
