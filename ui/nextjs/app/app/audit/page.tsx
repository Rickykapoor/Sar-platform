'use client';
import { useEffect, useState } from 'react';
import { sarApi } from '@/lib/api';
import { Clock, Shield, RefreshCw, User, Hash } from 'lucide-react';

const EVENT_COLORS: Record<string, { color: string; bg: string }> = {
  'PII_STRIPPED':      { color: '#a78bfa', bg: 'rgba(167,139,250,0.12)' },
  'SAR_APPROVED':      { color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
  'CASE_REJECTED':     { color: '#f43f5e', bg: 'rgba(244,63,94,0.12)' },
  'CASE_OPEN':         { color: '#60a5fa', bg: 'rgba(96,165,250,0.12)' },
  'PAGE_VIEW':         { color: '#52525b', bg: 'rgba(82,82,91,0.10)' },
  'GRAPH_ACCESS':      { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  'STR_EXPORTED':      { color: '#fb923c', bg: 'rgba(251,146,60,0.12)' },
  'AUDIT_QUERIED':     { color: '#3f3f46', bg: 'rgba(63,63,70,0.10)' },
  'PII_VIEW_UNMASKED': { color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
  'SESSION_TERMINATED':{ color: '#f43f5e', bg: 'rgba(244,63,94,0.12)' },
  'AUDIT_LOG':         { color: '#60a5fa', bg: 'rgba(96,165,250,0.12)' },
};

const EVT_ICON: Record<string, string> = {
  'PII_STRIPPED': '🔒', 'SAR_APPROVED': '✅', 'CASE_REJECTED': '❌',
  'CASE_OPEN': '📂', 'PAGE_VIEW': '👁', 'GRAPH_ACCESS': '🕸',
  'STR_EXPORTED': '📄', 'PII_VIEW_UNMASKED': '🔓', 'SESSION_TERMINATED': '🚫',
};

function EventBadge({ type }: { type: string }) {
  const c = EVENT_COLORS[type] ?? { color: '#71717a', bg: 'rgba(113,113,122,0.12)' };
  return (
    <span style={{ fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 20, color: c.color, background: c.bg, whiteSpace: 'nowrap', letterSpacing: 0.5 }}>
      {EVT_ICON[type] ?? '•'} {type.replace(/_/g, ' ')}
    </span>
  );
}

export default function AuditTrailPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const load = () => {
    setLoading(true);
    sarApi.getAuditTrail(200)
      .then(d => setEntries(d?.entries ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  // Log this page view
  useEffect(() => {
    sarApi.logAuditEvent({
      user_id: 'analyst-demo', user_role: 'ANALYST_L2',
      event_type: 'PAGE_VIEW', metadata: { page: '/app/audit' },
    }).catch(() => {});
  }, []);

  const filtered = entries.filter(e =>
    !filter ||
    e.event_type?.toLowerCase().includes(filter.toLowerCase()) ||
    e.user_role?.toLowerCase().includes(filter.toLowerCase()) ||
    e.case_id?.toLowerCase().includes(filter.toLowerCase())
  );

  // Stats
  const piiCount    = entries.filter(e => e.event_type === 'PII_STRIPPED').length;
  const approvals   = entries.filter(e => e.event_type === 'SAR_APPROVED').length;
  const piiViews    = entries.filter(e => e.event_type === 'PII_VIEW_UNMASKED').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Audit Trail</h1>
          <p style={{ fontSize: 13, color: '#52525b' }}>Append-only · SHA-256 tamper-sealed · PMLA 2002 compliant</p>
        </div>
        <button onClick={load} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: '#71717a', fontSize: 12, padding: '7px 12px', cursor: 'pointer' }}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          { label: 'Total Events', value: entries.length, color: '#60a5fa', bg: 'rgba(96,165,250,0.1)' },
          { label: 'PII Strips', value: piiCount, color: '#a78bfa', bg: 'rgba(167,139,250,0.1)' },
          { label: 'SAR Approvals', value: approvals, color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
          { label: 'Unmasked PII Views', value: piiViews, color: '#f43f5e', bg: 'rgba(244,63,94,0.1)' },
        ].map(s => (
          <div key={s.label} style={{ background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: 16 }}>
            <div style={{ width: 28, height: 28, borderRadius: 7, background: s.bg, marginBottom: 10 }} />
            <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{loading ? '—' : s.value}</div>
            <div style={{ fontSize: 11, color: '#52525b' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <input
        value={filter} onChange={e => setFilter(e.target.value)}
        placeholder="Filter by event type, role, or case ID…"
        className="input-dark"
        style={{ width: '100%', boxSizing: 'border-box' }}
      />

      {/* Timeline */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: 14, display: 'flex', gap: 12 }}>
              <div className="shimmer" style={{ width: 32, height: 32, borderRadius: '50%' }} />
              <div style={{ flex: 1 }}>
                <div className="shimmer" style={{ height: 12, width: '40%', borderRadius: 4, marginBottom: 6 }} />
                <div className="shimmer" style={{ height: 10, width: '70%', borderRadius: 4 }} />
              </div>
            </div>
          ))
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 16px', color: '#3f3f46', fontSize: 13 }}>
            {entries.length === 0 ? 'No audit events yet. Activity will appear here as the platform is used.' : 'No events match your filter.'}
          </div>
        ) : filtered.map((entry, i) => (
          <div key={i} className="row-hover" style={{ background: '#111', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 12, padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            {/* Avatar */}
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <User size={13} color="#60a5fa" />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                <EventBadge type={entry.event_type} />
                <span style={{ fontSize: 11, color: '#52525b' }}>{entry.user_role}</span>
                <span style={{ fontSize: 11, color: '#3f3f46', marginLeft: 'auto' }}>
                  {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '—'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {entry.case_id && (
                  <span style={{ fontSize: 11, color: '#71717a' }}>
                    Case: <code style={{ color: '#3b82f6' }}>{entry.case_id}</code>
                  </span>
                )}
                {entry.pii_categories_found?.length > 0 && (
                  <span style={{ fontSize: 11, color: '#a78bfa' }}>
                    PII: {entry.pii_categories_found.join(', ')}
                  </span>
                )}
                {entry.metadata && typeof entry.metadata === 'object' && Object.keys(entry.metadata).length > 0 && (
                  <span style={{ fontSize: 11, color: '#52525b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
                    {JSON.stringify(entry.metadata)}
                  </span>
                )}
              </div>
            </div>
            {/* Hash chip */}
            {entry.entry_hash && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
                <Hash size={10} color="#3f3f46" />
                <span style={{ fontSize: 10, fontFamily: 'monospace', color: '#3f3f46' }}>{entry.entry_hash.slice(0, 8)}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
