import React from 'react';
import { useAuthStore } from '../stores/authStore';
import { WorkspaceSwitcher } from './WorkspaceSwitcher';
import { LogOut, UserCircle } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, logout } = useAuthStore();
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
      <WorkspaceSwitcher />
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-sm text-slate-700">
          <UserCircle className="w-5 h-5 text-slate-400" />
          <span className="font-medium">{user?.full_name}</span>
        </div>
        <button onClick={logout} className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-slate-100 transition-colors">
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
