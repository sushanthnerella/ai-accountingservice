import React from 'react';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { Link } from 'react-router-dom';
import { UploadCloud } from 'lucide-react';

export const FreelancerWorkspace: React.FC = () => {
  const { currentOrg } = useWorkspaceStore();
  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900">Freelancer Workspace</h1>
        <p className="text-sm text-slate-500">Sec 44ADA Presumptive Taxation Intelligence</p>
      </div>
      <div className="bg-slate-900 text-white p-6 rounded-xl flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold">Document Processing Gateway</h3>
          <p className="text-xs text-slate-300 mt-1">Upload client invoices and bank statements for reconciliation.</p>
        </div>
        <Link to="/documents/upload" className="px-4 py-2 bg-indigo-600 rounded-lg text-sm font-semibold flex items-center space-x-2">
          <UploadCloud className="w-4 h-4" />
          <span>Upload</span>
        </Link>
      </div>
    </div>
  );
};
