import { NextRequest, NextResponse } from 'next/server';
import * as Sentry from '@sentry/nextjs';

interface ProxyOptions {
  endpoint: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: any;
  contentType?: string;
  requestInit?: RequestInit;
}

/**
 * Generic API proxy function to reduce code duplication across route handlers
 */
export async function proxyApiRequest(
  request: NextRequest | null,
  options: ProxyOptions
): Promise<NextResponse> {
  try {
    const { endpoint, method = 'GET', body, contentType = 'application/json', requestInit = {} } = options;

    // Get API URL and token from environment variables
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const apiToken = process.env.NEXT_PUBLIC_API_TOKEN;

    if (!apiUrl) {
      throw new Error('API URL not configured');
    }

    if (!apiToken) {
      throw new Error('API token not configured');
    }

    // Construct the full URL (ensuring it has proper protocol)
    let fullUrl = apiUrl;
    if (!fullUrl.startsWith('http://') && !fullUrl.startsWith('https://')) {
      fullUrl = `https://${fullUrl}`;
    }

    // Set up headers
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${apiToken}`,
      ...(requestInit.headers as Record<string, string> || {}),
    };

    // Only add Content-Type for requests with bodies, or if it's not a FormData request
    if (body && contentType !== 'multipart/form-data') {
      headers['Content-Type'] = contentType;
    }

    // Prepare the request
    const requestOptions: RequestInit = {
      method,
      headers,
      ...requestInit,
    };

    // Add body if needed
    if (body !== undefined) {
      requestOptions.body = body instanceof FormData || body instanceof ReadableStream
        ? body
        : JSON.stringify(body);
    } else if (request?.body) {
      // Pass through request body for FormData uploads
      requestOptions.body = request.body;
    }

    // Make the request to the backend API
    const response = await fetch(`${fullUrl}${endpoint}`, requestOptions);

    // Handle non-successful responses
    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`API error: ${response.status} - ${errorData}`);
    }

    // Return the response from the backend
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    // Log the error to Sentry
    Sentry.captureException(error, {
      tags: {
        component: 'API Proxy',
        endpoint: options.endpoint,
        method: options.method || 'GET',
      },
      extra: {
        message: error.message || 'No error message',
        stack: error.stack || 'No stack trace',
      }
    });

    console.error('API Proxy Error:', error);

    // Return an error response
    return NextResponse.json(
      { error: `Failed to process request: ${error.message}` },
      { status: 500 }
    );
  }
}
