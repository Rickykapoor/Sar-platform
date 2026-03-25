const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SARCase {
  case_id: string;
  status: 'pending' | 'in_review' | 'filed' | 'dismissed' | 'approved';
  raw_transaction?: Record<string, unknown>;
  normalized?: NormalizedCase;
  risk_assessment?: RiskAssessment;
  narrative?: SARNarrative;
  compliance?: ComplianceResult;
  audit?: AuditRecord;
  analyst_approved_by?: string;
  final_filed_timestamp?: string;
  audit_trail: AuditEntry[];
  error_log: ErrorEntry[];
}

export interface NormalizedCase {
  case_id: string;
  transactions: Transaction[];
  subject_name: string;
  subject_account_ids: string[];
  date_range_start: string;
  date_range_end: string;
  total_amount_usd: number;
  ingestion_timestamp: string;
  presidio_masked: boolean;
}

export interface Transaction {
  transaction_id: string;
  account_id: string;
  counterparty_account_id: string;
  amount_usd: number;
  timestamp: string;
  transaction_type: string;
  channel: string;
  geography: string;
}

export interface RiskAssessment {
  case_id: string;
  risk_tier: 'green' | 'amber' | 'red' | 'critical';
  risk_score: number;
  matched_typology: string;
  typology_confidence: number;
  signals: RiskSignal[];
  shap_values: Record<string, number>;
  neo4j_pattern_found: boolean;
  assessment_timestamp: string;
}

export interface RiskSignal {
  signal_type: string;
  description: string;
  confidence: number;
  supporting_transaction_ids: string[];
}

export interface SARNarrative {
  case_id: string;
  narrative_body?: string;
  summary?: string;
  subject_info?: string;
  part1_report_details: { date_of_sending: string; is_replacement: boolean; date_of_original_report?: string };
  part2_principal_officer: Record<string, string>;
  part3_reporting_branch: Record<string, string>;
  part4_linked_individuals: { name: string; customer_id: string }[];
  part5_linked_entities: { name: string; customer_id: string }[];
  part6_linked_accounts: { account_number: string; account_holder_name: string }[];
  part7_suspicion_details: { reasons_for_suspicion: string[]; grounds_of_suspicion: string };
  part8_action_taken: { under_investigation: boolean; agency_details: string };
  generation_timestamp: string;
}

export interface ComplianceResult {
  case_id: string;
  bsa_compliant: boolean;
  all_fields_complete: boolean;
  fincen_format_valid: boolean;
  compliance_issues: string[];
  validated_timestamp: string;
}

export interface AuditRecord {
  case_id: string;
  neo4j_audit_node_id: string;
  agent_timeline: AuditEntry[];
  shap_explanations: Record<string, number>;
  data_sources_cited: string[];
  audit_timestamp: string;
  immutable_hash: string;
}

export interface AuditEntry {
  agent: string;
  action: string;
  confidence: number;
  timestamp: string;
}

export interface ErrorEntry {
  agent: string;
  error: string;
  timestamp: string;
}

export interface CaseSummary {
  case_id: string;
  status: string;
  risk_tier: string;
  subject: string;
  last_updated: string;
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export const sarApi = {
  health: () => api<{ status: string; timestamp: string }>('/health'),
  getCases: () => api<CaseSummary[]>('/cases'),
  getCase: (id: string) => api<SARCase>(`/case/${id}`),
  submitTransaction: (payload: Record<string, unknown>) =>
    api<{ case_id: string; status: string }>('/submit-transaction', { method: 'POST', body: JSON.stringify(payload) }),
  runPipeline: (id: string) => api<{ status: string; risk_tier: string }>(`/case/${id}/run-pipeline`, { method: 'POST' }),
  getPipelineStatus: (id: string) => api<Record<string, unknown>>(`/case/${id}/pipeline-status`),
  generateNarrative: (id: string) => api<{ narrative_body: string; narrative: SARNarrative }>(`/case/${id}/generate-narrative`, { method: 'POST' }),
  approveCase: (id: string, analystName: string) =>
    api<{ status: string; case_status: string }>(`/case/${id}/approve`, { method: 'POST', body: JSON.stringify({ analyst_name: analystName }) }),
  dismissCase: (id: string) => api<{ status: string }>(`/case/${id}/dismiss`, { method: 'POST' }),
  getGraph: (id: string) => api<{ nodes: unknown[]; edges: unknown[] }>(`/case/${id}/graph`),
  simulateScenario: (scenario: 'structuring' | 'layering' | 'smurfing') =>
    api<{ case_id: string; scenario_type: string; raw_transaction: Record<string, unknown> }>(`/demo/simulate/${scenario}`, { method: 'POST' }),
};
