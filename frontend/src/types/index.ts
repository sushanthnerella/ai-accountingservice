export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export type OrgType = 'FREELANCER' | 'CA_FIRM' | 'ENTERPRISE';
export type MemberRole = 'FIRM_ADMIN' | 'SENIOR_CA' | 'STAFF_ACCOUNTANT' | 'CLIENT_VIEWER' | 'AUDITOR';

export interface Organization {
  id: string;
  name: string;
  slug: string;
  org_type: OrgType;
  is_active: boolean;
  created_at: string;
  user_role?: MemberRole;
}

export type BusinessType = 'PROPRIETORSHIP' | 'INDIVIDUAL' | 'PARTNERSHIP' | 'LLP' | 'PVT_LTD' | 'OTHER';

export interface ClientBusiness {
  id: string;
  organization_id: string;
  legal_name: string;
  trade_name?: string;
  business_type: BusinessType;
  pan: string;
  gstin?: string;
  state_code: string;
  is_composition_scheme: boolean;
  is_active: boolean;
  created_at: string;
}

export interface UploadedFile {
  document_id: string;
  file_name: string;
  sha256_hash: string;
  status: string;
  is_duplicate: boolean;
  duplicate_of_id?: string;
}

export interface BatchUploadResponse {
  batch_id: string;
  batch_reference: string;
  total_files: number;
  uploaded_files: UploadedFile[];
}

export type DocumentBatch = BatchUploadResponse;

export interface DocumentItem {
  id: string;
  organization_id: string;
  client_business_id: string;
  batch_id?: string;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  sha256_hash: string;
  category: string;
  status: string;
  is_duplicate: boolean;
  duplicate_of_id?: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface AuditEventItem {
  id: string;
  organization_id: string;
  user_id?: string;
  event_type: string;
  ip_address?: string;
  user_agent?: string;
  entity_name: string;
  entity_id?: string;
  payload_before?: Record<string, any>;
  payload_after?: Record<string, any>;
  created_at: string;
}
