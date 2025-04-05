import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import * as Sentry from '@sentry/nextjs';

// This function can be marked `async` if using `await` inside
export function middleware(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const isApiRoute = requestUrl.pathname.startsWith('/api/');

  try {
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
      const isValidReferer = referer &&
        (referer.includes(host || '') ||
         referer.includes('localhost:') ||
         // Add any additional trusted origins here
         process.env.NODE_ENV === 'development'); // Allow any referer in development

      // If external request but not health check, block it
      if (!isValidReferer && !request.headers.has('x-api-internal-req')) {
        console.warn(`Blocked API access: ${requestUrl.pathname} - Invalid referer: ${referer}`);

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
  } catch (error: any) {
    // Log middleware errors to Sentry
    Sentry.captureException(error, {
      tags: {
        component: 'Middleware',
        path: requestUrl.pathname,
      },
      extra: {
        url: request.url,
        method: request.method,
        referer: request.headers.get('referer') || 'none',
      }
    });

    console.error('Middleware error:', error);
  }

  // Continue for non-API routes
  return NextResponse.next();
}

// Only run middleware on API routes
export const config = {
  matcher: '/api/:path*',
};
