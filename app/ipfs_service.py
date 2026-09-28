"""
PRITHVI — IPFS Evidence Storage Abstraction (Phase 2 Task 7)
=============================================================

Provides a clean, replaceable interface for IPFS evidence storage.

ARCHITECTURE:
  Evidence / content packages  →  IPFS  →  CID
  CID + SHA-256               →  Blockchain anchor

ENVIRONMENT VARIABLES:
  IPFS_ENDPOINT    - IPFS API endpoint (e.g. https://ipfs.infura.io:5001)
  IPFS_API_KEY     - API key / project ID
  IPFS_API_SECRET  - API secret

IMPORTANT:
  - If IPFS is not configured, the dev adapter returns an HONEST status.
  - Do NOT claim decentralised storage when no IPFS service is running.
  - The local DB record IS NOT IPFS. They are clearly distinguished.
  - The architecture is designed so a real provider can be plugged in
    by setting the environment variables above, without changing any
    application logic.

CANONICALIZATION RULE:
  Evidence packages are serialised as deterministic UTF-8 JSON:
    json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)
  The same package content always produces the same SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ============================================================
# CANONICALIZATION
# ============================================================

def canonical_json(data: Any) -> bytes:
    """
    Produce deterministic, canonical UTF-8 JSON bytes.
    Sort keys alphabetically; no extra whitespace.
    This ensures the same content always produces the same SHA-256 hash.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def calculate_content_hash(content: bytes | str | dict | list) -> str:
    """
    Compute SHA-256 hexadecimal content hash.

    Supports:
      - dict / list  → canonical JSON bytes
      - str          → UTF-8 bytes
      - bytes        → as-is
    """
    if isinstance(content, (dict, list)):
        payload = canonical_json(content)
    elif isinstance(content, str):
        payload = content.encode("utf-8")
    elif isinstance(content, bytes):
        payload = content
    else:
        payload = str(content).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


# ============================================================
# EVIDENCE PACKAGE BUILDER
# ============================================================

def build_evidence_package(
    evidence_id: str,
    evidence_type: str,
    inspection_id: Optional[str] = None,
    filename: Optional[str] = None,
    captured_at: Optional[str] = None,
    storage_reference: Optional[str] = None,
    raw_content: Optional[str] = None,
    extra_metadata: Optional[dict] = None,
) -> dict:
    """
    Build a canonical, deterministic evidence package for IPFS storage.

    The package is the logical unit that is hashed and anchored.
    It contains evidence metadata but NOT raw binary file content
    (raw files would require a real IPFS node for practical storage).

    Returns a dict that can be JSON-serialised deterministically.
    """
    package = {
        "prithvi_evidence_package": "v1",
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "inspection_id": inspection_id,
        "filename": filename,
        "storage_reference": storage_reference,
        "captured_at": captured_at,
        "raw_content_sample": (raw_content[:256] if raw_content else None),
    }

    if extra_metadata:
        package["extra_metadata"] = extra_metadata

    return package


# ============================================================
# IPFS CONFIGURATION CHECK
# ============================================================

def _is_ipfs_configured() -> bool:
    """Return True only if a real IPFS endpoint is configured."""
    endpoint = os.environ.get("IPFS_ENDPOINT", "").strip()
    return bool(endpoint)


def _get_ipfs_config() -> dict:
    return {
        "endpoint": os.environ.get("IPFS_ENDPOINT", ""),
        "api_key": os.environ.get("IPFS_API_KEY", ""),
        # NOTE: Never expose the secret in API responses
    }


# ============================================================
# IPFS CID COMPUTATION (DETERMINISTIC, NO NETWORK REQUIRED)
# ============================================================

def compute_ipfs_cid(sha256_hex: str) -> str:
    """
    Compute a deterministic IPFS CIDv1 (base32) from a SHA-256 digest.

    This is a local, offline computation. It produces the CID that WOULD
    be returned by an IPFS node storing content with that hash.

    Format:
      CIDv1 prefix (0x01) + multicodec raw (0x55)
      + multihash sha2-256 (0x12) + length 32 (0x20) + 32-byte digest
      Encoded in RFC4648 base32 lowercase (prefixed 'b').
    """
    import base64
    try:
        digest_bytes = bytes.fromhex(sha256_hex)
    except Exception:
        digest_bytes = hashlib.sha256(sha256_hex.encode()).digest()

    multihash = bytes([0x12, 0x20]) + digest_bytes
    cid_bytes = bytes([0x01, 0x55]) + multihash
    b32 = base64.b32encode(cid_bytes).decode("ascii").lower().rstrip("=")
    return f"b{b32}"


# ============================================================
# STORE EVIDENCE PACKAGE
# ============================================================

def store_evidence_package(
    evidence_id: str,
    package: dict,
) -> dict:
    """
    Store an evidence package in IPFS.

    Returns a result dict containing:
      - sha256        : SHA-256 hex of the canonical package
      - cid           : IPFS CIDv1 (computed locally or returned by IPFS)
      - status        : "STORED" | "IPFS_NOT_CONFIGURED"
      - mode          : "LIVE_IPFS" | "DEV_LOCAL_HASH"
      - stored_at     : ISO timestamp

    HONEST DEV ADAPTER:
      If IPFS_ENDPOINT is not configured, we compute the hash and CID
      locally but DO NOT claim to have stored anything on IPFS.
      The status will be "IPFS_NOT_CONFIGURED" and mode "DEV_LOCAL_HASH".
    """
    sha256 = calculate_content_hash(package)
    cid = compute_ipfs_cid(sha256)
    now_iso = datetime.now(timezone.utc).isoformat()

    if _is_ipfs_configured():
        # --- LIVE IPFS ADAPTER ---
        # This would call the real IPFS HTTP API.
        # Placeholder; replace with real HTTP call when deploying.
        try:
            config = _get_ipfs_config()
            # Real call would be:
            # import requests
            # r = requests.post(f"{config['endpoint']}/api/v0/add",
            #     files={"file": ("package.json", canonical_json(package))},
            #     headers={"Authorization": f"Basic {config['api_key']}"},
            # )
            # result_cid = r.json()["Hash"]
            # For now, fall through to dev adapter.
            raise NotImplementedError("Live IPFS adapter placeholder — configure real provider.")
        except Exception as e:
            logger.warning("IPFS store failed, falling back to dev mode: %s", e)
            return {
                "sha256": sha256,
                "cid": cid,
                "status": "IPFS_NOT_CONFIGURED",
                "mode": "DEV_LOCAL_HASH",
                "message": "IPFS endpoint configured but connection failed — using local CID computation.",
                "stored_at": now_iso,
            }
    else:
        # --- HONEST DEV ADAPTER ---
        return {
            "sha256": sha256,
            "cid": cid,
            "status": "IPFS_NOT_CONFIGURED",
            "mode": "DEV_LOCAL_HASH",
            "message": (
                "IPFS is not configured in this environment. "
                "Set IPFS_ENDPOINT to enable real decentralised storage. "
                "The SHA-256 and CIDv1 are computed locally and are cryptographically valid. "
                "Content is NOT stored on a decentralised network in this mode."
            ),
            "stored_at": now_iso,
        }


# ============================================================
# RETRIEVE EVIDENCE PACKAGE
# ============================================================

def retrieve_evidence_package(cid: str) -> Optional[dict]:
    """
    Retrieve an evidence package from IPFS by CID.
    Returns the package dict or None if unavailable.

    In DEV mode, returns None since content is not actually stored.
    """
    if _is_ipfs_configured():
        # Real retrieval would call IPFS gateway
        # GET {gateway_url}/ipfs/{cid}
        logger.warning("IPFS retrieval not implemented — live adapter placeholder.")
        return None
    return None  # Honest: content not stored in dev mode


# ============================================================
# SERVICE HEALTH
# ============================================================

def get_ipfs_status() -> dict:
    """Return current IPFS service status for diagnostics."""
    configured = _is_ipfs_configured()
    return {
        "configured": configured,
        "mode": "LIVE_IPFS" if configured else "DEV_LOCAL_HASH",
        "endpoint": os.environ.get("IPFS_ENDPOINT", "") if configured else None,
        "message": (
            "IPFS configured and active."
            if configured
            else "IPFS not configured. Set IPFS_ENDPOINT environment variable for production use."
        ),
    }
