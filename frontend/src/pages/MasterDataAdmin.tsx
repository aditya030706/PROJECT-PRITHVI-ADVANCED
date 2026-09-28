import React, { useState, useEffect } from "react";
import {
  fetchOrganizationUnits,
  createOrganizationUnit,
  createOperationalUnit,
  fetchContractors,
  createContractor,
  fetchContracts,
  createContract,
  fetchWorkers,
  createWorker,
  fetchOrganizationAuditEvents,
} from "../api/hierarchy";
import type {
  OrganizationUnit,
  ContractorMaster,
  ContractMaster,
  WorkerMaster,
  OrganizationAuditEvent,
} from "../api/hierarchy";
import { useAuth } from "../auth/AuthContext";

export const MasterDataAdmin: React.FC = () => {
  const { session } = useAuth();
  const [activeTab, setActiveTab] = useState<
    "orgs" | "operational" | "contractors" | "contracts" | "workers" | "audit"
  >("orgs");

  // Data states
  const [orgUnits, setOrgUnits] = useState<OrganizationUnit[]>([]);
  const [contractors, setContractors] = useState<ContractorMaster[]>([]);
  const [contracts, setContracts] = useState<ContractMaster[]>([]);
  const [workers, setWorkers] = useState<WorkerMaster[]>([]);
  const [auditEvents, setAuditEvents] = useState<OrganizationAuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Forms states
  const [newOrg, setNewOrg] = useState({
    unit_type: "AREA",
    code: "",
    name: "",
    parent_id: "",
    state: "",
    district: "",
    headquarters: "",
  });

  const [newOpUnit, setNewOpUnit] = useState({
    mine_id: "MINE-BCCL-JHARIA-01",
    unit_type: "VENTILATION_DISTRICT",
    code: "",
    name: "",
    parent_operational_unit_id: "",
  });

  const [newContractor, setNewContractor] = useState({
    legal_name: "",
    display_name: "",
    contractor_type: "WORK_ORDER",
    registration_reference: "",
  });

  const [newContract, setNewContract] = useState({
    contractor_id: "",
    mine_id: "MINE-BCCL-JHARIA-01",
    contract_type: "WORK_ORDER",
    contract_number: "",
    scope: "",
    start_date: new Date().toISOString().split("T")[0],
    workforce_limit: 100,
  });

  const [newWorker, setNewWorker] = useState({
    worker_code: "",
    name: "",
    worker_type: "CONTRACTOR",
    contractor_id: "",
    contract_id: "",
    mine_id: "MINE-BCCL-JHARIA-01",
    skill_category: "SKILLED",
    department: "MINING",
  });

  useEffect(() => {
    loadTabContent();
  }, [activeTab]);

  const loadTabContent = async () => {
    setLoading(true);
    setActionMessage(null);
    setActionError(null);
    try {
      if (activeTab === "orgs") {
        const units = await fetchOrganizationUnits();
        setOrgUnits(units);
      } else if (activeTab === "contractors") {
        const data = await fetchContractors();
        setContractors(data);
      } else if (activeTab === "contracts") {
        const [contractsData, contractorsData] = await Promise.all([
          fetchContracts(),
          fetchContractors(),
        ]);
        setContracts(contractsData);
        setContractors(contractorsData);
      } else if (activeTab === "workers") {
        const [workersData, contractorsData, contractsData] = await Promise.all([
          fetchWorkers(),
          fetchContractors(),
          fetchContracts(),
        ]);
        setWorkers(workersData);
        setContractors(contractorsData);
        setContracts(contractsData);
      } else if (activeTab === "audit") {
        const data = await fetchOrganizationAuditEvents();
        setAuditEvents(data);
      }
    } catch (err: any) {
      console.error(err);
      setActionError(err.message || "Failed to load master data");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    try {
      await createOrganizationUnit(newOrg);
      setActionMessage(`Organization Unit ${newOrg.code} created successfully.`);
      setNewOrg({ unit_type: "AREA", code: "", name: "", parent_id: "", state: "", district: "", headquarters: "" });
      loadTabContent();
    } catch (err: any) {
      setActionError(err.message || "Failed to create unit");
    }
  };

  const handleCreateOpUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    try {
      await createOperationalUnit(newOpUnit);
      setActionMessage(`Operational Unit ${newOpUnit.code} created successfully.`);
      setNewOpUnit({ mine_id: "MINE-BCCL-JHARIA-01", unit_type: "VENTILATION_DISTRICT", code: "", name: "", parent_operational_unit_id: "" });
    } catch (err: any) {
      setActionError(err.message || "Failed to create operational unit");
    }
  };

  const handleCreateContractor = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    try {
      await createContractor(newContractor);
      setActionMessage(`Contractor ${newContractor.display_name} created successfully.`);
      setNewContractor({ legal_name: "", display_name: "", contractor_type: "WORK_ORDER", registration_reference: "" });
      loadTabContent();
    } catch (err: any) {
      setActionError(err.message || "Failed to create contractor");
    }
  };

  const handleCreateContract = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    try {
      await createContract(newContract);
      setActionMessage(`Contract ${newContract.contract_number} registered successfully.`);
      loadTabContent();
    } catch (err: any) {
      setActionError(err.message || "Failed to create contract");
    }
  };

  const handleCreateWorker = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    try {
      await createWorker({
        ...newWorker,
        name: `${newWorker.name} [DEMO / SIMULATED]`,
      });
      setActionMessage(`Worker ${newWorker.worker_code} registered in muster ledger.`);
      setNewWorker({ worker_code: "", name: "", worker_type: "CONTRACTOR", contractor_id: "", contract_id: "", mine_id: "MINE-BCCL-JHARIA-01", skill_category: "SKILLED", department: "MINING" });
      loadTabContent();
    } catch (err: any) {
      setActionError(err.message || "Failed to register worker");
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Institutional Top Bar */}
      <div className="bg-white border-b-2 border-stone-800 shadow-xs p-5 rounded">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-stone-800 text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                MASTER DATA ADMINISTRATION
              </span>
              <span className="text-red-700 text-xs font-semibold">RESTRICTED CORPORATE AUTHORITY</span>
            </div>
            <h1 className="text-2xl font-bold text-stone-900 mt-1">
              Governance Master Data & Enterprise Directory
            </h1>
            <p className="text-stone-600 text-sm mt-0.5">
              Controlled master data provisioning for organizations, areas, operational units, commercial contracts, and registered workforce.
            </p>
          </div>
          <div className="text-right text-xs text-stone-500 font-mono">
            Active Role: <span className="font-bold text-stone-900">{session?.role || "GUEST"}</span>
            {loading && <span className="text-xs text-stone-400 font-mono ml-2 animate-pulse">Loading...</span>}
          </div>
        </div>
      </div>

      {/* Notifications */}
      {actionMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 text-emerald-800 text-xs rounded font-medium">
          ✓ {actionMessage}
        </div>
      )}
      {actionError && (
        <div className="p-3 bg-red-50 border border-red-300 text-red-800 text-xs rounded font-medium">
          ✕ {actionError}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="bg-white border border-stone-200 rounded p-1 shadow-xs flex flex-wrap gap-1 text-xs font-bold">
        {[
          { id: "orgs", label: "ORGANIZATIONS & AREAS" },
          { id: "operational", label: "OPERATIONAL UNITS" },
          { id: "contractors", label: "CONTRACTORS" },
          { id: "contracts", label: "CONTRACTS & MDO" },
          { id: "workers", label: "WORKER MASTER" },
          { id: "audit", label: "AUDIT LOG EVENTS" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2.5 rounded transition ${
              activeTab === tab.id
                ? "bg-stone-800 text-white shadow-xs"
                : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: ORGANIZATIONS */}
      {activeTab === "orgs" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Create Unit Form (4 cols) */}
          <div className="lg:col-span-4 bg-white border border-stone-200 rounded p-5 shadow-xs h-fit">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2 mb-4">
              Add Organizational Unit
            </h2>
            <form onSubmit={handleCreateOrg} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Unit Type</label>
                <select
                  value={newOrg.unit_type}
                  onChange={(e) => setNewOrg({ ...newOrg, unit_type: e.target.value })}
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                >
                  <option value="AREA">AREA (Operational Coal Area)</option>
                  <option value="MINE">MINE (Mine / Project)</option>
                  <option value="SUBSIDIARY">SUBSIDIARY</option>
                </select>
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Parent Unit</label>
                <select
                  value={newOrg.parent_id}
                  onChange={(e) => setNewOrg({ ...newOrg, parent_id: e.target.value })}
                  className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
                  required
                >
                  <option value="">Select Parent Organizational Node...</option>
                  {orgUnits.map((u) => (
                    <option key={u.id} value={u.id}>
                      [{u.unit_type}] {u.name} ({u.code})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Unit Code (Uppercase)</label>
                <input
                  type="text"
                  value={newOrg.code}
                  onChange={(e) => setNewOrg({ ...newOrg, code: e.target.value.toUpperCase() })}
                  placeholder="e.g. AREA-KORBA"
                  className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Unit Name</label>
                <input
                  type="text"
                  value={newOrg.name}
                  onChange={(e) => setNewOrg({ ...newOrg, name: e.target.value })}
                  placeholder="e.g. Korba Coalfields Area"
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold text-stone-700 block mb-1">State</label>
                  <input
                    type="text"
                    value={newOrg.state}
                    onChange={(e) => setNewOrg({ ...newOrg, state: e.target.value })}
                    className="w-full border border-stone-300 rounded p-2 text-xs"
                  />
                </div>
                <div>
                  <label className="font-semibold text-stone-700 block mb-1">District</label>
                  <input
                    type="text"
                    value={newOrg.district}
                    onChange={(e) => setNewOrg({ ...newOrg, district: e.target.value })}
                    className="w-full border border-stone-300 rounded p-2 text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Headquarters</label>
                <input
                  type="text"
                  value={newOrg.headquarters}
                  onChange={(e) => setNewOrg({ ...newOrg, headquarters: e.target.value })}
                  placeholder="e.g. Bilaspur / Korba"
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 bg-red-700 hover:bg-red-800 text-white rounded font-bold transition shadow-xs mt-2"
              >
                Create Organizational Node
              </button>
            </form>
          </div>

          {/* Units Table (8 cols) */}
          <div className="lg:col-span-8 bg-white border border-stone-200 rounded p-5 shadow-xs overflow-x-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2 mb-4">
              Registered Organizational Nodes ({orgUnits.length})
            </h2>
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-stone-50 border-b border-stone-200 text-stone-600 font-semibold">
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Code</th>
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">Parent ID</th>
                  <th className="py-2.5 px-3">Location</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {orgUnits.map((u) => (
                  <tr key={u.id} className="hover:bg-stone-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold">
                      <span className="px-1.5 py-0.5 rounded bg-stone-100 border text-[10px]">
                        {u.unit_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-stone-900 font-semibold">{u.code}</td>
                    <td className="py-2.5 px-3 font-medium text-stone-800">{u.name}</td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-stone-500">
                      {u.parent_id || "Root"}
                    </td>
                    <td className="py-2.5 px-3 text-stone-600">
                      {u.district ? `${u.district}, ${u.state}` : u.state || "—"}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {u.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: OPERATIONAL UNITS */}
      {activeTab === "operational" && (
        <div className="bg-white border border-stone-200 rounded p-6 shadow-xs space-y-4 max-w-2xl">
          <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2">
            Register Operational Unit with Mine-Type Enforcement
          </h2>
          <p className="text-xs text-stone-500">
            Enforces strict operational model compatibility: Underground mines accept Shafts, Ventilation Districts, Panels, Sections, and Working Faces; Opencast mines accept Pits, Benches, Haul Roads, Dumps, and HEMM Parks.
          </p>

          <form onSubmit={handleCreateOpUnit} className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-stone-700 block mb-1">Target Mine</label>
              <select
                value={newOpUnit.mine_id}
                onChange={(e) => setNewOpUnit({ ...newOpUnit, mine_id: e.target.value })}
                className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
              >
                <option value="MINE-BCCL-JHARIA-01">MINE-BCCL-JHARIA-01 (Underground Bord & Pillar)</option>
                <option value="MINE-ECL-RANIGANJ-01">MINE-ECL-RANIGANJ-01 (Underground Mechanised)</option>
                <option value="MINE-MCL-TALCHER-01">MINE-MCL-TALCHER-01 (Opencast)</option>
                <option value="MINE-SECL-GEVRA-01">MINE-SECL-GEVRA-01 (Opencast Mega Pit)</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-stone-700 block mb-1">Operational Unit Type</label>
              <select
                value={newOpUnit.unit_type}
                onChange={(e) => setNewOpUnit({ ...newOpUnit, unit_type: e.target.value })}
                className="w-full border border-stone-300 rounded p-2 text-xs"
              >
                <optgroup label="Underground Mining Units">
                  <option value="SHAFT_INCLINE">SHAFT / INCLINE</option>
                  <option value="VENTILATION_DISTRICT">VENTILATION DISTRICT</option>
                  <option value="PANEL">PANEL</option>
                  <option value="SECTION">SECTION</option>
                  <option value="WORKING_FACE">WORKING FACE</option>
                </optgroup>
                <optgroup label="Opencast Mining Units">
                  <option value="PIT">PIT</option>
                  <option value="BENCH">BENCH</option>
                  <option value="HAUL_ROAD">HAUL ROAD</option>
                  <option value="DUMP_STOCK">DUMP / STOCK</option>
                  <option value="HEMM_PARK">HEMM PARK</option>
                </optgroup>
              </select>
            </div>

            <div>
              <label className="font-semibold text-stone-700 block mb-1">Unit Code</label>
              <input
                type="text"
                value={newOpUnit.code}
                onChange={(e) => setNewOpUnit({ ...newOpUnit, code: e.target.value.toUpperCase() })}
                placeholder="e.g. WF-15 / PIT-02"
                className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-stone-700 block mb-1">Unit Name</label>
              <input
                type="text"
                value={newOpUnit.name}
                onChange={(e) => setNewOpUnit({ ...newOpUnit, name: e.target.value })}
                placeholder="e.g. Working Face 15 Depillaring"
                className="w-full border border-stone-300 rounded p-2 text-xs"
                required
              />
            </div>

            <button
              type="submit"
              className="py-2.5 px-5 bg-red-700 hover:bg-red-800 text-white rounded font-bold transition shadow-xs"
            >
              Register Operational Unit
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: CONTRACTORS */}
      {activeTab === "contractors" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 bg-white border border-stone-200 rounded p-5 shadow-xs h-fit">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2 mb-4">
              Register Contractor / MDO Master
            </h2>
            <form onSubmit={handleCreateContractor} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Contractor Type</label>
                <select
                  value={newContractor.contractor_type}
                  onChange={(e) => setNewContractor({ ...newContractor, contractor_type: e.target.value })}
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                >
                  <option value="DEPARTMENTAL">DEPARTMENTAL (In-House CIL)</option>
                  <option value="WORK_ORDER">WORK ORDER (Commercial Contractor)</option>
                  <option value="MDO">MDO (Mine Developer and Operator)</option>
                  <option value="SERVICE">SERVICE (Specialized Testing/Inspection)</option>
                </select>
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Display Name</label>
                <input
                  type="text"
                  value={newContractor.display_name}
                  onChange={(e) => setNewContractor({ ...newContractor, display_name: e.target.value })}
                  placeholder="e.g. L&T Mining"
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Legal Registered Name</label>
                <input
                  type="text"
                  value={newContractor.legal_name}
                  onChange={(e) => setNewContractor({ ...newContractor, legal_name: e.target.value })}
                  placeholder="e.g. Larsen & Toubro Mining Ltd"
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">CIN / Registration Reference</label>
                <input
                  type="text"
                  value={newContractor.registration_reference}
                  onChange={(e) => setNewContractor({ ...newContractor, registration_reference: e.target.value })}
                  placeholder="e.g. CIN-U10100MH2000PLC192831"
                  className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 bg-red-700 hover:bg-red-800 text-white rounded font-bold transition shadow-xs mt-2"
              >
                Register Contractor
              </button>
            </form>
          </div>

          <div className="lg:col-span-8 bg-white border border-stone-200 rounded p-5 shadow-xs overflow-x-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2 mb-4">
              Contractor Master Registry ({contractors.length})
            </h2>
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-stone-50 border-b border-stone-200 text-stone-600 font-semibold">
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Display Name</th>
                  <th className="py-2.5 px-3">Legal Registered Entity</th>
                  <th className="py-2.5 px-3">Registration Ref</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {contractors.map((c) => (
                  <tr key={c.id} className="hover:bg-stone-50/50">
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-900 font-mono text-[10px] font-semibold">
                        {c.contractor_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-stone-900">{c.display_name}</td>
                    <td className="py-2.5 px-3 text-stone-600">{c.legal_name}</td>
                    <td className="py-2.5 px-3 font-mono text-stone-500 text-[11px]">{c.registration_reference || "—"}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: CONTRACTS */}
      {activeTab === "contracts" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 bg-white border border-stone-200 rounded p-5 shadow-xs h-fit">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2 mb-4">
              Bind Contract to Mine
            </h2>
            <p className="text-[11px] text-stone-500 mb-3">
              Derives Area and Subsidiary automatically from canonical Mine lineage.
            </p>
            <form onSubmit={handleCreateContract} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Contractor</label>
                <select
                  value={newContract.contractor_id}
                  onChange={(e) => setNewContract({ ...newContract, contractor_id: e.target.value })}
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                  required
                >
                  <option value="">Select Contractor / Department...</option>
                  {contractors.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.display_name} ({c.contractor_type})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Mine</label>
                <select
                  value={newContract.mine_id}
                  onChange={(e) => setNewContract({ ...newContract, mine_id: e.target.value })}
                  className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
                >
                  <option value="MINE-BCCL-JHARIA-01">MINE-BCCL-JHARIA-01 (BCCL Jharia)</option>
                  <option value="MINE-ECL-RANIGANJ-01">MINE-ECL-RANIGANJ-01 (ECL Raniganj)</option>
                  <option value="MINE-MCL-TALCHER-01">MINE-MCL-TALCHER-01 (MCL Talcher)</option>
                  <option value="MINE-SECL-GEVRA-01">MINE-SECL-GEVRA-01 (SECL Gevra)</option>
                </select>
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Contract Number</label>
                <input
                  type="text"
                  value={newContract.contract_number}
                  onChange={(e) => setNewContract({ ...newContract, contract_number: e.target.value.toUpperCase() })}
                  placeholder="e.g. WO-2024-CIL-09"
                  className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Operational Scope</label>
                <input
                  type="text"
                  value={newContract.scope}
                  onChange={(e) => setNewContract({ ...newContract, scope: e.target.value })}
                  placeholder="e.g. Overburden Haulage & Pit Operations"
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 bg-red-700 hover:bg-red-800 text-white rounded font-bold transition shadow-xs mt-2"
              >
                Register Contract
              </button>
            </form>
          </div>

          <div className="lg:col-span-8 bg-white border border-stone-200 rounded p-5 shadow-xs overflow-x-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2 mb-4">
              Active Contracts & Work Orders ({contracts.length})
            </h2>
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-stone-50 border-b border-stone-200 text-stone-600 font-semibold">
                  <th className="py-2.5 px-3">Contract No.</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Mine Location</th>
                  <th className="py-2.5 px-3">Scope</th>
                  <th className="py-2.5 px-3">Limit</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {contracts.map((c) => (
                  <tr key={c.id} className="hover:bg-stone-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-stone-900">{c.contract_number}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-900 font-mono text-[10px] font-semibold">
                        {c.contract_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-medium text-stone-800">{c.mine_name || c.mine_id}</td>
                    <td className="py-2.5 px-3 text-stone-600 truncate max-w-xs">{c.scope || "—"}</td>
                    <td className="py-2.5 px-3 font-mono text-stone-600">{c.workforce_limit || "Uncapped"}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: WORKERS */}
      {activeTab === "workers" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 bg-white border border-stone-200 rounded p-5 shadow-xs h-fit">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2 mb-4">
              Register Worker in Muster
            </h2>
            <p className="text-[11px] text-stone-500 mb-3">
              Workers are independent from application users. All demo records are marked [DEMO / SIMULATED].
            </p>
            <form onSubmit={handleCreateWorker} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Worker Code (Unique)</label>
                <input
                  type="text"
                  value={newWorker.worker_code}
                  onChange={(e) => setNewWorker({ ...newWorker, worker_code: e.target.value.toUpperCase() })}
                  placeholder="e.g. CIL-EMP-9821"
                  className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Full Name</label>
                <input
                  type="text"
                  value={newWorker.name}
                  onChange={(e) => setNewWorker({ ...newWorker, name: e.target.value })}
                  placeholder="e.g. Anil Kumar Mahato"
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Worker Classification</label>
                <select
                  value={newWorker.worker_type}
                  onChange={(e) => setNewWorker({ ...newWorker, worker_type: e.target.value })}
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                >
                  <option value="DEPARTMENTAL">DEPARTMENTAL (Company Muster)</option>
                  <option value="CONTRACTOR">CONTRACTOR (Work Order Muster)</option>
                  <option value="MDO">MDO (Mine Developer Staff)</option>
                </select>
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Contract Binding</label>
                <select
                  value={newWorker.contract_id}
                  onChange={(e) => setNewWorker({ ...newWorker, contract_id: e.target.value })}
                  className="w-full border border-stone-300 rounded p-2 text-xs"
                >
                  <option value="">None / Departmental Direct</option>
                  {contracts.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.contract_number} ({c.mine_id})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold text-stone-700 block mb-1">Mine</label>
                <select
                  value={newWorker.mine_id}
                  onChange={(e) => setNewWorker({ ...newWorker, mine_id: e.target.value })}
                  className="w-full border border-stone-300 rounded p-2 text-xs font-mono"
                >
                  <option value="MINE-BCCL-JHARIA-01">MINE-BCCL-JHARIA-01 (Jharia UG)</option>
                  <option value="MINE-ECL-RANIGANJ-01">MINE-ECL-RANIGANJ-01 (Raniganj UG)</option>
                  <option value="MINE-MCL-TALCHER-01">MINE-MCL-TALCHER-01 (Talcher OC)</option>
                  <option value="MINE-SECL-GEVRA-01">MINE-SECL-GEVRA-01 (Gevra OC)</option>
                </select>
              </div>
              <button
                type="submit"
                className="w-full py-2.5 bg-red-700 hover:bg-red-800 text-white rounded font-bold transition shadow-xs mt-2"
              >
                Register Worker
              </button>
            </form>
          </div>

          <div className="lg:col-span-8 bg-white border border-stone-200 rounded p-5 shadow-xs overflow-x-auto">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900 border-b border-stone-200 pb-2 mb-4">
              Registered Muster Roll ({workers.length})
            </h2>
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-stone-50 border-b border-stone-200 text-stone-600 font-semibold">
                  <th className="py-2.5 px-3">Code</th>
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Mine</th>
                  <th className="py-2.5 px-3">Training</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {workers.map((w) => (
                  <tr key={w.id} className="hover:bg-stone-50/50">
                    <td className="py-2.5 px-3 font-mono font-bold text-stone-900">{w.worker_code}</td>
                    <td className="py-2.5 px-3 font-medium text-stone-900">{w.name}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded bg-stone-100 text-stone-800 font-mono text-[10px] font-semibold">
                        {w.worker_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-stone-700 font-mono text-[11px]">{w.mine_name || w.mine_id}</td>
                    <td className="py-2.5 px-3 text-stone-600 text-[11px]">{w.training_status}</td>
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
        </div>
      )}

      {/* TAB 6: AUDIT EVENTS */}
      {activeTab === "audit" && (
        <div className="bg-white border border-stone-200 rounded p-5 shadow-xs overflow-x-auto space-y-4">
          <div className="flex items-center justify-between border-b border-stone-200 pb-2">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-stone-900">
                Immutable Governance Audit Ledger ({auditEvents.length})
              </h2>
              <p className="text-[11px] text-stone-500">
                Tracks all administrative modifications to the Master Organizational & Operational Hierarchy.
              </p>
            </div>
            <button
              onClick={loadTabContent}
              className="text-xs text-stone-600 hover:text-red-700 underline font-medium"
            >
              Refresh Audit Log
            </button>
          </div>

          {auditEvents.length === 0 ? (
            <div className="p-8 text-center text-stone-400 text-xs">
              No audit log entries recorded.
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-stone-50 border-b border-stone-200 text-stone-600 font-semibold">
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3">Entity Type</th>
                  <th className="py-2.5 px-3">Entity ID</th>
                  <th className="py-2.5 px-3">Actor</th>
                  <th className="py-2.5 px-3">Reason / Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 font-mono text-[11px]">
                {auditEvents.map((evt) => (
                  <tr key={evt.event_id} className="hover:bg-stone-50/50">
                    <td className="py-2.5 px-3 text-stone-500">
                      {new Date(evt.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-red-800">{evt.action}</td>
                    <td className="py-2.5 px-3 text-stone-700">{evt.entity_type}</td>
                    <td className="py-2.5 px-3 text-stone-900 font-semibold">{evt.entity_id}</td>
                    <td className="py-2.5 px-3 text-stone-600">{evt.actor_id}</td>
                    <td className="py-2.5 px-3 text-stone-500 font-sans text-xs">
                      {evt.reason || "Administrative update"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};

export default MasterDataAdmin;
