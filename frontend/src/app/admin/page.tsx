'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import AuthGuard from '@/components/auth/AuthGuard';
import Link from 'next/link';

// TODO: Implement User Management features (List, Role Change, Delete)

const AdminPage: React.FC = () => {
  const { currentUser } = useAuth();

  return (
    <AuthGuard requiredRole="admin">
      {/* Require admin role */}
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Admin Panel</h1>

            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200">Welcome, Admin!</h2>
                {currentUser && (
                    <p className="text-gray-700 dark:text-gray-300">
                        Your UID: {currentUser.uid}
                    </p>
                )}
                 <p className="mt-4 text-gray-700 dark:text-gray-300">
                   User management features (listing, role changes, deletion) will be implemented here.
                 </p>
            </div>

             <Link href="/dashboard" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
                Return to Dashboard
             </Link>
        </div>
    </AuthGuard>
  );
};

export default AdminPage;
