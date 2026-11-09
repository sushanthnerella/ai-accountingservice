import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Organization, ClientBusiness } from '../types';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { Building2, Briefcase } from 'lucide-react';

export const WorkspaceSwitcher: React.FC = () => {
  const { currentOrg, currentClient, setCurrentOrg, setCurrentClient } = useWorkspaceStore();
  const { data: orgs } = useQuery<Organization[]>({
    queryKey: ['organizations'],
    queryFn: async () => (await apiClient.get('/organizations')).data.data,
  });

  const { data: clients } = useQuery<ClientBusiness[]>({
    queryKey: ['clients', currentOrg?.id],
    queryFn: async () => (await apiClient.get('/clients')).data.data,
    enabled: !!currentOrg,
  });

  useEffect(() => {
    if (orgs && orgs.length > 0 && !currentOrg) setCurrentOrg(orgs[0]);
  }, [orgs, currentOrg, setCurrentOrg]);

  useEffect(() => {
    if (clients && clients.length > 0 && !currentClient) setCurrentClient(clients[0]);
  }, [clients, currentClient, setCurrentClient]);

  return (
    <div className="flex items-center space-x-3 bg-slate-800 text-white px-3 py-1.5 rounded-lg border border-slate-700 text-sm">
      <div className="flex items-center space-x-1.5">
        <Building2 className="w-4 h-4 text-indigo-400" />
        <select
          value={currentOrg?.id || ''}
          onChange={(e) => {
            const org = orgs?.find((o) => o.id === e.target.value);
            setCurrentOrg(org || null);
            setCurrentClient(null);
          }}
          className="bg-transparent text-white font-medium focus:outline-none cursor-pointer text-xs"
        >
          {orgs?.map((o) => (
            <option key={o.id} value={o.id} className="bg-slate-900 text-white">
              {o.name} ({o.org_type})
            </option>
          ))}
        </select>
      </div>
      {currentOrg?.org_type === 'CA_FIRM' && (
        <>
          <span className="text-slate-500">/</span>
          <div className="flex items-center space-x-1.5">
            <Briefcase className="w-4 h-4 text-emerald-400" />
            <select
              value={currentClient?.id || ''}
              onChange={(e) => {
                const client = clients?.find((c) => c.id === e.target.value);
                setCurrentClient(client || null);
              }}
              className="bg-transparent text-white font-medium focus:outline-none cursor-pointer text-xs"
            >
              <option value="" disabled className="bg-slate-900 text-slate-400">Select Client</option>
              {clients?.map((c) => (
                <option key={c.id} value={c.id} className="bg-slate-900 text-white">
                  {c.legal_name} ({c.pan})
                </option>
              ))}
            </select>
          </div>
        </>
      )}
    </div>
  );
};
