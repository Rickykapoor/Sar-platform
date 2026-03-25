'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, FileText, Play, Shield, ExternalLink } from 'lucide-react';

const NAV = [
  { href: '/app', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { href: '/app/cases', icon: FileText, label: 'All Cases' },
  { href: '/app/demo', icon: Play, label: 'Demo Center' },
];

export function Sidebar() {
  const pathname = usePathname();
  const isActive = (href: string, exact?: boolean) =>
    exact ? pathname === href : pathname === href || pathname.startsWith(href + '/');

  return (
    <aside className="sidebar w-56 flex-shrink-0 flex flex-col">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-white/5">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
            <Shield className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white leading-tight">SAR Platform</div>
            <div className="text-[10px] text-zinc-600 leading-tight">AML Intelligence</div>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="px-4 py-3 border-b border-white/5">
        <BackendStatus />
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        <div className="text-[10px] text-zinc-600 px-2 mb-2 uppercase tracking-widest font-semibold">Navigation</div>
        {NAV.map(({ href, icon: Icon, label, exact }) => (
          <Link key={href} href={href}
            className={`nav-item ${isActive(href, exact) ? 'active' : ''}`}>
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span>{label}</span>
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-white/5 space-y-2">
        <Link href="/" className="nav-item text-xs">
          <ExternalLink className="w-3.5 h-3.5" />
          Landing Page
        </Link>
        <div className="px-2 pt-2 space-y-1.5">
          {[['XGBoost + SHAP', 'blue'], ['Groq LLM', 'purple'], ['8 AML Rules', 'green']].map(([label, color]) => (
            <div key={label} className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full bg-${color}-400`} style={{flexShrink:0}} />
              <span className="text-[11px] text-zinc-500">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

function BackendStatus() {
  const [online, setOnline] = React.useState<boolean | null>(null);
  React.useEffect(() => {
    fetch('http://localhost:8000/health').then(() => setOnline(true)).catch(() => setOnline(false));
  }, []);
  return (
    <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-zinc-900 border border-white/5">
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
        online === null ? 'bg-zinc-600' : online ? 'bg-green-400 pulse-ring' : 'bg-red-400'
      }`} />
      <span className={`text-[11px] font-medium ${
        online === null ? 'text-zinc-600' : online ? 'text-green-400' : 'text-red-400'
      }`}>
        {online === null ? 'Checking…' : online ? 'Backend Online' : 'Backend Offline'}
      </span>
    </div>
  );
}

import React from 'react';
