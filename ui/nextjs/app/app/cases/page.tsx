'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { sarApi, CaseSummary } from '@/lib/api';
import { RiskBadge, StatusBadge } from '@/components/RiskBadge';
import { Search, RefreshCw, ArrowRight, SlidersHorizontal } from 'lucide-react';

const TIERS = ['all', 'red', 'amber', 'green', 'pending'];

const card: React.CSSProperties = {
  background: '#111',
  border: '1px solid rgba(255,255,255,0.07)',
  borderRadius: 16,
  overflow: 'hidden',
};

export default function CasesPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [tier, setTier] = useState('all');

  const load = () => {
    setLoading(true);
    sarApi.getCases().then(setCases).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const filtered = cases.filter(c => {
    const q = search.toLowerCase();
    return (c.case_id.toLowerCase().includes(q) || c.subject.toLowerCase().includes(q))
      && (tier === 'all' || c.risk_tier === tier);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginBottom: 4 }}>All Cases</h1>
          <p style={{ fontSize: 12, color: '#52525b' }}>{cases.length} case{cases.length !== 1 ? 's' : ''} in memory</p>
        </div>
        <button onClick={load}
          style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: '#71717a', fontSize: 12, padding: '7px 12px', cursor: 'pointer' }}>
          <RefreshCw style={{ width: 13, height: 13 }} /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', width: 13, height: 13, color: '#3f3f46' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search case ID or subject…"
            className="input-dark" style={{ paddingLeft: 36 }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '0 12px' }}>
          <SlidersHorizontal style={{ width: 13, height: 13, color: '#3f3f46', marginRight: 6 }} />
          {TIERS.map(t => (
            <button key={t} onClick={() => setTier(t)}
              style={{
                fontSize: 10, fontWeight: 700, textTransform: 'uppercase', padding: '6px 10px', borderRadius: 6, cursor: 'pointer', border: 'none',
                background: tier === t ? 'rgba(59,130,246,0.15)' : 'transparent',
                color: tier === t ? '#60a5fa' : '#52525b',
                transition: 'all 0.1s',
              }}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={card}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              {['Case ID', 'Subject', 'Risk', 'Status', 'Updated', ''].map(h => (
                <th key={h} className="th">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="td">
                      <div className="shimmer" style={{ height: 13, borderRadius: 4, width: `${55 + j * 8}%` }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '60px 16px', color: '#3f3f46', fontSize: 13 }}>
                {cases.length === 0 ? 'No cases yet — run a demo scenario first' : 'No matches'}
              </td></tr>
            ) : filtered.map((c, i) => (
              <tr key={c.case_id} className="row-hover" style={{ borderTop: i > 0 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                <td className="td"><span className="mono" style={{ color: '#3b82f6', fontSize: 12, fontWeight: 500 }}>{c.case_id}</span></td>
                <td className="td" style={{ maxWidth: 130 }}><span style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>{c.subject}</span></td>
                <td className="td"><RiskBadge tier={c.risk_tier} size="sm" /></td>
                <td className="td"><StatusBadge status={c.status} /></td>
                <td className="td" style={{ color: '#3f3f46', fontSize: 11 }}>
                  {c.last_updated !== 'Unknown' ? new Date(c.last_updated).toLocaleDateString() : '—'}
                </td>
                <td className="td">
                  <Link href={`/app/cases/${c.case_id}`}
                    style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#3b82f6', textDecoration: 'none' }}>
                    Open <ArrowRight style={{ width: 12, height: 12 }} />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
