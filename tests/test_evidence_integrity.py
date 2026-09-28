"""
PRITHVI — Phase 2 Task 7: Evidence Integrity & Blockchain Audit Chain Tests
===========================================================================

Tests:
 1.  SHA-256 hash generation is deterministic
 2.  Same content → same hash
 3.  Modified content → different hash
 4.  Evidence package is canonical (deterministic)
 5.  IPFS CID is deterministic from hash
 6.  store_evidence_package returns honest IPFS_NOT_CONFIGURED status in dev
 7.  anchor_hash returns DEMO_AUDIT_MODE in dev
 8.  Anchoring persists an integrity record in DB
 9.  verify_evidence_integrity returns INTEGRITY_VERIFIED for unmodified evidence
10.  verify_evidence_integrity returns AUDIT_PROOF_PENDING when not yet anchored
11.  Private blockchain credentials never appear in anchor_hash output
12.  inspection_audit_integrity auto-anchors and returns coverage summary
"""

import os
import sys
import sqlite3
import tempfile
import pytest

# Ensure we can import the app package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ============================================================
# IMPORT SERVICES
# ============================================================

from app.ipfs_service import (
    calculate_content_hash,
    build_evidence_package,
    compute_ipfs_cid,
    store_evidence_package,
    get_ipfs_status,
)
from app.blockchain_service import (
    anchor_hash,
    verify_hash,
    get_blockchain_status,
    _generate_demo_anchor_ref,
)
from app.audit_proof import (
    generate_content_hash,
    generate_ipfs_cid,
    create_audit_proof_record,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Redirect DB to a fresh temporary file for each test."""
    from pathlib import Path
    db_path = tmp_path / "test_prithvi.db"
    monkeypatch.setenv("PRITHVI_DB_PATH", str(db_path))

    import app.database as db_module
    monkeypatch.setattr(db_module, "DB_PATH", Path(db_path))

    from app.database import init_db
    init_db()
    yield db_path


@pytest.fixture
def sample_evidence(temp_db):
    """Create a minimal evidence record in the test DB for integrity testing."""
    import app.database as db_module
    conn = sqlite3.connect(str(temp_db))
    conn.row_factory = sqlite3.Row

    # Insert prerequisite mine
    conn.execute("""
        INSERT OR IGNORE INTO mines (mine_id, name, mine_type, gassy_degree, mechanised,
                                      uses_hemm, has_winding_installation, blasting_operation, active)
        VALUES ('MINE-TST', 'Test Mine', 'underground_coal', 'degree_ii', 1, 0, 0, 0, 1)
    """)

    # Insert prerequisite inspection
    conn.execute("""
        INSERT OR IGNORE INTO inspections
            (inspection_id, mine_id, template_id, inspector_id, inspection_date, status)
        VALUES ('INS-TST-001', 'MINE-TST', 'TPL-001', 'INSP-01', '2026-09-01', 'submitted')
    """)

    # Insert evidence record
    conn.execute("""
        INSERT OR IGNORE INTO evidence
            (evidence_id, inspection_id, evidence_type, filename, sha256)
        VALUES ('EV-TST-001', 'INS-TST-001', 'photo', 'test_photo.jpg',
                'aaabbbbccccddddeeeeffffaaaabbbbccccddddeeeeffffaaaabbbbccccdddd01')
    """)
    conn.commit()
    conn.close()
    return "EV-TST-001"


# ============================================================
# 1. SHA-256 hash generation is deterministic
# ============================================================

def test_sha256_is_deterministic():
    content = {"key": "value", "number": 42}
    h1 = calculate_content_hash(content)
    h2 = calculate_content_hash(content)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex is 64 chars


# ============================================================
# 2. Same content → same hash
# ============================================================

def test_same_content_same_hash():
    content = "PRITHVI statutory inspection evidence package v1"
    h1 = calculate_content_hash(content)
    h2 = calculate_content_hash(content)
    assert h1 == h2


# ============================================================
# 3. Modified content → different hash
# ============================================================

def test_modified_content_different_hash():
    original = {"measurement": "CH4", "value": 1.25, "unit": "percent"}
    modified = {"measurement": "CH4", "value": 1.26, "unit": "percent"}  # value changed
    h1 = calculate_content_hash(original)
    h2 = calculate_content_hash(modified)
    assert h1 != h2


# ============================================================
# 4. Evidence package is canonical (deterministic)
# ============================================================

def test_evidence_package_is_canonical():
    p1 = build_evidence_package(
        evidence_id="EV-001",
        evidence_type="photo",
        inspection_id="INS-001",
        filename="photo.jpg",
    )
    p2 = build_evidence_package(
        evidence_id="EV-001",
        evidence_type="photo",
        inspection_id="INS-001",
        filename="photo.jpg",
    )
    h1 = calculate_content_hash(p1)
    h2 = calculate_content_hash(p2)
    assert h1 == h2, "Same evidence package should produce same hash"


# ============================================================
# 5. IPFS CID is deterministic from hash
# ============================================================

def test_ipfs_cid_is_deterministic():
    sha = "abc123" * 10 + "abcd"  # 64-char hex
    # Use the audit_proof module CID generator which is the canonical one
    cid1 = generate_ipfs_cid(sha)
    cid2 = generate_ipfs_cid(sha)
    assert cid1 == cid2
    assert cid1.startswith("b")


def test_ipfs_cid_differs_for_different_hashes():
    h1 = calculate_content_hash({"a": 1})
    h2 = calculate_content_hash({"a": 2})
    cid1 = compute_ipfs_cid(h1)
    cid2 = compute_ipfs_cid(h2)
    assert cid1 != cid2


# ============================================================
# 6. store_evidence_package returns IPFS_NOT_CONFIGURED in dev
# ============================================================

def test_store_evidence_returns_honest_status(monkeypatch):
    # Ensure IPFS_ENDPOINT is not set
    monkeypatch.delenv("IPFS_ENDPOINT", raising=False)

    package = build_evidence_package(
        evidence_id="EV-TEST",
        evidence_type="document",
        filename="report.pdf",
    )
    result = store_evidence_package("EV-TEST", package)

    assert result["status"] == "IPFS_NOT_CONFIGURED", (
        f"Expected IPFS_NOT_CONFIGURED in dev mode, got: {result['status']}"
    )
    assert result["mode"] == "DEV_LOCAL_HASH"
    assert "sha256" in result
    assert "cid" in result
    assert len(result["sha256"]) == 64


# ============================================================
# 7. anchor_hash returns DEMO_AUDIT_MODE in dev
# ============================================================

def test_anchor_hash_returns_demo_mode(monkeypatch):
    monkeypatch.delenv("BLOCKCHAIN_RPC_URL", raising=False)
    monkeypatch.delenv("BLOCKCHAIN_PRIVATE_KEY", raising=False)

    sha = calculate_content_hash({"test": "data"})
    result = anchor_hash(
        evidence_id="EV-DEMO",
        sha256_hex=sha,
        reference_type="INSPECTION_EVIDENCE",
    )

    assert result["mode"] == "DEMO_AUDIT_MODE", (
        f"Expected DEMO_AUDIT_MODE in dev, got: {result['mode']}"
    )
    assert result["tx_ref"].startswith("DEMO-PRITHVI"), (
        f"Demo tx_ref should start with DEMO-PRITHVI, got: {result['tx_ref']}"
    )
    assert result["ledger_standard"] == "PRITHVI-STATUTORY-AUDIT-V1"
    # IMPORTANT: no actual private key VALUE in output
    # (the field NAME "BLOCKCHAIN_PRIVATE_KEY" is OK in dev guidance messages)
    for sensitive_value in ("-----BEGIN", "0x", "12345678abcdef"):
        # These would indicate an actual key, not just a field name
        assert sensitive_value not in str(result)


# ============================================================
# 8. Anchoring persists an integrity record in DB
# ============================================================

def test_anchor_evidence_persists_record(sample_evidence, monkeypatch):
    import app.database as db_module

    monkeypatch.delenv("BLOCKCHAIN_RPC_URL", raising=False)
    monkeypatch.delenv("IPFS_ENDPOINT", raising=False)

    from app.integrity_service import anchor_evidence
    record = anchor_evidence(sample_evidence, actor_id="INSP-01")

    assert record is not None
    assert record["evidence_id"] == sample_evidence
    assert record["status"] == "ANCHORED"
    assert record["content_hash"] is not None
    assert len(record["content_hash"]) == 64
    assert record["ipfs_status"] == "IPFS_NOT_CONFIGURED"
    assert record["anchor_mode"] == "DEMO_AUDIT_MODE"
    assert record["transaction_ref"].startswith("DEMO-PRITHVI")

    # Verify persisted in DB
    persisted = db_module.get_evidence_integrity_by_evidence_id(sample_evidence)
    assert persisted is not None
    assert persisted["evidence_id"] == sample_evidence
    assert persisted["status"] == "ANCHORED"


# ============================================================
# 9. verify_evidence_integrity returns INTEGRITY_VERIFIED for unmodified
# ============================================================

def test_verify_integrity_verified_for_unmodified(sample_evidence, monkeypatch):
    monkeypatch.delenv("BLOCKCHAIN_RPC_URL", raising=False)
    monkeypatch.delenv("IPFS_ENDPOINT", raising=False)

    from app.integrity_service import anchor_evidence, verify_evidence_integrity

    # Anchor first
    anchor_evidence(sample_evidence, actor_id="INSP-01")

    # Verify — same evidence, same content → should pass
    result = verify_evidence_integrity(sample_evidence)

    assert result["matches"] is True, (
        f"Expected INTEGRITY_VERIFIED, got: {result['verification_status']}"
    )
    assert result["verification_status"] == "INTEGRITY_VERIFIED"


# ============================================================
# 10. verify returns AUDIT_PROOF_PENDING when not yet anchored
# ============================================================

def test_verify_returns_pending_when_not_anchored(temp_db):
    from app.integrity_service import verify_evidence_integrity

    result = verify_evidence_integrity("EV-NONEXISTENT-9999")
    assert result["verification_status"] == "AUDIT_PROOF_PENDING"
    assert result["matches"] is False


# ============================================================
# 11. Private credentials never appear in anchor output
# ============================================================

def test_no_private_credentials_in_anchor_output(monkeypatch):
    FAKE_SECRET = "SUPERSECRET_DO_NOT_EXPOSE_XYZ9876"
    monkeypatch.setenv("BLOCKCHAIN_PRIVATE_KEY", FAKE_SECRET)
    monkeypatch.setenv("BLOCKCHAIN_RPC_URL", "http://localhost:8545")

    sha = calculate_content_hash({"test": "credential_check"})

    # anchor_hash falls through to demo mode when live adapter is not implemented
    result = anchor_hash(evidence_id="EV-CRED-TEST", sha256_hex=sha)
    result_str = str(result)

    assert FAKE_SECRET not in result_str, (
        "CRITICAL: Private key VALUE found in API response! "
        f"The secret '{FAKE_SECRET}' must never appear in any output."
    )
    # The field name "blockchain_private_key" is OK to see in docs/messages,
    # but the actual secret value must never be exposed.


# ============================================================
# 12. inspection_audit_integrity auto-anchors and returns summary
# ============================================================

def test_inspection_audit_integrity_auto_anchors(sample_evidence, monkeypatch):
    monkeypatch.delenv("BLOCKCHAIN_RPC_URL", raising=False)
    monkeypatch.delenv("IPFS_ENDPOINT", raising=False)

    from app.integrity_service import get_inspection_audit_integrity

    result = get_inspection_audit_integrity("INS-TST-001")

    assert result["inspection_id"] == "INS-TST-001"
    assert result["total_evidence"] >= 1
    assert result["anchored_count"] >= 1
    assert result["integrity_coverage"] in ("FULL", "PARTIAL", "NONE")
    assert "ipfs_service_status" in result
    assert "blockchain_service_status" in result
    assert result["ipfs_service_status"]["mode"] == "DEV_LOCAL_HASH"
    assert result["blockchain_service_status"]["mode"] == "DEMO_AUDIT_MODE"

    # Check evidence items have integrity records
    for ev_item in result["evidence_integrity"]:
        if ev_item["integrity"] is not None:
            assert "content_hash" in ev_item["integrity"]
            assert "transaction_ref" in ev_item["integrity"]
