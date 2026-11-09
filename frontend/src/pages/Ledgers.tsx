import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { BookOpen } from 'lucide-react';

export const Ledgers: React.FC = () => {
  const { currentOrg, currentClient } = useWorkspaceStore();

  const { data: tb } = useQuery({
    queryKey: ['trial-balance', currentOrg?.id, currentClient?.id],
    queryFn: async () => {
      if (!currentOrg || !currentClient) return [];
      const res = await apiClient.get('/ledger/trial-balance');
      return res.data.data;
    },
    enabled: !!currentOrg && !!currentClient,
  });

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200">
        <h1 className="text-xl font-bold text-slate-900">Trial Balance & General Ledger</h1>
        <p className="text-xs text-slate-500 mt-1">Append-only immutable double-entry ledger with zero floating-point drift.</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="px-6 py-3">Account Code</th>
              <th className="px-6 py-3">Account Name</th>
              <th className="px-6 py-3">Account Type</th>
              <th className="px-6 py-3 text-right">Debit (₹)</th>
              <th className="px-6 py-3 text-right">Credit (₹)</th>
              <th className="px-6 py-3 text-right">Net Balance (₹)</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {tb?.map((acc: any) => (
              <tr key={acc.account_code}>
                <td className="px-6 py-3 font-mono">{acc.account_code}</td>
                <td className="px-6 py-3 font-semibold">{acc.account_name}</td>
                <td className="px-6 py-3 text-slate-600">{acc.account_type}</td>
                <td className="px-6 py-3 text-right font-mono font-medium">{acc.total_debit}</td>
                <td className="px-6 py-3 text-right font-mono font-medium">{acc.total_credit}</td>
                <td className="px-6 py-3 text-right font-mono font-bold text-slate-900">{acc.net_balance}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
