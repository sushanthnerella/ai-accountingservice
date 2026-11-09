import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { CheckSquare, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';

export const DocumentReview: React.FC = () => {
  const { currentOrg, currentClient } = useWorkspaceStore();
  const [taxable, setTaxable] = useState('10000.00');
  const [cgst, setCgst] = useState('900.00');
  const [sgst, setSgst] = useState('900.00');
  const [igst, setIgst] = useState('0.00');
  const [total, setTotal] = useState('11800.00');

  const computedTotal = (parseFloat(taxable || '0') + parseFloat(cgst || '0') + parseFloat(sgst || '0') + parseFloat(igst || '0')).toFixed(2);
  const isBalanced = Math.abs(parseFloat(computedTotal) - parseFloat(total || '0')) <= 0.05;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200">
        <h1 className="text-xl font-bold text-slate-900">Document AI Review & Override</h1>
        <p className="text-xs text-slate-500 mt-1">Side-by-side extraction with strict arithmetic invariant validation.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 text-white p-6 rounded-xl flex flex-col justify-center items-center">
          <div className="text-slate-400 text-xs mb-2">Original Document Preview</div>
          <div className="w-full h-80 border border-slate-800 rounded-lg flex items-center justify-center bg-slate-950 font-mono text-xs text-slate-500">
            [PDF Vector Rendering Pane]
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
          <h3 className="text-sm font-bold text-slate-800">Extracted Invariant Check</h3>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Taxable Amount (₹)</label>
            <input type="text" value={taxable} onChange={(e) => setTaxable(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">CGST (9%)</label>
              <input type="text" value={cgst} onChange={(e) => setCgst(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">SGST (9%)</label>
              <input type="text" value={sgst} onChange={(e) => setSgst(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Total Amount (₹)</label>
            <input type="text" value={total} onChange={(e) => setTotal(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
          </div>

          <div className={`p-3 rounded-lg border text-xs flex items-center space-x-2 ${isBalanced ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'}`}>
            {isBalanced ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <ShieldAlert className="w-4 h-4 text-rose-600" />}
            <span>{isBalanced ? 'Arithmetic Invariant Verified: Debits & Taxes Match Total' : `Math Drift Detected: Sum is ₹${computedTotal} vs Total ₹${total}`}</span>
          </div>

          <button disabled={!isBalanced} className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold disabled:opacity-50">
            Accept & Stage to Books
          </button>
        </div>
      </div>
    </div>
  );
};
