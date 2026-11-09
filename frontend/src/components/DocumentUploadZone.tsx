import React, { useState, useRef } from 'react';
import { apiClient } from '../api/client';
import { useWorkspaceStore } from '../stores/workspaceStore';
import { BatchUploadResponse } from '../types';
import { UploadCloud, File, AlertTriangle, CheckCircle, Lock, Trash2, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const DocumentUploadZone: React.FC = () => {
  const { currentOrg, currentClient } = useWorkspaceStore();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [category, setCategory] = useState('AUTO_DETECT');
  const [pdfPassword, setPdfPassword] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<BatchUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleUpload = async () => {
    if (!currentOrg?.id || !currentClient?.id) {
      setError('Please select an active Organization and Client Business before uploading.');
      return;
    }
    if (selectedFiles.length === 0) {
      setError('Please select at least one file to upload.');
      return;
    }

    setUploading(true);
    setError(null);
    const formData = new FormData();
    selectedFiles.forEach((file) => formData.append('files', file));
    formData.append('category', category);
    if (pdfPassword) formData.append('pdf_password', pdfPassword);

    try {
      const res = await apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadResult(res.data.data);
      setSelectedFiles([]);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Document upload failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Multi-File Document Ingestion</h1>
        <p className="text-sm text-slate-500 mt-1">
          Client: <span className="font-semibold text-slate-800">{currentClient ? `${currentClient.legal_name} (${currentClient.pan})` : 'None selected'}</span>
        </p>

        {error && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center space-x-2 text-rose-700 text-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div
          onClick={() => fileInputRef.current?.click()}
          className="mt-6 border-2 border-dashed border-slate-300 hover:border-slate-400 bg-slate-50/50 rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer transition-colors"
        >
          <input
            type="file"
            multiple
            ref={fileInputRef}
            onChange={(e) => e.target.files && setSelectedFiles(Array.from(e.target.files))}
            accept=".pdf,.png,.jpg,.jpeg,.csv,.xls,.xlsx,.zip"
            className="hidden"
          />
          <UploadCloud className="w-8 h-8 text-indigo-600 mb-2" />
          <div className="text-sm font-semibold text-slate-700">Click to upload files (PDF, PNG, JPG, CSV, XLS, XLSX)</div>
        </div>

        {selectedFiles.length > 0 && (
          <div className="mt-4">
            <div className="text-xs text-slate-500 mb-2">Selected ({selectedFiles.length}) files</div>
            <button onClick={handleUpload} disabled={uploading} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold">
              {uploading ? 'Uploading...' : 'Submit Batch'}
            </button>
          </div>
        )}

        {uploadResult && (
          <div className="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-800">
            Batch staged successfully: {uploadResult.batch_reference} ({uploadResult.total_files} files)
          </div>
        )}
      </div>
    </div>
  );
};
