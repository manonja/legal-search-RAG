import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import * as Sentry from '@sentry/nextjs';
import { SESSION_COOKIE_NAME } from '@/lib/constants'; // Assuming you have this constant defined
// import { adminAuth } from '@/lib/firebase-admin'; // DO NOT use firebase-admin in middleware

// Define protected routes requiring authentication
const protectedRoutes = ['/dashboard', '/admin', '/search', '/rag-search']; // Add any other protected routes
// Define routes accessible only by unauthenticated users
const authRoutes = ['/login', '/signup'];
// Define public routes (accessible to everyone)
// Let's assume '/', '/search', '/rag-search', '/book-demo', '/about' are public
// The matcher config will primarily handle inclusion/exclusion

// Middleware performs optimistic checks and redirects based on cookie presence.
// Actual session verification MUST happen in Server Components or API Routes.
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME)?.value;

  console.log(`[Middleware] Processing ${pathname} (Session Cookie: ${sessionCookie ? 'Present' : 'Absent'})`);

  try {
    const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
    const isAuthRoute = authRoutes.some(route => pathname.startsWith(route));

    // 1. Redirect unauthenticated users from protected routes (optimistic check)
    if (isProtectedRoute && !sessionCookie) {
      const url = request.nextUrl.clone();
      url.pathname = '/login';
      url.searchParams.set('redirectedFrom', pathname);
      url.searchParams.set('bypassAuthRedirect', 'true'); // Ensure they can access the login page
      console.log(`[Middleware] No session cookie found for protected route ${pathname}, redirecting to /login`);
      return NextResponse.redirect(url);
    }

    // 2. Redirect authenticated users from auth routes (optimistic check)
    if (isAuthRoute && sessionCookie) {
      // Allow manual access to login page with a special query parameter
      // This ensures users can access login/signup pages when needed
      if (request.nextUrl.searchParams.get('bypassAuthRedirect') === 'true') {
        console.log(`[Middleware] Bypassing auth route redirection for ${pathname} with bypass parameter`);
        return NextResponse.next();
      }

      const url = request.nextUrl.clone();
      url.pathname = '/'; // Redirect to home
      console.log(`[Middleware] Session cookie found for auth route ${pathname}, redirecting to /`);
      return NextResponse.redirect(url);
    }

    // 3. Handle API Route Protection (Example - can keep referer check, remove auth here)
    if (pathname.startsWith('/api/')) {
      if (pathname === '/api/health') {
        return NextResponse.next();
      }
      // API routes MUST verify the session cookie internally using Firebase Admin SDK
      // Example check REMOVED as userId is not available here
      // const requiresAuth = [\'/api/documents\', \'/api/query\'].some(route => pathname.startsWith(route));
      // if (requiresAuth && !userId) { // userId is not available here
      //   console.log(`[Middleware] Unauthenticated API access attempt to ${pathname}`);\n      //   return NextResponse.json({ error: \'Authentication required\' }, { status: 401 });\n      // }\n

      // Optional: Keep Referer Check for basic CSRF protection
      if (process.env.NODE_ENV === 'production') {
        const referer = request.headers.get('referer');
        const host = request.headers.get('host');
        const isInternal = request.headers.get('x-api-internal-req') === '1';
        if (!isInternal && (!referer || !host || new URL(referer).host !== host)) {
          const allowedReferer = referer && new URL(referer).hostname === 'localhost';
          if (!allowedReferer) {
            console.warn(`[Middleware] Blocked external API request to ${pathname} from referer: ${referer}`);
            return NextResponse.json({ error: 'Unauthorized access' }, { status: 403 });
          }
        }
      }
      const response = NextResponse.next();
      response.headers.set('x-api-internal-req', '1'); // Still useful for non-auth API routes
      return response;
    }

    // 4. Allow request to proceed
    console.log(`[Middleware] Allowed access to ${pathname} (Cookie ${sessionCookie ? 'Present' : 'Absent'})`);
    return NextResponse.next();

  } catch (error) {
    console.error(`[Middleware] Error processing request for ${pathname}:`, error);
    Sentry.captureException(error, {
      extra: {
        pathname: pathname,
        hasSessionCookie: !!sessionCookie,
        // userIdAttempted: userId, // REMOVED userId reference
      },
    });
    return NextResponse.next(); // Allow request even on error
  }
}

// Matcher configuration: applies middleware to specified paths
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - /manifest.json (PWA manifest)
     * - /robots.txt (SEO robots file)
     * - Files with extensions like .png, .jpg, .svg etc.
     */
    '/((?!_next/static|_next/image|favicon.ico|manifest.json|robots.txt|.*\\.(?:png|jpg|jpeg|gif|svg|webp)$).*)',
    // Apply specifically to API routes if the general matcher misses them (optional)
    // '/api/:path*',
  ],
};
