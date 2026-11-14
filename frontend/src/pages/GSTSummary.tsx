import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { FileSpreadsheet, ShieldAlert, CheckCircle, Calculator } from 'lucide-react';

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
        <h1 className="text-xl font-bold text-slate-900">GSTR-3B Monthly Statutory Computation</h1>
        <p className="text-xs text-slate-500 mt-1">Automated tax attribution with Section 17(5) blocked ITC filtering and Reverse Charge (RCM).</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Table 3.1: Outward Supplies */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
          <div className="flex items-center space-x-2">
            <FileSpreadsheet className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-800">Table 3.1: Outward Taxable Supplies</h3>
          </div>
          <div className="space-y-1 text-xs font-mono">
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Taxable Value:</span>
              <span className="font-semibold">₹ {summary?.table_3_1_outward_supplies?.taxable_amount || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">CGST (Central Tax):</span>
              <span className="font-semibold">₹ {summary?.table_3_1_outward_supplies?.cgst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">SGST (State Tax):</span>
              <span className="font-semibold">₹ {summary?.table_3_1_outward_supplies?.sgst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">IGST (Integrated Tax):</span>
              <span className="font-semibold">₹ {summary?.table_3_1_outward_supplies?.igst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1.5 font-bold text-slate-900 bg-slate-50 px-2 rounded">
              <span>Total Outward Tax Liability:</span>
              <span>₹ {summary?.table_3_1_outward_supplies?.total_tax || '0.00'}</span>
            </div>
          </div>
        </div>

        {/* Table 4: Eligible & Ineligible ITC */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <h3 className="text-sm font-bold text-slate-800">Table 4: Input Tax Credit (ITC)</h3>
          </div>
          <div className="space-y-1 text-xs font-mono">
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Eligible CGST:</span>
              <span className="font-semibold text-emerald-700">₹ {summary?.table_4_eligible_itc?.cgst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Eligible SGST:</span>
              <span className="font-semibold text-emerald-700">₹ {summary?.table_4_eligible_itc?.sgst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Eligible IGST:</span>
              <span className="font-semibold text-emerald-700">₹ {summary?.table_4_eligible_itc?.igst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1.5 font-bold text-emerald-800 bg-emerald-50 px-2 rounded">
              <span>Total Eligible ITC:</span>
              <span>₹ {summary?.table_4_eligible_itc?.total_itc || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 text-rose-700 pt-2 border-t">
              <span className="flex items-center space-x-1">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Blocked under Sec 17(5):</span>
              </span>
              <span className="font-semibold">₹ {summary?.table_4_blocked_itc_17_5?.total_blocked_itc || '0.00'}</span>
            </div>
          </div>
        </div>

        {/* Table 3.1(d): RCM Supplies */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
          <h3 className="text-sm font-bold text-slate-800">Table 3.1(d): Reverse Charge (RCM) Inward Supplies</h3>
          <div className="space-y-1 text-xs font-mono">
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">RCM Taxable Value:</span>
              <span>₹ {summary?.table_3_1_d_inward_rcm_supplies?.taxable_amount || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">RCM Total Liability:</span>
              <span className="font-semibold text-amber-700">₹ {summary?.table_3_1_d_inward_rcm_supplies?.total_rcm_liability || '0.00'}</span>
            </div>
          </div>
        </div>

        {/* Net GST Payable */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
          <div className="flex items-center space-x-2">
            <Calculator className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-800">Net GST Cash Payable</h3>
          </div>
          <div className="space-y-1 text-xs font-mono">
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">CGST Payable:</span>
              <span className="font-semibold">₹ {summary?.net_gst_payable?.cgst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">SGST Payable:</span>
              <span className="font-semibold">₹ {summary?.net_gst_payable?.sgst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">IGST Payable:</span>
              <span className="font-semibold">₹ {summary?.net_gst_payable?.igst || '0.00'}</span>
            </div>
            <div className="flex justify-between py-1.5 font-bold text-indigo-900 bg-indigo-50 px-2 rounded">
              <span>Total Net Cash Payable:</span>
              <span>₹ {summary?.net_gst_payable?.total || '0.00'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
