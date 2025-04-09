import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import { getFirestore, enableIndexedDbPersistence, connectFirestoreEmulator, CACHE_SIZE_UNLIMITED } from "firebase/firestore";
import { getAuth, connectAuthEmulator } from "firebase/auth";
// Optionally import other Firebase services you need, e.g.:
// import { getFirestore } from "firebase/firestore";
// import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Initialize Firebase for SSR + SSG, prevents initializing more than once
let firebaseApp: FirebaseApp;
if (!getApps().length) {
  console.log("[Firebase] Initializing Firebase app");
  firebaseApp = initializeApp(firebaseConfig);
} else {
  console.log("[Firebase] Using existing Firebase app");
  firebaseApp = getApp();
}

// Export the initialized app
export { firebaseApp };

// Export other initialized services
export const db = getFirestore(firebaseApp);
export const auth = getAuth(firebaseApp);

// Enable offline persistence for Firestore (only in client)
if (typeof window !== 'undefined') {
  enableIndexedDbPersistence(db)
    .then(() => {
      console.log("[Firebase] Firestore persistence enabled successfully");
    })
    .catch((err) => {
      console.error("[Firebase] Error enabling Firestore persistence:", err);
      if (err.code === 'failed-precondition') {
        console.warn("[Firebase] Multiple tabs open, persistence can only be enabled in one tab at a time");
      } else if (err.code === 'unimplemented') {
        console.warn("[Firebase] The current browser doesn't support all of the features required to enable persistence");
      }
    });
}

// Connect to emulators in development mode if available
if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATORS === 'true') {
  if (typeof window !== 'undefined') {
    // Only connect to emulators on the client side
    connectFirestoreEmulator(db, 'localhost', 8080);
    connectAuthEmulator(auth, 'http://localhost:9099');
    console.log("[Firebase] Connected to Firebase emulators");
  }
}

// Optionally export other initialized services
// export const db = getFirestore(firebaseApp);
// export const auth = getAuth(firebaseApp);
