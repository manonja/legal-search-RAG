import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { adminAuth } from '@/lib/firebase-admin'; // Use the initialized Admin SDK
import { SESSION_COOKIE_NAME } from '@/lib/constants';
import { z } from 'zod';
import { Auth } from 'firebase-admin/auth'; // Import Auth type

// Type guard to check if we have the real Admin SDK Auth instance
function isAdminAuth(auth: any): auth is Auth {
  return typeof auth?.verifyIdToken === 'function'; // Check for a method specific to the real SDK
}

// Define schema for the expected request body (POST)
const PostRequestSchema = z.object({
  idToken: z.string().min(1, { message: "ID token is required" }),
});

// Define the session cookie options
const expiresIn = 60 * 60 * 24 * 5 * 1000; // 5 days in milliseconds

/**
 * POST handler to create/update the session cookie.
 * Receives the Firebase ID token from the client.
 */
export async function POST(request: NextRequest) {
  let idToken: string;
  console.log('[API /api/auth/session] POST request received');

  // 1. Validate Request Body
  try {
    const body = await request.json();
    console.log('[API /api/auth/session] Request body received');
    const parsed = PostRequestSchema.safeParse(body);
    if (!parsed.success) {
      console.error('[API /api/auth/session] Invalid request body:', parsed.error.errors);
      return NextResponse.json(
        { error: 'Invalid request body', details: parsed.error.errors },
        { status: 400 }
      );
    }
    idToken = parsed.data.idToken;
    console.log('[API /api/auth/session] ID token validated');
  } catch (error) {
    console.error('[API /api/auth/session] Failed to parse request body:', error);
    return NextResponse.json({ error: 'Failed to parse request body' }, { status: 400 });
  }

  // Check if we have the real Admin SDK
  if (!isAdminAuth(adminAuth)) {
    console.error('[API /api/auth/session] Firebase Admin SDK not properly initialized. Cannot create session.');
    console.error('[API /api/auth/session] Make sure your FIREBASE_PRIVATE_KEY, FIREBASE_PROJECT_ID, and FIREBASE_CLIENT_EMAIL are set correctly in your .env file');
    return NextResponse.json({
      error: 'Server configuration error',
      details: 'Firebase Admin SDK not properly initialized. Please contact the administrator.'
    }, { status: 500 });
  }

  // 2. Verify ID Token & Create Session Cookie
  try {
    // Verify the ID token first. This checks if the token is valid and not expired.
    console.log('[API /api/auth/session] Verifying ID token');
    const decodedToken = await adminAuth.verifyIdToken(idToken);
    console.log('[API /api/auth/session] ID token verified for user:', decodedToken.uid);

    // Set session expiration to 14 days.
    const expiresIn = 60 * 60 * 24 * 14 * 1000;
    console.log('[API /api/auth/session] Creating session cookie');
    const sessionCookie = await adminAuth.createSessionCookie(idToken, { expiresIn });
    console.log('[API /api/auth/session] Session cookie created');

    // 3. Set the session cookie in the response
    const options = {
      name: SESSION_COOKIE_NAME,
      value: sessionCookie,
      maxAge: expiresIn / 1000, // maxAge is in seconds
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production', // Use secure cookies in production
      path: '/', // Cookie available across the entire site
      sameSite: 'lax' as const, // Helps mitigate CSRF attacks
    };

    // Set cookie using the ResponseCookies API
    const response = NextResponse.json({ status: 'success', message: 'Session cookie set successfully' }, { status: 200 });
    response.cookies.set(options);

    console.log(`[API /api/auth/session] Session cookie set successfully for user: ${decodedToken.uid}`);
    return response;

  } catch (error: any) {
    console.error('[API /api/auth/session] Error creating session cookie:', error.message);
    return NextResponse.json({ error: 'Failed to create session cookie', details: error.message }, { status: 401 }); // Unauthorized or bad token
  }
}

/**
 * DELETE handler to clear the session cookie.
 */
export async function DELETE(request: NextRequest) {
  const sessionCookieValue = cookies().get(SESSION_COOKIE_NAME)?.value;

  if (!sessionCookieValue) {
    // No session to clear, maybe already logged out
    return NextResponse.json({ status: 'success', message: 'No active session found' }, { status: 200 });
  }

  // Check if we have the real Admin SDK
  if (!isAdminAuth(adminAuth)) {
    console.error('[API /api/auth/session] Firebase Admin SDK not properly initialized. Cannot clear session cleanly.');
    // Still attempt to clear cookie client-side even if server-side fails
     const response = NextResponse.json({ error: 'Server configuration error, attempting client-side clear.' }, { status: 500 });
     response.cookies.set({
      name: SESSION_COOKIE_NAME,
      value: '',
      maxAge: -1,
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      path: '/',
      sameSite: 'lax' as const,
    });
    return response;
  }

  try {
    // Verify the session cookie to get the UID before revoking tokens
    const decodedClaims = await adminAuth.verifySessionCookie(sessionCookieValue);

    // Revoke refresh tokens for the user
    if (decodedClaims) {
        await adminAuth.revokeRefreshTokens(decodedClaims.uid);
    }

    // Clear the cookie by setting an expired one
    const options = {
      name: SESSION_COOKIE_NAME,
      value: '',
      maxAge: -1, // Expire immediately
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      path: '/',
      sameSite: 'lax' as const,
    };

    const response = NextResponse.json({ status: 'success' }, { status: 200 });
    response.cookies.set(options);

    console.log(`[API /api/auth/session] Session cookie cleared successfully for UID: ${decodedClaims?.uid ?? 'unknown'}`);
    return response;

  } catch (error: any) {
    console.error('[API /api/auth/session] Error clearing session cookie:', error.message);
    // Even if verification/revocation fails, attempt to clear the cookie client-side
    const response = NextResponse.json({ error: 'Failed to properly clear session on server', details: error.message }, { status: 500 });
     response.cookies.set({
      name: SESSION_COOKIE_NAME,
      value: '',
      maxAge: -1,
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      path: '/',
      sameSite: 'lax' as const,
    });
    return response;
  }
}
