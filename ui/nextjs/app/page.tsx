'use client';
import Link from 'next/link';
import { Shield, ArrowRight, Zap, Lock, BarChart2, FileText, CheckCircle } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/90 backdrop-blur-xl">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
            <Shield className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-semibold text-sm text-white">SAR Platform</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/app" className="text-sm text-zinc-400 hover:text-white transition-colors">Dashboard</Link>
          <Link href="/app/demo" className="text-sm bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors">
            Try Demo →
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-24 px-6 text-center relative">
        {/* Blue glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-600/10 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-400 text-xs font-semibold mb-8 animate-fade-up">
            <Zap className="w-3 h-3" />
            India&apos;s first AI-native AML platform
          </div>
          <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight mb-6 animate-fade-up-1 leading-none">
            File better SARs,<br />
            <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">10× faster.</span>
          </h1>
          <p className="text-lg text-zinc-400 max-w-2xl mx-auto mb-10 animate-fade-up-2 leading-relaxed">
            End-to-end Suspicious Activity Report automation. XGBoost risk scoring, Groq AI narrative generation, FIU-IND STR format, downloadable PDF — in one platform.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center animate-fade-up-3">
            <Link href="/app/demo" className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-8 py-3.5 rounded-xl text-base transition-all hover:shadow-[0_0_30px_rgba(59,130,246,0.4)]">
              <Zap className="w-4 h-4" />
              Run Live Demo
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/app" className="inline-flex items-center justify-center gap-2 border border-white/10 hover:border-white/20 hover:bg-white/5 text-zinc-300 hover:text-white font-medium px-8 py-3.5 rounded-xl text-base transition-all">
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="px-6 pb-20">
        <div className="max-w-3xl mx-auto grid grid-cols-3 gap-6">
          {[
            { n: '6', label: 'AI Agents' },
            { n: '8', label: 'AML Rules' },
            { n: '<30s', label: 'To SAR Report' },
          ].map(({ n, label }) => (
            <div key={label} className="text-center p-6 rounded-2xl bg-white/3 border border-white/5">
              <div className="text-3xl font-bold text-white mb-1">{n}</div>
              <div className="text-sm text-zinc-500">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-6 pb-24 max-w-6xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold text-white mb-3">Built for compliance teams</h2>
          <p className="text-zinc-400 max-w-xl mx-auto">Production-grade AML intelligence with explainable AI and regulatory-ready output.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: <BarChart2 className="w-5 h-5 text-blue-400" />, title: 'XGBoost Risk Scoring', desc: 'ML model trained on 6 AML typologies (structuring, layering, smurfing, etc.) with SHAP explainability for every prediction.', color: 'blue' },
            { icon: <FileText className="w-5 h-5 text-purple-400" />, title: 'Groq AI Narrative', desc: 'Llama 3 generates a complete 8-part FIU-IND STR. BSA-compliant, structured, and downloadable as PDF.', color: 'purple' },
            { icon: <Lock className="w-5 h-5 text-green-400" />, title: 'Immutable Audit Trail', desc: 'SHA256-hashed case record. 6-agent timeline with timestamps, confidence scores, and tamper detection.', color: 'green' },
            { icon: <Shield className="w-5 h-5 text-amber-400" />, title: '8 AML Compliance Rules', desc: 'FinCEN 314(a), BSA threshold, structuring, geography, round numbers, dormant accounts — all automated.', color: 'amber' },
          ].map(f => (
            <div key={f.title} className="group p-6 rounded-2xl bg-zinc-950 border border-white/5 hover:border-white/10 hover:bg-zinc-900 transition-all duration-200 cursor-default">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 border border-white/5 ${
                f.color === 'blue' ? 'bg-blue-500/10' : f.color === 'purple' ? 'bg-purple-500/10' : f.color === 'green' ? 'bg-green-500/10' : 'bg-amber-500/10'
              }`}>
                {f.icon}
              </div>
              <h3 className="font-semibold text-white mb-2 text-base">{f.title}</h3>
              <p className="text-sm text-zinc-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Demo CTA */}
      <section className="px-6 pb-24 max-w-6xl mx-auto">
        <div className="rounded-2xl bg-gradient-to-br from-zinc-950 to-zinc-900 border border-white/8 p-10 md:p-14">
          <div className="flex flex-col lg:flex-row gap-12 items-center">
            <div className="flex-1">
              <div className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-3">Judge Demo Center</div>
              <h2 className="text-3xl font-bold text-white mb-4">3 real AML scenarios,<br/>ready in one click.</h2>
              <p className="text-zinc-400 text-sm mb-7 leading-relaxed max-w-lg">
                Each demo runs the full pipeline in seconds — risk scoring, Groq AI narrative, compliance checks, and a downloadable PDF report.
              </p>
              <div className="space-y-2.5 mb-8">
                {['XGBoost risk score with SHAP explanation', 'Auto-generated FIU-IND STR (8 parts)', 'One-click PDF download', 'Immutable SHA256 audit hash'].map(item => (
                  <div key={item} className="flex items-center gap-2.5 text-sm text-zinc-300">
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                    {item}
                  </div>
                ))}
              </div>
              <Link href="/app/demo" className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-all">
                <Zap className="w-4 h-4" />
                Open Demo Center
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="flex-1 space-y-3 w-full">
              {[
                { tag: 'Structuring', color: 'red' as const, desc: 'ACC-9812 splits $49,000 into 5 transfers of $9,800 — all below the BSA $10k threshold.' },
                { tag: 'Layering', color: 'blue' as const, desc: '$180,000 through Cayman Islands + Panama via crypto merchant.' },
                { tag: 'Smurfing', color: 'amber' as const, desc: '8 accounts depositing round amounts ($2k–$5k) to a central account on the same day.' },
              ].map(s => (
                <Link key={s.tag} href="/app/demo" className="flex items-center gap-4 p-4 rounded-xl bg-black border border-white/5 hover:border-white/10 hover:bg-zinc-950 transition-all group">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full border flex-shrink-0 ${
                    s.color === 'red' ? 'text-red-400 bg-red-400/8 border-red-400/20' :
                    s.color === 'blue' ? 'text-purple-400 bg-purple-400/8 border-purple-400/20' :
                    'text-amber-400 bg-amber-400/8 border-amber-400/20'
                  }`}>{s.tag}</span>
                  <p className="text-sm text-zinc-400 flex-1">{s.desc}</p>
                  <ArrowRight className="w-4 h-4 text-zinc-700 group-hover:text-white transition-colors flex-shrink-0" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Report Generation Workflow */}
      <section className="px-6 pb-24 max-w-5xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold text-white mb-3">Automated SAR Generation Workflow</h2>
          <p className="text-zinc-400 max-w-2xl mx-auto">From raw transaction to a regulatory-ready PDF report in under 30 seconds.</p>
        </div>
        
        <div className="relative border-l border-white/10 ml-4 md:ml-10 space-y-8">
          {[
            { tag: '01', title: 'Data Ingestion & Normalization', desc: 'Raw banking vectors are synthesized into a standard JSON schema. Identifies sender, receiver, amounts, and flags offshore routing.', icon: <Zap className="w-5 h-5 text-blue-400" /> },
            { tag: '02', title: 'XGBoost Risk Scoring', desc: 'Machine learning model evaluates the transaction against 6 AML typologies (Structuring, Layering, etc.) and outputs a risk score with SHAP feature importance.', icon: <BarChart2 className="w-5 h-5 text-purple-400" /> },
            { tag: '03', title: 'Groq AI Narrative Generation', desc: 'Llama 3 processes the transaction facts and risk signals to author a comprehensive, human-readable 8-part FIU-IND Suspicious Transaction Report.', icon: <FileText className="w-5 h-5 text-cyan-400" /> },
            { tag: '04', title: 'AML Compliance Check', desc: 'Rule-based engine verifies the generated narrative against strict FinCEN/BSA guidelines, ensuring no mandatory fields are missing.', icon: <Shield className="w-5 h-5 text-amber-400" /> },
            { tag: '05', title: 'Immutable Audit Hashing', desc: 'The entire case state, including ML models and AI outputs, is cryptographically hashed (SHA256) to ensure tamper-proof regulatory compliance.', icon: <Lock className="w-5 h-5 text-green-400" /> },
            { tag: '06', title: 'Analyst Review & PDF Download', desc: 'Compliance officer reviews the fully assembled case, approves the SAR, and exports a text-based, formatted PDF document.', icon: <CheckCircle className="w-5 h-5 text-red-400" /> },
          ].map((s) => (
            <div key={s.tag} className="relative pl-10 md:pl-16">
              <div className="absolute -left-6 top-1 w-12 h-12 bg-black border border-white/10 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(0,0,0,0.5)]">
                {s.icon}
              </div>
              <div className="bg-zinc-950 border border-white/5 p-6 rounded-2xl hover:border-white/10 transition-colors">
                <div className="text-xs font-mono font-semibold text-zinc-500 mb-2">STEP {s.tag}</div>
                <h3 className="text-lg font-bold text-white mb-2">{s.title}</h3>
                <p className="text-zinc-400 leading-relaxed text-sm">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 px-6 py-8 text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Shield className="w-4 h-4 text-zinc-700" />
          <span className="text-sm font-medium text-zinc-700">SAR Platform</span>
        </div>
        <p className="text-xs text-zinc-800">FIU-IND STR Compliant · XGBoost + Groq AI · Built for Indian Banks</p>
      </footer>
    </div>
  );
}
