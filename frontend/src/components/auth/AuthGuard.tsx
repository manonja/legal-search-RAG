'use client';

import React, { ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { UserRole } from '@/types/user';

interface AuthGuardProps {
  children: ReactNode;
  requiredRole?: UserRole; // Optional: Specify 'admin' if admin access is needed
  // Optional: Customize redirect paths or loading component
  // loginPath?: string;
  // unauthorizedPath?: string;
  // LoadingComponent?: React.ComponentType;
}

const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  requiredRole,
  // loginPath = '/login',
  // unauthorizedPath = '/dashboard', // Or a specific unauthorized page
  // LoadingComponent = () => <div>Loading auth state...</div>, // Default loading
}) => {
  const { currentUser, loading } = useAuth();
  const router = useRouter();

  // 1. Handle Loading State
  if (loading) {
    // Use the LoadingComponent or a default placeholder
    // return <LoadingComponent />;
    return (
      <div className="flex justify-center items-center min-h-[200px]">
        <p className="text-gray-500 dark:text-gray-400">Checking authentication...</p>
      </div>
    );
  }

  // 2. Handle Not Authenticated
  if (!currentUser) {
    // Redirect to login page. The middleware often handles this for initial page loads,
    // but this client-side check is useful for dynamic route changes or components
    // mounted after initial load where middleware might not re-run.
    console.log('AuthGuard: Not authenticated, redirecting...');
    // In a real app, consider adding the current path as a redirect query param
    // so the user can be sent back after login.
    router.replace('/login'); // Use replace to avoid adding login to history
    return null; // Render nothing while redirecting
  }

  // 3. Handle Role Check (if required)
  if (requiredRole && currentUser.role !== requiredRole) {
    console.log(`AuthGuard: Role mismatch (required: ${requiredRole}, user: ${currentUser.role}), redirecting...`);
    // Redirect if user doesn't have the required role
    router.replace('/dashboard'); // Redirect to a default authorized page
    return null; // Render nothing while redirecting
  }

  // 4. User is authenticated and has the required role (if specified)
  return <>{children}</>; // Render the protected content
};

export default AuthGuard;
