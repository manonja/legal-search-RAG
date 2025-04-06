import * as Sentry from '@sentry/nextjs';
import { proxyApiRequest } from '@/lib/apiProxy';

// Mock NextResponse before importing
jest.mock('next/server', () => ({
  NextResponse: {
    json: jest.fn((data, init) => ({ data, init })),
  },
}));

// Import after mocking
import { NextResponse } from 'next/server';

jest.mock('@sentry/nextjs', () => ({
  captureException: jest.fn(),
}));

// Mock fetch globally
global.fetch = jest.fn();

describe('apiProxy', () => {
  // Store original env vars and restore after tests
  const originalEnv = process.env;

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();

    // Mock environment variables
    process.env = {
      ...originalEnv,
      NEXT_PUBLIC_API_URL: 'api.example.com',
      NEXT_PUBLIC_API_TOKEN: 'test-token-123',
    };

    // Mock successful fetch response
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: { id: '123' } }),
      text: async () => '{"success": true}',
    });
  });

  afterAll(() => {
    // Restore env vars
    process.env = originalEnv;
  });

  // Helper function to create a mock NextRequest
  const createMockRequest = (body?: any) => {
    const request = {
      json: jest.fn().mockResolvedValue(body || { test: 'data' }),
      body: body instanceof FormData ? body : undefined,
      headers: {
        get: jest.fn(),
        has: jest.fn(),
      },
    };
    return request;
  };

  describe('proxyApiRequest', () => {
    it('should proxy a GET request correctly', async () => {
      // Arrange
      const request = createMockRequest();
      const options = {
        endpoint: '/api/test',
        method: 'GET' as const,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.any(Headers),
        })
      );
      // Check specific header on the Headers object
      const actualHeaders = (global.fetch as jest.Mock).mock.calls[0][1].headers as Headers;
      expect(actualHeaders.get('Authorization')).toBe('Bearer test-token-123');
    });

    it('should handle POST requests with JSON body', async () => {
      // Arrange
      const body = { name: 'Test', query: 'search term' };
      const request = createMockRequest(body);
      const options = {
        endpoint: '/api/search',
        method: 'POST' as const,
        body,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/search',
        expect.objectContaining({
          method: 'POST',
          headers: expect.any(Headers),
          body: JSON.stringify(body),
        })
      );
      // More specific header check
      const actualHeaders = (global.fetch as jest.Mock).mock.calls[0][1].headers as Headers;
      expect(actualHeaders.get('Authorization')).toBe('Bearer test-token-123');
      expect(actualHeaders.get('Content-Type')).toBe('application/json');
    });

    it('should handle FormData correctly', async () => {
      // Arrange
      const formData = new FormData();
      formData.append('file', new Blob(['test content']), 'test.txt');

      // Create mock request with formData
      const mockRequestWithFormData = {
        json: jest.fn().mockResolvedValue({}),
        body: formData,
        headers: {
          get: jest.fn(),
          has: jest.fn(),
        },
      };

      const options = {
        endpoint: '/api/documents/upload',
        method: 'POST' as const,
        contentType: 'multipart/form-data',
      };

      // Act
      await proxyApiRequest(mockRequestWithFormData as any, options);

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/documents/upload',
        expect.objectContaining({
          method: 'POST',
          headers: expect.any(Headers), // Check for Headers object type
          body: formData,
        })
      );

      // Should not include Content-Type header for FormData
      const actualHeadersFD = (global.fetch as jest.Mock).mock.calls[0][1].headers as Headers;
      expect(actualHeadersFD.has('Content-Type')).toBe(false);
    });

    it('should handle API URL without protocol', async () => {
      // Arrange
      process.env.NEXT_PUBLIC_API_URL = 'api.noprotocol.com';
      const request = createMockRequest();
      const options = {
        endpoint: '/api/test',
        method: 'GET' as const,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.noprotocol.com/api/test',
        expect.anything()
      );
    });

    it('should handle API URL with http protocol', async () => {
      // Arrange
      process.env.NEXT_PUBLIC_API_URL = 'http://api.example.com';
      const request = createMockRequest();
      const options = {
        endpoint: '/api/test',
        method: 'GET' as const,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        'http://api.example.com/api/test',
        expect.anything()
      );
    });

    it('should throw when API URL is not configured', async () => {
      // Arrange
      delete process.env.NEXT_PUBLIC_API_URL;
      const request = createMockRequest();
      const options = {
        endpoint: '/api/test',
        method: 'GET' as const,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(Sentry.captureException).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'API URL not configured',
        }),
        expect.anything()
      );
      expect(NextResponse.json).toHaveBeenCalledWith(
        expect.objectContaining({
          error: expect.stringContaining('API URL not configured'),
        }),
        expect.objectContaining({ status: 500 })
      );
    });

    it('should throw when API token is not configured', async () => {
      // Arrange
      delete process.env.NEXT_PUBLIC_API_TOKEN;
      const request = createMockRequest();
      const options = {
        endpoint: '/api/test',
        method: 'GET' as const,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(Sentry.captureException).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'API token not configured',
        }),
        expect.anything()
      );
      expect(NextResponse.json).toHaveBeenCalledWith(
        expect.objectContaining({
          error: expect.stringContaining('API token not configured'),
        }),
        expect.objectContaining({ status: 500 })
      );
    });

    it('should handle API error response', async () => {
      // Arrange
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
        text: async () => 'Document not found',
      });

      const request = createMockRequest();
      const options = {
        endpoint: '/api/documents/999',
        method: 'GET' as const,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(Sentry.captureException).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'API error: 404 - Document not found',
        }),
        expect.objectContaining({
          tags: expect.objectContaining({
            endpoint: '/api/documents/999',
          }),
        })
      );
      expect(NextResponse.json).toHaveBeenCalledWith(
        expect.objectContaining({
          error: expect.stringContaining('API error: 404'),
        }),
        expect.objectContaining({ status: 500 })
      );
    });

    it('should handle fetch errors', async () => {
      // Arrange
      const networkError = new Error('Network error');
      (global.fetch as jest.Mock).mockRejectedValue(networkError);

      const request = createMockRequest();
      const options = {
        endpoint: '/api/test',
        method: 'GET' as const,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(Sentry.captureException).toHaveBeenCalledWith(
        networkError,
        expect.anything()
      );
      expect(NextResponse.json).toHaveBeenCalledWith(
        expect.objectContaining({
          error: expect.stringContaining('Network error'),
        }),
        expect.objectContaining({ status: 500 })
      );
    });

    it('should use custom content type if provided', async () => {
      // Arrange
      const body = { xmlData: '<test></test>' };
      const request = createMockRequest();
      const options = {
        endpoint: '/api/custom',
        method: 'POST' as const,
        body,
        contentType: 'application/xml',
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/custom',
        expect.objectContaining({
          headers: expect.any(Headers),
          body: JSON.stringify(body),
        })
      );
      // More specific header check
      const actualHeadersCustom = (global.fetch as jest.Mock).mock.calls[0][1].headers as Headers;
      expect(actualHeadersCustom.get('Content-Type')).toBe('application/xml');
    });

    it('should include additional request options if provided', async () => {
      // Arrange
      const request = createMockRequest();
      const options = {
        endpoint: '/api/test',
        method: 'GET' as const,
        requestInit: {
          cache: 'no-cache',
          credentials: 'include',
        } as RequestInit,
      };

      // Act
      await proxyApiRequest(request as any, options);

      // Assert
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/test',
        expect.objectContaining({
          cache: 'no-cache',
          credentials: 'include',
        })
      );
    });
  });
});
