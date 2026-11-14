import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { BookOpen, Scale, TrendingUp, Filter } from 'lucide-react';

export const Ledgers: React.FC = () => {
  const { currentOrg, currentClient } = useWorkspaceStore();
  const [includeZeros, setIncludeZeros] = useState(false);
  const [activeTab, setActiveTab] = useState<'TB' | 'PNL' | 'BS'>('TB');

  const { data: tb } = useQuery({
    queryKey: ['trial-balance', currentOrg?.id, currentClient?.id, includeZeros],
    queryFn: async () => {
      if (!currentOrg || !currentClient) return [];
      const res = await apiClient.get(`/ledger/trial-balance?include_zero_balances=${includeZeros}`);
      return res.data.data;
    },
    enabled: !!currentOrg && !!currentClient,
  });

  const { data: pnl } = useQuery({
    queryKey: ['profit-loss', currentOrg?.id, currentClient?.id],
    queryFn: async () => {
      if (!currentOrg || !currentClient) return null;
      const res = await apiClient.get('/ledger/profit-and-loss');
      return res.data.data;
    },
    enabled: !!currentOrg && !!currentClient && activeTab === 'PNL',
  });

  const { data: bs } = useQuery({
    queryKey: ['balance-sheet', currentOrg?.id, currentClient?.id],
    queryFn: async () => {
      if (!currentOrg || !currentClient) return null;
      const res = await apiClient.get('/ledger/balance-sheet');
      return res.data.data;
    },
    enabled: !!currentOrg && !!currentClient && activeTab === 'BS',
  });

  const totalDr = tb?.reduce((acc: number, item: any) => acc + parseFloat(item.total_debit || '0'), 0).toFixed(2);
  const totalCr = tb?.reduce((acc: number, item: any) => acc + parseFloat(item.total_credit || '0'), 0).toFixed(2);
  const isTBBalanced = Math.abs(parseFloat(totalDr || '0') - parseFloat(totalCr || '0')) <= 0.01;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-white p-6 rounded-xl border border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Financial Reports & General Ledger</h1>
          <p className="text-xs text-slate-500 mt-1">Indian Financial Year (April 1 to March 31) immutable double-entry ledger.</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('TB')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'TB' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Trial Balance
          </button>
          <button
            onClick={() => setActiveTab('PNL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'PNL' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Profit & Loss
          </button>
          <button
            onClick={() => setActiveTab('BS')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'BS' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Balance Sheet
          </button>
        </div>
      </div>

      {activeTab === 'TB' && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden space-y-2">
          <div className="flex justify-between items-center p-4 border-b">
            <span className="text-xs font-semibold text-slate-700">All Accounts Breakdown</span>
            <label className="flex items-center space-x-1.5 text-xs text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={includeZeros}
                onChange={(e) => setIncludeZeros(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-0"
              />
              <span>Include Zero Balances</span>
            </label>
          </div>

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
                  <td className="px-6 py-3 font-mono text-slate-600">{acc.account_code}</td>
                  <td className="px-6 py-3 font-semibold text-slate-800">{acc.account_name}</td>
                  <td className="px-6 py-3 text-slate-500">{acc.account_type}</td>
                  <td className="px-6 py-3 text-right font-mono font-medium">{acc.total_debit}</td>
                  <td className="px-6 py-3 text-right font-mono font-medium">{acc.total_credit}</td>
                  <td className="px-6 py-3 text-right font-mono font-bold text-slate-900">{acc.net_balance}</td>
                </tr>
              ))}
              {tb && tb.length > 0 && (
                <tr className="bg-slate-50 font-bold border-t-2">
                  <td colSpan={3} className="px-6 py-3 text-right">Trial Balance Total:</td>
                  <td className="px-6 py-3 text-right font-mono text-indigo-700">₹ {totalDr}</td>
                  <td className="px-6 py-3 text-right font-mono text-indigo-700">₹ {totalCr}</td>
                  <td className="px-6 py-3 text-right font-mono">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${isTBBalanced ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                      {isTBBalanced ? 'MATCH / BALANCED' : 'IMBALANCE DETECTED'}
                    </span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'PNL' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
            <h3 className="text-sm font-bold text-slate-800 border-b pb-2">Revenues (Income)</h3>
            <div className="space-y-1 text-xs font-mono">
              {pnl?.revenues?.map((r: any) => (
                <div key={r.code} className="flex justify-between py-1 border-b">
                  <span>{r.name} ({r.code}):</span>
                  <span className="font-semibold">₹ {r.amount}</span>
                </div>
              ))}
              <div className="flex justify-between py-2 font-bold text-emerald-700 bg-emerald-50 px-2 rounded mt-2">
                <span>Total Revenues:</span>
                <span>₹ {pnl?.total_revenue || '0.00'}</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
            <h3 className="text-sm font-bold text-slate-800 border-b pb-2">Expenses</h3>
            <div className="space-y-1 text-xs font-mono">
              {pnl?.expenses?.map((e: any) => (
                <div key={e.code} className="flex justify-between py-1 border-b">
                  <span>{e.name} ({e.code}):</span>
                  <span className="font-semibold">₹ {e.amount}</span>
                </div>
              ))}
              <div className="flex justify-between py-2 font-bold text-rose-700 bg-rose-50 px-2 rounded mt-2">
                <span>Total Expenses:</span>
                <span>₹ {pnl?.total_expenses || '0.00'}</span>
              </div>
            </div>

            <div className="pt-4">
              <div className="flex justify-between items-center p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs font-bold text-indigo-900 font-mono">
                <span>NET PROFIT / (LOSS):</span>
                <span className="text-base">₹ {pnl?.net_profit || '0.00'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'BS' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
            <h3 className="text-sm font-bold text-slate-800 border-b pb-2">Assets</h3>
            <div className="space-y-1 text-xs font-mono">
              {bs?.assets?.map((a: any) => (
                <div key={a.code} className="flex justify-between py-1 border-b">
                  <span>{a.name} ({a.code}):</span>
                  <span className="font-semibold">₹ {a.amount}</span>
                </div>
              ))}
              <div className="flex justify-between py-2 font-bold text-slate-900 bg-slate-50 px-2 rounded mt-2">
                <span>Total Assets:</span>
                <span>₹ {bs?.total_assets || '0.00'}</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
            <h3 className="text-sm font-bold text-slate-800 border-b pb-2">Liabilities & Equity</h3>
            <div className="space-y-1 text-xs font-mono">
              <div className="text-[11px] font-semibold text-slate-500 pt-1">Liabilities</div>
              {bs?.liabilities?.map((l: any) => (
                <div key={l.code} className="flex justify-between py-1 border-b">
                  <span>{l.name} ({l.code}):</span>
                  <span>₹ {l.amount}</span>
                </div>
              ))}
              <div className="text-[11px] font-semibold text-slate-500 pt-2">Equity & Retained Earnings</div>
              <div className="flex justify-between py-1 border-b">
                <span>Owner Capital:</span>
                <span>₹ {bs?.owner_capital || '0.00'}</span>
              </div>
              <div className="flex justify-between py-1 border-b">
                <span>Net Profit for Period:</span>
                <span>₹ {bs?.net_profit_period || '0.00'}</span>
              </div>
              <div className="flex justify-between py-2 font-bold text-slate-900 bg-slate-50 px-2 rounded mt-2">
                <span>Total Liabilities & Equity:</span>
                <span>₹ {(parseFloat(bs?.total_liabilities || '0') + parseFloat(bs?.total_equity_with_profit || '0')).toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
