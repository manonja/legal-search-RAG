import { api } from "@/lib/api";
import axios from "axios";

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", { value: mockLocalStorage });

// Mock the axios module directly
jest.mock("axios", () => {
  return {
    create: jest.fn().mockReturnValue({
      get: jest.fn().mockImplementation(() => Promise.resolve({ data: {} })),
      post: jest.fn().mockImplementation(() => Promise.resolve({ data: {} })),
      interceptors: {
        request: {
          use: jest.fn((callback) => {
            // Store the callback for testing
            (jest as any).requestInterceptorCallback = callback;
            return callback;
          }),
        },
        response: {
          use: jest.fn(),
        },
      },
    }),
  };
});

describe("API Client", () => {
  // Get the mocked axios instance from the api module
  const mockAxiosInstance = (axios.create as jest.Mock)();

  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReset();
    mockLocalStorage.setItem.mockReset();
    process.env.NEXT_PUBLIC_API_TOKEN = undefined;
  });

  // Test for the request interceptor that adds the Authorization header
  it("should add the Authorization header with token from localStorage", () => {
    // Set up the test
    const mockToken = "test-token-123";
    mockLocalStorage.getItem.mockReturnValue(mockToken);
    const mockConfig = { headers: {} };

    // Call the interceptor callback
    const result = (jest as any).requestInterceptorCallback(mockConfig);

    // Verify the Authorization header was added correctly
    expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`);
    expect(mockLocalStorage.getItem).toHaveBeenCalledWith("api_token");
  });

  it("should add the Authorization header with token from environment variable", () => {
    // Set up the test with no localStorage token
    mockLocalStorage.getItem.mockReturnValue(null);
    const mockEnvToken = "env-token-456";
    process.env.NEXT_PUBLIC_API_TOKEN = mockEnvToken;
    const mockConfig = { headers: {} };

    // Call the interceptor callback
    const result = (jest as any).requestInterceptorCallback(mockConfig);

    // Verify the Authorization header was added correctly
    expect(result.headers.Authorization).toBe(`Bearer ${mockEnvToken}`);
  });

  it("should call the correct endpoint for searchDocuments", async () => {
    const mockData = [{ text: "test", metadata: {}, distance: 0.5 }];
    mockAxiosInstance.post.mockResolvedValueOnce({ data: mockData });

    const searchQuery = { query: "test query", limit: 5 };
    const result = await api.searchDocuments(searchQuery);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith(
      "/api/search/",
      searchQuery
    );
    expect(result).toEqual(mockData);
  });

  it("should call the correct endpoint for legacy search", async () => {
    const mockData = { results: [], total_found: 0 };
    mockAxiosInstance.post.mockResolvedValueOnce({ data: mockData });

    const searchQuery = { query_text: "test query", n_results: 10 };
    const result = await api.legacySearchDocuments(searchQuery);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith(
      "/api/search/api",
      searchQuery
    );
    expect(result).toEqual(mockData);
  });

  it("should call the correct endpoint for RAG search", async () => {
    const mockData = {
      answer: "test answer",
      sources: ["source1", "source2"],
      confidence: 0.8,
    };
    mockAxiosInstance.post.mockResolvedValueOnce({ data: mockData });

    const queryRequest = { query: "test question", max_results: 5 };
    const result = await api.ragSearch(queryRequest);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith(
      "/api/rag-search",
      queryRequest
    );
    expect(result).toEqual(mockData);
  });

  it("should call the correct endpoint for document query", async () => {
    const mockData = {
      answer: "test answer",
      sources: ["source1", "source2"],
      confidence: 0.8,
    };
    mockAxiosInstance.post.mockResolvedValueOnce({ data: mockData });

    const queryRequest = { query: "test question", max_results: 5 };
    const result = await api.queryDocuments(queryRequest);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith(
      "/api/query",
      queryRequest
    );
    expect(result).toEqual(mockData);
  });

  it("should call the correct endpoint for health check", async () => {
    const mockData = { status: "ok" };
    mockAxiosInstance.get.mockResolvedValueOnce({ data: mockData });

    const result = await api.healthCheck();

    expect(mockAxiosInstance.get).toHaveBeenCalledWith("/api/health");
    expect(result).toEqual(mockData);
  });

  it("should call the correct endpoint for document retrieval", async () => {
    const mockData = {
      content: "document content",
      metadata: {},
      source: "source.pdf",
      chunks: ["chunk1", "chunk2"],
    };
    mockAxiosInstance.get.mockResolvedValueOnce({ data: mockData });

    const documentId = "test-document-id";
    const result = await api.getDocument(documentId);

    expect(mockAxiosInstance.get).toHaveBeenCalledWith(
      `/api/documents/${encodeURIComponent(documentId)}`
    );
    expect(result).toEqual(mockData);
  });

  it("should call the correct endpoint for document upload", async () => {
    const mockData = { document_id: "new-doc-id" };
    mockAxiosInstance.post.mockResolvedValueOnce({ data: mockData });

    const mockFile = new File(["test content"], "test.pdf", {
      type: "application/pdf",
    });
    const result = await api.uploadDocument(mockFile);

    expect(mockAxiosInstance.post).toHaveBeenCalledWith(
      "/api/documents/upload",
      expect.any(FormData),
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "multipart/form-data",
        }),
      })
    );
    expect(result).toEqual(mockData);
  });
});
