'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import AuthGuard from '@/components/auth/AuthGuard';
import Link from 'next/link'; // Import Link
import axios from 'axios'; // Import axios for logout API call
import { useRouter } from 'next/navigation'; // For redirect after logout

const DashboardPage: React.FC = () => {
  const { currentUser, firebaseUser } = useAuth(); // Removed logout from here
  const router = useRouter();

  const handleLogout = async () => {
    try {
      // Call the server-side API route to clear the session cookie
      await axios.delete('/api/auth/session');
      // Client-side state updates are handled by onAuthStateChanged in AuthContext
      // which will trigger automatically after sign-out completes.
      // Optionally redirect after successful API call, though middleware should handle it.
      // router.push('/login');
      console.log('Logout initiated via API');
    } catch (error) {
      console.error('Failed to logout via API:', error);
      // Handle logout error (e.g., show a notification)
    }
  };

  // We rely on AuthGuard to handle loading and redirection if not authenticated
  // So, if we reach this point, currentUser should exist.

  return (
    <AuthGuard>
      {/* Wrap content with AuthGuard */}
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Dashboard</h1>

        {currentUser && (
          <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">User Information</h2>
            <p className="text-gray-700 dark:text-gray-300">
              <span className="font-medium">Email:</span> {currentUser.email || 'N/A'}
            </p>
            <p className="text-gray-700 dark:text-gray-300">
              <span className="font-medium">UID:</span> {currentUser.uid}
            </p>
            <p className="text-gray-700 dark:text-gray-300 capitalize">
              <span className="font-medium">Role:</span> {currentUser.role}
            </p>
            {/* Add display name, created date etc. if needed */}
            {/* <p>Display Name: {currentUser.displayName || 'N/A'}</p> */}
            {/* <p>Account Created: {currentUser.createdAt?.toDate().toLocaleDateString()}</p> */}

            {/* Conditionally render Admin Panel link */}
            {currentUser.role === 'admin' && (
              <div className="mt-4">
                <Link href="/admin" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
                  Go to Admin Panel
                </Link>
              </div>
            )}
          </div>
        )}

        <button
          onClick={handleLogout}
          className="rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
        >
          Sign Out
        </button>
      </div>
    </AuthGuard>
  );
};

export default DashboardPage;
