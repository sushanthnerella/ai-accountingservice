import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { CheckCircle2, ShieldAlert, FileText, Check } from 'lucide-react';

export const DocumentReview: React.FC = () => {
  const { currentOrg, currentClient } = useWorkspaceStore();
  const [selectedInvoice, setSelectedInvoice] = useState<any>(null);

  const [taxable, setTaxable] = useState('10000.00');
  const [cgst, setCgst] = useState('900.00');
  const [sgst, setSgst] = useState('900.00');
  const [igst, setIgst] = useState('0.00');
  const [roundOff, setRoundOff] = useState('0.00');
  const [total, setTotal] = useState('11800.00');
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const { data: invoices, refetch } = useQuery({
    queryKey: ['invoices-review', currentOrg?.id, currentClient?.id],
    queryFn: async () => {
      if (!currentOrg || !currentClient) return [];
      const res = await apiClient.get('/invoices');
      return res.data.data;
    },
    enabled: !!currentOrg && !!currentClient,
  });

  useEffect(() => {
    if (invoices && invoices.length > 0 && !selectedInvoice) {
      const inv = invoices.find((i: any) => i.approval_status === 'PENDING') || invoices[0];
      setSelectedInvoice(inv);
    }
  }, [invoices, selectedInvoice]);

  useEffect(() => {
    if (selectedInvoice) {
      setTaxable(String(selectedInvoice.taxable_amount || '0.00'));
      setCgst(String(selectedInvoice.cgst_amount || '0.00'));
      setSgst(String(selectedInvoice.sgst_amount || '0.00'));
      setIgst(String(selectedInvoice.igst_amount || '0.00'));
      setRoundOff(String(selectedInvoice.round_off_amount || '0.00'));
      setTotal(String(selectedInvoice.total_amount || '0.00'));
      setActionMessage(null);
    }
  }, [selectedInvoice]);

  const computedTotal = (
    parseFloat(taxable || '0') +
    parseFloat(cgst || '0') +
    parseFloat(sgst || '0') +
    parseFloat(igst || '0') +
    parseFloat(roundOff || '0')
  ).toFixed(2);

  const isBalanced = Math.abs(parseFloat(computedTotal) - parseFloat(total || '0')) <= 0.05;

  const handleApprove = async () => {
    if (!selectedInvoice) return;
    try {
      const res = await apiClient.post(`/invoices/${selectedInvoice.id}/approve`);
      setActionMessage(res.data.message || 'Invoice posted to general ledger');
      refetch();
    } catch (err: any) {
      setActionMessage(err.response?.data?.detail?.message || 'Approval failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200">
        <h1 className="text-xl font-bold text-slate-900">Document AI Review & Override</h1>
        <p className="text-xs text-slate-500 mt-1">Side-by-side extraction with strict arithmetic invariant validation and ledger posting.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-2 lg:col-span-1">
          <h3 className="text-sm font-bold text-slate-800 mb-2">Pending Invoice Queue</h3>
          <div className="space-y-1.5 max-h-96 overflow-y-auto">
            {invoices?.length === 0 && (
              <p className="text-xs text-slate-400 py-4 text-center">No invoices uploaded yet</p>
            )}
            {invoices?.map((inv: any) => (
              <div
                key={inv.id}
                onClick={() => setSelectedInvoice(inv)}
                className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                  selectedInvoice?.id === inv.id
                    ? 'border-indigo-500 bg-indigo-50/50'
                    : 'border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="flex justify-between font-semibold">
                  <span>{inv.invoice_number}</span>
                  <span>₹ {inv.total_amount}</span>
                </div>
                <div className="text-[11px] text-slate-500 truncate mt-0.5">{inv.counterparty_name}</div>
                <div className="flex justify-between items-center mt-1 text-[10px]">
                  <span className="font-mono text-slate-400">{inv.invoice_date}</span>
                  <span className={`px-1.5 py-0.5 rounded ${inv.approval_status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                    {inv.approval_status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4 lg:col-span-2">
          <div className="flex justify-between items-center border-b pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-800">
                {selectedInvoice ? `Reviewing ${selectedInvoice.invoice_number} - ${selectedInvoice.counterparty_name}` : 'Invoice Data'}
              </h3>
              <p className="text-xs text-slate-400">
                {selectedInvoice?.counterparty_gstin ? `GSTIN: ${selectedInvoice.counterparty_gstin}` : 'No GSTIN'} • Place of Supply: {selectedInvoice?.place_of_supply_state_code}
              </p>
            </div>
            {selectedInvoice?.approval_status === 'APPROVED' && (
              <span className="flex items-center space-x-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <Check className="w-3.5 h-3.5" />
                <span>Posted to Ledger</span>
              </span>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Taxable Amount (₹)</label>
            <input type="text" value={taxable} onChange={(e) => setTaxable(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">CGST (₹)</label>
              <input type="text" value={cgst} onChange={(e) => setCgst(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">SGST (₹)</label>
              <input type="text" value={sgst} onChange={(e) => setSgst(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">IGST (₹)</label>
              <input type="text" value={igst} onChange={(e) => setIgst(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Round Off (±₹)</label>
              <input type="text" value={roundOff} onChange={(e) => setRoundOff(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Total Amount (₹)</label>
              <input type="text" value={total} onChange={(e) => setTotal(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm font-mono" />
            </div>
          </div>

          <div className={`p-3 rounded-lg border text-xs flex items-center space-x-2 ${isBalanced ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'}`}>
            {isBalanced ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />}
            <span>{isBalanced ? 'Arithmetic Invariant Verified: Debits & Taxes Match Total' : `Math Drift Detected: Sum is ₹${computedTotal} vs Total ₹${total}`}</span>
          </div>

          {actionMessage && (
            <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-800">
              {actionMessage}
            </div>
          )}

          <button
            onClick={handleApprove}
            disabled={!isBalanced || selectedInvoice?.approval_status === 'APPROVED'}
            className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-500 disabled:opacity-50 transition"
          >
            {selectedInvoice?.approval_status === 'APPROVED' ? 'Invoice Already Staged & Posted' : 'Accept & Stage to Books'}
          </button>
        </div>
      </div>
    </div>
  );
};
