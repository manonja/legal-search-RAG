import * as searchRoute from '@/app/api/search/route';
import * as legacySearchRoute from '@/app/api/search/api/route';
import * as ragSearchRoute from '@/app/api/rag-search/route';
import * as documentsRoute from '@/app/api/documents/[id]/route';
import * as uploadRoute from '@/app/api/documents/upload/route';
import * as apiProxy from '@/lib/apiProxy';

// Mock the apiProxy
jest.mock('@/lib/apiProxy', () => ({
  proxyApiRequest: jest.fn().mockResolvedValue({ success: true }),
}));

// Mock NextResponse
jest.mock('next/server', () => ({
  NextResponse: {
    json: jest.fn((data, init) => ({ data, init })),
  },
}));

// Import after mocking
import { NextResponse } from 'next/server';

describe('API Route Handlers', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Helper to create a mock request with JSON body
  const createMockRequest = (body: any = {}) => {
    return {
      json: jest.fn().mockResolvedValue(body),
      body: null,
      headers: {
        get: jest.fn(),
        has: jest.fn(),
      },
    };
  };

  describe('Search API', () => {
    it('should handle POST requests and forward to proxyApiRequest', async () => {
      // Arrange
      const mockBody = { query: 'test search', limit: 10 };
      const request = createMockRequest(mockBody);

      // Act
      await searchRoute.POST(request as any);

      // Assert
      expect(apiProxy.proxyApiRequest).toHaveBeenCalledWith(
        request,
        expect.objectContaining({
          endpoint: '/api/search/',
          method: 'POST',
          body: mockBody,
        })
      );
    });

    it('should reject non-POST methods', async () => {
      // Act & Assert
      const response = await searchRoute.GET();
      expect(response.status).toBe(405);
    });

    it('should handle errors and return 500 with error message', async () => {
      // Arrange
      const request = createMockRequest();
      (request.json as jest.Mock).mockRejectedValue(new Error('Parse error'));

      // Act
      const response = await searchRoute.POST(request as any);

      // Assert
      expect(NextResponse.json).toHaveBeenCalledWith(
        { error: 'Failed to search documents' },
        { status: 500 }
      );
    });
  });

  describe('Legacy Search API', () => {
    it('should handle POST requests and forward to proxyApiRequest', async () => {
      // Arrange
      const mockBody = { query_text: 'legacy search', n_results: 5 };
      const request = createMockRequest(mockBody);

      // Act
      await legacySearchRoute.POST(request as any);

      // Assert
      expect(apiProxy.proxyApiRequest).toHaveBeenCalledWith(
        request,
        expect.objectContaining({
          endpoint: '/api/search/api',
          method: 'POST',
          body: mockBody,
        })
      );
    });

    it('should reject non-POST methods', async () => {
      // Act & Assert
      const response = await legacySearchRoute.GET();
      expect(response.status).toBe(405);
    });
  });

  describe('RAG Search API', () => {
    it('should handle POST requests and forward to proxyApiRequest', async () => {
      // Arrange
      const mockBody = { query: 'rag query', max_results: 3 };
      const request = createMockRequest(mockBody);

      // Act
      await ragSearchRoute.POST(request as any);

      // Assert
      expect(apiProxy.proxyApiRequest).toHaveBeenCalledWith(
        request,
        expect.objectContaining({
          endpoint: '/api/rag-search',
          method: 'POST',
          body: mockBody,
        })
      );
    });
  });

  describe('Document API', () => {
    it('should handle GET requests and forward to proxyApiRequest', async () => {
      // Arrange
      const request = createMockRequest();
      const params = { id: 'doc123' };

      // Act
      await documentsRoute.GET(request as any, { params });

      // Assert
      expect(apiProxy.proxyApiRequest).toHaveBeenCalledWith(
        null,
        expect.objectContaining({
          endpoint: '/api/documents/doc123',
          method: 'GET',
        })
      );
    });

    it('should handle document IDs with special characters', async () => {
      // Arrange
      const request = createMockRequest();
      const params = { id: 'doc/with space+special&chars' };

      // Act
      await documentsRoute.GET(request as any, { params });

      // Assert
      expect(apiProxy.proxyApiRequest).toHaveBeenCalledWith(
        null,
        expect.objectContaining({
          endpoint: '/api/documents/doc%2Fwith%20space%2Bspecial%26chars',
          method: 'GET',
        })
      );
    });
  });

  describe('Document Upload API', () => {
    it('should handle POST requests and forward to proxyApiRequest with FormData content type', async () => {
      // Arrange
      const formData = new FormData();
      formData.append('file', new Blob(['test content']), 'test.txt');

      // Create mock request with formData
      const request = {
        json: jest.fn().mockResolvedValue({}),
        body: formData,
        headers: {
          get: jest.fn(),
          has: jest.fn(),
        },
      };

      // Act
      await uploadRoute.POST(request as any);

      // Assert
      expect(apiProxy.proxyApiRequest).toHaveBeenCalledWith(
        request,
        expect.objectContaining({
          endpoint: '/api/documents/upload',
          method: 'POST',
          contentType: 'multipart/form-data',
        })
      );
    });

    it('should reject non-POST methods', async () => {
      // Act & Assert
      const response = await uploadRoute.GET();
      expect(response.status).toBe(405);
    });
  });
});
