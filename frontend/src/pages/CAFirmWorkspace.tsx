import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { ClientBusiness } from '../types';
import { ClientOnboardingModal } from '../components/ClientOnboardingModal';
import { Plus } from 'lucide-react';

export const CAFirmWorkspace: React.FC = () => {
  const { currentOrg, setCurrentClient } = useWorkspaceStore();
  const [modalOpen, setModalOpen] = useState(false);
  const { data: clients, refetch } = useQuery<ClientBusiness[]>({
    queryKey: ['clients', currentOrg?.id],
    queryFn: async () => (await apiClient.get('/clients')).data.data,
    enabled: !!currentOrg,
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-white p-6 rounded-xl border border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">CA Client Portfolio</h1>
          <p className="text-sm text-slate-500">Active Practice: {currentOrg?.name}</p>
        </div>
        <button onClick={() => setModalOpen(true)} className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold">
          <Plus className="w-4 h-4" />
          <span>Onboard Client</span>
        </button>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="px-6 py-3">Legal Name</th>
              <th className="px-6 py-3">PAN</th>
              <th className="px-6 py-3">GSTIN</th>
              <th className="px-6 py-3">State</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {clients?.map((c) => (
              <tr key={c.id}>
                <td className="px-6 py-3 font-semibold">{c.legal_name}</td>
                <td className="px-6 py-3 font-mono">{c.pan}</td>
                <td className="px-6 py-3 font-mono">{c.gstin || '-'}</td>
                <td className="px-6 py-3">{c.state_code}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ClientOnboardingModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSuccess={() => refetch()} />
    </div>
  );
};
