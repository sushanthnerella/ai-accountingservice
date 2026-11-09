import { create } from 'zustand';
import { User } from '../types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: JSON.parse(localStorage.getItem('auth_user') || 'null'),
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  setAuth: (user, accessToken, refreshToken) => {
    localStorage.setItem('auth_user', JSON.stringify(user));
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    set({ user, accessToken, refreshToken });
  },
  logout: () => {
    localStorage.removeItem('auth_user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('active_org_id');
    localStorage.removeItem('active_client_id');
    set({ user: null, accessToken: null, refreshToken: null });
  },
}));
