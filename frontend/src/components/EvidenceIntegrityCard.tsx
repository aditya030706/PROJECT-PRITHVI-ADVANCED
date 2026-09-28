/**
 * PRITHVI — Evidence Integrity Card Component (Phase 2 Task 7)
 *
 * Displays tamper-evident integrity status for a single evidence item.
 * Uses PRITHVI's established dark theme (#060608, #0D0D12, orange #F97316).
 *
 * Shows:
 *  - Evidence type + filename
 *  - SHA-256 fingerprint (truncated, expandable)
 *  - IPFS status (STORED | IPFS_NOT_CONFIGURED)
 *  - IPFS CID (truncated, expandable)
 *  - Blockchain anchor reference (truncated, expandable)
 *  - Blockchain mode (DEMO_AUDIT_MODE | LIVE_BLOCKCHAIN)
 *  - Overall integrity status badge
 */

import { useState } from 'react';

import type { EvidenceWithIntegrity, EvidenceIntegrityRecord } from '../api/integrity';

interface EvidenceIntegrityCardProps {
  evidence: EvidenceWithIntegrity;
  onAnchor?: (evidenceId: string) => void;
  onVerify?: (evidenceId: string) => void;
  loading?: boolean;
}

function truncate(s: string | null | undefined, len = 20): string {
  if (!s) return '—';
  return s.length > len ? s.slice(0, len) + '…' : s;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, { bg: string; color: string; label: string }> = {
    VERIFIED: { bg: '#052e16', color: '#4ade80', label: '✓ Verified' },
    ANCHORED: { bg: '#172554', color: '#60a5fa', label: '⟳ Anchored' },
    PENDING: { bg: '#1c1917', color: '#a8a29e', label: '○ Pending' },
    FAILED: { bg: '#450a0a', color: '#f87171', label: '✗ Failed' },
    INTEGRITY_VERIFIED: { bg: '#052e16', color: '#4ade80', label: '✓ Integrity Verified' },
    INTEGRITY_CHECK_FAILED: { bg: '#450a0a', color: '#f87171', label: '✗ Integrity Check Failed' },
    AUDIT_PROOF_PENDING: { bg: '#1c1917', color: '#a8a29e', label: '○ Awaiting Anchor' },
    IPFS_NOT_CONFIGURED: { bg: '#1c1917', color: '#a8a29e', label: 'Local CID' },
    STORED: { bg: '#052e16', color: '#4ade80', label: 'IPFS Stored' },
    DEMO_AUDIT_MODE: { bg: '#1e1b4b', color: '#818cf8', label: 'Demo Mode' },
    LIVE_BLOCKCHAIN: { bg: '#052e16', color: '#4ade80', label: 'Live Chain' },
  };

  const s = styles[status] || { bg: '#1c1917', color: '#a8a29e', label: status };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 10px',
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 600,
        background: s.bg,
        color: s.color,
        letterSpacing: '0.02em',
        border: `1px solid ${s.color}22`,
      }}
    >
      {s.label}
    </span>
  );
}

function ExpandableHash({
  label,
  value,
  mono = true,
}: {
  label: string;
  value: string | null | undefined;
  mono?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  if (!value) return null;

  return (
    <div style={{ marginBottom: 6 }}>
      <span style={{ fontSize: 11, color: '#6b7280', marginRight: 6 }}>{label}:</span>
      <span
        onClick={() => setExpanded(e => !e)}
        style={{
          fontSize: 11,
          color: '#d1d5db',
          fontFamily: mono ? 'monospace' : 'inherit',
          cursor: 'pointer',
          wordBreak: 'break-all',
          borderBottom: '1px dashed #374151',
        }}
        title="Click to expand"
      >
        {expanded ? value : truncate(value, 28)}
        <span style={{ color: '#6b7280', marginLeft: 4 }}>
          {expanded ? '▲' : '▼'}
        </span>
      </span>
    </div>
  );
}

export function EvidenceIntegrityCard({
  evidence,
  onAnchor,
  onVerify,
  loading,
}: EvidenceIntegrityCardProps) {
  const r = evidence.integrity as EvidenceIntegrityRecord | null;

  const typeIcon: Record<string, string> = {
    photo: '📷',
    document: '📄',
    video: '🎥',
    voice: '🎙️',
    sensor: '📡',
    manual_reading: '📋',
  };
  const icon = typeIcon[evidence.evidence_type] || '📎';

  return (
    <div
      style={{
        background: '#0D0D12',
        border: '1px solid #1f2937',
        borderRadius: 10,
        padding: '14px 16px',
        marginBottom: 10,
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18 }}>{icon}</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#e5e7eb' }}>
              {evidence.filename || evidence.evidence_type}
            </div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>
              {evidence.evidence_type.toUpperCase()}
              {evidence.captured_at && ` · ${evidence.captured_at.slice(0, 10)}`}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {r ? (
            <StatusBadge status={r.status} />
          ) : (
            <StatusBadge status="PENDING" />
          )}
        </div>
      </div>

      {/* Integrity details */}
      {r ? (
        <div
          style={{
            background: '#060608',
            borderRadius: 8,
            padding: '10px 12px',
            marginBottom: 10,
          }}
        >
          <ExpandableHash label="SHA-256" value={r.content_hash} />
          <ExpandableHash label="IPFS CID" value={r.ipfs_cid} />
          <ExpandableHash label="Anchor Ref" value={r.transaction_ref} />

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
            <StatusBadge status={r.ipfs_status} />
            <StatusBadge status={r.anchor_mode} />
            {r.verification_result && <StatusBadge status={r.verification_result} />}
          </div>

          {r.anchor_mode === 'DEMO_AUDIT_MODE' && (
            <div
              style={{
                marginTop: 8,
                padding: '6px 10px',
                background: '#1e1b4b',
                borderRadius: 6,
                fontSize: 11,
                color: '#a5b4fc',
                lineHeight: 1.5,
              }}
            >
              <strong>Demo Audit Mode</strong> — SHA-256 fingerprint and CIDv1 computed locally.
              In production, configure IPFS and blockchain providers for real anchoring.
            </div>
          )}

          {r.verified_at && (
            <div style={{ marginTop: 6, fontSize: 11, color: '#6b7280' }}>
              Verified: {r.verified_at.slice(0, 19)}
            </div>
          )}
        </div>
      ) : (
        <div
          style={{
            background: '#060608',
            borderRadius: 8,
            padding: '10px 12px',
            marginBottom: 10,
            fontSize: 12,
            color: '#6b7280',
          }}
        >
          No integrity record. Click <strong style={{ color: '#F97316' }}>Anchor</strong> to create one.
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 8 }}>
        {onAnchor && (
          <button
            onClick={() => onAnchor(evidence.evidence_id)}
            disabled={loading}
            style={{
              padding: '5px 14px',
              borderRadius: 6,
              border: '1px solid #F97316',
              background: 'transparent',
              color: '#F97316',
              fontSize: 12,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1,
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = '#F9731622')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            {r ? 'Re-Anchor' : 'Anchor'}
          </button>
        )}
        {onVerify && r && (
          <button
            onClick={() => onVerify(evidence.evidence_id)}
            disabled={loading}
            style={{
              padding: '5px 14px',
              borderRadius: 6,
              border: '1px solid #60a5fa',
              background: 'transparent',
              color: '#60a5fa',
              fontSize: 12,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1,
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = '#60a5fa22')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            Verify Integrity
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================
// AUDIT INTEGRITY PANEL (for Inspection / Case views)
// ============================================================

interface AuditIntegrityPanelProps {
  title?: string;
  total: number;
  anchoredCount: number;
  verifiedCount: number;
  pendingCount: number;
  coverage: 'FULL' | 'PARTIAL' | 'NONE';
  evidenceItems: EvidenceWithIntegrity[];
  ipfsStatus?: Record<string, unknown>;
  blockchainStatus?: Record<string, unknown>;
  onAnchor?: (evidenceId: string) => void;
  onVerify?: (evidenceId: string) => void;
  loading?: boolean;
}

export function AuditIntegrityPanel({
  title = 'Evidence Integrity Audit Chain',
  total,
  anchoredCount,
  verifiedCount,
  pendingCount,
  coverage,
  evidenceItems,
  ipfsStatus,
  blockchainStatus,
  onAnchor,
  onVerify,
  loading,
}: AuditIntegrityPanelProps) {
  const coverageColor =
    coverage === 'FULL'
      ? '#4ade80'
      : coverage === 'PARTIAL'
      ? '#fbbf24'
      : '#f87171';

  return (
    <div
      style={{
        background: '#0D0D12',
        border: '1px solid #1f2937',
        borderRadius: 12,
        padding: 20,
        marginTop: 16,
      }}
    >
      {/* Panel header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 16,
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#e5e7eb' }}>
            🔗 {title}
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: 12, color: '#6b7280' }}>
            Tamper-evident cryptographic proof · SHA-256 · IPFS · Blockchain Anchor
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: '#060608',
            border: `1px solid ${coverageColor}`,
            borderRadius: 20,
            padding: '4px 14px',
          }}
        >
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: coverageColor, display: 'inline-block' }} />
          <span style={{ fontSize: 12, color: coverageColor, fontWeight: 600 }}>
            {coverage} COVERAGE
          </span>
        </div>
      </div>

      {/* Stats bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 8,
          marginBottom: 16,
        }}
      >
        {[
          { label: 'Total Evidence', value: total, color: '#e5e7eb' },
          { label: 'Anchored', value: anchoredCount, color: '#60a5fa' },
          { label: 'Verified', value: verifiedCount, color: '#4ade80' },
          { label: 'Pending', value: pendingCount, color: '#fbbf24' },
        ].map(stat => (
          <div
            key={stat.label}
            style={{
              background: '#060608',
              borderRadius: 8,
              padding: '8px 12px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 22, fontWeight: 700, color: stat.color }}>
              {stat.value}
            </div>
            <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Service status pills */}
      {(ipfsStatus || blockchainStatus) && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          {ipfsStatus && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                background: '#1c1917',
                borderRadius: 6,
                padding: '4px 10px',
                fontSize: 11,
                color: '#a8a29e',
              }}
            >
              <span>📦</span>
              IPFS: <strong style={{ color: ipfsStatus['configured'] ? '#4ade80' : '#a8a29e' }}>
                {String(ipfsStatus['mode'] || 'DEV_LOCAL_HASH')}
              </strong>
            </div>
          )}
          {blockchainStatus && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                background: '#1e1b4b',
                borderRadius: 6,
                padding: '4px 10px',
                fontSize: 11,
                color: '#a5b4fc',
              }}
            >
              <span>⛓️</span>
              Chain: <strong>{String(blockchainStatus['mode'] || 'DEMO_AUDIT_MODE')}</strong>
            </div>
          )}
        </div>
      )}

      {/* Evidence items */}
      {evidenceItems.length === 0 ? (
        <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280', fontSize: 13 }}>
          No evidence attached to this record.
        </div>
      ) : (
        evidenceItems.map(ev => (
          <EvidenceIntegrityCard
            key={ev.evidence_id}
            evidence={ev}
            onAnchor={onAnchor}
            onVerify={onVerify}
            loading={loading}
          />
        ))
      )}
    </div>
  );
}

export default EvidenceIntegrityCard;
