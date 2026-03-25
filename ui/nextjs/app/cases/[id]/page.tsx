'use client';
import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { sarApi, SARCase } from '@/lib/api';
import { RiskBadge, StatusBadge } from '@/components/RiskBadge';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import {
  AlertTriangle, FileText, Shield, ChevronDown, ChevronUp,
  Download, CheckCircle, XCircle, ArrowLeft, Loader, Play,
  Copy, Check, TrendingUp, Lock, Clock, User
} from 'lucide-react';

const TABS = ['Overview', 'Risk Analysis', 'SAR Report', 'Compliance', 'Audit Trail'];

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [caseData, setCaseData] = useState<SARCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Overview');
  const [running, setRunning] = useState(false);
  const [genNarrative, setGenNarrative] = useState(false);
  const [analystName, setAnalystName] = useState('Analyst-1');
  const [approving, setApproving] = useState(false);
  const [copied, setCopied] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);

  const load = async () => {
    try {
      const data = await sarApi.getCase(id);
      setCaseData(data);
    } catch { /* 404 */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, [id]);

  const runPipeline = async () => {
    if (!caseData) return;
    setRunning(true);
    try {
      await sarApi.runPipeline(id);
      await load();
    } catch (e) { console.error(e); }
    setRunning(false);
  };

  const generateNarrative = async () => {
    setGenNarrative(true);
    try {
      await sarApi.generateNarrative(id);
      await load();
    } catch (e) { console.error(e); }
    setGenNarrative(false);
  };

  const approve = async () => {
    setApproving(true);
    try {
      await sarApi.approveCase(id, analystName);
      await load();
    } catch (e) { console.error(e); }
    setApproving(false);
  };

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadPDF = async () => {
    if (!reportRef.current || !caseData) return;
    const { default: jsPDF } = await import('jspdf');
    const { default: html2canvas } = await import('html2canvas');
    const canvas = await html2canvas(reportRef.current, { scale: 2, backgroundColor: '#050b18' });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    const w = pdf.internal.pageSize.getWidth();
    const h = (canvas.height * w) / canvas.width;
    let y = 0;
    while (y < h) {
      pdf.addImage(imgData, 'PNG', 0, -y, w, h);
      y += pdf.internal.pageSize.getHeight();
      if (y < h) pdf.addPage();
    }
    pdf.save(`SAR_Report_${id}.pdf`);
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader className="w-6 h-6 text-blue-400 animate-spin" />
    </div>
  );

  if (!caseData) return (
    <div className="text-center py-20">
      <div className="text-[#4a5568] mb-4">Case not found</div>
      <button onClick={() => router.push('/cases')} className="text-blue-400 text-sm">← Back to cases</button>
    </div>
  );

  const risk = caseData.risk_assessment;
  const narrative = caseData.narrative;
  const compliance = caseData.compliance;
  const audit = caseData.audit;
  const isPipelined = !!caseData.normalized;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button onClick={() => router.push('/cases')}
          className="flex items-center gap-1.5 text-xs text-[#8899aa] hover:text-white mb-4">
          <ArrowLeft className="w-3 h-3" /> All Cases
        </button>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="mono text-xl font-bold text-white">{id}</h1>
              <StatusBadge status={caseData.status} />
              {risk && <RiskBadge tier={risk.risk_tier} size="md" />}
            </div>
            <div className="text-sm text-[#8899aa]">
              {caseData.normalized?.subject_name ?? 'Unknown Subject'} •{' '}
              ${caseData.normalized?.total_amount_usd?.toLocaleString() ?? '0'} •{' '}
              {caseData.audit_trail.length} agent events
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            {!isPipelined && (
              <button onClick={runPipeline} disabled={running}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-xl text-white text-sm font-semibold transition-all">
                {running ? <Loader className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Run Pipeline
              </button>
            )}
            {isPipelined && !narrative && (
              <button onClick={generateNarrative} disabled={genNarrative}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-xl text-white text-sm font-semibold transition-all">
                {genNarrative ? <Loader className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                Generate Narrative
              </button>
            )}
            {narrative && (
              <button onClick={downloadPDF}
                className="flex items-center gap-2 px-4 py-2 bg-green-600/20 hover:bg-green-600/30 text-green-400 border border-green-500/30 rounded-xl text-sm font-semibold transition-all">
                <Download className="w-4 h-4" />
                Download PDF
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/5 pb-0">
        {TABS.map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all -mb-px ${
              activeTab === t
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-[#8899aa] hover:text-white'
            }`}>
            {t}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'Overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoCard title="Transaction" icon={<TrendingUp className="w-4 h-4 text-blue-400" />}>
            {caseData.raw_transaction ? (
              Object.entries(caseData.raw_transaction).map(([k, v]) => (
                <Row key={k} label={k.replace(/_/g, ' ')} value={String(v)} />
              ))
            ) : <div className="text-[#4a5568] text-xs">No raw transaction</div>}
          </InfoCard>
          <InfoCard title="Pipeline Status" icon={<Shield className="w-4 h-4 text-green-400" />}>
            {[
              { label: 'Agent 1 — Ingestion', done: !!caseData.normalized },
              { label: 'Agent 2 — Risk Score', done: !!caseData.risk_assessment },
              { label: 'Agent 3 — Narrative', done: !!caseData.narrative },
              { label: 'Agent 4 — Compliance', done: !!caseData.compliance },
              { label: 'Agent 5 — Audit Hash', done: !!caseData.audit },
              { label: 'Agent 6 — Human Review', done: !!caseData.analyst_approved_by },
            ].map(({ label, done }) => (
              <div key={label} className="flex items-center gap-2 py-1">
                {done
                  ? <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
                  : <div className="w-3.5 h-3.5 rounded-full border border-[#4a5568] flex-shrink-0" />}
                <span className={`text-xs ${done ? 'text-white' : 'text-[#4a5568]'}`}>{label}</span>
              </div>
            ))}
          </InfoCard>
          {caseData.error_log.length > 0 && (
            <InfoCard title={`Errors (${caseData.error_log.length})`} icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}>
              {caseData.error_log.map((e, i) => (
                <div key={i} className="py-1.5 border-b border-white/5 last:border-0">
                  <div className="text-xs text-amber-400 font-medium">{e.agent}</div>
                  <div className="text-xs text-[#8899aa] mt-0.5">{e.error}</div>
                </div>
              ))}
            </InfoCard>
          )}
        </div>
      )}

      {activeTab === 'Risk Analysis' && (
        <div className="space-y-4">
          {!risk ? (
            <NoData msg="Run the pipeline to see risk analysis" />
          ) : (
            <>
              <div className="grid grid-cols-3 gap-4">
                <div className="glass rounded-xl p-5 text-center bg-gradient-to-br from-blue-600/20 to-blue-600/5">
                  <div className="text-4xl font-bold text-white mb-1">{(risk.risk_score * 100).toFixed(0)}<span className="text-lg text-[#8899aa]">%</span></div>
                  <div className="text-xs text-[#8899aa]">Risk Score</div>
                </div>
                <div className="glass rounded-xl p-5 text-center">
                  <div className="mb-2"><RiskBadge tier={risk.risk_tier} size="lg" /></div>
                  <div className="text-xs text-[#8899aa]">Risk Tier</div>
                </div>
                <div className="glass rounded-xl p-5 text-center">
                  <div className="text-sm font-bold text-purple-400 mb-1 capitalize">{risk.matched_typology}</div>
                  <div className="text-xs text-[#8899aa]">Matched Typology</div>
                  <div className="text-xs text-[#4a5568] mt-1">{(risk.typology_confidence * 100).toFixed(0)}% conf.</div>
                </div>
              </div>

              {/* SHAP Chart */}
              {Object.keys(risk.shap_values).length > 0 && (
                <div className="glass rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4">SHAP Feature Importance</h3>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={Object.entries(risk.shap_values).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: Math.abs(v), raw: v }))} layout="vertical">
                      <XAxis type="number" tick={{ fill: '#4a5568', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="name" width={160} tick={{ fill: '#8899aa', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ background: '#0d1e35', border: '1px solid #1a3050', borderRadius: 8 }}
                        labelStyle={{ color: '#e2e8f0' }}
                        formatter={(v: number, _: string, props: {payload?: {raw: number}}) => [props.payload?.raw?.toFixed(4) ?? v, 'SHAP Impact']}
                      />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {Object.entries(risk.shap_values).map(([, v], i) => (
                          <Cell key={i} fill={v > 0 ? '#3b82f6' : '#ef4444'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="flex gap-4 mt-2">
                    <div className="flex items-center gap-1.5 text-xs text-[#8899aa]"><span className="w-3 h-2 rounded bg-blue-500 inline-block" /> Increases risk</div>
                    <div className="flex items-center gap-1.5 text-xs text-[#8899aa]"><span className="w-3 h-2 rounded bg-red-500 inline-block" /> Decreases risk</div>
                  </div>
                </div>
              )}

              {/* Signals */}
              {risk.signals.length > 0 && (
                <div className="glass rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4">Risk Signals Detected</h3>
                  <div className="space-y-3">
                    {risk.signals.map((sig, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 bg-[#0a1628] rounded-lg border border-white/5">
                        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <div className="text-xs font-semibold text-amber-400 capitalize">{sig.signal_type}</div>
                          <div className="text-xs text-[#8899aa] mt-0.5">{sig.description}</div>
                          <div className="text-[10px] text-[#4a5568] mt-1">Confidence: {(sig.confidence * 100).toFixed(0)}%</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'SAR Report' && (
        <div className="space-y-4">
          {!narrative ? (
            <NoData msg="Generate the narrative to view the FIU-IND STR report" action={
              <button onClick={generateNarrative} disabled={genNarrative}
                className="mt-4 flex items-center gap-2 px-4 py-2 bg-purple-600/20 text-purple-400 border border-purple-500/30 rounded-xl text-sm hover:bg-purple-600/30 transition-all mx-auto">
                {genNarrative ? <Loader className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                Generate Narrative
              </button>
            } />
          ) : (
            <>
              <div className="flex justify-end">
                <button onClick={downloadPDF}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600/20 hover:bg-green-600/30 text-green-400 border border-green-500/30 rounded-xl text-sm font-semibold transition-all">
                  <Download className="w-4 h-4" /> Download PDF Report
                </button>
              </div>

              <div ref={reportRef} className="space-y-4">
                <div className="glass rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/5">
                    <Shield className="w-5 h-5 text-blue-400" />
                    <span className="font-bold text-white">FIU-IND Suspicious Transaction Report (STR)</span>
                    <span className="ml-auto mono text-xs text-[#4a5568]">{id}</span>
                  </div>

                  <SARSection title="Part 1 — Report Details">
                    <Row label="Date of Sending" value={narrative.part1_report_details?.date_of_sending ?? '—'} />
                    <Row label="Replacement Report" value={narrative.part1_report_details?.is_replacement ? 'Yes' : 'No'} />
                  </SARSection>

                  <SARSection title="Part 2 — Principal Officer">
                    {Object.entries(narrative.part2_principal_officer ?? {}).map(([k, v]) => (
                      <Row key={k} label={k.replace(/_/g, ' ')} value={String(v)} />
                    ))}
                  </SARSection>

                  <SARSection title="Part 3 — Reporting Branch">
                    {Object.entries(narrative.part3_reporting_branch ?? {}).map(([k, v]) => (
                      <Row key={k} label={k.replace(/_/g, ' ')} value={String(v)} />
                    ))}
                  </SARSection>

                  <SARSection title="Part 4 — Linked Individuals">
                    {narrative.part4_linked_individuals?.length ? narrative.part4_linked_individuals.map((ind, i) => (
                      <Row key={i} label={`Individual ${i + 1}`} value={`${ind.name} (ID: ${ind.customer_id})`} />
                    )) : <div className="text-xs text-[#4a5568]">None</div>}
                  </SARSection>

                  <SARSection title="Part 6 — Linked Accounts">
                    {narrative.part6_linked_accounts?.length ? narrative.part6_linked_accounts.map((acc, i) => (
                      <Row key={i} label={acc.account_holder_name} value={acc.account_number} mono />
                    )) : <div className="text-xs text-[#4a5568]">None</div>}
                  </SARSection>

                  <SARSection title="Part 7 — Grounds of Suspicion">
                    <div className="mb-3">
                      <div className="text-[10px] text-[#4a5568] uppercase mb-1.5">Reasons</div>
                      {narrative.part7_suspicion_details?.reasons_for_suspicion?.map((r, i) => (
                        <div key={i} className="flex gap-2 text-xs text-[#8899aa] py-0.5">
                          <span className="text-blue-400 flex-shrink-0">•</span>{r}
                        </div>
                      ))}
                    </div>
                    <div>
                      <div className="text-[10px] text-[#4a5568] uppercase mb-1.5">Narrative Sequence</div>
                      <div className="text-xs text-[#8899aa] leading-relaxed whitespace-pre-wrap bg-[#0a1628] p-4 rounded-lg border border-white/5">
                        {narrative.part7_suspicion_details?.grounds_of_suspicion}
                      </div>
                    </div>
                  </SARSection>

                  <SARSection title="Part 8 — Action Taken">
                    <Row label="Under Investigation" value={narrative.part8_action_taken?.under_investigation ? 'Yes' : 'No'} />
                    <Row label="Agency Details" value={narrative.part8_action_taken?.agency_details || 'None'} />
                  </SARSection>

                  <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
                    <div className="text-[10px] text-[#4a5568]">Generated: {new Date(narrative.generation_timestamp).toLocaleString()}</div>
                    <div className="text-[10px] text-green-400">✓ FIU-IND SBA01-04 Format</div>
                  </div>
                </div>

                {/* Analyst approval */}
                {caseData.status !== 'filed' && caseData.status !== 'dismissed' && (
                  <div className="glass rounded-xl p-6">
                    <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                      <User className="w-4 h-4 text-blue-400" /> Analyst Review
                    </h3>
                    <div className="flex gap-3">
                      <input value={analystName} onChange={e => setAnalystName(e.target.value)}
                        placeholder="Analyst name"
                        className="flex-1 px-3 py-2 bg-[#0a1628] border border-white/5 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500" />
                      <button onClick={approve} disabled={approving || !analystName}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 rounded-lg text-white text-sm font-semibold transition-all">
                        {approving ? <Loader className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                        Approve & File
                      </button>
                      <button onClick={() => sarApi.dismissCase(id).then(load)}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 rounded-lg text-sm font-semibold transition-all">
                        <XCircle className="w-4 h-4" /> Dismiss
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'Compliance' && (
        <div className="glass rounded-xl p-6 space-y-4">
          {!compliance ? (
            <NoData msg="Compliance run after pipeline execution" />
          ) : (
            <>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <CompliancePill label="BSA Compliant" ok={compliance.bsa_compliant} />
                <CompliancePill label="All Fields" ok={compliance.all_fields_complete} />
                <CompliancePill label="FinCEN Format" ok={compliance.fincen_format_valid} />
              </div>
              <h3 className="text-sm font-semibold text-white">Compliance Issues</h3>
              {compliance.compliance_issues.length === 0 ? (
                <div className="flex items-center gap-2 text-green-400 text-sm py-3">
                  <CheckCircle className="w-5 h-5" />
                  All 8 AML compliance rules passed
                </div>
              ) : (
                <div className="space-y-2">
                  {compliance.compliance_issues.map((issue, i) => (
                    <div key={i} className="flex gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-lg">
                      <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                      <span className="text-xs text-[#8899aa]">{issue}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'Audit Trail' && (
        <div className="space-y-4">
          {caseData.audit_trail.length === 0 ? (
            <NoData msg="No audit events yet" />
          ) : (
            <div className="glass rounded-xl overflow-hidden">
              <div className="divide-y divide-white/5">
                {caseData.audit_trail.map((entry, i) => (
                  <div key={i} className="px-6 py-4 flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-xs font-bold text-blue-400 flex-shrink-0">{i + 1}</div>
                      {i < caseData.audit_trail.length - 1 && <div className="w-px flex-1 bg-white/5 mt-2" />}
                    </div>
                    <div className="pb-4 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-white">{entry.agent}</span>
                        <span className="text-[10px] text-[#4a5568] mono">{(entry.confidence * 100).toFixed(0)}% confidence</span>
                      </div>
                      <div className="text-xs text-[#8899aa]">{entry.action}</div>
                      <div className="flex items-center gap-1 text-[10px] text-[#4a5568] mt-1.5">
                        <Clock className="w-3 h-3" />{new Date(entry.timestamp).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {audit && (
            <div className="glass rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Lock className="w-4 h-4 text-green-400" />
                <span className="text-sm font-semibold text-white">Immutable SHA256 Hash</span>
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 mono text-xs text-green-400 bg-[#0a1628] p-3 rounded-lg border border-white/5 break-all">
                  {audit.immutable_hash}
                </code>
                <button onClick={() => copyHash(audit.immutable_hash)}
                  className="p-2 glass glass-hover rounded-lg text-[#4a5568] hover:text-white">
                  {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <div className="text-[10px] text-[#4a5568] mt-2">Immutable — cannot be modified or deleted</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---- Sub-components ----
function InfoCard({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="glass rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
        {icon}
        <span className="text-sm font-semibold text-white">{title}</span>
      </div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}
function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1">
      <span className="text-[10px] text-[#4a5568] uppercase tracking-wide flex-shrink-0 capitalize">{label}</span>
      <span className={`text-xs text-right ${mono ? 'mono text-blue-400' : 'text-[#8899aa]'}`}>{value}</span>
    </div>
  );
}
function SARSection({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="mb-4">
      <button onClick={() => setOpen(o => !o)}
        className="flex items-center justify-between w-full py-2 text-left">
        <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">{title}</span>
        {open ? <ChevronUp className="w-3 h-3 text-[#4a5568]" /> : <ChevronDown className="w-3 h-3 text-[#4a5568]" />}
      </button>
      {open && <div className="mt-2 space-y-1 pl-2 border-l border-white/5">{children}</div>}
    </div>
  );
}
function CompliancePill({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className={`flex items-center gap-2 p-3 rounded-lg border text-xs font-semibold ${
      ok ? 'border-green-500/30 bg-green-500/5 text-green-400' : 'border-red-500/30 bg-red-500/5 text-red-400'
    }`}>
      {ok ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
      {label}
    </div>
  );
}
function NoData({ msg, action }: { msg: string; action?: React.ReactNode }) {
  return (
    <div className="glass rounded-xl p-12 text-center">
      <div className="text-[#4a5568] text-sm">{msg}</div>
      {action}
    </div>
  );
}
