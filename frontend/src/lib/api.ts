import axios from "axios";
import { constructApiUrl } from "./utils";

// Types based on the current OpenAPI specification
export interface QueryRequest {
  query: string;
  max_results?: number;
  temperature?: number;
  max_tokens?: number;
}

export interface SearchResult {
  text: string;
  metadata: Record<string, any>;
  distance: number;
}

export interface SearchQuery {
  query: string;
  limit?: number;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
  confidence: number;
}

export interface SearchQueryResponse {
  results: SearchResult[];
  total_found: number;
}

export interface DocumentResponse {
  content: string;
  metadata: Record<string, any>;
  source: string;
  chunks: string[];
}

// Used for backward compatibility with existing components
export interface LegacySearchResult {
  chunk: string;
  metadata: Record<string, any>;
  similarity: number;
  rank: number;
}

export interface LegacyQueryResponse {
  results: LegacySearchResult[];
  total_found: number;
}

export interface LegacyQueryRequest {
  query_text: string;
  n_results?: number;
  min_similarity?: number;
  metadata_filter?: Record<string, any>;
}

// Create axios instance with base URL from environment variable
const apiClient = axios.create({
  baseURL: constructApiUrl(),
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 seconds timeout
});

// API functions
export const api = {
  // Search documents - new endpoint
  async searchDocuments(request: SearchQuery): Promise<SearchResult[]> {
    const response = await apiClient.post("/api/search/", request);
    return response.data;
  },

  // Legacy search endpoint - for backward compatibility
  async legacySearchDocuments(
    request: LegacyQueryRequest
  ): Promise<LegacyQueryResponse> {
    const response = await apiClient.post("/api/search/api", request);
    return response.data;
  },

  // RAG search
  async ragSearch(request: QueryRequest): Promise<QueryResponse> {
    const response = await apiClient.post("/api/rag-search", request);
    return response.data;
  },

  // Query documents
  async queryDocuments(request: QueryRequest): Promise<QueryResponse> {
    const response = await apiClient.post("/api/query", request);
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<Record<string, any>> {
    const response = await apiClient.get("/api/health");
    return response.data;
  },

  // Get full document
  async getDocument(documentId: string): Promise<DocumentResponse> {
    const response = await apiClient.get(
      `/api/documents/${encodeURIComponent(documentId)}`
    );
    return response.data;
  },

  // Upload document
  async uploadDocument(file: File): Promise<Record<string, any>> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post("/api/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },
};

export default api;
