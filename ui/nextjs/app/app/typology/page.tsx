'use client';
import { useEffect, useState } from 'react';
import { sarApi } from '@/lib/api';
import { Tag, RefreshCw, AlertTriangle, TrendingUp, Shield } from 'lucide-react';

const COLOR_MAP: Record<string, string> = {
  'MONEY_MULE_RAPID_CASHOUT':    '#f43f5e',
  'LAYERING_CRYPTO_OFFLOAD':     '#a78bfa',
  'PASS_THROUGH_IMMEDIATE':      '#f59e0b',
  'SMURFING_INFLOW_AGGREGATION': '#fb923c',
};

const badge = (code: string | null) => {
  if (!code) return <span style={{ color: '#3f3f46', fontSize: 11 }}>— No Match</span>;
  const color = COLOR_MAP[code] ?? '#60a5fa';
  return (
    <span style={{ fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 20, color, background: `${color}1a`, letterSpacing: 1 }}>
      {code.replace(/_/g, ' ')}
    </span>
  );
};

const RollupBar = ({ label, value, total }: { label: string; value: number; total: number }) => {
  const pct = total > 0 ? Math.min((value / total) * 100, 100) : 0;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#71717a', marginBottom: 4 }}>
        <span>{label}</span><span>INR {value.toLocaleString('en-IN')}</span>
      </div>
      <div style={{ height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 4 }}>
        <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg,#3b82f6,#8b5cf6)', borderRadius: 4, transition: 'width 0.5s' }} />
      </div>
    </div>
  );
};

export default function TypologyPage() {
  const [cases, setCases] = useState<any[]>([]);
  const [results, setResults] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [registry, setRegistry] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'cases' | 'registry'>('cases');

  const load = async () => {
    setLoading(true);
    try {
      const [caseList, regData] = await Promise.all([
        sarApi.getCases(),
        sarApi.getTypologyRegistry(),
      ]);
      setCases(caseList.slice(0, 20));
      setRegistry(regData?.typologies ?? []);

      // Fetch typology for first 10 cases in parallel
      const top10 = caseList.slice(0, 10);
      const typologyResults = await Promise.allSettled(
        top10.map(c => sarApi.getTypology(c.case_id).then(d => ({ id: c.case_id, data: d })))
      );
      const map: Record<string, any> = {};
      typologyResults.forEach(r => { if (r.status === 'fulfilled') map[r.value.id] = r.value.data; });
      setResults(map);
    } catch (e) {
      // ignore
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Typology Reports</h1>
          <p style={{ fontSize: 13, color: '#52525b' }}>FIU-IND AML typology classification · ML-MULE · ML-LAYER · ML-PASS · ML-SMRF</p>
        </div>
        <button onClick={load} style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: '#71717a', fontSize: 12, padding: '7px 12px', cursor: 'pointer' }}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: 4, width: 'fit-content' }}>
        {(['cases', 'registry'] as const).map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            style={{ fontSize: 12, fontWeight: 600, padding: '6px 16px', borderRadius: 7, cursor: 'pointer', border: 'none',
              background: activeTab === t ? 'rgba(59,130,246,0.15)' : 'transparent',
              color: activeTab === t ? '#60a5fa' : '#52525b' }}>
            {t === 'cases' ? 'Case Analysis' : 'Typology Registry'}
          </button>
        ))}
      </div>

      {activeTab === 'cases' && (
        <div style={{ background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                {['Case ID', 'Typology Code', 'FIU-IND Code', 'Risk Weight', 'Rolling 90d (INR)', 'Breach'].map(h => (
                  <th key={h} className="th">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="td"><div className="shimmer" style={{ height: 12, borderRadius: 4, width: '70%' }} /></td>
                    ))}
                  </tr>
                ))
              ) : cases.map((c, i) => {
                const d = results[c.case_id];
                const tm = d?.typology_match;
                const rw = d?.rolling_windows;
                return (
                  <tr key={c.case_id} className="row-hover" style={{ borderTop: i > 0 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                    <td className="td"><span className="mono" style={{ color: '#3b82f6', fontSize: 12 }}>{c.case_id}</span></td>
                    <td className="td">{badge(tm?.typology_code ?? null)}</td>
                    <td className="td"><span style={{ fontSize: 11, fontFamily: 'monospace', color: '#71717a' }}>{tm?.fiu_ind_code ?? '—'}</span></td>
                    <td className="td">
                      {tm ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ height: 4, width: `${(tm.risk_weight ?? 0) * 60}px`, background: '#f43f5e', borderRadius: 4, minWidth: 8 }} />
                          <span style={{ fontSize: 11, color: '#71717a' }}>{tm.risk_weight?.toFixed(2) ?? '—'}</span>
                        </div>
                      ) : <span style={{ color: '#3f3f46', fontSize: 11 }}>—</span>}
                    </td>
                    <td className="td">
                      <span style={{ fontSize: 12, color: '#a1a1aa' }}>
                        {rw ? `₹${(rw['90d_total'] ?? 0).toLocaleString('en-IN')}` : '—'}
                      </span>
                    </td>
                    <td className="td">
                      {rw ? (
                        <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
                          color: rw['90d_breach'] ? '#f43f5e' : '#10b981',
                          background: rw['90d_breach'] ? 'rgba(244,63,94,0.12)' : 'rgba(16,185,129,0.12)' }}>
                          {rw['90d_breach'] ? 'BREACH' : 'CLEAR'}
                        </span>
                      ) : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'registry' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {registry.map((t: any) => (
            <div key={t.typology_code} style={{ background: '#111', border: `1px solid ${(COLOR_MAP[t.typology_code] ?? '#3b82f6')}30`, borderRadius: 16, padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <Tag size={14} color={COLOR_MAP[t.typology_code] ?? '#60a5fa'} />
                <span style={{ fontSize: 11, fontFamily: 'monospace', color: COLOR_MAP[t.typology_code] ?? '#60a5fa', fontWeight: 700 }}>
                  {t.fiu_ind_typology_code}
                </span>
                <span style={{ marginLeft: 'auto', fontSize: 10, color: '#52525b' }}>
                  weight: <strong style={{ color: '#f59e0b' }}>{t.risk_weight?.toFixed(2)}</strong>
                </span>
              </div>
              <p style={{ fontSize: 13, fontWeight: 600, color: '#e4e4e7', marginBottom: 6 }}>
                {t.typology_code.split('_').map((w: string) => w[0] + w.slice(1).toLowerCase()).join(' ')}
              </p>
              <p style={{ fontSize: 12, color: '#71717a', lineHeight: 1.6, marginBottom: 10 }}>{t.description}</p>
              <p style={{ fontSize: 10, color: '#3f3f46', fontStyle: 'italic' }}>{t.regulatory_reference}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
