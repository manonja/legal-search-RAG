import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import * as Sentry from '@sentry/nextjs';

// This function can be marked `async` if using `await` inside
export function middleware(request: NextRequest) {
  try {
    const requestUrl = new URL(request.url);
    const isApiRoute = requestUrl.pathname.startsWith('/api/');

    // Only apply to API routes
    if (isApiRoute) {
      // Allow health checks from any source
      if (requestUrl.pathname === '/api/health') {
        return NextResponse.next();
      }

      // Get the referer to check if the request is coming from our own frontend
      const referer = request.headers.get('referer');
      const host = request.headers.get('host');

      // Check if the request has a valid referer from our own domain or localhost
      const isValidReferer =
        referer &&
        (referer.includes(host || '') ||
          referer.includes('localhost:') ||
          // Add any additional trusted origins here
          process.env.NODE_ENV === 'development'); // Allow any referer in development

      // If external request but not health check, block it
      if (!isValidReferer && !request.headers.has('x-api-internal-req')) {
        console.warn(
          `Blocked API access: ${requestUrl.pathname} - Invalid referer: ${
            referer || 'undefined'
          }`
        );

        return new NextResponse(
          JSON.stringify({ error: 'Unauthorized access' }),
          {
            status: 403,
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );
      }

      // Request is valid, add a custom header to mark it as internally verified
      const response = NextResponse.next();
      response.headers.set('x-api-internal-req', '1');
      return response;
    }

    // Continue for non-API routes that didn't throw an error
    return NextResponse.next();

  } catch (error: any) {
    // Log middleware errors to Sentry
    console.error('Middleware error caught:', error);

    // Capture the error without trying to access potentially faulty request properties
    Sentry.captureException(error, {
      tags: {
        component: 'Middleware',
        path: '(error during request processing)',
      },
      extra: {
        // Only include safe-to-access properties like referer
        referer: request?.headers?.get('referer') || 'none',
      },
    });

    // Return a response even in case of error, as expected by the test
    return NextResponse.next();
  }
}

// Only run middleware on API routes
export const config = {
  matcher: '/api/:path*',
};
