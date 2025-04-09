'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { User as FirebaseUser, onAuthStateChanged, signOut as firebaseSignOut, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendPasswordResetEmail, UserCredential } from 'firebase/auth';
import { doc, getDoc, setDoc, serverTimestamp, onSnapshot } from 'firebase/firestore';
import { auth, db } from '@/lib/firebase';
import { User, UserRole } from '@/types/user';
import { LoginFormData, SignupFormData, ResetPasswordFormData } from '@/types/forms';

// Define the shape of the context value
interface AuthContextType {
  currentUser: User | null;
  firebaseUser: FirebaseUser | null;
  loading: boolean;
  logout: () => Promise<void>;
  login: (data: LoginFormData) => Promise<UserCredential>;
  signup: (data: SignupFormData) => Promise<UserCredential>;
  resetPassword: (data: ResetPasswordFormData) => Promise<void>;
  // Add other auth methods later: resetPassword
}

// Create the context with a default undefined value to detect misuse
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Define the props for the provider component
interface AuthProviderProps {
  children: ReactNode;
}

// Create the provider component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [unsubscribeUserDoc, setUnsubscribeUserDoc] = useState<(() => void) | null>(null);

  // Clean up any existing listener when component unmounts or user changes
  useEffect(() => {
    return () => {
      if (unsubscribeUserDoc) {
        console.log("[AuthContext] Cleaning up Firestore user doc listener");
        unsubscribeUserDoc();
      }
    };
  }, [unsubscribeUserDoc]);

  useEffect(() => {
    console.log("[AuthContext] Setting up auth state change listener");

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      console.log("[AuthContext] Auth state changed:", user ? `User: ${user.uid}` : "No user");
      setFirebaseUser(user);

      // Clean up any existing Firestore listener when auth state changes
      if (unsubscribeUserDoc) {
        console.log("[AuthContext] Cleaning up previous user doc listener");
        unsubscribeUserDoc();
        setUnsubscribeUserDoc(null);
      }

      if (user) {
        const userDocRef = doc(db, 'users', user.uid);
        try {
          console.log("[AuthContext] Fetching user document from Firestore");
          const userDoc = await getDoc(userDocRef);

          if (userDoc.exists()) {
            console.log("[AuthContext] User document found in Firestore");
            setCurrentUser(userDoc.data() as User);

            // Set up a real-time listener for user document changes
            console.log("[AuthContext] Setting up real-time listener for user document");
            const unsub = onSnapshot(userDocRef, (doc) => {
              if (doc.exists()) {
                console.log("[AuthContext] User document updated in real-time");
                setCurrentUser(doc.data() as User);
              } else {
                console.warn("[AuthContext] User document no longer exists in real-time update");
                setCurrentUser(null);
              }
            }, (error) => {
              console.error("[AuthContext] Error in real-time user document listener:", error);
            });

            setUnsubscribeUserDoc(() => unsub);
          } else {
            console.warn("[AuthContext] Firestore user document not found for UID:", user.uid);
            console.log("[AuthContext] Creating new user document in Firestore");

            const newUser: Omit<User, 'createdAt'> = {
              uid: user.uid,
              email: user.email,
              displayName: user.displayName,
              role: 'user', // Default role
            };

            try {
              await setDoc(userDocRef, { ...newUser, createdAt: serverTimestamp() });
              console.log("[AuthContext] New user document created, fetching it");

              const newUserDoc = await getDoc(userDocRef); // Re-fetch after creation
              if (newUserDoc.exists()) {
                console.log("[AuthContext] New user document fetched successfully");
                setCurrentUser(newUserDoc.data() as User);

                // Set up a real-time listener for the newly created user document
                console.log("[AuthContext] Setting up real-time listener for new user document");
                const unsub = onSnapshot(userDocRef, (doc) => {
                  if (doc.exists()) {
                    console.log("[AuthContext] New user document updated in real-time");
                    setCurrentUser(doc.data() as User);
                  } else {
                    console.warn("[AuthContext] New user document no longer exists in real-time update");
                    setCurrentUser(null);
                  }
                }, (error) => {
                  console.error("[AuthContext] Error in real-time new user document listener:", error);
                });

                setUnsubscribeUserDoc(() => unsub);
              } else {
                console.error("[AuthContext] Failed to create and fetch Firestore user document");
                setCurrentUser(null); // Set to null if creation/fetch failed
              }
            } catch (createError) {
              console.error("[AuthContext] Error creating Firestore user document:", createError);
              setCurrentUser(null);
            }
          }
        } catch (fetchError) {
          console.error("[AuthContext] Error fetching Firestore user document:", fetchError);
          setCurrentUser(null);
        }
      } else {
        console.log("[AuthContext] No user found, setting currentUser to null");
        setCurrentUser(null);
      }

      setLoading(false);
      console.log("[AuthContext] Auth state loading complete");
    });

    return () => {
      console.log("[AuthContext] Cleaning up auth state change listener");
      unsubscribe();
    };
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      console.log("[AuthContext] Logout initiated");
      if (unsubscribeUserDoc) {
        console.log("[AuthContext] Cleaning up user doc listener before logout");
        unsubscribeUserDoc();
        setUnsubscribeUserDoc(null);
      }
      await firebaseSignOut(auth);
      console.log("[AuthContext] Firebase signOut complete");
      // State updates (currentUser=null, firebaseUser=null) are handled by onAuthStateChanged
    } catch (error) {
      console.error("[AuthContext] Error signing out: ", error);
      // Optionally handle logout errors (e.g., display a message)
      throw error; // Re-throw error for components to handle if needed
    }
  }, [unsubscribeUserDoc]);

  // Login function
  const login = useCallback(async ({ email, password }: LoginFormData) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      // State updates are handled by onAuthStateChanged listener
      return userCredential;
    } catch (error) {
      console.error("Error signing in: ", error);
      // Handle specific error codes if needed (e.g., wrong password, user not found)
      throw error; // Re-throw error for UI components to handle
    }
  }, []);

  // Signup function
  const signup = useCallback(async ({ email, password }: SignupFormData) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      // Firebase user created successfully.
      // The onAuthStateChanged listener will handle fetching/creating the Firestore document.
      return userCredential;
    } catch (error) {
      console.error("Error signing up: ", error);
      // Handle specific errors (e.g., email-already-in-use)
      throw error; // Re-throw error for UI components to handle
    }
  }, []);

  // Reset Password function
  const resetPassword = useCallback(async ({ email }: ResetPasswordFormData) => {
    try {
      await sendPasswordResetEmail(auth, email);
      // Usually, no immediate state change needed, UI might show a confirmation message
    } catch (error) {
      console.error("Error sending password reset email: ", error);
      // Handle specific errors (e.g., user not found)
      throw error; // Re-throw error for UI components to handle
    }
  }, []);

  const value = {
    currentUser,
    firebaseUser,
    loading,
    logout,
    login,
    signup,
    resetPassword,
    // resetPassword will go here
  };

  return (
    <AuthContext.Provider value={value}>
      {/* Render children unconditionally, let consumers handle loading state */}
      {children}
    </AuthContext.Provider>
  );
};

// Create a custom hook for using the auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
