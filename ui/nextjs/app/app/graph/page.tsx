'use client';
import { useEffect, useState } from 'react';
import { sarApi } from '@/lib/api';
import { Network, AlertTriangle, Shield, ChevronRight, RefreshCw, GitBranch } from 'lucide-react';

const badge = (label: string, color: string, bg: string) => (
  <span style={{ fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 20, color, background: bg, letterSpacing: 1, textTransform: 'uppercase' as const }}>
    {label}
  </span>
);

const SIG_MAP: Record<string, { label: string; color: string; bg: string }> = {
  'FAN_IN_SMURFING':    { label: 'Fan-In Smurfing', color: '#f43f5e', bg: 'rgba(244,63,94,0.12)' },
  'PASS_THROUGH':       { label: 'Pass-Through',    color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  'LAYERING_SUSPECTED': { label: 'Layering',        color: '#a78bfa', bg: 'rgba(167,139,250,0.12)' },
  'CLEAN':              { label: 'Clean',            color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
};

export default function GraphExplorer() {
  const [caseIds, setCaseIds] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingCases, setLoadingCases] = useState(true);

  useEffect(() => {
    sarApi.getCases()
      .then(cases => setCaseIds(cases.slice(0, 30).map(c => c.case_id)))
      .catch(() => {})
      .finally(() => setLoadingCases(false));
  }, []);

  const analyze = (id: string) => {
    setSelected(id);
    setLoading(true);
    setGraphData(null);
    sarApi.getGraphContext(id)
      .then(setGraphData)
      .catch(() => setGraphData(null))
      .finally(() => setLoading(false));
  };

  const g = graphData?.graph_analysis;
  const f = graphData?.fan_in_analysis;
  const sig = g ? SIG_MAP[g.graph_signature] ?? SIG_MAP['CLEAN'] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Graph Explorer</h1>
        <p style={{ fontSize: 13, color: '#52525b' }}>Multi-hop upstream funding network · 4-hop Neo4j traversal · Fan-In smurfing detection</p>
      </div>

      {/* Case selector */}
      <div style={{ background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: 16 }}>
        <p style={{ fontSize: 11, color: '#52525b', marginBottom: 10, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase' }}>Select a Case to Analyze</p>
        {loadingCases ? (
          <p style={{ color: '#3f3f46', fontSize: 12 }}>Loading cases…</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {caseIds.map(id => (
              <button key={id} onClick={() => analyze(id)}
                style={{
                  fontSize: 11, fontFamily: 'monospace', padding: '5px 10px', borderRadius: 6, cursor: 'pointer',
                  border: `1px solid ${selected === id ? 'rgba(59,130,246,0.5)' : 'rgba(255,255,255,0.07)'}`,
                  background: selected === id ? 'rgba(59,130,246,0.15)' : '#0a0a0a',
                  color: selected === id ? '#60a5fa' : '#71717a',
                }}>
                {id}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Graph Result */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 60, color: '#3f3f46' }}>
          <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite', marginBottom: 8 }} />
          <p style={{ fontSize: 13 }}>Running 4-hop graph traversal…</p>
        </div>
      )}

      {graphData && g && f && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Graph Signature Card */}
          <div style={{ background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: 20, gridColumn: '1 / -1' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <GitBranch size={18} color="#60a5fa" />
                <span style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>Graph Signature — {graphData.case_id}</span>
              </div>
              {sig && badge(sig.label, sig.color, sig.bg)}
            </div>
            {/* Visual graph representation */}
            <div style={{ position: 'relative', height: 160, background: '#0a0a0a', borderRadius: 12, overflow: 'hidden', marginBottom: 16 }}>
              {/* Upstream nodes */}
              {Array.from({ length: Math.min(f.fan_in_count, 8) }).map((_, i) => {
                const angle = (i / Math.min(f.fan_in_count, 8)) * Math.PI * 2;
                const x = 50 + 35 * Math.cos(angle);
                const y = 50 + 35 * Math.sin(angle);
                return (
                  <div key={i} style={{
                    position: 'absolute', left: `${x}%`, top: `${y}%`, transform: 'translate(-50%,-50%)',
                    width: 24, height: 24, borderRadius: '50%',
                    background: g.smurfing_indicator ? 'rgba(244,63,94,0.3)' : 'rgba(59,130,246,0.3)',
                    border: `1px solid ${g.smurfing_indicator ? '#f43f5e' : '#3b82f6'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 8, color: '#fff',
                  }}>S{i+1}</div>
                );
              })}
              {/* Center target node */}
              <div style={{
                position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)',
                width: 36, height: 36, borderRadius: '50%',
                background: 'rgba(16,185,129,0.3)', border: '2px solid #10b981',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 9, color: '#10b981', fontWeight: 700,
              }}>TARGET</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10 }}>
              {[
                { label: 'Pass-Through Score', value: `${(g.pass_through_score * 100).toFixed(1)}%`, highlight: g.pass_through_score > 0.65 },
                { label: 'Upstream Cash Deposits', value: g.upstream_cash_deposit_count },
                { label: 'Unique States', value: g.upstream_unique_states?.length ?? 0 },
                { label: 'Hops Analyzed', value: g.hops_analyzed },
              ].map(({ label, value, highlight }) => (
                <div key={label} style={{ padding: 12, background: '#0a0a0a', borderRadius: 10 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: highlight ? '#f43f5e' : '#60a5fa', marginBottom: 4 }}>{value}</div>
                  <div style={{ fontSize: 10, color: '#52525b' }}>{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Fan-In Analysis */}
          <div style={{ background: '#111', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 16, padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <Network size={16} color="#a78bfa" />
              <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>Fan-In Detection</span>
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: f.typology_match !== 'NORMAL' ? '#f43f5e' : '#10b981', marginBottom: 4 }}>
              {f.fan_in_count} senders
            </div>
            <div style={{ marginBottom: 12 }}>{badge(f.typology_match, f.typology_match !== 'NORMAL' ? '#f43f5e' : '#10b981', f.typology_match !== 'NORMAL' ? 'rgba(244,63,94,0.12)' : 'rgba(16,185,129,0.12)')}</div>
            <p style={{ fontSize: 12, color: '#71717a', lineHeight: 1.6 }}>{f.description}</p>
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                { label: 'Cross-State',    val: f.cross_state_flag },
                { label: 'Cross-City',     val: f.cross_city_flag },
                { label: 'Sequential Timing', val: f.sequential_timing_flag },
              ].map(({ label, val }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                  <span style={{ color: '#52525b' }}>{label}</span>
                  <span style={{ color: val ? '#f43f5e' : '#10b981', fontWeight: 600 }}>{val ? 'YES' : 'NO'}</span>
                </div>
              ))}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                <span style={{ color: '#52525b' }}>Low KYC Ratio</span>
                <span style={{ color: f.low_kyc_ratio > 0.5 ? '#f43f5e' : '#10b981', fontWeight: 600 }}>{(f.low_kyc_ratio * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>

          {/* Smurfing Indicator */}
          <div style={{ background: '#111', border: `1px solid ${g.smurfing_indicator ? 'rgba(244,63,94,0.3)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 16, padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <AlertTriangle size={16} color={g.smurfing_indicator ? '#f43f5e' : '#52525b'} />
              <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>Smurfing Indicator</span>
            </div>
            <div style={{ fontSize: 36, fontWeight: 700, color: g.smurfing_indicator ? '#f43f5e' : '#10b981', marginBottom: 8 }}>
              {g.smurfing_indicator ? 'ACTIVE' : 'CLEAR'}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {(g.upstream_unique_states || []).slice(0, 5).map((st: string) => (
                <div key={st} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#f43f5e' }} />
                  <span style={{ fontSize: 12, color: '#a1a1aa' }}>{st}</span>
                </div>
              ))}
              {g.upstream_unique_states?.length > 5 && (
                <span style={{ fontSize: 11, color: '#3f3f46' }}>+{g.upstream_unique_states.length - 5} more states</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
