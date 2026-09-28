"""
PRITHVI — Evidence Integrity Service (Phase 2 Task 7)
======================================================

Coordinates IPFS storage, blockchain anchoring, and integrity
verification for all evidence records.

This service is the single point of truth for:
  1. Building evidence content packages
  2. Computing content hashes (SHA-256)
  3. Storing packages in IPFS (or dev adapter)
  4. Anchoring hashes to blockchain (or demo adapter)
  5. Verifying integrity on demand
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from . import database as db
from .ipfs_service import (
    build_evidence_package,
    calculate_content_hash,
    compute_ipfs_cid,
    store_evidence_package,
    get_ipfs_status,
)
from .blockchain_service import (
    anchor_hash,
    verify_hash,
    get_blockchain_status,
)


# ============================================================
# ANCHOR EVIDENCE
# ============================================================

def anchor_evidence(
    evidence_id: str,
    actor_id: str = "SYSTEM",
    reference_type: str = "INSPECTION_EVIDENCE",
) -> dict:
    """
    Compute SHA-256, store in IPFS (or dev adapter), anchor to blockchain
    (or demo adapter), and persist the integrity record.

    Returns the integrity record dict.
    """
    # Fetch evidence from DB
    conn = db._connect()
    ev = conn.execute(
        "SELECT * FROM evidence WHERE evidence_id = ?",
        (evidence_id,),
    ).fetchone()
    conn.close()

    if ev is None:
        raise ValueError(f"Evidence {evidence_id!r} not found.")

    ev_dict = dict(ev)

    # Build canonical evidence package
    package = build_evidence_package(
        evidence_id=evidence_id,
        evidence_type=ev_dict.get("evidence_type", "unknown"),
        inspection_id=ev_dict.get("inspection_id"),
        filename=ev_dict.get("filename"),
        captured_at=str(ev_dict.get("captured_at") or ""),
        storage_reference=ev_dict.get("storage_reference"),
        raw_content=None,  # Never include raw binary in the package
        extra_metadata={
            "sha256_of_file": ev_dict.get("sha256"),
            "perceptual_hash": ev_dict.get("perceptual_hash"),
            "latitude": ev_dict.get("latitude"),
            "longitude": ev_dict.get("longitude"),
            "metadata_verified": ev_dict.get("metadata_verified"),
        },
    )

    # IPFS storage
    ipfs_result = store_evidence_package(evidence_id, package)
    content_hash = ipfs_result["sha256"]
    ipfs_cid = ipfs_result["cid"]
    ipfs_status = ipfs_result["status"]

    # Blockchain anchor
    now_iso = datetime.now(timezone.utc).isoformat()
    anchor_result = anchor_hash(
        evidence_id=evidence_id,
        sha256_hex=content_hash,
        timestamp=now_iso,
        reference_type=reference_type,
        ipfs_cid=ipfs_cid,
    )

    integrity_id = f"INT-{uuid4().hex[:12].upper()}"

    record = {
        "integrity_id": integrity_id,
        "evidence_id": evidence_id,
        "content_hash": content_hash,
        "hash_algorithm": "SHA-256",
        "ipfs_cid": ipfs_cid,
        "ipfs_status": ipfs_status,
        "blockchain_network": anchor_result.get("network", "DEMO_AUDIT_MODE"),
        "transaction_ref": anchor_result.get("tx_ref"),
        "block_ref": anchor_result.get("block_ref"),
        "anchored_at": anchor_result.get("anchored_at", now_iso),
        "anchor_mode": anchor_result.get("mode", "DEMO_AUDIT_MODE"),
        "status": "ANCHORED",
        "verified_at": None,
        "verification_result": None,
        "created_at": now_iso,
    }

    db.save_evidence_integrity(record)

    # Also update the evidence table with the IPFS CID and anchor status
    conn = db._connect()
    conn.execute(
        "UPDATE evidence SET ipfs_cid = ?, anchor_status = ? WHERE evidence_id = ?",
        (ipfs_cid, "ANCHORED", evidence_id),
    )
    conn.commit()
    conn.close()

    return _enrich_integrity_record(record)


# ============================================================
# VERIFY EVIDENCE INTEGRITY
# ============================================================

def verify_evidence_integrity(evidence_id: str) -> dict:
    """
    Recompute the content hash and compare against the stored anchor.
    Returns a verification result dict.
    """
    record = db.get_evidence_integrity_by_evidence_id(evidence_id)

    if record is None:
        return {
            "evidence_id": evidence_id,
            "matches": False,
            "verification_status": "AUDIT_PROOF_PENDING",
            "mode": "DEMO_AUDIT_MODE",
            "details": (
                "No integrity record found for this evidence. "
                "Anchor this evidence first via POST /api/evidence/{id}/anchor."
            ),
            "integrity": None,
        }

    # Re-fetch evidence and rebuild package to recompute hash
    conn = db._connect()
    ev = conn.execute(
        "SELECT * FROM evidence WHERE evidence_id = ?",
        (evidence_id,),
    ).fetchone()
    conn.close()

    if ev is None:
        return {
            "evidence_id": evidence_id,
            "matches": False,
            "verification_status": "INTEGRITY_CHECK_FAILED",
            "mode": "DEMO_AUDIT_MODE",
            "details": "Evidence record not found in database.",
            "integrity": _enrich_integrity_record(record),
        }

    ev_dict = dict(ev)
    package = build_evidence_package(
        evidence_id=evidence_id,
        evidence_type=ev_dict.get("evidence_type", "unknown"),
        inspection_id=ev_dict.get("inspection_id"),
        filename=ev_dict.get("filename"),
        captured_at=str(ev_dict.get("captured_at") or ""),
        storage_reference=ev_dict.get("storage_reference"),
        raw_content=None,
        extra_metadata={
            "sha256_of_file": ev_dict.get("sha256"),
            "perceptual_hash": ev_dict.get("perceptual_hash"),
            "latitude": ev_dict.get("latitude"),
            "longitude": ev_dict.get("longitude"),
            "metadata_verified": ev_dict.get("metadata_verified"),
        },
    )
    recomputed_hash = calculate_content_hash(package)

    # Compare hashes
    stored_hash = record.get("content_hash", "")
    hashes_match = recomputed_hash == stored_hash

    # Verify blockchain anchor
    blockchain_verify = verify_hash(
        sha256_hex=stored_hash,
        tx_ref=record.get("transaction_ref", ""),
        evidence_id=evidence_id,
    )

    # Combine results
    overall_matches = hashes_match and blockchain_verify.get("matches", False)
    verification_result = "INTEGRITY_VERIFIED" if overall_matches else "INTEGRITY_CHECK_FAILED"

    if not hashes_match:
        details = (
            f"INTEGRITY CHECK FAILED — Content hash mismatch. "
            f"Expected: {stored_hash[:16]}..., Got: {recomputed_hash[:16]}..."
        )
    else:
        details = blockchain_verify.get("details", "Hash verified.")

    now_iso = datetime.now(timezone.utc).isoformat()
    db.update_evidence_integrity_verification(
        evidence_id=evidence_id,
        verification_result=verification_result,
        verified_at=now_iso,
        status="VERIFIED" if overall_matches else "FAILED",
    )

    # Re-fetch updated record
    updated = db.get_evidence_integrity_by_evidence_id(evidence_id)

    return {
        "evidence_id": evidence_id,
        "matches": overall_matches,
        "verification_status": verification_result,
        "mode": blockchain_verify.get("mode", "DEMO_AUDIT_MODE"),
        "details": details,
        "integrity": _enrich_integrity_record(updated) if updated else None,
    }


# ============================================================
# GET EVIDENCE INTEGRITY
# ============================================================

def get_evidence_integrity(evidence_id: str) -> Optional[dict]:
    """Return the enriched integrity record for an evidence item."""
    record = db.get_evidence_integrity_by_evidence_id(evidence_id)
    if record is None:
        return None
    return _enrich_integrity_record(record)


# ============================================================
# INSPECTION AUDIT INTEGRITY
# ============================================================

def get_inspection_audit_integrity(inspection_id: str) -> dict:
    """
    Return full audit integrity summary for all evidence in an inspection.
    Auto-anchors any unanchored evidence before returning.
    """
    conn = db._connect()
    evidence_rows = conn.execute(
        "SELECT * FROM evidence WHERE inspection_id = ?",
        (inspection_id,),
    ).fetchall()
    inspection_row = conn.execute(
        "SELECT mine_id FROM inspections WHERE inspection_id = ?",
        (inspection_id,),
    ).fetchone()
    conn.close()

    mine_id = inspection_row["mine_id"] if inspection_row else None
    evidence_list = [dict(r) for r in evidence_rows]

    results = []
    anchored_count = 0
    verified_count = 0
    pending_count = 0

    for ev in evidence_list:
        eid = ev["evidence_id"]
        record = db.get_evidence_integrity_by_evidence_id(eid)

        if record is None:
            # Auto-anchor
            try:
                record = anchor_evidence(eid, actor_id="SYSTEM", reference_type="INSPECTION_EVIDENCE")
            except Exception:
                pending_count += 1
                results.append({
                    "evidence_id": eid,
                    "evidence_type": ev.get("evidence_type", "unknown"),
                    "filename": ev.get("filename"),
                    "captured_at": str(ev.get("captured_at") or ""),
                    "sha256": ev.get("sha256"),
                    "integrity": None,
                })
                continue

        enriched = _enrich_integrity_record(record) if isinstance(record, dict) else record
        status = enriched.get("status", "PENDING") if isinstance(enriched, dict) else "PENDING"

        if status == "ANCHORED" or status == "VERIFIED":
            anchored_count += 1
        if status == "VERIFIED":
            verified_count += 1
        if status == "PENDING" or status == "FAILED":
            pending_count += 1

        results.append({
            "evidence_id": eid,
            "evidence_type": ev.get("evidence_type", "unknown"),
            "filename": ev.get("filename"),
            "captured_at": str(ev.get("captured_at") or ""),
            "sha256": ev.get("sha256"),
            "integrity": enriched,
        })

    total = len(evidence_list)
    if total == 0:
        coverage = "NONE"
    elif anchored_count == total:
        coverage = "FULL"
    elif anchored_count > 0:
        coverage = "PARTIAL"
    else:
        coverage = "NONE"

    return {
        "inspection_id": inspection_id,
        "mine_id": mine_id,
        "total_evidence": total,
        "anchored_count": anchored_count,
        "verified_count": verified_count,
        "pending_count": pending_count,
        "integrity_coverage": coverage,
        "evidence_integrity": results,
        "ipfs_service_status": get_ipfs_status(),
        "blockchain_service_status": get_blockchain_status(),
    }


# ============================================================
# CASE AUDIT INTEGRITY
# ============================================================

def get_case_audit_integrity(case_id: str) -> dict:
    """Return audit integrity summary for correction evidence linked to a case."""
    conn = db._connect()
    case_row = conn.execute(
        "SELECT mine_id FROM compliance_cases WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    cce_rows = conn.execute(
        "SELECT * FROM case_correction_evidence WHERE case_id = ?",
        (case_id,),
    ).fetchall()
    conn.close()

    mine_id = case_row["mine_id"] if case_row else None
    cce_list = [dict(r) for r in cce_rows]

    results = []
    anchored_count = 0
    verified_count = 0

    for cce in cce_list:
        eid = cce["evidence_id"]

        conn2 = db._connect()
        ev = conn2.execute(
            "SELECT * FROM evidence WHERE evidence_id = ?",
            (eid,),
        ).fetchone()
        conn2.close()

        ev_dict = dict(ev) if ev else {}
        record = db.get_evidence_integrity_by_evidence_id(eid)

        if record is None:
            try:
                record = anchor_evidence(eid, actor_id="SYSTEM", reference_type="CORRECTIVE_ACTION_EVIDENCE")
            except Exception:
                results.append({
                    "evidence_id": eid,
                    "evidence_type": ev_dict.get("evidence_type", "unknown"),
                    "filename": ev_dict.get("filename"),
                    "captured_at": str(ev_dict.get("captured_at") or ""),
                    "sha256": ev_dict.get("sha256"),
                    "integrity": None,
                })
                continue

        enriched = _enrich_integrity_record(record) if isinstance(record, dict) else record
        status = enriched.get("status", "PENDING") if isinstance(enriched, dict) else "PENDING"
        if status in ("ANCHORED", "VERIFIED"):
            anchored_count += 1
        if status == "VERIFIED":
            verified_count += 1

        results.append({
            "evidence_id": eid,
            "evidence_type": ev_dict.get("evidence_type", "unknown"),
            "filename": ev_dict.get("filename"),
            "captured_at": str(ev_dict.get("captured_at") or ""),
            "sha256": ev_dict.get("sha256"),
            "integrity": enriched,
        })

    total = len(cce_list)
    if total == 0:
        coverage = "NONE"
    elif anchored_count == total:
        coverage = "FULL"
    elif anchored_count > 0:
        coverage = "PARTIAL"
    else:
        coverage = "NONE"

    return {
        "case_id": case_id,
        "mine_id": mine_id,
        "total_correction_evidence": total,
        "anchored_count": anchored_count,
        "verified_count": verified_count,
        "integrity_coverage": coverage,
        "evidence_integrity": results,
        "ipfs_service_status": get_ipfs_status(),
        "blockchain_service_status": get_blockchain_status(),
    }


# ============================================================
# HELPER: ENRICH INTEGRITY RECORD
# ============================================================

def _enrich_integrity_record(record: dict) -> dict:
    """Add human-readable labels to an integrity record."""
    if not record:
        return record

    mode = record.get("anchor_mode", "DEMO_AUDIT_MODE")
    ipfs_status = record.get("ipfs_status", "PENDING")
    status = record.get("status", "PENDING")

    if mode == "DEMO_AUDIT_MODE":
        mode_label = "Demo Audit Mode — Locally anchored cryptographic proof"
    elif mode == "LIVE_BLOCKCHAIN":
        mode_label = f"Blockchain Anchored — {record.get('blockchain_network', 'Unknown')}"
    else:
        mode_label = mode

    if status == "VERIFIED":
        integrity_label = "✓ Integrity Verified"
    elif status == "ANCHORED":
        integrity_label = "⟳ Anchored — Pending Verification"
    elif status == "FAILED":
        integrity_label = "✗ Integrity Check Failed"
    else:
        integrity_label = "○ Pending Anchor"

    return {
        **record,
        "mode_label": mode_label,
        "integrity_label": integrity_label,
    }
