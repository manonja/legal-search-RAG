import axios from "axios";
import { constructApiUrl } from "./utils";

// Types based on the FastAPI models
export interface QueryRequest {
  query_text: string;
  n_results?: number;
  min_similarity?: number;
  metadata_filter?: Record<string, any>;
}

export interface SearchResult {
  chunk: string;
  metadata: Record<string, any>;
  similarity: number;
  rank: number;
}

export interface QueryResponse {
  results: SearchResult[];
  total_found: number;
}

export interface UsageInfo {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost: number;
}

export interface RagRequest {
  query: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  n_results?: number;
  min_similarity?: number;
  conversation_id?: string;
  messages?: Array<{ role: string; content: string }>;
}

export interface RagResponse {
  answer: string;
  source_documents: Array<{
    content: string;
    metadata: Record<string, any>;
    similarity: number;
  }>;
  conversation_id: string;
  usage?: UsageInfo;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  chroma_status: string;
  document_count: number;
  tenant_id?: string;
}

export interface DocumentResponse {
  content: string;
  metadata: Record<string, any>;
  source: string;
  chunks: string[];
}

// Authentication interfaces
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  email: string;
  full_name?: string;
  tenant_id: string;
  is_admin: boolean;
}

// Tenant interfaces
export interface TenantCreateRequest {
  name: string;
  admin_email: string;
  description?: string;
}

export interface Tenant {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  active: boolean;
}

// Create axios instance with base URL from environment variable
const apiClient = axios.create({
  baseURL: constructApiUrl(),
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 seconds timeout
});

// Add auth token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API functions
export const api = {
  // Search documents
  async searchDocuments(request: QueryRequest): Promise<QueryResponse> {
    const response = await apiClient.post("/api/search", request);
    return response.data;
  },

  // RAG search
  async ragSearch(request: RagRequest): Promise<RagResponse> {
    const response = await apiClient.post("/api/rag-search", request);
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await apiClient.get("/api/health");
    return response.data;
  },

  // Get full document
  async getDocument(documentId: string): Promise<DocumentResponse> {
    // Extract just the filename from the path and remove the "chunked_" prefix
    const filename = documentId.split("/").pop() || documentId;
    const processedFilename = filename.replace(/^chunked_/, "");

    const response = await apiClient.get(
      `/api/documents/${encodeURIComponent(processedFilename)}`
    );
    return response.data;
  },

  // Get original document for a search result
  async getOriginalDocument(result: SearchResult): Promise<DocumentResponse> {
    const source = result.metadata.source;
    if (!source) {
      throw new Error("No document source found in search result");
    }
    return this.getDocument(source);
  },

  // Authentication
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const formData = new FormData();
    formData.append("username", credentials.username);
    formData.append("password", credentials.password);

    const response = await axios.post(
      `${constructApiUrl()}/auth/token`,
      formData,
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );

    // Store token in localStorage
    if (response.data.access_token) {
      localStorage.setItem("auth_token", response.data.access_token);
    }

    return response.data;
  },

  async getUserProfile(): Promise<UserProfile> {
    const response = await apiClient.get("/api/users/me");
    return response.data;
  },

  async logout(): Promise<void> {
    localStorage.removeItem("auth_token");
  },

  // Tenant management
  async createTenant(data: TenantCreateRequest): Promise<Tenant> {
    const response = await apiClient.post("/tenant", data);
    return response.data;
  },

  async getTenantInfo(): Promise<{
    tenant_id: string;
    environment_tenant: string;
  }> {
    const response = await apiClient.get("/api/tenant-info");
    return response.data;
  },

  async listTenants(): Promise<Tenant[]> {
    const response = await apiClient.get("/tenant");
    return response.data;
  },
};

export default api;
