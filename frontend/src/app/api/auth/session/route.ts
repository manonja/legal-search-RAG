import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { adminAuth } from '@/lib/firebaseAdmin'; // Import adminAuth

// Define the session cookie options
const SESSION_COOKIE_NAME = '__session'; // Or your preferred cookie name
const expiresIn = 60 * 60 * 24 * 5 * 1000; // 5 days in milliseconds

export async function POST(request: NextRequest) {
  try {
    const { idToken } = await request.json();

    if (!idToken) {
      return NextResponse.json({ error: 'ID token is required' }, { status: 400 });
    }

    // Verify the ID token first (optional but recommended for immediate feedback)
    // Note: createSessionCookie also implicitly verifies the token
    // await adminAuth.verifyIdToken(idToken);

    // Create the session cookie
    const sessionCookie = await adminAuth.createSessionCookie(idToken, { expiresIn });

    // Set cookie policy for session cookie.
    const options = {
      name: SESSION_COOKIE_NAME,
      value: sessionCookie,
      maxAge: expiresIn / 1000, // maxAge is in seconds
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production', // Use secure cookies in production
      path: '/', // Cookie available across the entire site
      sameSite: 'lax' as const, // Generally recommended for session cookies
    };

    // Set the cookie using the Next.js cookies() utility
    cookies().set(options);

    console.log(`Session cookie created for user.`); // Avoid logging sensitive info
    return NextResponse.json({ status: 'success' }, { status: 200 });

  } catch (error: any) {
    console.error('Error creating session cookie:', error);
    // Handle specific Firebase Admin errors if necessary
    // e.g., if (error.code === 'auth/id-token-expired') { ... }
    return NextResponse.json({ error: 'Failed to create session', details: error.message }, { status: 401 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const sessionCookie = cookies().get(SESSION_COOKIE_NAME)?.value;

    if (sessionCookie) {
      // Optionally, revoke the session on the server side using Admin SDK
      // This prevents the cookie from being used even if somehow stolen before expiry
      // try {
      //   const decodedClaims = await adminAuth.verifySessionCookie(sessionCookie, true /* checkRevoked */);
      //   await adminAuth.revokeRefreshTokens(decodedClaims.sub); // Revoke tokens for the user (sub is uid)
      //   console.log(`Revoked refresh tokens for user: ${decodedClaims.sub}`);
      // } catch (verifyError: any) {
      //   // Handle cases where cookie is invalid or already revoked - still clear the client cookie
      //   console.warn('Error verifying session cookie during logout/revocation:', verifyError.code);
      // }

      // Clear the cookie by setting its Max-Age to 0
      cookies().set({
        name: SESSION_COOKIE_NAME,
        value: '',
        maxAge: 0,
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        path: '/',
        sameSite: 'lax' as const,
      });

      console.log('Session cookie cleared.');
      return NextResponse.json({ status: 'success' }, { status: 200 });
    } else {
      // No cookie found, arguably still a success from client perspective
      return NextResponse.json({ status: 'success', message: 'No session cookie found.' }, { status: 200 });
    }

  } catch (error: any) {
    console.error('Error clearing session cookie:', error);
    return NextResponse.json({ error: 'Failed to clear session' }, { status: 500 });
  }
}
