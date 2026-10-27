import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { WorkspacePage } from './pages/WorkspacePage';
import { AuditPage } from './pages/AuditPage';
import { Shield, LayoutDashboard, History, ExternalLink } from 'lucide-react';

const Navbar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50 px-6 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-sm tracking-tight text-slate-100">QForge</span>
            <span className="ml-1.5 text-[10px] font-semibold text-emerald-400 bg-emerald-950/80 border border-emerald-800/80 px-1.5 py-0.5 rounded">
              ENTERPRISE v1.0
            </span>
          </div>
        </div>

        <nav className="flex items-center gap-1">
          <Link
            to="/"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition ${
              isActive('/')
                ? 'bg-slate-800 text-slate-100 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Workspace</span>
          </Link>

          <Link
            to="/audit"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition ${
              isActive('/audit')
                ? 'bg-slate-800 text-slate-100 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Audit Trail</span>
          </Link>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <span>FastAPI Docs</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </header>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="h-full w-full bg-slate-950 flex flex-col font-sans overflow-hidden">
        <Navbar />
        <main className="flex-1 min-h-0 overflow-hidden">
          <Routes>
            <Route path="/" element={<WorkspacePage />} />
            <Route path="/audit" element={<AuditPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
