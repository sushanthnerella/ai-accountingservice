import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const orgId = localStorage.getItem('active_org_id');
  if (orgId) config.headers['X-Organization-Id'] = orgId;
  const clientId = localStorage.getItem('active_client_id');
  if (clientId) config.headers['X-Client-Business-Id'] = clientId;
  return config;
});
