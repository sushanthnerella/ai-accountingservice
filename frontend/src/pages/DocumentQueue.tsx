import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { DocumentItem } from '../types';

export const DocumentQueue: React.FC = () => {
  const { currentOrg, currentClient } = useWorkspaceStore();
  const { data: docs } = useQuery<DocumentItem[]>({
    queryKey: ['documents', currentOrg?.id, currentClient?.id],
    queryFn: async () => (await apiClient.get('/documents')).data.data,
    enabled: !!currentOrg,
    refetchInterval: 3000,
  });

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200">
      <h1 className="text-xl font-bold mb-4">Document Queue</h1>
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-50 border-b">
          <tr>
            <th className="px-4 py-2">Filename</th>
            <th className="px-4 py-2">Category</th>
            <th className="px-4 py-2">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {docs?.map((d) => (
            <tr key={d.id}>
              <td className="px-4 py-2">{d.original_filename}</td>
              <td className="px-4 py-2">{d.category}</td>
              <td className="px-4 py-2">{d.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
