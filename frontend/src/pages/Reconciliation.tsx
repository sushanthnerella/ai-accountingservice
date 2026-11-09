import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { GitCompare, Check, X, ShieldCheck } from 'lucide-react';

export const Reconciliation: React.FC = () => {
  const { currentOrg, currentClient } = useWorkspaceStore();

  const { data: matches, refetch } = useQuery({
    queryKey: ['reconciliation-matches', currentOrg?.id, currentClient?.id],
    queryFn: async () => {
      if (!currentOrg || !currentClient) return [];
      const res = await apiClient.get('/reconciliation/matches');
      return res.data.data;
    },
    enabled: !!currentOrg && !!currentClient,
  });

  const handleApprove = async (matchId: string, approved: boolean) => {
    await apiClient.post(`/reconciliation/matches/${matchId}/approve`, {
      approval_status: approved ? 'APPROVED' : 'REJECTED',
    });
    refetch();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-white p-6 rounded-xl border border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Multi-Scenario Reconciliation Engine</h1>
          <p className="text-xs text-slate-500">Human-in-the-loop gate: AI proposes matches; qualified accountants approve.</p>
        </div>
        <button
          onClick={async () => {
            await apiClient.post('/reconciliation/propose');
            refetch();
          }}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold"
        >
          Run Match Proposer
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="px-6 py-3">Scenario</th>
              <th className="px-6 py-3">Allocated Amount</th>
              <th className="px-6 py-3">TDS Deduction</th>
              <th className="px-6 py-3">Confidence</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3 text-right">Approval Gate</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {matches?.map((m: any) => (
              <tr key={m.id}>
                <td className="px-6 py-4 font-semibold">{m.match_scenario}</td>
                <td className="px-6 py-4 font-mono font-medium">₹ {m.allocated_amount}</td>
                <td className="px-6 py-4 font-mono text-amber-700">
                  {m.tds_deducted_amount > 0 ? `₹ ${m.tds_deducted_amount} (${m.tds_section})` : '-'}
                </td>
                <td className="px-6 py-4 font-mono">{(m.confidence_score * 100).toFixed(0)}%</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${m.approval_status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}`}>
                    {m.approval_status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right space-x-2">
                  {m.approval_status === 'PENDING' && (
                    <>
                      <button onClick={() => handleApprove(m.id, true)} className="p-1 text-emerald-600 hover:bg-emerald-50 rounded">
                        <Check className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleApprove(m.id, false)} className="p-1 text-rose-600 hover:bg-rose-50 rounded">
                        <X className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
