import { create } from 'zustand';
import { Organization, ClientBusiness } from '../types';

interface WorkspaceState {
  currentOrg: Organization | null;
  currentClient: ClientBusiness | null;
  setCurrentOrg: (org: Organization | null) => void;
  setCurrentClient: (client: ClientBusiness | null) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  currentOrg: JSON.parse(localStorage.getItem('active_org') || 'null'),
  currentClient: JSON.parse(localStorage.getItem('active_client') || 'null'),
  setCurrentOrg: (org) => {
    if (org) {
      localStorage.setItem('active_org', JSON.stringify(org));
      localStorage.setItem('active_org_id', org.id);
    } else {
      localStorage.removeItem('active_org');
      localStorage.removeItem('active_org_id');
    }
    set({ currentOrg: org });
  },
  setCurrentClient: (client) => {
    if (client) {
      localStorage.setItem('active_client', JSON.stringify(client));
      localStorage.setItem('active_client_id', client.id);
    } else {
      localStorage.removeItem('active_client');
      localStorage.removeItem('active_client_id');
    }
    set({ currentClient: client });
  },
}));
