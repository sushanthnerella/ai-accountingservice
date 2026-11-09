import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { FileSpreadsheet } from 'lucide-react';

export const GSTSummary: React.FC = () => {
  const { currentOrg, currentClient } = useWorkspaceStore();

  const { data: summary } = useQuery({
    queryKey: ['gstr-3b-summary', currentOrg?.id, currentClient?.id],
    queryFn: async () => {
      if (!currentOrg || !currentClient) return null;
      const res = await apiClient.get('/gst/gstr-3b-summary');
      return res.data.data;
    },
    enabled: !!currentOrg && !!currentClient,
  });

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200">
        <h1 className="text-xl font-bold text-slate-900">GSTR-3B Monthly Computation</h1>
        <p className="text-xs text-slate-500 mt-1">Automated tax attribution with Section 17(5) blocked ITC filtering.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
          <h3 className="text-sm font-bold text-slate-800">Table 3.1: Outward Taxable Supplies</h3>
          <div className="space-y-1 text-xs font-mono">
            <div className="flex justify-between py-1 border-b">
              <span>Taxable Value:</span>
              <span className="font-semibold">₹ {summary?.table_3_1_outward_supplies?.taxable_amount || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span>Total Output Tax:</span>
              <span className="font-semibold">₹ {summary?.table_3_1_outward_supplies?.total_tax || '0.00'}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
          <h3 className="text-sm font-bold text-slate-800">Table 4: Eligible Input Tax Credit (ITC)</h3>
          <div className="space-y-1 text-xs font-mono">
            <div className="flex justify-between py-1 border-b">
              <span>Eligible ITC:</span>
              <span className="font-semibold text-emerald-700">₹ {summary?.table_4_eligible_itc?.total_itc || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b text-rose-700">
              <span>Blocked under Sec 17(5):</span>
              <span>₹ {summary?.table_4_blocked_itc_17_5?.cgst || '0.00'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
