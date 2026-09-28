/**
 * PRITHVI — Evidence Audit Chain Page (Phase 2 Task 7)
 *
 * Standalone page for viewing and verifying evidence integrity
 * for a specific inspection or compliance case.
 *
 * Route: /audit-chain/:type/:id
 *   type = 'inspection' | 'case'
 *   id   = inspection_id or case_id
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AuditIntegrityPanel } from '../components/EvidenceIntegrityCard';
import {
  getInspectionAuditIntegrity,
  getCaseAuditIntegrity,
  anchorEvidence,
  verifyEvidenceIntegrity,
  getIntegrityServiceStatus,
} from '../api/integrity';
import type {
  InspectionAuditIntegrityResponse,
  CaseAuditIntegrityResponse,
  IntegrityServiceStatus,
} from '../api/integrity';

type AuditData = InspectionAuditIntegrityResponse | CaseAuditIntegrityResponse;

function isInspectionAudit(data: AuditData): data is InspectionAuditIntegrityResponse {
  return 'inspection_id' in data;
}

export default function EvidenceAuditChain() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<AuditData | null>(null);
  const [serviceStatus, setServiceStatus] = useState<IntegrityServiceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const fetchData = async () => {
    if (!id || !type) return;
    setLoading(true);
    setError(null);
    try {
      const result =
        type === 'case'
          ? await getCaseAuditIntegrity(id)
          : await getInspectionAuditIntegrity(id);
      setData(result);

      const status = await getIntegrityServiceStatus();
      setServiceStatus(status);
    } catch (err) {
      setError('Failed to load audit integrity data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, [id, type]);

  const showNotification = (type: 'success' | 'error', msg: string) => {
    setNotification({ type, msg });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleAnchor = async (evidenceId: string) => {
    setActionLoading(true);
    try {
      await anchorEvidence(evidenceId, { actor_id: 'PRITHVI-USER' });
      showNotification('success', `Evidence ${evidenceId} anchored successfully.`);
      await fetchData();
    } catch {
      showNotification('error', 'Anchoring failed. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerify = async (evidenceId: string) => {
    setActionLoading(true);
    try {
      const result = await verifyEvidenceIntegrity(evidenceId);
      if (result.matches) {
        showNotification('success', `✓ Integrity Verified — ${evidenceId}`);
      } else {
        showNotification('error', `✗ Integrity Check Failed — ${result.verification_status}`);
      }
      await fetchData();
    } catch {
      showNotification('error', 'Verification failed. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const title =
    type === 'case'
      ? `Case Audit Chain — ${id}`
      : `Inspection Audit Chain — ${id}`;

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#060608',
        padding: '0 0 60px',
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: '#0D0D12',
          borderBottom: '1px solid #1f2937',
          padding: '18px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <button
            onClick={() => navigate(-1)}
            style={{
              background: 'none',
              border: 'none',
              color: '#6b7280',
              cursor: 'pointer',
              fontSize: 13,
              marginBottom: 6,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: 0,
            }}
          >
            ← Back
          </button>
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#f9fafb' }}>
            🔗 {title}
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: '#6b7280' }}>
            Tamper-evident evidence integrity · SHA-256 · IPFS · Blockchain Anchor
          </p>
        </div>

        {/* Service Status Pills */}
        {serviceStatus && (
          <div style={{ display: 'flex', gap: 8 }}>
            <div
              style={{
                background: '#1c1917',
                borderRadius: 8,
                padding: '6px 14px',
                fontSize: 12,
                color: '#a8a29e',
                border: '1px solid #292524',
              }}
            >
              <span style={{ color: '#fbbf24' }}>📦</span> IPFS:{' '}
              <strong>{serviceStatus.ipfs.mode}</strong>
            </div>
            <div
              style={{
                background: '#1e1b4b',
                borderRadius: 8,
                padding: '6px 14px',
                fontSize: 12,
                color: '#a5b4fc',
                border: '1px solid #312e81',
              }}
            >
              <span>⛓️</span> Chain:{' '}
              <strong>{serviceStatus.blockchain.mode}</strong>
            </div>
          </div>
        )}
      </div>

      {/* Notification */}
      {notification && (
        <div
          style={{
            position: 'fixed',
            top: 20,
            right: 20,
            zIndex: 9999,
            background: notification.type === 'success' ? '#052e16' : '#450a0a',
            border: `1px solid ${notification.type === 'success' ? '#4ade80' : '#f87171'}`,
            color: notification.type === 'success' ? '#4ade80' : '#f87171',
            borderRadius: 10,
            padding: '12px 20px',
            fontSize: 13,
            fontWeight: 600,
            maxWidth: 380,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            animation: 'fadeIn 0.2s',
          }}
        >
          {notification.msg}
        </div>
      )}

      {/* Content */}
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '24px 24px 0' }}>
        {/* Blockchain architecture info */}
        <div
          style={{
            background: '#0D0D12',
            border: '1px solid #1e1b4b',
            borderRadius: 12,
            padding: '16px 20px',
            marginBottom: 20,
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 0,
          }}
        >
          {[
            { label: 'Evidence', icon: '📎', color: '#e5e7eb' },
            { label: 'SHA-256 Hash', icon: '🔢', color: '#60a5fa', arrow: true },
            { label: 'IPFS CID', icon: '📦', color: '#a78bfa', arrow: true },
            { label: 'Blockchain Anchor', icon: '⛓️', color: '#4ade80', arrow: true },
          ].map((step) => (
            <div
              key={step.label}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              {step.arrow && (
                <span style={{ color: '#374151', fontSize: 18 }}>→</span>
              )}
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: 20 }}>{step.icon}</div>
                <div style={{ fontSize: 11, color: step.color, fontWeight: 600, marginTop: 4 }}>
                  {step.label}
                </div>
              </div>
            </div>
          ))}
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: '#6b7280' }}>
            <div style={{ fontSize: 28, marginBottom: 12, animation: 'spin 1s linear infinite' }}>⏳</div>
            Loading audit integrity chain…
          </div>
        ) : error ? (
          <div
            style={{
              background: '#450a0a',
              border: '1px solid #f87171',
              borderRadius: 10,
              padding: '20px 24px',
              color: '#fca5a5',
              fontSize: 14,
            }}
          >
            {error}
          </div>
        ) : data ? (
          <AuditIntegrityPanel
            title={isInspectionAudit(data) ? 'Inspection Evidence Audit Chain' : 'Case Correction Evidence Audit Chain'}
            total={isInspectionAudit(data) ? data.total_evidence : (data as CaseAuditIntegrityResponse).total_correction_evidence}
            anchoredCount={data.anchored_count}
            verifiedCount={data.verified_count}
            pendingCount={
              isInspectionAudit(data)
                ? data.pending_count
                : Math.max(
                    0,
                    (data as CaseAuditIntegrityResponse).total_correction_evidence - data.anchored_count
                  )
            }
            coverage={data.integrity_coverage}
            evidenceItems={data.evidence_integrity}
            ipfsStatus={data.ipfs_service_status as Record<string, unknown>}
            blockchainStatus={data.blockchain_service_status as Record<string, unknown>}
            onAnchor={handleAnchor}
            onVerify={handleVerify}
            loading={actionLoading}
          />
        ) : null}

        {/* Ledger standard note */}
        {serviceStatus && (
          <div
            style={{
              marginTop: 20,
              background: '#0D0D12',
              border: '1px solid #1f2937',
              borderRadius: 10,
              padding: '14px 18px',
              fontSize: 12,
              color: '#6b7280',
              lineHeight: 1.6,
            }}
          >
            <strong style={{ color: '#9ca3af' }}>
              Ledger Standard: {serviceStatus.blockchain.ledger_standard}
            </strong>
            <br />
            {serviceStatus.note}
          </div>
        )}
      </div>
    </div>
  );
}
