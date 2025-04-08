import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import * as Sentry from '@sentry/nextjs';

const SESSION_COOKIE_NAME = '__session';

// --- Define Protected & Public Routes ---
// Add routes that require authentication
const AUTH_REQUIRED_ROUTES = ['/dashboard', '/search', '/rag-search']; // Example protected pages
// Add routes that require admin role
const ADMIN_REQUIRED_ROUTES = ['/admin']; // Example admin page
// Public routes accessible without login
const PUBLIC_ROUTES = ['/', '/login', '/signup', '/about', '/book-demo'];
// Public API routes (login/logout itself, health checks)
const PUBLIC_API_ROUTES = ['/api/health', '/api/auth/session'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const requestUrl = new URL(request.url);

  // --- Bypass checks for static files and Next.js internals ---
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/static/') ||
    pathname.includes('.') // Assume files with extensions are static assets
   ) {
    return NextResponse.next();
  }

  const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME)?.value;

  // --- Handle API Routes ---
  if (pathname.startsWith('/api/')) {
    // Allow public API routes
    if (PUBLIC_API_ROUTES.some(route => pathname === route)) {
        return NextResponse.next();
    }

    // For non-public API routes, check for session cookie presence
    if (!sessionCookie) {
        console.warn(`API Auth failed for ${pathname}: No session cookie`);
        return new NextResponse(JSON.stringify({ error: 'Authentication required' }), { status: 401 });
    }

    // Actual verification will happen within the API route handler itself
    // using adminAuth.verifySessionCookie

    // Optional Referer Check (kept for now)
    const referer = request.headers.get('referer');
    const host = request.headers.get('host');
    const isValidReferer =
      referer &&
      (referer.includes(host || '') || referer.includes('localhost:') || process.env.NODE_ENV === 'development');

    if (!isValidReferer && !request.headers.has('x-api-internal-req')) {
      console.warn(`Blocked API access: ${pathname} - Invalid referer: ${referer || 'undefined'}`);
      return new NextResponse(JSON.stringify({ error: 'Unauthorized access' }), { status: 403 });
    }

    // Cookie exists and referer is valid (if checked)
    return NextResponse.next();
  }

  // --- Handle Page Routes ---

  // Check if the route requires authentication
  const requiresAuth = AUTH_REQUIRED_ROUTES.some(route => pathname.startsWith(route)) ||
                     ADMIN_REQUIRED_ROUTES.some(route => pathname.startsWith(route));
  const isAdminRoute = ADMIN_REQUIRED_ROUTES.some(route => pathname.startsWith(route));
  const isPublicRoute = PUBLIC_ROUTES.some(route => pathname === route);

  if (isPublicRoute && !requiresAuth) {
    // Allow access to public routes
    return NextResponse.next();
  }

  // Handle protected routes
  if (requiresAuth) {
      if (!sessionCookie) {
          // No cookie, redirect to login
          console.log(`Redirecting unauthenticated user from ${pathname} to /login (no cookie)`);
          const loginUrl = new URL('/login', request.url);
          loginUrl.searchParams.set('redirect', pathname);
          return NextResponse.redirect(loginUrl);
      }
      // Cookie exists, let the request through.
      // Verification and role checks happen in Server Components/Page logic.
      return NextResponse.next();
  }

  // Handle auth pages (login/signup) when a cookie *exists*
  // Redirect logged-in users away from login/signup
  if ((pathname === '/login' || pathname === '/signup') && sessionCookie) {
      // We don't know for *sure* they are validly logged in here, but they have a cookie.
      // Redirecting to dashboard is usually the desired UX.
      // The dashboard page itself MUST verify the cookie.
      console.log(`Redirecting user with session cookie from ${pathname} to /dashboard`);
      return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Allow any other routes (e.g., public pages not explicitly listed)
  return NextResponse.next();
}

// Update the matcher to include pages and API routes
export const config = {
  // Match all routes except static files and internal Next.js paths
  matcher: [
    '/((?!_next/static|favicon.ico|.*\\..*).)*', // Match general paths, excluding static files
    // Explicitly include API routes if needed beyond the general matcher
    // '/api/:path*',
  ],
};
