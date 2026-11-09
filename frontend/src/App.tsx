import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './stores/authStore';
import { useWorkspaceStore } from './stores/workspaceStore';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { AppShell } from './components/AppShell';
import { FreelancerWorkspace } from './pages/FreelancerWorkspace';
import { CAFirmWorkspace } from './pages/CAFirmWorkspace';
import { DocumentUploadZone } from './components/DocumentUploadZone';
import { DocumentQueue } from './pages/DocumentQueue';
import { DocumentReview } from './pages/DocumentReview';
import { Reconciliation } from './pages/Reconciliation';
import { Ledgers } from './pages/Ledgers';
import { GSTSummary } from './pages/GSTSummary';
import { Integrations } from './pages/Integrations';
import { AuditLog } from './pages/AuditLog';

const queryClient = new QueryClient();

const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

const WorkspaceRouter: React.FC = () => {
  const { currentOrg } = useWorkspaceStore();
  return currentOrg?.org_type === 'CA_FIRM' ? <CAFirmWorkspace /> : <FreelancerWorkspace />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
            <Route index element={<WorkspaceRouter />} />
            <Route path="clients" element={<CAFirmWorkspace />} />
            <Route path="documents/upload" element={<DocumentUploadZone />} />
            <Route path="documents" element={<DocumentQueue />} />
            <Route path="review" element={<DocumentReview />} />
            <Route path="reconciliation" element={<Reconciliation />} />
            <Route path="ledgers" element={<Ledgers />} />
            <Route path="gst" element={<GSTSummary />} />
            <Route path="integrations" element={<Integrations />} />
            <Route path="audit" element={<AuditLog />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};
export default App;
