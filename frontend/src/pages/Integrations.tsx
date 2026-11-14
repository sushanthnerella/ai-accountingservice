import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { Download, RefreshCw, CheckCircle2, FileCode, Layers } from 'lucide-react';

export const Integrations: React.FC = () => {
  const { currentClient } = useWorkspaceStore();
  const [zohoStatus, setZohoStatus] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  const downloadBlob = async (endpoint: string, defaultFilename: string) => {
    try {
      setDownloading(defaultFilename);
      const res = await apiClient.get(endpoint, { responseType: 'blob' });
      const blob = new Blob([res.data], { type: 'application/xml' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = defaultFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download Tally XML', err);
      alert('Error downloading XML package. Please ensure an active client workspace is selected.');
    } finally {
      setDownloading(null);
    }
  };

  const handleSyncZoho = async () => {
    try {
      const res = await apiClient.post('/integrations/zoho/sync');
      setZohoStatus(res.data.data.message);
    } catch (err: any) {
      setZohoStatus(err.response?.data?.detail?.message || 'Sync failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200">
        <h1 className="text-xl font-bold text-slate-900">External Accounting Master Sync</h1>
        <p className="text-xs text-slate-500 mt-1">Export balanced, verified vouchers to TallyPrime and Zoho Books.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
          <div className="flex items-center space-x-2">
            <FileCode className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-800">TallyPrime Desktop Integration</h3>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Generate and download TDL-compliant XML packages wrapped in standard &lt;ENVELOPE&gt; tags with idempotency GUIDs. Ready to import directly into TallyPrime (Alt+O &gt; Import &gt; Transactions).
          </p>

          <div className="flex flex-wrap gap-2 pt-2">
            <button
              onClick={() => downloadBlob('/integrations/tally/export-xml', `Tally_Package_${currentClient?.id || 'client'}.xml`)}
              disabled={!!downloading}
              className="flex items-center space-x-2 px-3 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-500 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>{downloading?.includes('Package') ? 'Generating...' : 'Download Full Package'}</span>
            </button>

            <button
              onClick={() => downloadBlob('/integrations/tally/export-masters-xml', `Masters_${currentClient?.id || 'client'}.xml`)}
              disabled={!!downloading}
              className="flex items-center space-x-2 px-3 py-2 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-200 disabled:opacity-50 border border-slate-300"
            >
              <Layers className="w-4 h-4" />
              <span>Masters.xml</span>
            </button>

            <button
              onClick={() => downloadBlob('/integrations/tally/export-vouchers-xml', `Vouchers_${currentClient?.id || 'client'}.xml`)}
              disabled={!!downloading}
              className="flex items-center space-x-2 px-3 py-2 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-200 disabled:opacity-50 border border-slate-300"
            >
              <FileCode className="w-4 h-4" />
              <span>Vouchers.xml</span>
            </button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-5 h-5 text-emerald-600" />
            <h3 className="text-base font-bold text-slate-800">Zoho Books Cloud REST Sync</h3>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Bi-directional synchronization of approved sales and purchase bills via OAuth2 REST API with automatic client party mapping.
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
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{zohoStatus}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
