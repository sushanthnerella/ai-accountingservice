import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { ShieldCheck } from 'lucide-react';

export const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [orgName, setOrgName] = useState('');
  const [orgType, setOrgType] = useState<'FREELANCER' | 'CA_FIRM'>('FREELANCER');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const { setCurrentOrg } = useWorkspaceStore();
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiClient.post('/auth/register', { email, password, full_name: fullName });
      const loginRes = await apiClient.post('/auth/login', { email, password });
      const { access_token, refresh_token } = loginRes.data.data;
      const meRes = await apiClient.get('/auth/me', { headers: { Authorization: `Bearer ${access_token}` } });
      setAuth(meRes.data.data, access_token, refresh_token);
      const slug = orgName.toLowerCase().replace(/[^a-z0-9]/g, '-').slice(0, 30);
      const orgRes = await apiClient.post('/organizations', { name: orgName, slug, org_type: orgType }, { headers: { Authorization: `Bearer ${access_token}` } });
      setCurrentOrg(orgRes.data.data);
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <h2 className="text-2xl font-bold text-white">Create Workspace</h2>
      </div>
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800 py-8 px-4 shadow sm:rounded-xl sm:px-10 border border-slate-700">
          <form className="space-y-4" onSubmit={handleRegister}>
            <div>
              <label className="block text-sm text-slate-300">Full Name</label>
              <input type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full px-3 py-2 bg-slate-900 border rounded-lg text-white text-sm" />
            </div>
            <div>
              <label className="block text-sm text-slate-300">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-3 py-2 bg-slate-900 border rounded-lg text-white text-sm" />
            </div>
            <div>
              <label className="block text-sm text-slate-300">Password</label>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-3 py-2 bg-slate-900 border rounded-lg text-white text-sm" />
            </div>
            <div>
              <label className="block text-sm text-slate-300">Firm / Practice Name</label>
              <input type="text" required value={orgName} onChange={(e) => setOrgName(e.target.value)} className="w-full px-3 py-2 bg-slate-900 border rounded-lg text-white text-sm" />
            </div>
            <div>
              <label className="block text-sm text-slate-300">Workspace Type</label>
              <select value={orgType} onChange={(e) => setOrgType(e.target.value as any)} className="w-full px-3 py-2 bg-slate-900 border rounded-lg text-white text-sm">
                <option value="FREELANCER">Freelancer</option>
                <option value="CA_FIRM">CA Firm</option>
              </select>
            </div>
            <button type="submit" disabled={loading} className="w-full py-2.5 bg-indigo-600 rounded-lg text-white font-semibold text-sm">Create</button>
          </form>
        </div>
      </div>
    </div>
  );
};
