import * as Sentry from '@sentry/nextjs';
import { middleware } from '@/middleware';

// Mock dependencies
jest.mock('@sentry/nextjs', () => ({
  captureException: jest.fn(),
}));

// Mock Next.js modules completely instead of using requireActual
jest.mock('next/server', () => {
  const originalModule = jest.requireActual('next/server');

  // Mock the constructor - this function will be called with 'new NextResponse(...)'
  const mockConstructor = jest.fn((body, init) => ({
    body,
    init,
    headers: new Map([['Content-Type', 'application/json']]), // Mock instance properties
    // Add other instance methods/properties if needed by the code under test, e.g., status
    status: init?.status || 200,
  }));

  // Attach static methods mocks directly to the mock constructor function
  (mockConstructor as any).next = jest.fn().mockReturnValue({
    headers: { // Mock the returned object from next()
      set: jest.fn(),
      get: jest.fn(),
      has: jest.fn(),
      // Ensure it's iterable or provide necessary methods if tests need them
      [Symbol.iterator]: jest.fn(),
      entries: jest.fn(() => [['x-api-internal-req', '1']]),
      keys: jest.fn(),
      values: jest.fn(),
    },
    // Add other properties of the object returned by next() if needed
    ok: true,
    status: 200,
  });

  (mockConstructor as any).json = jest.fn((body, init) => ({ // Mock the returned object from json()
    body,
    init,
    headers: new Map([['Content-Type', 'application/json']]),
    ok: init?.status ? init.status >= 200 && init.status < 300 : true,
    status: init?.status || 200,
  }));

  return {
    ...originalModule,
    NextResponse: mockConstructor, // Use the function with attached static methods as the mock
  };
});

// Import after mocking
import { NextResponse } from 'next/server';

// Mock process.env
const originalEnv = process.env;

describe('Middleware', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Reset process.env for each test
    process.env = { ...originalEnv };
    // Set default environment to development
    jest.replaceProperty(process.env, 'NODE_ENV', 'development');
  });

  afterAll(() => {
    // Restore process.env
    process.env = originalEnv;
  });

  // Helper to create a mock NextRequest
  const createMockRequest = (
    path: string,
    referer?: string,
    host?: string,
    headers?: Record<string, string>
  ) => {
    const url = `https://example.com${path}`;

    const headersObj = new Map();
    if (referer) headersObj.set('referer', referer);
    if (host) headersObj.set('host', host);

    if (headers) {
      Object.entries(headers).forEach(([key, value]) => {
        headersObj.set(key, value);
      });
    }

    return {
      url: url,
      nextUrl: new URL(url),
      headers: {
        get: (name: string) => headersObj.get(name),
        has: (name: string) => headersObj.has(name),
      },
      method: 'GET',
    };
  };

  it('should allow non-API routes to pass through', () => {
    // Arrange
    const request = createMockRequest('/non-api-route');

    // Act
    middleware(request as any);

    // Assert
    expect(NextResponse.next).toHaveBeenCalled();
  });

  it('should allow health check endpoint from any source', () => {
    // Arrange - no referer or host
    const request = createMockRequest('/api/health');

    // Act
    middleware(request as any);

    // Assert
    expect(NextResponse.next).toHaveBeenCalled();
    // No request rejection
    expect(NextResponse.json).not.toHaveBeenCalled();
  });

  it('should allow API requests with a valid referer from the same host', () => {
    // Arrange
    const host = 'example.com';
    const referer = 'https://example.com/some-page';
    const request = createMockRequest('/api/search', referer, host);

    // Act
    middleware(request as any);

    // Assert
    expect(NextResponse.next).toHaveBeenCalled();
    // The middleware should add the internal request header
    expect(NextResponse.next().headers.set).toHaveBeenCalledWith(
      'x-api-internal-req',
      '1'
    );
  });

  it('should allow API requests with a valid localhost referer', () => {
    // Arrange
    const referer = 'http://localhost:3000/some-page';
    const request = createMockRequest('/api/search', referer, 'example.com');

    // Act
    middleware(request as any);

    // Assert
    expect(NextResponse.next).toHaveBeenCalled();
  });

  it('should allow API requests with the internal req header already set', () => {
    // Arrange
    const request = createMockRequest(
      '/api/search',
      undefined,
      'example.com',
      { 'x-api-internal-req': '1' }
    );

    // Act
    middleware(request as any);

    // Assert
    expect(NextResponse.next).toHaveBeenCalled();
  });

  it('should block API requests from external referers in production', () => {
    // Arrange
    jest.replaceProperty(process.env, 'NODE_ENV', 'production');
    const referer = 'https://malicious-site.com/page';
    const request = createMockRequest('/api/search', referer, 'example.com');

    // Act
    middleware(request as any);

    // Assert
    expect(NextResponse).toHaveBeenCalledWith(
      JSON.stringify({ error: 'Unauthorized access' }),
      expect.objectContaining({
        status: 403,
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      })
    );
    expect(NextResponse.next).not.toHaveBeenCalled();
  });

  it('should allow any referer in development environment', () => {
    // Arrange - NODE_ENV is already set to 'development' in beforeEach
    const referer = 'https://external-site.com/page';
    const request = createMockRequest('/api/search', referer, 'example.com');

    // Act
    middleware(request as any);

    // Assert
    expect(NextResponse.next).toHaveBeenCalled();
  });

  it('should handle middleware errors and report to Sentry', () => {
    // Arrange
    const request = createMockRequest('/api/search');

    // Simulate an error by forcing URL to throw
    Object.defineProperty(request, 'url', {
      get: () => {
        throw new Error('Simulated URL error');
      },
    });

    // Act
    middleware(request as any);

    // Assert
    expect(Sentry.captureException).toHaveBeenCalledWith(
      expect.objectContaining({ message: 'Simulated URL error' }),
      expect.anything()
    );
    expect(NextResponse.next).toHaveBeenCalled();
  });

  it('should block API requests without a referer in production', () => {
    // Arrange
    jest.replaceProperty(process.env, 'NODE_ENV', 'production');
    const request = createMockRequest('/api/search', undefined, 'example.com');

    // Act
    middleware(request as any);

    // Assert
    expect(NextResponse).toHaveBeenCalledWith(
      JSON.stringify({ error: 'Unauthorized access' }),
      expect.objectContaining({
        status: 403,
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      })
    );
    expect(NextResponse.next).not.toHaveBeenCalled();
  });
});
