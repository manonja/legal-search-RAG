import axios from 'axios';
import { api } from '@/lib/api';
import * as Sentry from '@sentry/nextjs';
import { constructApiUrl } from '@/lib/utils';

// Set up Node globals needed for tests
if (typeof window === 'undefined') {
  global.FormData = require('form-data');
}

// Mock dependencies
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

jest.mock('@sentry/nextjs', () => ({
  captureException: jest.fn(),
}));

jest.mock('@/lib/utils', () => ({
  constructApiUrl: jest.fn().mockReturnValue('https://api.example.com'),
}));

describe('API Client', () => {
  const originalEnv = process.env;
  // Mock localStorage
  const mockLocalStorage: Record<string, any> = {
    getItem: jest.fn().mockReturnValue(null),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
    length: 0,
    key: jest.fn(),
  };

  // Store interceptors for testing
  let requestInterceptor: any;
  let responseErrorInterceptor: any;

  beforeEach(() => {
    jest.clearAllMocks();

    // Set up localStorage mock
    Object.defineProperty(global, 'localStorage', {
      value: mockLocalStorage,
      writable: true
    });

    // Mock environment variables
    process.env = {
      ...originalEnv,
      NEXT_PUBLIC_API_TOKEN: 'env-token-123',
    };

    // Mock axios's interceptor methods
    mockedAxios.interceptors = {
      request: {
        use: jest.fn((onFulfilled) => {
          requestInterceptor = onFulfilled;
          return 0; // Return a number as the interceptor ID
        }),
        eject: jest.fn(),
      },
      response: {
        use: jest.fn((onFulfilled, onRejected) => {
          responseErrorInterceptor = onRejected;
          return 0; // Return a number as the interceptor ID
        }),
        eject: jest.fn(),
      },
    } as any;

    // Mock axios create
    mockedAxios.create.mockReturnValue(mockedAxios);

    // Mock successful response
    mockedAxios.post.mockResolvedValue({
      data: { success: true, results: [{ id: '123' }] },
    });

    mockedAxios.get.mockResolvedValue({
      data: { success: true, data: { id: '123' } },
    });

    // Force initialization of the API client
    // This will register the interceptors
    jest.isolateModules(() => {
      require('@/lib/api');
    });
  });

  afterAll(() => {
    process.env = originalEnv;
    // Restore globals by setting to undefined
    Object.defineProperty(global, 'localStorage', {
      value: undefined,
      writable: true
    });
  });

  describe('API Client Initialization', () => {
    it('should initialize with correct base URL', () => {
      // Assert
      expect(constructApiUrl).toHaveBeenCalled();
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: 'https://api.example.com',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });
  });

  describe('Request Interceptor', () => {
    it('should add token from environment variable', () => {
      // Arrange
      const config = { headers: {} };

      // Act
      const result = requestInterceptor(config);

      // Assert
      expect(result.headers.Authorization).toBe('Bearer env-token-123');
    });

    it('should use token from localStorage when env token is not available', () => {
      // Arrange
      delete process.env.NEXT_PUBLIC_API_TOKEN;
      mockLocalStorage.getItem.mockReturnValue('storage-token-456');
      const config = { headers: {} };

      // Act
      const result = requestInterceptor(config);

      // Assert
      expect(result.headers.Authorization).toBe('Bearer storage-token-456');
    });

    it('should handle when no token is available', () => {
      // Arrange
      delete process.env.NEXT_PUBLIC_API_TOKEN;
      mockLocalStorage.getItem.mockReturnValue(null);
      const config = { headers: {} };

      // Act
      const result = requestInterceptor(config);

      // Assert
      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should handle errors and report to Sentry', () => {
      // Arrange
      const error = new Error('Request interceptor error');
      const configWithError = { headers: { get: () => { throw error; } } };

      // Act & Assert
      expect(() => requestInterceptor(configWithError)).toThrow();

      // Should report to Sentry
      expect(Sentry.captureException).toHaveBeenCalledWith(
        error,
        expect.objectContaining({
          tags: expect.objectContaining({
            component: 'API',
            stage: 'requestSetup',
          }),
        })
      );
    });
  });

  describe('Response Interceptor', () => {
    it('should handle API errors and report to Sentry', async () => {
      // Arrange
      const error = {
        message: 'API Error',
        code: 'ERR_BAD_REQUEST',
        response: { status: 400, data: { error: 'Bad request' } },
        config: { url: '/api/test', method: 'GET' },
        stack: 'Error stack trace',
      };

      // Act & Assert
      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);

      // Should report to Sentry
      expect(Sentry.captureException).toHaveBeenCalledWith(
        error,
        expect.objectContaining({
          tags: expect.objectContaining({
            component: 'API',
            status: 400,
            url: '/api/test',
          }),
          extra: expect.objectContaining({
            method: 'GET',
            responseData: { error: 'Bad request' },
          }),
        })
      );
    });

    it('should handle network errors with no response', async () => {
      // Arrange
      const error = {
        message: 'Network Error',
        code: 'ERR_NETWORK',
        config: { url: '/api/test', method: 'GET' },
      };

      // Act & Assert
      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);

      // Should report to Sentry
      expect(Sentry.captureException).toHaveBeenCalledWith(
        error,
        expect.objectContaining({
          tags: expect.objectContaining({
            component: 'API',
            status: 0,
          }),
        })
      );
    });
  });

  describe('API Functions', () => {
    it('should call searchDocuments with correct parameters', async () => {
      // Arrange
      const searchQuery = { query: 'test', limit: 10 };

      // Act
      await api.searchDocuments(searchQuery);

      // Assert
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/search/',
        searchQuery
      );
    });

    it('should call legacySearchDocuments with correct parameters', async () => {
      // Arrange
      const legacyQuery = { query_text: 'test', n_results: 5 };

      // Act
      await api.legacySearchDocuments(legacyQuery);

      // Assert
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/search/api',
        legacyQuery
      );
    });

    it('should call ragSearch with correct parameters', async () => {
      // Arrange
      const ragQuery = { query: 'test', max_results: 3 };

      // Act
      await api.ragSearch(ragQuery);

      // Assert
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/rag-search',
        ragQuery
      );
    });

    it('should call queryDocuments with correct parameters', async () => {
      // Arrange
      const query = { query: 'test question', max_tokens: 500 };

      // Act
      await api.queryDocuments(query);

      // Assert
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/query',
        query
      );
    });

    it('should call getDocument with correct parameters', async () => {
      // Arrange
      const documentId = 'doc123';

      // Act
      await api.getDocument(documentId);

      // Assert
      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/documents/doc123'
      );
    });

    it('should call uploadDocument with correct parameters', async () => {
      // Arrange
      const mockFile = {
        name: 'test.txt',
        type: 'text/plain',
        size: 123,
      } as File;

      // Act
      await api.uploadDocument(mockFile);

      // Assert
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/documents/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
      );
    });

    it('should call healthCheck with correct parameters', async () => {
      // Act
      await api.healthCheck();

      // Assert
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/health');
    });

    it('should handle errors in API functions', async () => {
      // Arrange
      const error = new Error('API error');
      mockedAxios.post.mockRejectedValueOnce(error);

      // Act & Assert
      await expect(api.searchDocuments({ query: 'test' })).rejects.toThrow();
    });
  });
});
