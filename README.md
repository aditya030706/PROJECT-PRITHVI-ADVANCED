# PROJECT PRITHVI — Mine Compliance Intelligence Platform

> **Smart India Hackathon 2026** | **Problem Statement: SIH26024** | **Ministry of Coal**  
> AI-Enabled Regulatory Compliance, Dynamic Inspection Governance & Cryptographic Evidence Verification for the Indian Coal Mining Sector.

---

## 📌 Executive Overview

**PROJECT PRITHVI** is a mission-critical compliance intelligence and regulatory oversight system engineered specifically for the Ministry of Coal and Directorate General of Mines Safety (DGMS). It bridges field inspection reporting with automated statutory compliance verification under the **Coal Mines Regulations (CMR) 2017** and **Mines Act 1952**.

PRITHVI eliminates "compliance theatre" by cross-verifying physical inspection documents, sensor telemetry, and historical baselines using semantic AI and cryptographic proof systems—ensuring regulatory violations and anomalous reports are immediately flagged for human audit.

---

## 🏛️ Multi-Tier Governance Architecture

PRITHVI enforces strict, role-specific operational contexts across five mining governance tiers:

1. **Field Inspector (`FIELD_INSPECTOR`)**: Field inspection plan execution, dynamic check-item registers, and physical PDF evidence registration with SHA-256 integrity verification.
2. **Mine Supervisor (`MINE_SUPERVISOR`)**: Shift-level safety logs, daily statutory compliance tracking, and frontline monitoring.
3. **Mine Manager (`MINE_MANAGER`)**: Comprehensive mine portfolio oversight, risk posture heatmaps, and corrective action approvals.
4. **DGMS Regulatory Officer (`DGMS_OFFICER`)**: Independent statutory oversight, AI-flagged anomaly queue, cryptographic document verification, and binding reinspection orders.
5. **Corporate Management (`CORPORATE_MANAGEMENT`)**: Multi-subsidiary governance across BCCL, ECL, and MCL with enterprise safety compliance analytics.

---

## ⚡ Core Technical Capabilities

### 1. Dynamic Regulatory Rule Engine
- Maps statutory obligations from **CMR 2017** (e.g., Reg 129, Reg 130, Reg 153) and **Mines Act 1952** (Sections 22, 22A, 23).
- Computes real-time applicability based on mine parameters: underground vs. opencast, gassy degree (Degree I/II/III), mechanisation, and blasting operations.

### 2. Multi-Modal Document & Semantic Verification Pipeline
- **Dual-Model Similarity Engine**: Combines **Sentence-Transformers (`all-MiniLM-L6-v2`)** dense semantic embeddings with **TF-IDF cosine similarity** to detect duplicate or plagiarized inspection reports.
- **Physical Evidence Integrity**: Extracts text and numeric readings from uploaded PDF evidence and computes live SHA-256 cryptographic fingerprints.
- **Source Anomaly Detection**: Cross-references reported physical readings against historical mine baselines to detect impossible or fabricated readings.

### 3. Human-in-the-Loop Regulatory Audit (DGMS)
- AI findings serve as advisory integrity signals, never automated verdicts.
- Critical verification cases are routed to the DGMS Regulatory Audit Queue (`/dgms/audit/:inspectionId`) where officers review anomaly signals and record binding decisions (Accept, Reject, Request Reinspection).

### 4. Resilient Session Hydration & Role Routing
- Synchronous role restoration with zero-flash hydration.
- Intelligent `RoleGuard` routing redirects unauthorized requests cleanly to each role's dedicated home route without dead-end error screens.

---

## 📁 Repository Structure

```
PROJECT-PRITHVI-ADVANCED/
├── app/                        # FastAPI Backend Architecture
│   ├── main.py                 # API Endpoints & Request Routing
│   ├── database.py             # SQLite Schema, Queries & Migration Data
│   ├── models.py               # Pydantic Schemas & Data Contracts
│   ├── similarity.py           # Sentence-Transformer & TF-IDF Semantic Engine
│   ├── pdf_processor.py        # PDF Parsing & Numeric Extraction
│   ├── verification_engine.py  # Regulatory Verification Pipeline
│   └── data/                   # Demonstration Mines, Database & Seed Documents
├── frontend/                   # React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── api/                # Typed REST API Clients
│   │   ├── auth/               # RoleGuard, AuthContext & Permissions Matrix
│   │   ├── components/         # Shared Regulatory & Industrial UI Components
│   │   ├── pages/              # Domain Pages (Dashboard, Mines, Inspections, DGMS)
│   │   ├── App.tsx             # Root Application & Route Topology
│   │   └── App.css             # Industrial Design System & Styling
│   ├── index.html              # HTML5 Shell
│   └── package.json            # Frontend Dependencies & Scripts
├── tests/                      # Automated Verification & Backend Tests
├── requirements.txt            # Python Dependencies
├── .gitignore                  # Git Ignore Rules
└── README.md                   # Platform Documentation
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/aditya030706/PROJECT-PRITHVI-ADVANCED.git
cd PROJECT-PRITHVI-ADVANCED

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI backend server
python -m uvicorn app.main:app --reload --port 8000
```
Backend API will be accessible at: `http://localhost:8000`  
Swagger API Docs available at: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend application will be accessible at: `http://localhost:5173`

---

## 🛠️ Demonstration Assets

The platform includes seed assets representing three core mining profiles:
- **Jharia Underground Mine** (`MINE-BCCL-JHARIA-01`) — BCCL, Underground Coal, Degree II Gassy.
- **Raniganj Underground Mine** (`MINE-ECL-RANIGANJ-01`) — ECL, Underground Coal, Degree I Gassy.
- **Talcher Opencast Mine** (`MINE-MCL-TALCHER-01`) — MCL, Opencast Coal, Mechanised / Heavy Earth Moving Machinery.

---

## ⚖️ Statutory & Legal Framework

- **Coal Mines Regulations (CMR), 2017**
- **Mines Act, 1952**
- **DGMS Technical Circulars & Safety Guidelines**

---

## 👥 Contributors

- **Team PRITHVI** — Smart India Hackathon 2026
