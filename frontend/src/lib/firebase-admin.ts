// This file is for server-side use only.
// It initializes the Firebase Admin SDK for use in server components and API routes.

// Firebase Admin SDK initialization
import admin from 'firebase-admin';
import { getApps } from 'firebase-admin/app';

// Create a mock/dummy implementation when environment variables aren't available
// This enables development without requiring the full Firebase Admin setup
class MockAdminAuth {
  async verifySessionCookie() {
    console.warn('Using mock Firebase Admin auth - session verification will always fail');
    return null; // Always return null to simulate an invalid/missing session
  }
}

// Check if we can initialize the real Admin SDK
const isDevelopment = process.env.NODE_ENV === 'development';
const hasServiceAccount =
  process.env.FIREBASE_PROJECT_ID &&
  process.env.FIREBASE_CLIENT_EMAIL &&
  process.env.FIREBASE_PRIVATE_KEY;

// Add some debug logging
console.log("Firebase Admin SDK Initialization Check:");
console.log("- Project ID available:", !!process.env.FIREBASE_PROJECT_ID);
console.log("- Client Email available:", !!process.env.FIREBASE_CLIENT_EMAIL);
console.log("- Private Key available:", !!process.env.FIREBASE_PRIVATE_KEY);
console.log("- Private Key empty:", process.env.FIREBASE_PRIVATE_KEY === '');

let adminAuth: admin.auth.Auth | MockAdminAuth;

// Only attempt to initialize Firebase Admin if we haven't already
if (!getApps().length) {
  // Try to get the private key from environment variables
  let privateKey = process.env.FIREBASE_PRIVATE_KEY;

  // Handle different formats of the private key
  if (privateKey) {
    // Remove quotes if they are wrapping the key
    if (privateKey.startsWith('"') && privateKey.endsWith('"')) {
      privateKey = privateKey.slice(1, -1);
    }
    // Replace literal \n with actual newlines if needed
    privateKey = privateKey.replace(/\\n/g, '\n');
  }

  const canInitializeAdmin =
    process.env.FIREBASE_PROJECT_ID &&
    process.env.FIREBASE_CLIENT_EMAIL &&
    privateKey &&
    privateKey !== '';

  if (canInitializeAdmin) {
    try {
      // Initialize with real service account credentials
      admin.initializeApp({
        credential: admin.credential.cert({
          projectId: process.env.FIREBASE_PROJECT_ID as string,
          clientEmail: process.env.FIREBASE_CLIENT_EMAIL as string,
          privateKey: privateKey,
        }),
      });
      console.log('Firebase Admin SDK Initialized with real credentials');
      adminAuth = admin.auth();
    } catch (error: any) {
      console.error('Firebase Admin initialization error:', error.message);
      adminAuth = new MockAdminAuth(); // Fallback to mock
    }
  } else {
    // Use mock implementation when credentials are missing
    console.warn(
      'Firebase Admin SDK not initialized: Missing environment variables. Using mock implementation.'
    );
    adminAuth = new MockAdminAuth();
  }
} else {
  // Firebase Admin SDK already initialized
  adminAuth = admin.auth();
}

export { adminAuth };
export default admin;
