import axios from "axios";
import * as Sentry from "@sentry/nextjs";
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

// Add request interceptor to include API token in all requests
apiClient.interceptors.request.use(
  (config) => {
    console.log("API Request interceptor: URL =", config.url);

    // Get API token from environment or local storage
    const apiTokenFromEnv = process.env.NEXT_PUBLIC_API_TOKEN;
    const apiTokenFromLocalStorage =
      typeof window !== "undefined" ? localStorage.getItem("api_token") : null;
    const apiToken = apiTokenFromEnv || apiTokenFromLocalStorage;

    console.log("API Request interceptor: Token from env?", !!apiTokenFromEnv);
    console.log(
      "API Request interceptor: Token from localStorage?",
      !!apiTokenFromLocalStorage
    );

    if (apiToken) {
      config.headers.Authorization = `Bearer ${apiToken}`;
      console.log(
        "API Request interceptor: Authorization header set successfully"
      );
    } else {
      console.warn(
        "API Request interceptor: No token available for request! Authentication will fail."
      );
    }

    return config;
  },
  (error) => {
    console.error("API Request interceptor: Error in request setup", error);
    // Report request setup errors to Sentry
    Sentry.captureException(error, {
      tags: {
        component: "API",
        stage: "requestSetup"
      }
    });
    return Promise.reject(error);
  }
);

// Add response interceptor to catch and report API errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error);

    // Make sure we have a proper message
    const errorMessage = error.message || "Unknown API error";
    const errorCode = error.code || "UNKNOWN_ERROR";
    const status = error.response?.status || 0;

    // Capture network errors in Sentry with more context
    Sentry.captureException(error, {
      tags: {
        component: "API",
        stage: "response",
        status: status,
        url: error.config?.url,
        errorCode: errorCode,
      },
      extra: {
        method: error.config?.method,
        params: error.config?.params,
        requestData: error.config?.data,
        responseData: error.response?.data,
        errorMessage: errorMessage,
        stack: error.stack
      }
    });

    // This ensures the error is logged even when running in Docker
    console.error("API Error Details for Sentry:", {
      message: errorMessage,
      code: errorCode,
      url: error.config?.url,
      method: error.config?.method
    });

    return Promise.reject(error);
  }
);

// API functions
export const api = {
  // Wrap API calls with error handling
  // Search documents - new endpoint
  async searchDocuments(request: SearchQuery): Promise<SearchResult[]> {
    try {
      const response = await apiClient.post("/api/search/", request);
      return response.data;
    } catch (error) {
      // Error is already captured by interceptor
      throw error;
    }
  },

  // Legacy search endpoint - for backward compatibility
  async legacySearchDocuments(
    request: LegacyQueryRequest
  ): Promise<LegacyQueryResponse> {
    try {
      const response = await apiClient.post("/api/search/api", request);
      return response.data;
    } catch (error) {
      // Error is already captured by interceptor
      throw error;
    }
  },

  // RAG search
  async ragSearch(request: QueryRequest): Promise<QueryResponse> {
    try {
      const response = await apiClient.post("/api/rag-search", request);
      return response.data;
    } catch (error) {
      // Error is already captured by interceptor
      throw error;
    }
  },

  // Query documents
  async queryDocuments(request: QueryRequest): Promise<QueryResponse> {
    try {
      const response = await apiClient.post("/api/query", request);
      return response.data;
    } catch (error) {
      // Error is already captured by interceptor
      throw error;
    }
  },

  // Health check
  async healthCheck(): Promise<Record<string, any>> {
    try {
      const response = await apiClient.get("/api/health");
      return response.data;
    } catch (error) {
      // Error is already captured by interceptor
      throw error;
    }
  },

  // Get full document
  async getDocument(documentId: string): Promise<DocumentResponse> {
    try {
      const response = await apiClient.get(
        `/api/documents/${encodeURIComponent(documentId)}`
      );
      return response.data;
    } catch (error) {
      // Error is already captured by interceptor
      throw error;
    }
  },

  // Upload document
  async uploadDocument(file: File): Promise<Record<string, any>> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await apiClient.post("/api/documents/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      // Error is already captured by interceptor
      throw error;
    }
  },
};

export default api;
