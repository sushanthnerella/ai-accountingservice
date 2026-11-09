import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { AuditEventItem } from '../types';

export const AuditLog: React.FC = () => {
  const { currentOrg } = useWorkspaceStore();
  const { data: events } = useQuery<AuditEventItem[]>({
    queryKey: ['audit', currentOrg?.id],
    queryFn: async () => (await apiClient.get('/audit')).data.data,
    enabled: !!currentOrg,
  });

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200">
      <h1 className="text-xl font-bold mb-4">Audit Trail</h1>
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-50 border-b">
          <tr>
            <th className="px-4 py-2">Event</th>
            <th className="px-4 py-2">Entity</th>
            <th className="px-4 py-2">Timestamp</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {events?.map((e) => (
            <tr key={e.id}>
              <td className="px-4 py-2">{e.event_type}</td>
              <td className="px-4 py-2">{e.entity_name}</td>
              <td className="px-4 py-2">{new Date(e.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
