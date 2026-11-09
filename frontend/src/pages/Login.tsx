import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { ShieldCheck, AlertCircle } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await apiClient.post('/auth/login', { email, password });
      const { access_token, refresh_token } = res.data.data;
      const meRes = await apiClient.get('/auth/me', { headers: { Authorization: `Bearer ${access_token}` } });
      setAuth(meRes.data.data, access_token, refresh_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="flex justify-center items-center space-x-2">
          <ShieldCheck className="w-10 h-10 text-indigo-400" />
          <h2 className="text-3xl font-extrabold text-white">AccounTech AI</h2>
        </div>
      </div>
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800 py-8 px-4 shadow sm:rounded-xl sm:px-10 border border-slate-700">
          <form className="space-y-4" onSubmit={handleLogin}>
            {error && <div className="text-rose-400 text-sm">{error}</div>}
            <div>
              <label className="block text-sm text-slate-300">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm" />
            </div>
            <div>
              <label className="block text-sm text-slate-300">Password</label>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm" />
            </div>
            <button type="submit" disabled={loading} className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white font-semibold text-sm">
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>
          <div className="mt-4 text-center text-xs text-slate-400">
            Don't have an account? <Link to="/register" className="text-indigo-400">Register</Link>
          </div>
        </div>
      </div>
    </div>
  );
};
