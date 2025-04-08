import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import * as Sentry from '@sentry/nextjs';
import { adminAuth } from './lib/firebaseAdmin'; // Import Admin SDK Auth

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

async function verifyAuth(request: NextRequest): Promise<{ uid: string | null; isAdmin: boolean; error?: any }> {
  const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME)?.value;

  if (!sessionCookie) {
    return { uid: null, isAdmin: false };
  }

  try {
    // Verify the session cookie. `checkRevoked` is true.
    const decodedClaims = await adminAuth.verifySessionCookie(sessionCookie, true);
    const isAdmin = decodedClaims.admin === true; // Check for custom admin claim
    return { uid: decodedClaims.uid, isAdmin };
  } catch (error: any) {
    // Session cookie is invalid or revoked. Firebase error codes:
    // auth/session-cookie-expired, auth/session-cookie-revoked, auth/argument-error
    console.warn(`Auth verification error: ${error.code}`);
    return { uid: null, isAdmin: false, error };
  }
}

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

  // --- Handle API Routes ---
  if (pathname.startsWith('/api/')) {
    // Allow public API routes
    if (PUBLIC_API_ROUTES.some(route => pathname === route)) {
        return NextResponse.next();
    }

    // --- Verify Session for non-public API routes ---
    const { uid: apiUid, error: apiAuthError } = await verifyAuth(request);
    if (!apiUid) {
        console.warn(`API Auth failed for ${pathname}: ${apiAuthError?.code || 'No session'}`);
        return new NextResponse(JSON.stringify({ error: 'Authentication required' }), { status: 401 });
    }

    // TODO: Potentially add role checks for specific API routes if needed
    // e.g., if (pathname.startsWith('/api/admin/') && !isAdmin) { return 403 }

    // --- Existing Referer Check (Optional - depends if APIs are exclusively internal) ---
    // You might remove this if session validation is sufficient, or keep it for extra defense
    const referer = request.headers.get('referer');
    const host = request.headers.get('host');
    const isValidReferer =
      referer &&
      (referer.includes(host || '') || referer.includes('localhost:') || process.env.NODE_ENV === 'development');

    if (!isValidReferer && !request.headers.has('x-api-internal-req')) {
      console.warn(`Blocked API access: ${pathname} - Invalid referer: ${referer || 'undefined'}`);
      return new NextResponse(JSON.stringify({ error: 'Unauthorized access' }), { status: 403 });
    }

    // If all checks pass for API route
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

  // Verify authentication status
  const { uid, isAdmin, error: authError } = await verifyAuth(request);

  if (!uid) {
    // Not authenticated
    if (requiresAuth) {
        console.log(`Redirecting unauthenticated user from ${pathname} to /login`);
        // Redirect to login, preserving the intended destination
        const loginUrl = new URL('/login', request.url);
        loginUrl.searchParams.set('redirect', pathname);
        return NextResponse.redirect(loginUrl);
    }
    // If it's not a specifically protected route, allow (might be handled by page logic)
    return NextResponse.next();
  }

  // User is authenticated (uid exists)

  // If trying to access auth pages (login/signup) while logged in, redirect to dashboard
  if (pathname === '/login' || pathname === '/signup') {
    console.log(`Redirecting authenticated user from ${pathname} to /dashboard`);
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Check for admin role if accessing an admin route
  if (isAdminRoute && !isAdmin) {
    console.log(`Redirecting non-admin user from ${pathname} to /dashboard`);
    // Redirect non-admins trying to access admin pages
    return NextResponse.redirect(new URL('/dashboard', request.url)); // Or an unauthorized page
  }

  // If authenticated and authorized for the route, allow access
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
