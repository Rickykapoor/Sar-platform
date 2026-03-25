'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, FileText, Play, Shield, ExternalLink } from 'lucide-react';

const NAV = [
  { href: '/app', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { href: '/app/cases', icon: FileText, label: 'All Cases' },
  { href: '/app/demo', icon: Play, label: 'Demo Center' },
];

function BackendPill() {
  const [s, setS] = useState<'checking'|'online'|'offline'>('checking');
  useEffect(() => {
    fetch('http://localhost:8000/health').then(() => setS('online')).catch(() => setS('offline'));
  }, []);
  const clr = s === 'online' ? '#4ade80' : s === 'offline' ? '#f87171' : '#52525b';
  return (
    <div style={{ background: '#0d0d0d', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, padding: '7px 12px', display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: clr, flexShrink: 0 }} />
      <span style={{ fontSize: 11, fontWeight: 500, color: clr }}>
        {s === 'checking' ? 'Checking…' : s === 'online' ? 'Backend Online' : 'Backend Offline'}
      </span>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isActive = (href: string, exact?: boolean) =>
    exact ? pathname === href : pathname === href || pathname.startsWith(href + '/');

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#000', overflow: 'hidden' }}>
      {/* Sidebar */}
      <aside className="sidebar-bg" style={{ width: 220, flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
        {/* Logo */}
        <div style={{ padding: '18px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 28, height: 28, borderRadius: 8, background: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Shield style={{ width: 14, height: 14, color: '#fff' }} />
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>SAR Platform</div>
              <div style={{ fontSize: 10, color: '#52525b' }}>AML Intelligence</div>
            </div>
          </div>
        </div>

        {/* Status */}
        <div style={{ padding: '10px 14px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <BackendPill />
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '14px 10px' }}>
          <div style={{ fontSize: 10, color: '#3f3f46', padding: '0 8px', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>Menu</div>
          {NAV.map(({ href, icon: Icon, label, exact }) => {
            const active = isActive(href, exact);
            return (
              <Link key={href} href={href} className={`nav-link ${active ? 'active' : ''}`} style={{ marginBottom: 2 }}>
                <Icon style={{ width: 15, height: 15, flexShrink: 0 }} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: '14px 14px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#52525b', textDecoration: 'none', marginBottom: 12 }}
            onMouseOver={e => { (e.currentTarget as HTMLElement).style.color = '#a1a1aa'; }}
            onMouseOut={e => { (e.currentTarget as HTMLElement).style.color = '#52525b'; }}>
            <ExternalLink style={{ width: 13, height: 13 }} />
            Back to Home
          </Link>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {[['XGBoost + SHAP', '#3b82f6'], ['Groq llama3', '#8b5cf6'], ['8 AML Rules', '#10b981']].map(([label, color]) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 5, height: 5, borderRadius: '50%', background: color, flexShrink: 0 }} />
                <span style={{ fontSize: 11, color: '#3f3f46' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, overflowY: 'auto', background: '#0d0d0d' }}>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
          {children}
        </div>
      </main>
    </div>
  );
}
