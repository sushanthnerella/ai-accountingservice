import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { BusinessType } from '../types';
import { X, AlertCircle } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ClientOnboardingModal: React.FC<Props> = ({ isOpen, onClose, onSuccess }) => {
  const [legalName, setLegalName] = useState('');
  const [tradeName, setTradeName] = useState('');
  const [businessType, setBusinessType] = useState<BusinessType>('PROPRIETORSHIP');
  const [pan, setPan] = useState('');
  const [gstin, setGstin] = useState('');
  const [stateCode, setStateCode] = useState('27');
  const [isComposition, setIsComposition] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await apiClient.post('/clients', {
        legal_name: legalName,
        trade_name: tradeName || null,
        business_type: businessType,
        pan: pan.toUpperCase(),
        gstin: gstin ? gstin.toUpperCase() : null,
        state_code: stateCode,
        is_composition_scheme: isComposition,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Failed to onboard client business');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-100 bg-slate-50">
          <h3 className="text-base font-semibold text-slate-800">Onboard New Client Business</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center space-x-2 text-rose-700 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Legal Name *</label>
            <input type="text" required value={legalName} onChange={(e) => setLegalName(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">PAN *</label>
              <input type="text" required maxLength={10} value={pan} onChange={(e) => setPan(e.target.value.toUpperCase())} className="w-full px-3 py-2 border rounded-lg text-sm font-mono uppercase" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">GSTIN</label>
              <input type="text" maxLength={15} value={gstin} onChange={(e) => setGstin(e.target.value.toUpperCase())} className="w-full px-3 py-2 border rounded-lg text-sm font-mono uppercase" />
            </div>
          </div>
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg text-sm font-medium">Cancel</button>
            <button type="submit" disabled={loading} className="px-4 py-2 bg-indigo-600 rounded-lg text-sm font-semibold text-white">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
};
