import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { Download, RefreshCw, CheckCircle2 } from 'lucide-react';

export const Integrations: React.FC = () => {
  const { currentClient } = useWorkspaceStore();
  const [zohoStatus, setZohoStatus] = useState<string | null>(null);

  const handleDownloadTallyXML = async () => {
    window.open(`/api/v1/integrations/tally/export-xml`, '_blank');
  };

  const handleSyncZoho = async () => {
    const res = await apiClient.post('/integrations/zoho/sync');
    setZohoStatus(res.data.data.message);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200">
        <h1 className="text-xl font-bold text-slate-900">External Accounting Master Sync</h1>
        <p className="text-xs text-slate-500 mt-1">Export balanced, verified vouchers to TallyPrime and Zoho Books.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
          <h3 className="text-base font-bold text-slate-800">TallyPrime Desktop Integration</h3>
          <p className="text-xs text-slate-600">
            Generate and download TDL-compliant XML voucher import packages with idempotency GUIDs.
          </p>
          <button
            onClick={handleDownloadTallyXML}
            className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-500"
          >
            <Download className="w-4 h-4" />
            <span>Download Tally XML Package</span>
          </button>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
          <h3 className="text-base font-bold text-slate-800">Zoho Books Cloud REST Sync</h3>
          <p className="text-xs text-slate-600">
            Bi-directional synchronization of approved sales and purchase bills via OAuth2 REST API.
          </p>
          <button
            onClick={handleSyncZoho}
            className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-semibold hover:bg-emerald-500"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Sync Approved Vouchers</span>
          </button>
          {zohoStatus && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{zohoStatus}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
