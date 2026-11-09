import React from 'react';
import { NavLink } from 'react-router-dom';
import { useWorkspaceStore } from '../stores/workspaceStore';
import {
  LayoutDashboard,
  UploadCloud,
  Users,
  FileText,
  CheckSquare,
  GitCompare,
  BookOpen,
  FileSpreadsheet,
  RefreshCw,
  History,
  ShieldCheck
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { currentOrg } = useWorkspaceStore();
  const isCAFirm = currentOrg?.org_type === 'CA_FIRM';

  const navItems = [
    { to: '/', label: 'Workspace', icon: LayoutDashboard },
    ...(isCAFirm ? [{ to: '/clients', label: 'Client Portfolio', icon: Users }] : []),
    { to: '/documents/upload', label: 'Upload Documents', icon: UploadCloud },
    { to: '/documents', label: 'Document Queue', icon: FileText },
    { to: '/review', label: 'Extraction Review', icon: CheckSquare },
    { to: '/reconciliation', label: 'Reconciliation', icon: GitCompare },
    { to: '/ledgers', label: 'Double-Entry Ledgers', icon: BookOpen },
    { to: '/gst', label: 'GST Intelligence', icon: FileSpreadsheet },
    { to: '/integrations', label: 'Tally & Zoho Sync', icon: RefreshCw },
    { to: '/audit', label: 'Audit Trail', icon: History },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between">
      <div>
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <ShieldCheck className="w-7 h-7 text-indigo-400 mr-2.5" />
          <span className="text-white font-bold tracking-tight text-base">AccounTech AI</span>
        </div>
        <nav className="p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center px-3.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                  isActive ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <item.icon className="w-4 h-4 mr-3" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500">
        <div>Complete Release (Phases 1-5)</div>
        <div className="text-[10px] text-slate-600 mt-0.5">Numeric(18, 4) Invariant Guard</div>
      </div>
    </aside>
  );
};
